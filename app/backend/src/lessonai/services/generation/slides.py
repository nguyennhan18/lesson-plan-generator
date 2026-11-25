import json
from typing import Any, Dict, List, Optional

from lessonai.llm import tracing
from lessonai.llm.gateway import llm_gateway
from lessonai.prompts.roles import (
    SLIDE_NARRATIVE_DESIGNER_PROMPT,
    SLIDE_REPAIR_REVIEWER_PROMPT,
    VISUAL_AND_QUIZ_SPECIALIST_PROMPT,
)
from lessonai.prompts.slides import SLIDE_SYSTEM_PROMPT  # Giữ tương thích ngược cho các import cũ
from lessonai.schemas.chain_schemas import (
    SlideNarrativeDeckSchema,
    SlideNarrativeItem,
    SlideRepairBatchSchema,
    SlideVisualQuizBatchSchema,
    SlideVisualQuizItem,
)
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.slide_schema import (
    ChartType,
    ClassProficiency,
    SlideDeckSchema,
    SlideLayout,
    SlideSchema,
    SlideType,
    ThemeType,
)


def _coerce_to_narrative_deck(
    raw_obj: Any,
    topic: str,
    subject: str,
    grade: int,
) -> tuple[SlideNarrativeDeckSchema, Optional[SlideDeckSchema]]:
    """
    Chuẩn hóa đầu ra của Vai trò 1 (`role.slide_narrative_designer`) về `SlideNarrativeDeckSchema`.
    Nếu một bài test cũ monkeypatch `generate_structured` trả thẳng `SlideDeckSchema`,
    giữ nguyên `SlideDeckSchema` đó để chạy trực tiếp qua Gate 3.
    """
    if isinstance(raw_obj, SlideNarrativeDeckSchema):
        return raw_obj, None

    if isinstance(raw_obj, SlideDeckSchema):
        narrative_slides: List[SlideNarrativeItem] = []
        for idx, s in enumerate(raw_obj.slides or [], 1):
            has_chart = bool(s.chart_spec and s.chart_spec.kind != ChartType.NONE)
            has_quiz = s.layout == SlideLayout.QUIZ_OPTION or bool(s.quiz_options)
            narrative_slides.append(
                SlideNarrativeItem(
                    slide_index=s.slide_index or idx,
                    source_outline_id=s.source_outline_id,
                    type=s.type or SlideType.CONCEPT_SLIDE,
                    layout=s.layout or SlideLayout.SINGLE_COLUMN,
                    title=s.title,
                    subtitle=s.subtitle,
                    bullet_points=list(s.bullet_points or []),
                    main_definition_latex=s.main_definition_latex,
                    worked_solution_steps=list(s.worked_solution_steps or []),
                    teacher_note=s.teacher_note,
                    activity_type=s.activity_type,
                    pedagogical_mode=s.pedagogical_mode,
                    question=s.question,
                    source_refs=list(s.source_refs) if s.source_refs else None,
                    needs_chart=has_chart,
                    needs_3d=bool(s.has_3d),
                    needs_quiz=has_quiz,
                )
            )
        narrative_deck = SlideNarrativeDeckSchema(
            generation_metadata=getattr(raw_obj, "generation_metadata", None),
            presentation_title=raw_obj.presentation_title or topic,
            subject=raw_obj.subject or subject,
            grade=raw_obj.grade or grade,
            theme=raw_obj.theme or ThemeType.MATH_ACADEMIC,
            slides=narrative_slides,
        )
        return narrative_deck, raw_obj

    raise TypeError(f"Đầu ra Vai trò 1 của Slide không hợp lệ: {type(raw_obj).__name__}")


def _merge_narrative_and_visual_quiz(
    narrative_deck: SlideNarrativeDeckSchema,
    visual_batch: Optional[SlideVisualQuizBatchSchema],
    *,
    topic: str,
    subject: str,
    grade: int,
    proficiency: ClassProficiency,
    target_outcome: Optional[str],
    approved_outline: Optional[dict],
) -> SlideDeckSchema:
    """
    Hợp nhất kịch bản nội dung của Vai trò 1 (`SlideNarrativeDeckSchema`) với cấu hình
    Đồ thị / 3D / Trắc nghiệm của Vai trò 2 (`SlideVisualQuizBatchSchema`) thành `SlideDeckSchema`.
    Tuân thủ ADR 0001 (Zero-Fallback): không tự bịa nội dung mẫu ngoài dữ liệu AI và `approved_outline`.
    """
    enrichment_by_idx: Dict[int, SlideVisualQuizItem] = {}
    if visual_batch and visual_batch.items:
        for item in visual_batch.items:
            enrichment_by_idx[item.slide_index] = item

    outline_items = (approved_outline or {}).get("outline_slides") or []

    assembled_slides: List[SlideSchema] = []
    for idx, n_slide in enumerate(narrative_deck.slides or [], 1):
        s_idx = n_slide.slide_index or idx
        enrich = enrichment_by_idx.get(s_idx)
        outline_item = outline_items[idx - 1] if idx - 1 < len(outline_items) else None

        source_outline_id = n_slide.source_outline_id
        if not source_outline_id and isinstance(outline_item, dict):
            source_outline_id = outline_item.get("id")

        chart_spec = enrich.chart_spec if enrich and enrich.chart_spec else None
        has_3d = bool(enrich.has_3d) if enrich is not None else bool(n_slide.needs_3d)
        polyhedron_type = enrich.polyhedron_type if enrich is not None else None
        scene_spec = enrich.scene_spec if enrich is not None else None
        quiz_options = list(enrich.quiz_options) if enrich and enrich.quiz_options else []
        math_formulas = list(enrich.math_formulas) if enrich and enrich.math_formulas else []
        blocks = list(enrich.blocks) if enrich and enrich.blocks else []
        table_data = enrich.table_data if enrich is not None else None

        layout = n_slide.layout
        if quiz_options and layout != SlideLayout.QUIZ_OPTION:
            layout = SlideLayout.QUIZ_OPTION

        slide_obj = SlideSchema(
            slide_index=s_idx,
            source_outline_id=source_outline_id,
            type=n_slide.type,
            layout=layout,
            title=n_slide.title,
            subtitle=n_slide.subtitle,
            bullet_points=n_slide.bullet_points,
            main_definition_latex=n_slide.main_definition_latex,
            worked_solution_steps=n_slide.worked_solution_steps,
            teacher_note=n_slide.teacher_note,
            question=n_slide.question,
            chart_spec=chart_spec,
            has_3d=has_3d,
            polyhedron_type=polyhedron_type,
            scene_spec=scene_spec,
            quiz_options=quiz_options,
            math_formulas=math_formulas,
            blocks=blocks,
            table_data=table_data,
            class_proficiency=proficiency,
            target_outcome=target_outcome,
            activity_type=n_slide.activity_type,
            pedagogical_mode=n_slide.pedagogical_mode,
            source_refs=n_slide.source_refs,
        )
        assembled_slides.append(slide_obj)

    deck = SlideDeckSchema(
        presentation_title=narrative_deck.presentation_title or topic,
        subject=narrative_deck.subject or subject,
        grade=narrative_deck.grade or grade,
        theme=narrative_deck.theme or ThemeType.MATH_ACADEMIC,
        slides=assembled_slides,
    )
    meta = getattr(visual_batch, "generation_metadata", None) or getattr(narrative_deck, "generation_metadata", None)
    if meta is not None:
        deck.generation_metadata = meta
    return deck


def _enforce_slide_deck_contracts(
    slide_deck: SlideDeckSchema,
    approved_outline: Optional[dict],
) -> List[str]:
    """
    Gate 3 (`gate.slide_contracts`):
    Kiểm định toàn bộ hợp đồng bắt buộc trên `feature/ban-lam-viec`:
      1. Chuẩn hóa & kiểm tra `polyhedron_type` thuộc `KINDS` (`geometry_scene.py`).
      2. Kiểm tra số lượng slide & `validate_slide_outline_item` (`outline_contract.py`).
      3. Kiểm tra `block_errors` (`content_blocks.py`).
      4. Từ chối trích dẫn nguồn khi RAG tạm ngừng.
    """
    if not slide_deck or not slide_deck.slides:
        raise ValueError("Nhà cung cấp chưa trả nội dung slide")

    for field in ("review_token", "quality_report"):
        if slide_deck.model_extra:
            slide_deck.model_extra.pop(field, None)

    from lessonai.services.content_blocks import block_errors
    from lessonai.services.generation.outline_contract import (
        normalize_polyhedron_type,
        validate_slide_outline_item,
    )
    from lessonai.services.geometry_scene import KINDS

    for slide in slide_deck.slides:
        slide.polyhedron_type = normalize_polyhedron_type(slide.polyhedron_type)
        if not slide.has_3d:
            slide.polyhedron_type = None
        elif slide.polyhedron_type is not None and slide.polyhedron_type not in KINDS:
            raise ValueError("Loại khối 3D không thuộc tập chuẩn được hỗ trợ")

    outline_warnings: List[str] = []
    if approved_outline:
        items = approved_outline["outline_slides"]
        if len(slide_deck.slides) != len(items):
            raise ValueError("Số slide không khớp dàn ý đã duyệt; cần sinh lại")
        for slide, item in zip(slide_deck.slides, items):
            outline_warnings.extend(validate_slide_outline_item(slide, item))
    if outline_warnings:
        slide_deck.outline_warnings = outline_warnings

    for slide in slide_deck.slides:
        errors = list(block_errors(slide.model_dump(mode="json")))
        if errors:
            raise ValueError(errors[0][1])

    for slide in slide_deck.slides:
        if slide.source_refs:
            raise ValueError("Không chấp nhận trích dẫn nguồn khi RAG tạm ngừng")

    return outline_warnings


def generate_slide_deck(
    topic: str,
    subject: str = "Toán học",
    grade: int = 12,
    lesson_id: Optional[str] = None,
    use_rag: bool = False,  # Retained for older API callers; generation does not use RAG.
    class_proficiency: Optional[ClassProficiency] = ClassProficiency.STANDARD,
    target_outcome: Optional[str] = None,
    approved_outline: Optional[dict] = None,
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None,
    plan: Optional[LessonPlanSchema] = None,
    session_id: Optional[str] = None,
) -> SlideDeckSchema:
    """
    Sinh bản nháp Bộ Slide theo kiến trúc Role-Based Prompt Chaining trên `feature/ban-lam-viec`:
      - Step 1 [agent]     : `role.slide_narrative_designer` -> `SlideNarrativeDeckSchema`
      - Step 2 [agent]     : `role.visual_and_quiz_specialist` -> `SlideVisualQuizBatchSchema`
      - Gate 3 [evaluator] : `gate.slide_contracts` (`outline_contract`, `KINDS` 3D, `block_errors`, no citations)
      - Step 3 [agent]     : `role.slide_repair_reviewer` (có điều kiện khi Gate 3 báo lỗi)
    Tuân thủ ADR 0001 (Zero-Fallback): lỗi provider hoặc vi phạm hợp đồng được chuyển về caller để giữ Bản soạn hiện tại.
    """
    if isinstance(class_proficiency, ClassProficiency):
        proficiency_enum = class_proficiency
        proficiency_str = class_proficiency.value
    else:
        proficiency_str = str(class_proficiency or "standard")
        try:
            proficiency_enum = ClassProficiency(proficiency_str)
        except ValueError:
            proficiency_enum = ClassProficiency.STANDARD

    target_str = f"\nMục tiêu chuẩn đầu ra cần đạt: {target_outcome}" if target_outcome else ""

    if approved_outline:
        items = approved_outline.get("outline_slides", [])
        if (
            not items
            or len({item.get("id") for item in items}) != len(items)
            or any(not item.get("id") for item in items)
        ):
            raise ValueError("Dàn ý đã duyệt thiếu ID hoặc có ID trùng")

    resolved_lid = lesson_id or (getattr(plan, "lesson_id", None) if plan else None)
    if not resolved_lid and grade == 12 and "toán" in subject.lower():
        try:
            from lessonai.rag.curriculum_registry import infer_lesson_id

            resolved_lid = infer_lesson_id(topic)
        except Exception:
            resolved_lid = None

    with tracing.trace_chain(
        "chain.slide_deck_generation",
        session_id=session_id,
        lesson_id=resolved_lid,
        topic=topic,
        proficiency=proficiency_str,
        input_data={
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "lesson_id": resolved_lid,
            "class_proficiency": proficiency_str,
            "has_approved_outline": approved_outline is not None,
        },
    ) as chain_obs:
        outline_instruction = ""
        if approved_outline:
            outline_instruction = (
                "\nDÀN Ý ĐÃ DUYỆT (bắt buộc đúng số trang, thứ tự, tiêu đề và các ý; mỗi slide ghi source_outline_id):\n"
                + json.dumps(approved_outline, ensure_ascii=False)
            )

        if plan:
            plan_json_str = plan.model_dump_json(indent=2)
            narrative_prompt = (
                f"Dựa trên Kế hoạch bài dạy chuẩn 5512 sau:\n{plan_json_str}\n\n"
                f"Hãy soạn kịch bản cấu trúc Slide bài giảng (`SlideNarrativeDeckSchema`) cho bài dạy: "
                f"'{topic}', Môn {subject}, Lớp {grade}.\n"
                f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
                f"{outline_instruction}"
            )
        else:
            narrative_prompt = (
                f"Hãy soạn kịch bản cấu trúc Slide bài giảng (`SlideNarrativeDeckSchema`) cho bài dạy: "
                f"'{topic}', Môn {subject}, Lớp {grade}.\n"
                f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
                f"{outline_instruction}"
            )

        # ================= STEP 1: VAI TRÒ 1 - THIẾT KẾ KỊCH BẢN & NỘI DUNG SLIDE =================
        with tracing.observe_role(
            SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
            prompt_name=SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
            prompt_version=SLIDE_NARRATIVE_DESIGNER_PROMPT.version,
            input_data={"topic": topic, "grade": grade, "proficiency": proficiency_str},
        ) as role1_obs:
            raw_role1 = llm_gateway.generate_structured(
                prompt=narrative_prompt,
                system_prompt=SLIDE_NARRATIVE_DESIGNER_PROMPT.system_prompt,
                response_schema=SlideNarrativeDeckSchema,
                task_type="slide",
                model_provider=model_provider,
                model_id=model_id,
                role_name=SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
                prompt_name=SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
                prompt_version=SLIDE_NARRATIVE_DESIGNER_PROMPT.version,
            )
            narrative_deck, prepopulated_deck = _coerce_to_narrative_deck(raw_role1, topic, subject, grade)
            role1_obs.set_output({
                "slides_count": len(narrative_deck.slides) if narrative_deck and narrative_deck.slides else 0
            })

        # ================= STEP 2: VAI TRÒ 2 - CHUYÊN GIA ĐỒ THỊ, 3D & TRẮC NGHIỆM =================
        if prepopulated_deck is not None:
            slide_deck = prepopulated_deck
        else:
            compact_slides = [
                {
                    "slide_index": s.slide_index or (idx + 1),
                    "source_outline_id": s.source_outline_id,
                    "type": s.type.value if hasattr(s.type, "value") else str(s.type),
                    "layout": s.layout.value if hasattr(s.layout, "value") else str(s.layout),
                    "title": s.title,
                    "needs_chart": s.needs_chart,
                    "needs_3d": s.needs_3d,
                    "needs_quiz": s.needs_quiz,
                    "visual_hint": s.visual_hint,
                    "main_definition_latex": s.main_definition_latex,
                }
                for idx, s in enumerate(narrative_deck.slides or [])
            ]
            visual_quiz_prompt = (
                f"Cho kịch bản các trang Slide của bài '{topic}' (Môn {subject}, Lớp {grade}, Trình độ '{proficiency_str}'):\n"
                f"{json.dumps(compact_slides, ensure_ascii=False)}\n\n"
                "Hãy thiết kế cấu hình kỹ thuật Đồ thị SymPy (`chart_spec`), Hình học 3D (`has_3d`, `polyhedron_type` thuộc "
                "{'cube', 'square_pyramid_regular', 'square_pyramid_at_a'}) và Câu hỏi trắc nghiệm (`quiz_options`) "
                "trong `SlideVisualQuizBatchSchema`."
                f"{outline_instruction}"
            )
            with tracing.observe_role(
                VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                prompt_name=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                prompt_version=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.version,
                input_data={"slides_count": len(compact_slides)},
            ) as role2_obs:
                raw_role2 = llm_gateway.generate_structured(
                    prompt=visual_quiz_prompt,
                    system_prompt=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.system_prompt,
                    response_schema=SlideVisualQuizBatchSchema,
                    task_type="slide",
                    model_provider=model_provider,
                    model_id=model_id,
                    role_name=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                    prompt_name=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                    prompt_version=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.version,
                )
                visual_batch = raw_role2 if isinstance(raw_role2, SlideVisualQuizBatchSchema) else SlideVisualQuizBatchSchema(items=[])
                role2_obs.set_output({"enriched_items_count": len(visual_batch.items)})

            slide_deck = _merge_narrative_and_visual_quiz(
                narrative_deck,
                visual_batch,
                topic=topic,
                subject=subject,
                grade=grade,
                proficiency=proficiency_enum,
                target_outcome=target_outcome,
                approved_outline=approved_outline,
            )

        # ================= GATE 3: KIỂM ĐỊNH HỢP ĐỒNG DÀN Ý, KHỐI 3D, BLOCKS & TRÍCH DẪN =================
        try:
            with tracing.observe_evaluator(
                "gate.slide_contracts",
                input_data={"slides_count": len(slide_deck.slides) if slide_deck and slide_deck.slides else 0},
            ) as gate3_obs:
                outline_warnings = _enforce_slide_deck_contracts(slide_deck, approved_outline)
                gate3_obs.set_output({"is_clean": True, "outline_warnings_count": len(outline_warnings)})
            tracing.record_trace_score("repair_triggered", 0.0)
            tracing.record_trace_score("slide_contract_valid", 1.0)
            chain_obs.set_output({
                "presentation_title": slide_deck.presentation_title,
                "slides_count": len(slide_deck.slides),
            })
            return slide_deck
        except ValueError as contract_err:
            # Nếu đang chạy từ mock 1 lượt của test cũ (`prepopulated_deck is not None`),
            # ném ngay ValueError để giữ nguyên hành vi kiểm thử đơn vị.
            if prepopulated_deck is not None or not slide_deck or not slide_deck.slides:
                tracing.record_trace_score("slide_contract_valid", 0.0)
                raise

            # ================= STEP 3 (CONDITIONAL): VAI TRÒ 3 - VÁ LỖI HỢP ĐỒNG SLIDE =================
            print(f"[AI Service] Gate 3 phát hiện lỗi hợp đồng Slide ({contract_err}). Kích hoạt Vai trò 3 (Slide Repair Reviewer)...")
            tracing.record_trace_score("repair_triggered", 1.0)
            repair_prompt = (
                f"Bộ Slide bài giảng '{topic}' hiện tại bị Cổng kiểm định Gate 3 từ chối với lỗi:\n"
                f"- Lỗi: {contract_err}\n"
                f"- Dữ liệu các slide hiện tại:\n{slide_deck.model_dump_json(indent=2)}\n"
                f"{outline_instruction}\n"
                "Hãy sửa chính xác các trang slide bị lỗi trong `SlideRepairBatchSchema`."
            )
            with tracing.observe_role(
                SLIDE_REPAIR_REVIEWER_PROMPT.name,
                prompt_name=SLIDE_REPAIR_REVIEWER_PROMPT.name,
                prompt_version=SLIDE_REPAIR_REVIEWER_PROMPT.version,
                input_data={"error": str(contract_err)},
            ) as repair_obs:
                repair_res = llm_gateway.generate_structured(
                    prompt=repair_prompt,
                    system_prompt=SLIDE_REPAIR_REVIEWER_PROMPT.system_prompt,
                    response_schema=SlideRepairBatchSchema,
                    task_type="slide",
                    model_provider=model_provider,
                    model_id=model_id,
                    role_name=SLIDE_REPAIR_REVIEWER_PROMPT.name,
                    prompt_name=SLIDE_REPAIR_REVIEWER_PROMPT.name,
                    prompt_version=SLIDE_REPAIR_REVIEWER_PROMPT.version,
                )
                if isinstance(repair_res, SlideRepairBatchSchema) and repair_res.patched_slides:
                    patched_by_idx = {ps.slide_index: ps for ps in repair_res.patched_slides}
                    for i, orig_s in enumerate(slide_deck.slides):
                        if orig_s.slide_index in patched_by_idx:
                            slide_deck.slides[i] = patched_by_idx[orig_s.slide_index]
                    repair_obs.set_output({"patched_count": len(patched_by_idx)})

            with tracing.observe_evaluator(
                "gate.slide_contracts_after_repair",
                input_data={"slides_count": len(slide_deck.slides)},
            ) as gate3_re_obs:
                outline_warnings = _enforce_slide_deck_contracts(slide_deck, approved_outline)
                gate3_re_obs.set_output({"is_clean": True, "outline_warnings_count": len(outline_warnings)})

            tracing.record_trace_score("slide_contract_valid", 1.0)
            chain_obs.set_output({
                "presentation_title": slide_deck.presentation_title,
                "slides_count": len(slide_deck.slides),
                "repaired": True,
            })
            return slide_deck
