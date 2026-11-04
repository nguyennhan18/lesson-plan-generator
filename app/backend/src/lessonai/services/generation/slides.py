from typing import Optional
from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.slide_schema import SlideDeckSchema, ClassProficiency, SlideType, SlideLayout, ChartType
from lessonai.prompts.slides import SLIDE_SYSTEM_PROMPT


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
    plan: Optional[LessonPlanSchema] = None
) -> SlideDeckSchema:
    """
    Sinh bản nháp theo dàn ý được duyệt và nguồn đã kiểm duyệt.
    Lỗi provider hoặc vi phạm hợp đồng được chuyển về caller để giữ bài hiện tại.
    """
    if isinstance(class_proficiency, ClassProficiency):
        proficiency_str = class_proficiency.value
    else:
        proficiency_str = str(class_proficiency or "standard")
    target_str = f"\nMục tiêu chuẩn đầu ra cần đạt: {target_outcome}" if target_outcome else ""

    rag_slide_context = ""
    source_refs = []
    resolved_lid = lesson_id
    if use_rag and grade == 12 and "toán" in subject.lower():
        try:
            from lessonai.rag.context_builder import PedagogicalContextBuilder
            from lessonai.rag.curriculum_registry import infer_lesson_id
            resolved_lid = lesson_id or (getattr(plan, 'lesson_id', None) if plan else None) or infer_lesson_id(topic)
            rag_slide_context, source_refs = PedagogicalContextBuilder.build_slide_deck_context(
                resolved_lid, topic=topic, proficiency=proficiency_str
            )
        except Exception as e:
            print(f"[AI Service] RAG Slide Context build exception: {e}")

    rag_instruction = f"\n\n{rag_slide_context}\n" if rag_slide_context else ""

    if plan:
        plan_json_str = plan.model_dump_json(indent=2)
        user_prompt = (
            f"Dựa trên Kế hoạch bài dạy chuẩn 5512 sau:\n{plan_json_str}\n\n"
            f"Hãy soạn cấu trúc Slide bài giảng JSON cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}.\n"
            f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
            f"{rag_instruction}"
        )
    else:
        user_prompt = (
            f"Hãy soạn cấu trúc Slide bài giảng JSON cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}.\n"
            f"Trình độ học lực lớp mục tiêu: '{proficiency_str}'.{target_str}"
            f"{rag_instruction}"
        )

    if approved_outline:
        import json
        items = approved_outline.get("outline_slides", [])
        if not items or len({item.get("id") for item in items}) != len(items) or any(not item.get("id") for item in items):
            raise ValueError("Dàn ý đã duyệt thiếu ID hoặc có ID trùng")
        user_prompt += "\nDÀN Ý ĐÃ DUYỆT (bắt buộc đúng số trang, thứ tự, tiêu đề và các ý; mỗi slide ghi source_outline_id):\n" + json.dumps(approved_outline, ensure_ascii=False)
    slide_deck = llm_gateway.generate_structured(
        prompt=user_prompt, system_prompt=SLIDE_SYSTEM_PROMPT,
        response_schema=SlideDeckSchema, task_type="slide", model_provider=model_provider, model_id=model_id)
    if not slide_deck or not slide_deck.slides:
        raise ValueError("Nhà cung cấp chưa trả nội dung slide")
    for field in ("review_token", "quality_report"):
        if slide_deck.model_extra:
            slide_deck.model_extra.pop(field, None)
    if approved_outline:
        items = approved_outline["outline_slides"]
        if len(slide_deck.slides) != len(items):
            raise ValueError("Số slide không khớp dàn ý đã duyệt; cần sinh lại")
        for slide, item in zip(slide_deck.slides, items):
            if slide.source_outline_id != item["id"] or slide.title != item["title"]:
                raise ValueError("Slide không giữ định danh/thứ tự/tiêu đề dàn ý đã duyệt")
            required = item.get("bullet_points") or item.get("key_points") or []
            if any(point not in slide.bullet_points for point in required):
                raise ValueError("Slide bỏ nội dung đã duyệt trong dàn ý")
            from lessonai.services.generation.outline_contract import validate_slide_role
            validate_slide_role(slide.model_dump(mode="json"), item)
    from lessonai.services.content_blocks import block_errors
    for slide in slide_deck.slides:
        errors = list(block_errors(slide.model_dump(mode="json")))
        if errors:
            raise ValueError(errors[0][1])
    allowed={(ref.get("source_type"),ref.get("id")):ref for ref in source_refs}
    for slide in slide_deck.slides:
        for ref in slide.source_refs or []:
            canonical = allowed.get((ref.source_type, ref.id))
            if canonical is None:
                raise ValueError("AI gắn nguồn không được cung cấp trong ngữ cảnh")
            supplied_hash = ref.model_dump().get("sha256")
            if supplied_hash and supplied_hash != canonical.get("sha256"):
                raise ValueError("AI gắn phiên bản nguồn không khớp ngữ cảnh")
            # Bind attribution to the exact source version actually supplied.
            if canonical.get("sha256"):
                ref.sha256 = canonical["sha256"]
    # A source ID returned by the model is an attribution to review, not proof.
    return slide_deck
