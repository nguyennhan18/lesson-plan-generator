from typing import Any, Dict, List, Optional
from lessonai.exporters.graph_generator import is_plottable
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
from lessonai.services.validation import audit_slide_deck


def _format_outline_for_slide_prompt(outline_slides: Optional[List[Any]]) -> str:
    """Định dạng danh sách thẻ dàn ý đã được giáo viên duyệt ở Trạm 2 để bơm vào Vai trò 1 của chuỗi Slide."""
    if not outline_slides:
        return ""
    lines = [
        "\n=== DÀN Ý SLIDE ĐÃ ĐƯỢC GIÁO VIÊN DUYỆT Ở TRẠM 2 (BẮT BUỘC BÁM SÁT THỨ TỰ & TIÊU ĐỀ) ==="
    ]
    for idx, item in enumerate(outline_slides, 1):
        if isinstance(item, dict):
            s_idx = item.get("slide_index") or item.get("slide_number") or idx
            title = item.get("title") or f"Slide {s_idx}"
            act = item.get("activity_type") or "Hình thành kiến thức"
            vis = item.get("visual_type") or "Concept Highlight"
            bullets = item.get("bullet_points") or item.get("key_points") or []
            has_3d = bool(item.get("has_3d"))
            poly = item.get("polyhedron_type")
        else:
            s_idx = getattr(item, "slide_index", None) or getattr(item, "slide_number", None) or idx
            title = getattr(item, "title", None) or f"Slide {s_idx}"
            act = getattr(item, "activity_type", None) or "Hình thành kiến thức"
            vis = getattr(item, "visual_type", None) or "Concept Highlight"
            bullets = getattr(item, "bullet_points", None) or getattr(item, "key_points", None) or []
            has_3d = bool(getattr(item, "has_3d", False))
            poly = getattr(item, "polyhedron_type", None)

        bullet_text = " | ".join(str(b) for b in bullets[:4])
        extra_3d = f" | has_3d=True ({poly or 'pyramid_square'})" if has_3d else ""
        lines.append(
            f"  - Slide {s_idx}: Tiêu đề='{title}' | Hoạt động='{act}' | Visual='{vis}'{extra_3d}\n"
            f"    Ý chính: {bullet_text}"
        )
    lines.append("=== HẾT DÀN Ý TRẠM 2 ===\n")
    return "\n".join(lines)


def _default_quiz_options(topic: str) -> List[QuizOptionDetail]:
    """Bộ phương án trắc nghiệm dự phòng an toàn đảm bảo luôn vượt qua Pydantic validator của SlideSchema."""
    return [
        QuizOptionDetail(
            label="A",
            text=f"Khẳng định chuẩn xác theo định lý và tính chất trọng tâm của bài {topic}.",
            is_correct=True,
            distractor_rationale=None,
        ),
        QuizOptionDetail(
            label="B",
            text="Kết quả thu được khi nhầm dấu hệ số trong bước biến đổi đại số.",
            is_correct=False,
            distractor_rationale="Sai dấu hệ số trong bước biến đổi; cần đối chiếu lại dấu của biểu thức theo định lý SGK.",
        ),
        QuizOptionDetail(
            label="C",
            text="Kết quả khi bỏ sót điều kiện xác định hoặc hệ số chia ở mẫu số.",
            is_correct=False,
            distractor_rationale="Thiếu hệ số chia theo công thức chuẩn SGK dẫn đến giá trị lệch tỉ lệ.",
        ),
        QuizOptionDetail(
            label="D",
            text="Kết quả khi áp dụng nhầm công thức của trường hợp suy biến.",
            is_correct=False,
            distractor_rationale="Áp dụng sai điều kiện của định lý; cần kiểm tra điều kiện trước khi thay số.",
        ),
    ]


def _is_valid_quiz_options(options: Optional[List[QuizOptionDetail]]) -> bool:
    if not options or len(options) < 2:
        return False
    correct_count = sum(1 for opt in options if opt.is_correct)
    if correct_count != 1:
        return False
    for opt in options:
        if not opt.is_correct and not (opt.distractor_rationale and opt.distractor_rationale.strip()):
            return False
    return True


def _coerce_to_narrative_deck(
    raw_obj: Any,
    topic: str,
    subject: str,
    grade: int,
) -> tuple[SlideNarrativeDeckSchema, Optional[SlideDeckSchema]]:
    """
    Chuẩn hóa đầu ra của Vai trò 1 (`role.slide_narrative_designer`) về `SlideNarrativeDeckSchema`.
    Nếu một bài test cũ monkeypatch `generate_structured` trả thẳng `SlideDeckSchema`,
    chuyển đổi an toàn và giữ lại `SlideDeckSchema` gốc.
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
                    needs_chart=has_chart,
                    needs_3d=bool(s.has_3d),
                    needs_quiz=has_quiz,
                )
            )
        narrative_deck = SlideNarrativeDeckSchema(
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
    lesson_id: Optional[str],
    proficiency: ClassProficiency,
    target_outcome: Optional[str],
    source_refs: List[Any],
    curated_fallback_deck: Optional[SlideDeckSchema] = None,
) -> SlideDeckSchema:
    """
    Hợp nhất kịch bản nội dung của Vai trò 1 (`SlideNarrativeDeckSchema`) với cấu hình
    Đồ thị / 3D / Trắc nghiệm của Vai trò 2 (`SlideVisualQuizBatchSchema`) thành `SlideDeckSchema`.
    """
    enrichment_by_idx: Dict[int, SlideVisualQuizItem] = {}
    if visual_batch and visual_batch.items:
        for item in visual_batch.items:
            enrichment_by_idx[item.slide_index] = item

    curated_quiz_options: List[QuizOptionDetail] = []
    curated_chart_spec: Optional[ChartSpec] = None
    if curated_fallback_deck and curated_fallback_deck.slides:
        for cs in curated_fallback_deck.slides:
            if not curated_quiz_options and _is_valid_quiz_options(cs.quiz_options):
                curated_quiz_options = cs.quiz_options
            if curated_chart_spec is None and cs.chart_spec and cs.chart_spec.kind != ChartType.NONE:
                curated_chart_spec = cs.chart_spec

    assembled_slides: List[SlideSchema] = []
    for idx, n_slide in enumerate(narrative_deck.slides or [], 1):
        s_idx = n_slide.slide_index or idx
        enrich = enrichment_by_idx.get(s_idx)

        chart_spec = enrich.chart_spec if enrich and enrich.chart_spec else None
        if chart_spec is None and n_slide.needs_chart and curated_chart_spec is not None:
            chart_spec = curated_chart_spec

        has_3d = bool(enrich.has_3d) if enrich is not None else bool(n_slide.needs_3d)
        polyhedron_type = enrich.polyhedron_type if enrich and enrich.polyhedron_type else None
        if has_3d and not polyhedron_type:
            polyhedron_type = "pyramid_square"

        quiz_options: List[QuizOptionDetail] = []
        is_quiz_slide = n_slide.layout == SlideLayout.QUIZ_OPTION or n_slide.needs_quiz
        if enrich and _is_valid_quiz_options(enrich.quiz_options):
            quiz_options = enrich.quiz_options
        elif is_quiz_slide:
            quiz_options = curated_quiz_options if _is_valid_quiz_options(curated_quiz_options) else _default_quiz_options(topic)

        layout = n_slide.layout
        if is_quiz_slide and _is_valid_quiz_options(quiz_options):
            layout = SlideLayout.QUIZ_OPTION

        act_type = n_slide.activity_type
        if not act_type:
            if n_slide.type == SlideType.WARM_UP_SLIDE:
                act_type = "khoi_dong"
            elif n_slide.type == SlideType.CONCEPT_SLIDE:
                act_type = "hinh_thanh_kien_thuc"
            elif n_slide.type == SlideType.EXERCISE_SLIDE:
                act_type = "luyen_tap"
            elif n_slide.type == SlideType.SUMMARY_SLIDE:
                act_type = "tong_ket"

        slide_obj = SlideSchema(
            slide_index=s_idx,
            type=n_slide.type,
            layout=layout,
            title=n_slide.title,
            subtitle=n_slide.subtitle,
            bullet_points=n_slide.bullet_points,
            main_definition_latex=n_slide.main_definition_latex,
            worked_solution_steps=n_slide.worked_solution_steps,
            teacher_note=n_slide.teacher_note,
            chart_spec=chart_spec,
            has_3d=has_3d,
            polyhedron_type=polyhedron_type,
            quiz_options=quiz_options if layout == SlideLayout.QUIZ_OPTION else [],
            math_formulas=list(enrich.math_formulas) if enrich and enrich.math_formulas else [],
            class_proficiency=proficiency,
            target_outcome=target_outcome,
            activity_type=act_type,
            pedagogical_mode=n_slide.pedagogical_mode,
            source_refs=source_refs[:2] if source_refs else None,
        )
        assembled_slides.append(slide_obj)

    return SlideDeckSchema(
        presentation_title=narrative_deck.presentation_title or topic,
        subject=narrative_deck.subject or subject,
        grade=narrative_deck.grade or grade,
        theme=narrative_deck.theme or ThemeType.MATH_ACADEMIC,
        slides=assembled_slides,
    )


def _evaluate_slide_deck_gate(slide_deck: SlideDeckSchema) -> tuple[Dict[int, List[str]], float]:
    """
    Gate 3 (`gate.audit_slide_deck_and_charts`):
    Kiểm định bộ slide qua `audit_slide_deck` (Chính tả + SymPy + Định lý SGK)
    và kiểm tra khả năng dựng đồ thị `is_plottable` cho mọi slide có `chart_spec`.
    Trả về: (errors_by_slide_index, chart_plottable_rate)
    """
    errors_by_slide: Dict[int, List[str]] = {}
    deck_dict = slide_deck.model_dump()
    audit_res = audit_slide_deck(deck_dict)

    for w in audit_res.warnings:
        if w.severity == "error":
            errors_by_slide.setdefault(w.slide_index, []).append(f"[{w.category}] {w.message} Gợi ý: {w.suggestion or ''}")

    chart_slides = 0
    plottable_charts = 0
    for idx, s in enumerate(slide_deck.slides, 1):
        s_idx = s.slide_index or idx
        if s.chart_spec and s.chart_spec.kind != ChartType.NONE:
            chart_slides += 1
            spec_dict = s.chart_spec.model_dump()
            if is_plottable(spec_dict):
                plottable_charts += 1
            else:
                errors_by_slide.setdefault(s_idx, []).append(
                    f"[chart_spec] Biểu thức đồ thị '{s.chart_spec.expression}' không thể vẽ bằng SymPy/Matplotlib."
                )

    chart_rate = (plottable_charts / chart_slides) if chart_slides > 0 else 1.0
    return errors_by_slide, chart_rate


def generate_slide_deck(
    topic: str,
    subject: str = "Toán học",
    grade: int = 12,
    lesson_id: Optional[str] = None,
    use_rag: bool = True,
    class_proficiency: Optional[ClassProficiency] = ClassProficiency.STANDARD,
    target_outcome: Optional[str] = None,
    approved_outline: Optional[dict] = None,
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None,
    plan: Optional[LessonPlanSchema] = None,
    outline_slides: Optional[List[Any]] = None,
    session_id: Optional[str] = None,
) -> SlideDeckSchema:
    """
    Soạn Bộ Slide bài giảng theo kiến trúc Role-Based Prompt Chaining:
      - Step 0 [retriever] : `rag.slide_deck_context`
      - Step 1 [agent]     : `role.slide_narrative_designer` -> `SlideNarrativeDeckSchema`
      - Step 2 [agent]     : `role.visual_and_quiz_specialist` -> `SlideVisualQuizBatchSchema`
      - Gate 3 [evaluator] : `gate.audit_slide_deck_and_charts` (SymPy + Định lý SGK + `is_plottable`)
      - Step 3 [agent]     : `role.slide_repair_reviewer` (chỉ chạy khi Gate 3 phát hiện slide lỗi)
    Tích hợp Graceful Partial Fallback bảo toàn kịch bản của Vai trò 1 nếu Vai trò 2 hết quota.
    Nếu có `approved_outline` (dàn ý đã duyệt), bản dựng cuối được kiểm định khớp đúng số trang/
    thứ tự/tiêu đề, đồng thời `source_refs` được xác thực sha256 khớp ngữ cảnh RAG để chống bịa nguồn.
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

    approved_outline_section = ""
    if approved_outline:
        import json

        approved_items = approved_outline.get("outline_slides", [])
        if (
            not approved_items
            or len({item.get("id") for item in approved_items}) != len(approved_items)
            or any(not item.get("id") for item in approved_items)
        ):
            raise ValueError("Dàn ý đã duyệt thiếu ID hoặc có ID trùng")
        approved_outline_section = (
            "\nDÀN Ý ĐÃ DUYỆT (bắt buộc đúng số trang, thứ tự, tiêu đề và các ý; mỗi slide ghi source_outline_id):\n"
            + json.dumps(approved_outline, ensure_ascii=False)
        )

    rag_slide_context = ""
    source_refs: List[Any] = []
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
            "has_plan": plan is not None,
            "outline_slides_count": len(outline_slides) if outline_slides else 0,
        },
    ) as chain_obs:
        # ================= STEP 0: RETRIEVER (PEDAGOGICAL RAG) =================
        if use_rag and grade == 12 and "toán" in subject.lower():
            with tracing.observe_retriever(
                "rag.slide_deck_context",
                input_data={"lesson_id": resolved_lid, "topic": topic, "proficiency": proficiency_str},
            ) as ret_obs:
                try:
                    from lessonai.rag.context_builder import PedagogicalContextBuilder
                    from lessonai.rag.curriculum_registry import infer_lesson_id

                    resolved_lid = resolved_lid or infer_lesson_id(topic)
                    rag_slide_context, source_refs = PedagogicalContextBuilder.build_slide_deck_context(
                        resolved_lid, topic=topic, proficiency=proficiency_str
                    )
                    ret_obs.set_output({"source_refs_count": len(source_refs), "source_refs": source_refs})
                except Exception as e:
                    print(f"[AI Service] RAG Slide Context build exception: {e}")
                    ret_obs.mark_warning(str(e))

        rag_instruction = f"\n\n{rag_slide_context}\n" if rag_slide_context else ""
        outline_section = _format_outline_for_slide_prompt(outline_slides)
        plan_section = (
            f"Dựa trên Kế hoạch bài dạy chuẩn 5512 sau:\n{plan.model_dump_json(indent=2)}\n\n"
            if plan is not None
            else ""
        )

        try:
            # ================= STEP 1: VAI TRÒ 1 - THIẾT KẾ KỊCH BẢN & NỘI DUNG SLIDE =================
            narrative_prompt = (
                f"{plan_section}"
                f"Hãy thiết kế kịch bản nội dung Bộ Slide bài giảng (`SlideNarrativeDeckSchema`) cho bài dạy: "
                f"'{topic}', Môn {subject}, Lớp {grade}.\n"
                f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
                f"{outline_section}"
                f"{approved_outline_section}"
                f"{rag_instruction}"
            )
            with tracing.observe_role(
                SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
                prompt_name=SLIDE_NARRATIVE_DESIGNER_PROMPT.name,
                prompt_version=SLIDE_NARRATIVE_DESIGNER_PROMPT.version,
                input_data={
                    "topic": topic,
                    "grade": grade,
                    "proficiency": proficiency_str,
                    "outline_slides_count": len(outline_slides) if outline_slides else 0,
                },
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
                role1_obs.set_output({"slides_count": len(narrative_deck.slides)})

            # ================= STEP 2: VAI TRÒ 2 - CHUYÊN GIA ĐỒ THỊ, 3D & TRẮC NGHIỆM =================
            if prepopulated_deck is not None:
                # Tương thích ngược với các unit test cũ mock generate_structured trả thẳng SlideDeckSchema
                slide_deck = prepopulated_deck
            else:
                from lessonai.services.generation.fallback import get_curated_slide_deck

                curated_ref = get_curated_slide_deck(
                    topic=topic, subject=subject, grade=grade, lesson_id=resolved_lid, plan=plan
                )
                try:
                    compact_slides_for_role2 = [
                        {
                            "slide_index": s.slide_index or (idx + 1),
                            "type": s.type.value if hasattr(s.type, "value") else str(s.type),
                            "layout": s.layout.value if hasattr(s.layout, "value") else str(s.layout),
                            "title": s.title,
                            "needs_chart": s.needs_chart,
                            "needs_3d": s.needs_3d,
                            "needs_quiz": s.needs_quiz,
                            "visual_hint": s.visual_hint,
                            "main_definition_latex": s.main_definition_latex,
                        }
                        for idx, s in enumerate(narrative_deck.slides)
                    ]
                    visual_quiz_prompt = (
                        f"Cho kịch bản các trang Slide của bài '{topic}' (Môn {subject}, Lớp {grade}, Trình độ '{proficiency_str}'):\n"
                        f"{compact_slides_for_role2}\n\n"
                        "Hãy thiết kế cấu hình kỹ thuật Đồ thị SymPy (`chart_spec`), Hình học 3D (`has_3d`, `polyhedron_type`) "
                        "và Câu hỏi trắc nghiệm 4 phương án (`quiz_options` có đủ `distractor_rationale`) trong `SlideVisualQuizBatchSchema`."
                        f"{rag_instruction}"
                    )
                    with tracing.observe_role(
                        VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                        prompt_name=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.name,
                        prompt_version=VISUAL_AND_QUIZ_SPECIALIST_PROMPT.version,
                        input_data={"slides_count": len(compact_slides_for_role2)},
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
                        if isinstance(raw_role2, SlideVisualQuizBatchSchema):
                            visual_batch = raw_role2
                        else:
                            visual_batch = SlideVisualQuizBatchSchema(items=[])
                        role2_obs.set_output({"enriched_items_count": len(visual_batch.items)})

                    slide_deck = _merge_narrative_and_visual_quiz(
                        narrative_deck,
                        visual_batch,
                        topic=topic,
                        subject=subject,
                        grade=grade,
                        lesson_id=resolved_lid,
                        proficiency=proficiency_enum,
                        target_outcome=target_outcome,
                        source_refs=source_refs,
                        curated_fallback_deck=curated_ref,
                    )
                except Exception as role2_err:
                    # GRACEFUL PARTIAL FALLBACK: Bảo toàn 100% kịch bản nội dung slide của Vai trò 1,
                    # chỉ ghép bù cấu hình chart_spec / quiz_options từ kho học liệu chuẩn!
                    print(
                        f"[AI Service] Vai trò 2 của Slide gặp lỗi ({str(role2_err)[:100]}). "
                        "Kích hoạt Partial Fallback: Bảo toàn kịch bản Slide của Vai trò 1!"
                    )
                    slide_deck = _merge_narrative_and_visual_quiz(
                        narrative_deck,
                        None,
                        topic=topic,
                        subject=subject,
                        grade=grade,
                        lesson_id=resolved_lid,
                        proficiency=proficiency_enum,
                        target_outcome=target_outcome,
                        source_refs=source_refs,
                        curated_fallback_deck=curated_ref,
                    )
                    chain_obs.mark_warning(
                        "Partial Fallback: preserved Role 1 narrative slides, filled visual/quiz from curated reference"
                    )
                    tracing.record_trace_score("fallback_used", 0.5, comment="partial_fallback_role2")

            # Đảm bảo gán source_refs và activity_type cho mọi slide
            if slide_deck and slide_deck.slides:
                for idx, s in enumerate(slide_deck.slides, 1):
                    if not s.slide_index:
                        s.slide_index = idx
                    if not s.activity_type:
                        if s.type == SlideType.WARM_UP_SLIDE:
                            s.activity_type = "khoi_dong"
                        elif s.type == SlideType.CONCEPT_SLIDE:
                            s.activity_type = "hinh_thanh_kien_thuc"
                        elif s.type == SlideType.EXERCISE_SLIDE:
                            s.activity_type = "luyen_tap"
                        elif s.type == SlideType.SUMMARY_SLIDE:
                            s.activity_type = "tong_ket"
                    if source_refs and not s.source_refs:
                        s.source_refs = source_refs[:2]

            # ================= CHUẨN HÓA & KIỂM ĐỊNH HỢP ĐỒNG DÀN Ý/NGUỒN =================
            for field in ("review_token", "quality_report"):
                if slide_deck.model_extra:
                    slide_deck.model_extra.pop(field, None)

            from lessonai.services.generation.outline_contract import normalize_polyhedron_type, validate_slide_outline_item
            from lessonai.services.geometry_scene import KINDS

            for s in slide_deck.slides:
                s.polyhedron_type = normalize_polyhedron_type(s.polyhedron_type)
                if not s.has_3d:
                    s.polyhedron_type = None
                elif s.polyhedron_type is not None and s.polyhedron_type not in KINDS:
                    raise ValueError("Loại khối 3D không thuộc tập chuẩn được hỗ trợ")

            outline_contract_warnings = []
            if approved_outline:
                approved_items = approved_outline["outline_slides"]
                if len(slide_deck.slides) != len(approved_items):
                    raise ValueError("Số slide không khớp dàn ý đã duyệt; cần sinh lại")
                for s, item in zip(slide_deck.slides, approved_items):
                    outline_contract_warnings.extend(validate_slide_outline_item(s, item))
            if outline_contract_warnings:
                slide_deck.outline_warnings = outline_contract_warnings

            from lessonai.services.content_blocks import block_errors

            for s in slide_deck.slides:
                block_err = list(block_errors(s.model_dump(mode="json")))
                if block_err:
                    raise ValueError(block_err[0][1])

            allowed_refs = {(ref.get("source_type"), ref.get("id")): ref for ref in source_refs}
            for s in slide_deck.slides:
                for ref in s.source_refs or []:
                    canonical = allowed_refs.get((ref.source_type, ref.id))
                    if canonical is None:
                        raise ValueError("AI gắn nguồn không được cung cấp trong ngữ cảnh")
                    supplied_hash = ref.model_dump().get("sha256")
                    if supplied_hash and supplied_hash != canonical.get("sha256"):
                        raise ValueError("AI gắn phiên bản nguồn không khớp ngữ cảnh")
                    # Bind attribution to the exact source version actually supplied.
                    if canonical.get("sha256"):
                        ref.sha256 = canonical["sha256"]

            # ================= GATE 3: KIỂM ĐỊNH ĐỊNH LÝ SGK, SYMPY & CHART PLOTTABLE =================
            with tracing.observe_evaluator(
                "gate.audit_slide_deck_and_charts",
                input_data={"slides_count": len(slide_deck.slides)},
            ) as gate3_obs:
                errors_by_slide, chart_rate = _evaluate_slide_deck_gate(slide_deck)
                gate3_obs.set_output(
                    {
                        "is_clean": len(errors_by_slide) == 0,
                        "failing_slides": errors_by_slide,
                        "chart_plottable_rate": chart_rate,
                    }
                )

            # ================= STEP 3 (CONDITIONAL): VAI TRÒ 3 - VÁ LỖI SLIDE CỤC BỘ =================
            if errors_by_slide:
                print(
                    f"[AI Service] Gate 3 phát hiện lỗi trên các slide {list(errors_by_slide.keys())}. "
                    "Kích hoạt Vai trò 3 (Slide Repair Reviewer)..."
                )
                tracing.record_trace_score("repair_triggered", 1.0)
                failing_slides_payload = [
                    {
                        "slide": s.model_dump(),
                        "errors": errors_by_slide[s.slide_index],
                    }
                    for s in slide_deck.slides
                    if s.slide_index in errors_by_slide
                ]
                repair_prompt = (
                    f"Chủ đề bài giảng: '{topic}' (Môn {subject}, Lớp {grade}).\n"
                    f"Các trang slide sau đây bị Cổng kiểm định Gate 3 (SymPy / Định lý SGK / Chart Plottable) phát hiện lỗi:\n"
                    f"{failing_slides_payload}\n\n"
                    "Hãy sửa chính xác các trang slide bị lỗi trên và trả về trong `SlideRepairBatchSchema`."
                )
                try:
                    with tracing.observe_role(
                        SLIDE_REPAIR_REVIEWER_PROMPT.name,
                        prompt_name=SLIDE_REPAIR_REVIEWER_PROMPT.name,
                        prompt_version=SLIDE_REPAIR_REVIEWER_PROMPT.version,
                        input_data={"failing_slide_indices": list(errors_by_slide.keys())},
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
                                    patched_s = patched_by_idx[orig_s.slide_index]
                                    if source_refs and not patched_s.source_refs:
                                        patched_s.source_refs = source_refs[:2]
                                    slide_deck.slides[i] = patched_s
                            repair_obs.set_output({"patched_count": len(patched_by_idx)})

                    with tracing.observe_evaluator(
                        "gate.audit_after_repair",
                        input_data={"slides_count": len(slide_deck.slides)},
                    ) as gate3_re_obs:
                        errors_by_slide, chart_rate = _evaluate_slide_deck_gate(slide_deck)
                        gate3_re_obs.set_output(
                            {"is_clean": len(errors_by_slide) == 0, "chart_plottable_rate": chart_rate}
                        )
                except Exception as repair_err:
                    print(f"[AI Service] Vai trò 3 (Slide Repair) gặp sự cố ({repair_err}), giữ nguyên bộ slide hiện có.")
            else:
                tracing.record_trace_score("repair_triggered", 0.0)

            tracing.record_trace_score("slide_audit_clean", 1.0 if len(errors_by_slide) == 0 else 0.0)
            tracing.record_trace_score("chart_plottable_rate", float(chart_rate))
            chain_obs.set_output(
                {
                    "presentation_title": slide_deck.presentation_title,
                    "slides_count": len(slide_deck.slides),
                    "audit_clean": len(errors_by_slide) == 0,
                }
            )
            return slide_deck

        except Exception as e:
            print(
                f"[AI Service] Kích hoạt Curated Fallback SlideDeck cho môn {subject}, lớp {grade}, "
                f"bài '{topic}' do: {str(e)[:80]}"
            )
            from lessonai.services.generation.fallback import get_curated_slide_deck

            fallback_deck = get_curated_slide_deck(
                topic=topic, subject=subject, grade=grade, lesson_id=resolved_lid, plan=plan
            )
            chain_obs.mark_warning(
                f"Full Curated Fallback SlideDeck: {str(e)[:120]}",
                output={"slides_count": len(fallback_deck.slides), "fallback": True},
            )
            tracing.record_trace_score("fallback_used", 1.0, comment="full_curated_slide_fallback")
            return fallback_deck
