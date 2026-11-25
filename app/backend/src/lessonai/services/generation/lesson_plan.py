import copy
import json
from typing import Any, List, Optional

from lessonai.llm import tracing
from lessonai.llm.gateway import llm_gateway
from lessonai.prompts.lesson_plan import SYSTEM_PROMPT  # Giữ tương thích ngược cho các import cũ
from lessonai.prompts.roles import (
    LESSON_ACTIVITY_AUTHOR_PROMPT,
    LESSON_REPAIR_REVIEWER_PROMPT,
    PEDAGOGICAL_ARCHITECT_PROMPT,
)
from lessonai.schemas.chain_schemas import (
    ActivityBlueprintItem,
    LessonActivitiesPayload,
    LessonBlueprintSchema,
    LessonRepairPayload,
)
from lessonai.schemas.schemas import LessonActivity, LessonPlanSchema
from lessonai.services.validation import ValidationResult, validate_5512_lesson_plan

_DEFAULT_ACTIVITY_TITLES = {
    1: "Hoạt động 1: Khởi động (Mở đầu)",
    2: "Hoạt động 2: Hình thành kiến thức mới",
    3: "Hoạt động 3: Luyện tập",
    4: "Hoạt động 4: Vận dụng",
}
_DEFAULT_ACTIVITY_MINUTES = {1: 5, 2: 15, 3: 15, 4: 10}


def _coerce_to_blueprint(
    raw_obj: Any,
    topic: str,
    subject: str,
    grade: int,
) -> tuple[LessonBlueprintSchema, Optional[LessonPlanSchema]]:
    if isinstance(raw_obj, LessonBlueprintSchema):
        return raw_obj, None

    if isinstance(raw_obj, LessonPlanSchema):
        blueprints = [
            ActivityBlueprintItem(
                activity_number=act.activity_number,
                title=_DEFAULT_ACTIVITY_TITLES.get(act.activity_number, f"Hoạt động {act.activity_number}"),
                time_minutes=act.time_minutes,
                objective_summary=act.goal,
                core_task_outline=act.expected_product,
            )
            for act in (raw_obj.activities or [])
        ]
        bp = LessonBlueprintSchema(
            generation_metadata=getattr(raw_obj, "generation_metadata", None),
            lesson_title=raw_obj.lesson_title or topic,
            subject=raw_obj.subject or subject,
            grade=raw_obj.grade or grade,
            knowledge_goals=list(raw_obj.knowledge_goals or []),
            competency_goals=list(raw_obj.competency_goals or []),
            skills_goals=list(raw_obj.skills_goals or []),
            character_goals=list(raw_obj.character_goals or []),
            teaching_equipment=list(raw_obj.teaching_equipment or []),
            activity_blueprints=blueprints,
        )
        return bp, raw_obj

    raise TypeError(f"Đầu ra Vai trò 1 không thuộc LessonBlueprintSchema: {type(raw_obj).__name__}")


def _validate_and_normalize_blueprint(
    blueprint: LessonBlueprintSchema,
    topic: str,
    subject: str,
    grade: int,
) -> tuple[LessonBlueprintSchema, bool, List[str]]:
    """Gate 1 (`gate.blueprint_5512`): Kiểm định khung mục tiêu và phân bổ 4 hoạt động 45 phút."""
    issues: List[str] = []

    if not blueprint.lesson_title or not blueprint.lesson_title.strip():
        blueprint.lesson_title = topic
    blueprint.subject = blueprint.subject or subject
    blueprint.grade = blueprint.grade or grade

    if not blueprint.knowledge_goals:
        issues.append("Blueprint thiếu knowledge_goals")
        blueprint.knowledge_goals = [f"Nắm vững định nghĩa, định lý và phương pháp giải bài toán thuộc chủ đề {topic}."]
    if not blueprint.competency_goals:
        issues.append("Blueprint thiếu competency_goals")
        blueprint.competency_goals = [f"Phát triển năng lực tư duy và lập luận toán học qua bài {topic}."]
    if not blueprint.skills_goals:
        blueprint.skills_goals = [f"Vận dụng công thức và quy trình giải toán cho chủ đề {topic}."]
    if not blueprint.character_goals:
        issues.append("Blueprint thiếu character_goals")
        blueprint.character_goals = ["Chăm chỉ, trung thực và trách nhiệm trong hoạt động học tập."]
    if not blueprint.teaching_equipment:
        blueprint.teaching_equipment = [
            "Giáo viên: Kế hoạch bài dạy 5512, bộ Slide trình chiếu, SGK Toán.",
            "Học sinh: SGK, vở ghi, máy tính cầm tay.",
        ]

    by_num = {
        item.activity_number: item
        for item in (blueprint.activity_blueprints or [])
        if 1 <= item.activity_number <= 4
    }
    normalized_items: List[ActivityBlueprintItem] = []
    for num in (1, 2, 3, 4):
        if num in by_num:
            item = by_num[num]
            if not item.title:
                item.title = _DEFAULT_ACTIVITY_TITLES[num]
            if item.time_minutes <= 0:
                item.time_minutes = _DEFAULT_ACTIVITY_MINUTES[num]
            normalized_items.append(item)
        else:
            issues.append(f"Blueprint thiếu hoạt động {num}")
            normalized_items.append(
                ActivityBlueprintItem(
                    activity_number=num,
                    title=_DEFAULT_ACTIVITY_TITLES[num],
                    time_minutes=_DEFAULT_ACTIVITY_MINUTES[num],
                    objective_summary=f"Thực hiện mục tiêu {_DEFAULT_ACTIVITY_TITLES[num]} cho bài {topic}.",
                    core_task_outline=f"Hoàn thành nhiệm vụ học tập phần {num}.",
                )
            )

    total_minutes = sum(i.time_minutes for i in normalized_items)
    raw_is_valid = len(issues) == 0 and total_minutes == 45
    if total_minutes != 45:
        issues.append(f"Tổng thời lượng Blueprint = {total_minutes} phút (khác 45 phút), chuẩn hóa về 45 phút.")
        for item in normalized_items:
            item.time_minutes = _DEFAULT_ACTIVITY_MINUTES[item.activity_number]

    blueprint.activity_blueprints = normalized_items
    return blueprint, raw_is_valid, issues


def _assemble_plan(
    blueprint: LessonBlueprintSchema,
    activities: List[LessonActivity],
    generation_metadata: Any = None,
) -> LessonPlanSchema:
    plan = LessonPlanSchema(
        lesson_title=blueprint.lesson_title,
        subject=blueprint.subject,
        grade=blueprint.grade,
        knowledge_goals=blueprint.knowledge_goals,
        competency_goals=blueprint.competency_goals,
        skills_goals=blueprint.skills_goals,
        character_goals=blueprint.character_goals,
        teaching_equipment=blueprint.teaching_equipment,
        activities=activities,
    )
    meta = generation_metadata or getattr(blueprint, "generation_metadata", None)
    if meta is not None:
        plan.generation_metadata = meta
    return plan


def _apply_repair_payload(plan: LessonPlanSchema, repair_res: Any) -> LessonPlanSchema:
    if isinstance(repair_res, LessonPlanSchema):
        return repair_res
    if isinstance(repair_res, LessonRepairPayload):
        if repair_res.knowledge_goals:
            plan.knowledge_goals = repair_res.knowledge_goals
        if repair_res.competency_goals:
            plan.competency_goals = repair_res.competency_goals
        if repair_res.character_goals:
            plan.character_goals = repair_res.character_goals
        if repair_res.patched_activities:
            patched_map = {a.activity_number: a for a in repair_res.patched_activities}
            existing_map = {a.activity_number: a for a in plan.activities}
            merged: List[LessonActivity] = []
            for num in (1, 2, 3, 4):
                if num in patched_map:
                    merged.append(patched_map[num])
                elif num in existing_map:
                    merged.append(existing_map[num])
            plan.activities = merged if len(merged) == 4 else repair_res.patched_activities
        if getattr(repair_res, "generation_metadata", None) is not None:
            plan.generation_metadata = repair_res.generation_metadata
    return plan


def generate_lesson_plan(
    topic: str,
    subject: str = "Toán học",
    grade: int = 12,
    lesson_id: Optional[str] = None,
    use_rag: bool = False,  # Retained for older API callers; generation does not use RAG.
    proficiency: str = "standard",
    max_retries: int = 2,
    approved_outline: Optional[dict] = None,
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> tuple[LessonPlanSchema, ValidationResult]:
    """
    Soạn giáo án Công văn 5512 theo kiến trúc Role-Based Prompt Chaining trên `feature/ban-lam-viec`:
      - Step 1 [agent]     : `role.pedagogical_architect` -> `LessonBlueprintSchema`
      - Gate 1 [evaluator] : `gate.blueprint_5512`
      - Step 2 [agent]     : `role.lesson_activity_author` -> `LessonActivitiesPayload`
      - Gate 2 [evaluator] : `gate.validate_5512_and_outline` (`validate_plan_outline` + `validate_5512_lesson_plan`)
      - Step 3 [agent]     : `role.lesson_repair_reviewer` (có điều kiện khi Gate 2 báo lỗi)
    Tuân thủ nghiêm ngặt ADR 0001 (Zero-Fallback: không bao giờ chèn giáo án mẫu).
    """
    resolved_lid = lesson_id
    if not resolved_lid and grade == 12 and "toán" in subject.lower():
        try:
            from lessonai.rag.curriculum_registry import infer_lesson_id

            resolved_lid = infer_lesson_id(topic)
        except Exception:
            resolved_lid = None

    with tracing.trace_chain(
        "chain.lesson_plan_generation",
        session_id=session_id,
        lesson_id=resolved_lid,
        topic=topic,
        proficiency=proficiency,
        input_data={
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "lesson_id": resolved_lid,
            "proficiency": proficiency,
            "has_approved_outline": approved_outline is not None,
        },
    ) as chain_obs:
        outline_instruction = ""
        if approved_outline:
            outline_instruction = (
                "\nDàn ý giáo viên đã duyệt: giữ nguyên văn tiêu đề, các ý, math_focus theo thứ tự trong goal "
                "hoặc execution của đúng hoạt động 1 khởi động, 2 hình thành kiến thức, 3 luyện tập, "
                "4 vận dụng/tổng kết. Không bỏ nội dung:\n"
                + json.dumps(approved_outline, ensure_ascii=False)
            )

        last_successful_plan: Optional[LessonPlanSchema] = None
        last_validation_result: Optional[ValidationResult] = None

        try:
            # ================= STEP 1: VAI TRÒ 1 - KIẾN TRÚC SƯ SƯ PHẠM =================
            architect_prompt = (
                f"Hãy thiết kế Khung Sư Phạm Tổng Thể (LessonBlueprintSchema) chuẩn Công văn 5512 cho bài dạy: "
                f"'{topic}', Môn {subject}, Lớp {grade} (Trình độ '{proficiency}').\n"
                "YÊU CẦU BẮT BUỘC:\n"
                "1. Đề xuất đầy đủ knowledge_goals, competency_goals, skills_goals, character_goals, teaching_equipment.\n"
                "2. Mảng `activity_blueprints` phải có ĐÚNG 4 phần tử tương ứng 4 hoạt động "
                "(activity_number = 1, 2, 3, 4: Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng) "
                "với tổng time_minutes đúng bằng 45 phút."
                f"{outline_instruction}"
            )
            with tracing.observe_role(
                PEDAGOGICAL_ARCHITECT_PROMPT.name,
                prompt_name=PEDAGOGICAL_ARCHITECT_PROMPT.name,
                prompt_version=PEDAGOGICAL_ARCHITECT_PROMPT.version,
                input_data={"topic": topic, "grade": grade, "proficiency": proficiency},
            ) as arch_obs:
                raw_arch = llm_gateway.generate_structured(
                    prompt=architect_prompt,
                    system_prompt=PEDAGOGICAL_ARCHITECT_PROMPT.system_prompt,
                    response_schema=LessonBlueprintSchema,
                    task_type="lesson_plan",
                    model_provider=model_provider,
                    model_id=model_id,
                    role_name=PEDAGOGICAL_ARCHITECT_PROMPT.name,
                    prompt_name=PEDAGOGICAL_ARCHITECT_PROMPT.name,
                    prompt_version=PEDAGOGICAL_ARCHITECT_PROMPT.version,
                )
                blueprint, prepopulated_plan = _coerce_to_blueprint(raw_arch, topic, subject, grade)
                arch_obs.set_output({
                    "lesson_title": blueprint.lesson_title,
                    "activities_count": len(blueprint.activity_blueprints),
                })

            # ================= GATE 1: KIỂM ĐỊNH & CHUẨN HÓA BLUEPRINT =================
            with tracing.observe_evaluator(
                "gate.blueprint_5512",
                input_data={"activities_count": len(blueprint.activity_blueprints)},
            ) as gate1_obs:
                blueprint, bp_valid, bp_issues = _validate_and_normalize_blueprint(
                    blueprint, topic=topic, subject=subject, grade=grade
                )
                gate1_obs.set_output({"is_valid": bp_valid, "issues": bp_issues})
                tracing.record_trace_score("blueprint_5512_valid", 1.0 if bp_valid else 0.0)

            # ================= STEP 2: VAI TRÒ 2 - TÁC GIẢ HOẠT ĐỘNG 5512 =================
            if prepopulated_plan is not None:
                plan = prepopulated_plan
            else:
                blueprint_json = blueprint.model_dump_json(indent=2)
                author_prompt = (
                    f"Dựa trên Khung Sư Phạm (LessonBlueprintSchema) từ Mắt xích 1:\n{blueprint_json}\n\n"
                    f"Hãy soạn chi tiết 4 hoạt động bài dạy (`LessonActivitiesPayload`) cho bài '{topic}', "
                    f"Môn {subject}, Lớp {grade}.\n"
                    "YÊU CẦU BẮT BUỘC:\n"
                    "1. Mảng `activities` phải có ĐÚNG 4 phần tử (`activity_number` = 1, 2, 3, 4) với tổng `time_minutes` đúng bằng 45 phút.\n"
                    "2. Mỗi hoạt động có `goal` mở đầu bằng tên hoạt động chuẩn 5512 (Khởi động / Hình thành kiến thức / Luyện tập / Vận dụng), `expected_product` và 4 bước `execution` chi tiết."
                    f"{outline_instruction}"
                )
                with tracing.observe_role(
                    LESSON_ACTIVITY_AUTHOR_PROMPT.name,
                    prompt_name=LESSON_ACTIVITY_AUTHOR_PROMPT.name,
                    prompt_version=LESSON_ACTIVITY_AUTHOR_PROMPT.version,
                    input_data={"lesson_title": blueprint.lesson_title},
                ) as author_obs:
                    raw_activities = llm_gateway.generate_structured(
                        prompt=author_prompt,
                        system_prompt=LESSON_ACTIVITY_AUTHOR_PROMPT.system_prompt,
                        response_schema=LessonActivitiesPayload,
                        task_type="lesson_plan",
                        model_provider=model_provider,
                        model_id=model_id,
                        role_name=LESSON_ACTIVITY_AUTHOR_PROMPT.name,
                        prompt_name=LESSON_ACTIVITY_AUTHOR_PROMPT.name,
                        prompt_version=LESSON_ACTIVITY_AUTHOR_PROMPT.version,
                    )
                    if isinstance(raw_activities, LessonPlanSchema):
                        plan = raw_activities
                    elif isinstance(raw_activities, LessonActivitiesPayload):
                        plan = _assemble_plan(
                            blueprint,
                            raw_activities.activities,
                            generation_metadata=getattr(raw_activities, "generation_metadata", None),
                        )
                    else:
                        raise TypeError(f"Đầu ra Vai trò 2 không hợp lệ: {type(raw_activities).__name__}")
                    author_obs.set_output({"activities_count": len(plan.activities)})

            plan.approved_outline = copy.deepcopy(approved_outline)
            plan.review_token = None
            plan.quality_report = None

            # ================= GATE 2: KIỂM ĐỊNH 5512 & ĐỘ TRUNG THÀNH DÀN Ý =================
            with tracing.observe_evaluator(
                "gate.validate_5512_and_outline",
                input_data={"lesson_title": plan.lesson_title, "has_approved_outline": approved_outline is not None},
            ) as gate2_obs:
                outline_warnings: List[str] = []
                if approved_outline:
                    from lessonai.services.generation.outline_contract import validate_plan_outline

                    outline_warnings = validate_plan_outline(plan, approved_outline) or []
                val_result = validate_5512_lesson_plan(plan)
                for w in outline_warnings:
                    if w not in val_result.warnings:
                        val_result.warnings.append(w)
                gate2_obs.set_output({
                    "is_valid": val_result.is_valid,
                    "errors": val_result.errors,
                    "warnings": val_result.warnings,
                })

            last_successful_plan = plan
            last_validation_result = val_result

            if val_result.is_valid or max_retries <= 0:
                tracing.record_trace_score("cv5512_valid", 1.0 if val_result.is_valid else 0.0)
                tracing.record_trace_score("repair_triggered", 0.0)
                chain_obs.set_output({"lesson_title": plan.lesson_title, "is_valid": val_result.is_valid})
                return plan, val_result

            # ================= STEP 3 (CONDITIONAL): VAI TRÒ 3 - VÁ LỖI 5512 =================
            tracing.record_trace_score("repair_triggered", 1.0)
            for attempt in range(max_retries):
                error_feedback = "\n".join(val_result.errors)
                print(f"[AI Service] Phát hiện lỗi 5512. Kích hoạt Vai trò 3 (Repair Reviewer) lần {attempt + 1}...\n{error_feedback}\n")
                repair_prompt = (
                    f"Bản Kế hoạch bài dạy 5512 hiện tại cho bài '{topic}' (Môn {subject}, Lớp {grade}):\n"
                    f"{plan.model_dump_json(indent=2)}\n\n"
                    f"Lưu ý các lỗi trước cần khắc phục triệt để theo chuẩn 5512:\n{error_feedback}"
                    f"{outline_instruction}"
                )
                with tracing.observe_role(
                    LESSON_REPAIR_REVIEWER_PROMPT.name,
                    prompt_name=LESSON_REPAIR_REVIEWER_PROMPT.name,
                    prompt_version=LESSON_REPAIR_REVIEWER_PROMPT.version,
                    input_data={"attempt": attempt + 1, "errors": val_result.errors},
                ) as repair_obs:
                    repair_res = llm_gateway.generate_structured(
                        prompt=repair_prompt,
                        system_prompt=LESSON_REPAIR_REVIEWER_PROMPT.system_prompt,
                        response_schema=LessonRepairPayload,
                        task_type="lesson_plan",
                        model_provider=model_provider,
                        model_id=model_id,
                        role_name=LESSON_REPAIR_REVIEWER_PROMPT.name,
                        prompt_name=LESSON_REPAIR_REVIEWER_PROMPT.name,
                        prompt_version=LESSON_REPAIR_REVIEWER_PROMPT.version,
                    )
                    plan = _apply_repair_payload(plan, repair_res)
                    plan.approved_outline = copy.deepcopy(approved_outline)
                    plan.review_token = None
                    plan.quality_report = None
                    repair_obs.set_output({"patched_activities_count": len(plan.activities)})

                with tracing.observe_evaluator(
                    "gate.validate_5512_after_repair",
                    input_data={"attempt": attempt + 1},
                ) as gate2_re_obs:
                    outline_warnings = []
                    if approved_outline:
                        from lessonai.services.generation.outline_contract import validate_plan_outline

                        outline_warnings = validate_plan_outline(plan, approved_outline) or []
                    val_result = validate_5512_lesson_plan(plan)
                    for w in outline_warnings:
                        if w not in val_result.warnings:
                            val_result.warnings.append(w)
                    gate2_re_obs.set_output({"is_valid": val_result.is_valid, "errors": val_result.errors})

                last_successful_plan = plan
                last_validation_result = val_result
                if val_result.is_valid:
                    break

            tracing.record_trace_score("cv5512_valid", 1.0 if val_result.is_valid else 0.0)
            chain_obs.set_output({"lesson_title": plan.lesson_title, "is_valid": val_result.is_valid, "repaired": True})
            return plan, val_result

        except Exception as e:
            err_msg = str(e)
            print(f"[AI Service] Chuỗi sinh giáo án gặp lỗi: {err_msg[:120]}")

            # Nếu đã sinh thành công bản kế hoạch ở mắt xích trước (khi bước Repair gặp lỗi 429/mạng),
            # hoàn trả bản nháp đó kèm cảnh báo; ngược lại ném lỗi theo ADR 0001 (Zero-Fallback).
            if last_successful_plan is not None:
                print("[AI Service] Kích hoạt Graceful Fallback: Trả về bản nháp gần nhất kèm kết quả kiểm tra!")
                res = last_validation_result or ValidationResult(is_valid=True, errors=[], warnings=[])
                res.warnings.append(
                    "Hệ thống đã tự động bảo toàn bản kế hoạch thành công gần nhất do mạng/quota gián đoạn."
                )
                chain_obs.mark_warning(
                    "Preserved last_successful_plan after repair exception",
                    output={"lesson_title": last_successful_plan.lesson_title},
                )
                tracing.record_trace_score("cv5512_valid", 1.0 if res.is_valid else 0.0)
                return last_successful_plan, res

            tracing.record_trace_score("cv5512_valid", 0.0)
            if isinstance(e, ValueError):
                raise
            raise RuntimeError("Không tạo được giáo án; bản soạn được giữ nguyên") from e
