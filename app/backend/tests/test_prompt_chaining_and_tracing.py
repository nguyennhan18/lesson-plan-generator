"""Bộ kiểm thử toàn diện cho kiến trúc Role-Based Prompt Chaining & Langfuse v5 Observability."""

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from lessonai.llm import tracing
from lessonai.schemas.chain_schemas import (
    ActivityBlueprintItem,
    LessonActivitiesPayload,
    LessonBlueprintSchema,
    LessonRepairPayload,
    SlideNarrativeDeckSchema,
    SlideNarrativeItem,
    SlideRepairBatchSchema,
    SlideVisualQuizBatchSchema,
    SlideVisualQuizItem,
)
from lessonai.schemas.schemas import (
    ExecutionSteps,
    LessonActivity,
    LessonPlanSchema,
    OutlineSlideItem,
)
from lessonai.schemas.slide_schema import (
    ChartSpec,
    ChartType,
    ClassProficiency,
    QuizOptionDetail,
    SlideDeckSchema,
    SlideLayout,
    SlideSchema,
    SlideType,
    ThemeType,
)
from lessonai.services.generation import (
    generate_lesson_plan,
    generate_presentation_outline,
    generate_slide_deck,
)


class FakeLangfuseObservation:
    def __init__(self, record: Dict[str, Any]):
        self.record = record

    def update(self, **kwargs: Any) -> "FakeLangfuseObservation":
        self.record.setdefault("updates", []).append(kwargs)
        if "output" in kwargs:
            self.record["output"] = kwargs["output"]
        if "usage_details" in kwargs:
            self.record["usage_details"] = kwargs["usage_details"]
        if "level" in kwargs:
            self.record["level"] = kwargs["level"]
        return self

    def end(self) -> None:
        self.record["ended"] = True


class FakeLangfuseClient:
    def __init__(self):
        self.observations: List[Dict[str, Any]] = []
        self.scores: List[Dict[str, Any]] = []

    @contextmanager
    def start_as_current_observation(self, **kwargs: Any):
        rec = dict(kwargs)
        self.observations.append(rec)
        obs = FakeLangfuseObservation(rec)
        yield obs

    def start_observation(self, **kwargs: Any) -> FakeLangfuseObservation:
        rec = dict(kwargs)
        self.observations.append(rec)
        return FakeLangfuseObservation(rec)

    def score_current_trace(self, **kwargs: Any) -> None:
        self.scores.append(dict(kwargs))

    def flush(self) -> None:
        pass


def _make_valid_activities(minutes=(5, 15, 15, 10), include_5512_keywords: bool = True) -> List[LessonActivity]:
    labels = {
        1: "Hoạt động 1 (Khởi động): ",
        2: "Hoạt động 2 (Hình thành kiến thức): ",
        3: "Hoạt động 3 (Luyện tập): ",
        4: "Hoạt động 4 (Vận dụng): ",
    }
    return [
        LessonActivity(
            activity_number=idx,
            time_minutes=m,
            goal=(
                f"{labels[idx] if include_5512_keywords else ''}Mục tiêu chi tiết của hoạt động {idx} "
                "về khảo sát sự biến thiên và cực trị của hàm số."
            ),
            expected_product=f"Học sinh trình bày đầy đủ bảng xét dấu đạo hàm và lời giải hoạt động {idx}.",
            execution=ExecutionSteps(
                step_1_assign=f"Giáo viên chuyển giao nhiệm vụ học tập số {idx} kèm phiếu học tập cho các nhóm.",
                step_2_excute=f"Học sinh thảo luận nhóm, tính đạo hàm y' và lập bảng biến thiên cho hoạt động {idx}.",
                step_3_report=f"Đại diện nhóm trình bày lời giải hoạt động {idx}; các nhóm khác nhận xét chéo.",
                step_4_conclusion=f"Giáo viên nhận xét, chính xác hóa định lý và chốt kiến thức trọng tâm mục {idx}.",
            ),
        )
        for idx, m in enumerate(minutes, 1)
    ]


def _make_sample_blueprint() -> LessonBlueprintSchema:
    return LessonBlueprintSchema(
        lesson_title="Bài 1: Tính đơn điệu và cực trị của hàm số (Role Architect)",
        subject="Toán học",
        grade=12,
        knowledge_goals=["Nhận biết tính đồng biến, nghịch biến và điểm cực trị của hàm số qua dấu đạo hàm."],
        competency_goals=["Năng lực tư duy và lập luận toán học; năng lực giải quyết vấn đề toán học."],
        skills_goals=["Lập bảng biến thiên và tìm điểm cực đại, cực tiểu của hàm số."],
        character_goals=["Chăm chỉ, trung thực và trách nhiệm khi thực hiện nhiệm vụ nhóm."],
        teaching_equipment=["GV: Kế hoạch bài dạy 5512, Slide tương tác.", "HS: SGK Toán 12, máy tính cầm tay."],
        activity_blueprints=[
            ActivityBlueprintItem(
                activity_number=i,
                title=f"Hoạt động {i}",
                time_minutes=m,
                objective_summary=f"Mục tiêu hoạt động {i}",
                core_task_outline=f"Nhiệm vụ trọng tâm {i}",
            )
            for i, m in enumerate((5, 15, 15, 10), 1)
        ],
    )


def test_lesson_plan_role_chain_happy_path_and_outline_forwarding(monkeypatch):
    """Kiểm tra chuỗi Giáo án chạy tuần tự Vai trò 1 (Architect) -> Vai trò 2 (Activity Author) và nhận Dàn ý Trạm 2."""
    called_roles: List[str] = []
    captured_prompts: List[str] = []

    def mock_generate_structured(prompt, system_prompt, response_schema, task_type="lesson_plan", **kwargs):
        called_roles.append(kwargs.get("role_name"))
        captured_prompts.append(prompt)
        if response_schema is LessonBlueprintSchema:
            return _make_sample_blueprint()
        if response_schema is LessonActivitiesPayload:
            return LessonActivitiesPayload(activities=_make_valid_activities())
        raise AssertionError(f"Unexpected schema: {response_schema}")

    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

    outline_slides = [
        OutlineSlideItem(
            id="outline-slide-1",
            slide_index=1,
            title="Khởi động: Tàu lượn siêu tốc và đạo hàm",
            activity_type="Khởi động",
            visual_type="2D Function Plot",
            bullet_points=["Quan sát độ dốc đường ray theo đạo hàm f'(x)"],
        )
    ]

    plan, val_result = generate_lesson_plan(
        topic="Tính đơn điệu và cực trị của hàm số",
        subject="Toán học",
        grade=12,
        lesson_id="M12-C1-B1",
        outline_slides=outline_slides,
        session_id="session-test-001",
    )

    assert called_roles == ["role.pedagogical_architect", "role.lesson_activity_author"]
    assert all("Tàu lượn siêu tốc và đạo hàm" in p for p in captured_prompts)
    assert val_result.is_valid is True
    assert plan.lesson_title == "Bài 1: Tính đơn điệu và cực trị của hàm số (Role Architect)"
    assert len(plan.activities) == 4
    assert sum(a.time_minutes for a in plan.activities) == 45


def test_lesson_plan_conditional_role3_repair_triggered_on_gate2_failure(monkeypatch):
    """Kiểm tra Vai trò 3 (`role.lesson_repair_reviewer`) chỉ chạy khi Gate 2 phát hiện lỗi 5512."""
    called_roles: List[str] = []

    def mock_generate_structured(prompt, system_prompt, response_schema, task_type="lesson_plan", **kwargs):
        called_roles.append(kwargs.get("role_name"))
        if response_schema is LessonBlueprintSchema:
            return _make_sample_blueprint()
        if response_schema is LessonActivitiesPayload:
            # Cố tình trả về thiếu từ khóa chuẩn 5512 trong goal để kích hoạt Gate 2 -> Role 3
            return LessonActivitiesPayload(activities=_make_valid_activities(include_5512_keywords=False))
        if response_schema is LessonRepairPayload:
            return LessonRepairPayload(patched_activities=_make_valid_activities(include_5512_keywords=True))
        raise AssertionError(f"Unexpected schema: {response_schema}")

    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

    plan, val_result = generate_lesson_plan(
        topic="Tính đơn điệu và cực trị của hàm số",
        subject="Toán học",
        grade=12,
        lesson_id="M12-C1-B1",
        max_retries=1,
    )

    assert called_roles == [
        "role.pedagogical_architect",
        "role.lesson_activity_author",
        "role.lesson_repair_reviewer",
    ]
    assert val_result.is_valid is True
    assert sum(a.time_minutes for a in plan.activities) == 45


def test_lesson_plan_partial_fallback_preserves_role1_blueprint(monkeypatch):
    """Khi Vai trò 1 thành công nhưng Vai trò 2 hết quota, hệ thống phải giữ nguyên mục tiêu của Vai trò 1."""
    def mock_generate_structured(prompt, system_prompt, response_schema, task_type="lesson_plan", **kwargs):
        if response_schema is LessonBlueprintSchema:
            bp = _make_sample_blueprint()
            bp.knowledge_goals = ["Mục tiêu độc quyền từ Kiến trúc sư Sư phạm Vai trò 1"]
            return bp
        if response_schema is LessonActivitiesPayload:
            raise RuntimeError("429 Quota limit reached on Role 2")
        raise AssertionError(f"Unexpected schema: {response_schema}")

    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

    plan, val_result = generate_lesson_plan(
        topic="Tính đơn điệu và cực trị của hàm số",
        subject="Toán học",
        grade=12,
        lesson_id="M12-C1-B1",
    )

    assert plan.knowledge_goals == ["Mục tiêu độc quyền từ Kiến trúc sư Sư phạm Vai trò 1"]
    assert len(plan.activities) == 4
    assert any("Partial Fallback" in w for w in val_result.warnings)


def test_slide_deck_role_chain_and_targeted_repair(monkeypatch):
    """
    Kiểm tra chuỗi Slide chạy tuần tự:
      Vai trò 1 (`role.slide_narrative_designer`)
      -> Vai trò 2 (`role.visual_and_quiz_specialist`)
      -> Gate 3 phát hiện công thức sai định lý SGK (\\Delta = b^2 + 4ac)
      -> Vai trò 3 (`role.slide_repair_reviewer`) chỉ nhận đúng slide bị lỗi để vá!
    """
    called_roles: List[str] = []
    repair_prompt_captured: List[str] = []

    def mock_generate_structured(prompt, system_prompt, response_schema, task_type="slide", **kwargs):
        called_roles.append(kwargs.get("role_name"))
        if response_schema is SlideNarrativeDeckSchema:
            return SlideNarrativeDeckSchema(
                presentation_title="Phương trình bậc hai và đồ thị Parabol",
                subject="Toán học",
                grade=10,
                theme=ThemeType.MATH_ACADEMIC,
                slides=[
                    SlideNarrativeItem(
                        slide_index=1,
                        type=SlideType.CONCEPT_SLIDE,
                        layout=SlideLayout.CONCEPT_HIGHLIGHT,
                        title="Slide 1: Công thức nghiệm bậc hai",
                        bullet_points=["Xét phương trình $ax^2 + bx + c = 0$ ($a \\neq 0$)."],
                        # Cố tình cài lỗi sai dấu biệt thức Delta (\Delta = b^2 + 4ac) để Gate 3 bắt lỗi!
                        main_definition_latex=r"\Delta = b^2 + 4ac",
                        teacher_note="GV nhấn mạnh dấu của biệt thức Delta.",
                        needs_chart=False,
                        needs_quiz=False,
                    ),
                    SlideNarrativeItem(
                        slide_index=2,
                        type=SlideType.CONCEPT_SLIDE,
                        layout=SlideLayout.IMAGE_TEXT,
                        title="Slide 2: Đồ thị Parabol",
                        bullet_points=["Giao điểm của Parabol $y = x^2 - 4$ với trục hoành $Ox$."],
                        teacher_note="Quan sát 2 giao điểm tại $x = -2$ và $x = 2$.",
                        needs_chart=True,
                        visual_hint="Vẽ đồ thị hàm số y = x**2 - 4",
                    ),
                    SlideNarrativeItem(
                        slide_index=3,
                        type=SlideType.EXERCISE_SLIDE,
                        layout=SlideLayout.QUIZ_OPTION,
                        title="Slide 3: Câu hỏi trắc nghiệm nhanh",
                        bullet_points=["Tìm nghiệm của phương trình $x^2 - 4 = 0$."],
                        needs_quiz=True,
                    ),
                ],
            )
        if response_schema is SlideVisualQuizBatchSchema:
            return SlideVisualQuizBatchSchema(
                items=[
                    SlideVisualQuizItem(
                        slide_index=2,
                        chart_spec=ChartSpec(
                            kind=ChartType.FUNCTION_PLOT,
                            expression="x**2 - 4",
                            x_min=-4.0,
                            x_max=4.0,
                            y_min=-5.0,
                            y_max=5.0,
                            chart_title="Đồ thị y = x² - 4",
                        ),
                    ),
                    SlideVisualQuizItem(
                        slide_index=3,
                        quiz_options=[
                            QuizOptionDetail(label="A", text="$x = \\pm 2$", is_correct=True),
                            QuizOptionDetail(
                                label="B",
                                text="$x = 4$",
                                is_correct=False,
                                distractor_rationale="Quên khai căn bậc hai của 4.",
                            ),
                            QuizOptionDetail(
                                label="C",
                                text="$x = 2$",
                                is_correct=False,
                                distractor_rationale="Thiếu nghiệm âm $x = -2$ khi khai căn.",
                            ),
                            QuizOptionDetail(
                                label="D",
                                text="Vô nghiệm",
                                is_correct=False,
                                distractor_rationale="Nhầm dấu $x^2 = -4$ với $x^2 = 4$.",
                            ),
                        ],
                    ),
                ]
            )
        if response_schema is SlideRepairBatchSchema:
            repair_prompt_captured.append(prompt)
            return SlideRepairBatchSchema(
                patched_slides=[
                    SlideSchema(
                        slide_index=1,
                        type=SlideType.CONCEPT_SLIDE,
                        layout=SlideLayout.CONCEPT_HIGHLIGHT,
                        title="Slide 1: Công thức nghiệm bậc hai (Đã hiệu đính SGK)",
                        bullet_points=["Xét phương trình $ax^2 + bx + c = 0$ ($a \\neq 0$)."],
                        main_definition_latex=r"\Delta = b^2 - 4ac",
                        teacher_note="GV nhấn mạnh dấu trừ trong biệt thức Delta chuẩn SGK.",
                    )
                ]
            )
        raise AssertionError(f"Unexpected schema: {response_schema}")

    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

    deck = generate_slide_deck(
        topic="Phương trình bậc hai một ẩn",
        subject="Toán học",
        grade=10,
        use_rag=False,
        class_proficiency=ClassProficiency.STANDARD,
        session_id="session-test-slide-001",
    )

    assert called_roles == [
        "role.slide_narrative_designer",
        "role.visual_and_quiz_specialist",
        "role.slide_repair_reviewer",
    ]
    assert len(repair_prompt_captured) == 1
    assert "b^2 + 4ac" in repair_prompt_captured[0]
    assert deck.slides[0].main_definition_latex == r"\Delta = b^2 - 4ac"
    assert deck.slides[1].chart_spec is not None
    assert deck.slides[1].chart_spec.expression == "x**2 - 4"
    assert len(deck.slides[2].quiz_options) == 4


def test_slide_deck_partial_fallback_preserves_role1_narrative(monkeypatch):
    """Khi Vai trò 1 của Slide thành công nhưng Vai trò 2 hết quota, phải bảo toàn kịch bản của Vai trò 1."""
    def mock_generate_structured(prompt, system_prompt, response_schema, task_type="slide", **kwargs):
        if response_schema is SlideNarrativeDeckSchema:
            return SlideNarrativeDeckSchema(
                presentation_title="Bộ Slide Độc Quyền Từ Vai Trò 1",
                subject="Toán học",
                grade=12,
                theme=ThemeType.MATH_ACADEMIC,
                slides=[
                    SlideNarrativeItem(
                        slide_index=1,
                        type=SlideType.WARM_UP_SLIDE,
                        layout=SlideLayout.SINGLE_COLUMN,
                        title="Slide 1: Tình huống khởi động độc quyền từ Role 1",
                        bullet_points=["Ý chính 1 từ Role 1"],
                    ),
                    SlideNarrativeItem(
                        slide_index=2,
                        type=SlideType.EXERCISE_SLIDE,
                        layout=SlideLayout.QUIZ_OPTION,
                        title="Slide 2: Trắc nghiệm cần bù từ Partial Fallback",
                        bullet_points=["Câu hỏi trắc nghiệm từ Role 1"],
                        needs_quiz=True,
                    ),
                ],
            )
        if response_schema is SlideVisualQuizBatchSchema:
            raise RuntimeError("429 Quota Exceeded on Visual & Quiz Specialist")
        raise AssertionError(f"Unexpected schema: {response_schema}")

    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

    deck = generate_slide_deck(
        topic="Tính đơn điệu và cực trị của hàm số",
        subject="Toán học",
        grade=12,
        lesson_id="M12-C1-B1",
    )

    assert deck.presentation_title == "Bộ Slide Độc Quyền Từ Vai Trò 1"
    assert deck.slides[0].title == "Slide 1: Tình huống khởi động độc quyền từ Role 1"
    assert deck.slides[1].layout == SlideLayout.QUIZ_OPTION
    assert len(deck.slides[1].quiz_options) == 4



def test_langfuse_full_observability_tree_and_token_usage(monkeypatch):
    """
    Kiểm tra cây quan sát Langfuse v5 ghi nhận đầy đủ:
      - `chain` (kèm session_id)
      - `retriever`
      - `agent` (kèm prompt_name & prompt_version)
      - `evaluator`
      - `scores` (blueprint_5512_valid, cv5512_valid, fallback_used...)
    và hàm `extract_usage_details` đọc đúng token usage từ Google GenAI & Groq/OpenRouter.
    """
    fake_client = FakeLangfuseClient()
    tracing.set_client_for_testing(fake_client)
    try:
        def mock_generate_structured(prompt, system_prompt, response_schema, task_type="lesson_plan", **kwargs):
            # Giả lập cả observation generation giống như bên trong LLMGateway
            gen = tracing.start_generation(
                name=kwargs.get("role_name") or task_type,
                provider="google",
                model="gemini-2.0-flash",
                system_prompt=system_prompt,
                prompt=prompt,
                temperature=0.7,
                role_name=kwargs.get("role_name"),
                prompt_name=kwargs.get("prompt_name"),
                prompt_version=kwargs.get("prompt_version"),
            )
            fake_google_res = SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=420,
                    candidates_token_count=310,
                    total_token_count=730,
                )
            )
            gen.finish(
                output="{\"ok\": true}",
                usage_details=tracing.extract_usage_details(fake_google_res, "google"),
            )
            if response_schema is LessonBlueprintSchema:
                return _make_sample_blueprint()
            if response_schema is LessonActivitiesPayload:
                return LessonActivitiesPayload(activities=_make_valid_activities())
            raise AssertionError(f"Unexpected schema: {response_schema}")

        monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", mock_generate_structured)

        outline_res = generate_presentation_outline(
            topic="Tính đơn điệu và cực trị của hàm số",
            lesson_id="M12-C1-B1",
            session_id="session-langfuse-999",
        )
        assert outline_res.session_id == "session-langfuse-999"

        plan, val_result = generate_lesson_plan(
            topic="Tính đơn điệu và cực trị của hàm số",
            lesson_id="M12-C1-B1",
            session_id="session-langfuse-999",
        )
        assert val_result.is_valid is True

        obs_types = [o.get("as_type") for o in fake_client.observations]
        obs_names = [o.get("name") for o in fake_client.observations]

        assert "chain" in obs_types
        assert "retriever" in obs_types
        assert "agent" in obs_types
        assert "generation" in obs_types
        assert "evaluator" in obs_types

        assert "chain.lesson_plan_generation" in obs_names
        assert "rag.lesson_plan_context" in obs_names
        assert "role.pedagogical_architect" in obs_names
        assert "gate.blueprint_5512" in obs_names
        assert "role.lesson_activity_author" in obs_names
        assert "gate.validate_5512" in obs_names

        generations = [o for o in fake_client.observations if o.get("as_type") == "generation"]
        assert len(generations) >= 2
        assert generations[-1].get("usage_details") == {"input": 420, "output": 310, "total": 730}
        assert generations[-1].get("version") == "v1.0"

        score_names = {s["name"] for s in fake_client.scores}
        assert {"blueprint_5512_valid", "cv5512_valid", "repair_triggered", "fallback_used"}.issubset(score_names)

        # Kiểm tra thêm extract_usage_details cho chuẩn OpenAI/Groq/OpenRouter
        fake_openai_res = SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=150, completion_tokens=250, total_tokens=400)
        )
        assert tracing.extract_usage_details(fake_openai_res, "groq") == {
            "input": 150,
            "output": 250,
            "total": 400,
        }
    finally:
        tracing.set_client_for_testing(None)
