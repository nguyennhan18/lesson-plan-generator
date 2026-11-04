from typing import Optional
from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.schemas import OutlineResponse, OutlineSlideItem


def generate_presentation_outline(
    topic: str,
    subject: str = "Toán học",
    grade: int = 12,
    num_slides: int = 8,
    lesson_id: Optional[str] = None,
    class_proficiency: Optional[str] = "standard",
    use_rag: bool = True,
    model_provider: Optional[str] = "gemini",
    model_id: Optional[str] = None,
    tone: Optional[str] = "academic",
    language: Optional[str] = "vi"
) -> OutlineResponse:
    """
    Sinh Dàn ý (Outline) bài thuyết trình/bài giảng trước khi sinh slide chi tiết (Task Trạm 2 theo FRONTEND_ARCHITECTURE.md).
    Cho phép giáo viên duyệt, chỉnh sửa từng gạch đầu dòng, đổi theme bảng màu.
    """
    from lessonai.rag.curriculum_registry import infer_lesson_id
    from lessonai.schemas.slide_schema import SlideType, SlideLayout, ChartType
    resolved_lid = lesson_id or infer_lesson_id(topic)

    prompt = (
        f"Hãy lập Dàn ý (Outline) bài thuyết trình {num_slides} slide cho bài học sau:\n"
        f"Chủ đề: {topic}\n"
        f"Môn học: {subject}, Lớp {grade}\n"
        f"Trình độ học lực: {class_proficiency}\n"
        f"Ngôn ngữ: {language}, Phong cách: {tone}\n"
        f"Yêu cầu:\n"
        f"- Cấu trúc đúng 5 bước sư phạm (Khởi động -> Khái niệm -> Ví dụ/3D -> Luyện tập trắc nghiệm -> Tổng kết)\n"
        f"- Mỗi slide có 2-4 gạch đầu dòng ý chính trọng tâm.\n"
        f"- Đánh dấu loại trực quan (visual_type): '3D Geometry', '2D Function Plot', 'Interactive Quiz', 'Concept Highlight', hoặc 'Text & Formula'.\n"
        f"- Nếu chủ đề là hình học không gian, ghi rõ has_3d=True và polyhedron_type (cube, square_pyramid_regular, square_pyramid_at_a; trường hợp khác ghi chưa hỗ trợ)."
    )

    if use_rag and resolved_lid:
        from lessonai.rag.context_builder import PedagogicalContextBuilder
        context, _ = PedagogicalContextBuilder.build_slide_deck_context(resolved_lid, topic=topic, proficiency=class_proficiency)
        prompt += "\nNguồn tham khảo; thiếu dữ kiện phải ghi rõ, không thêm hình để lấp chỗ trống:\n" + context
    outline_obj = llm_gateway.generate_structured(
        prompt=prompt, system_prompt="Lập dàn ý theo đúng yêu cầu. Chỉ đề xuất hình khi có dữ kiện, không tự chọn khối mẫu.",
        response_schema=OutlineResponse, task_type="outline", model_provider=model_provider, model_id=model_id)
    if not outline_obj or len(outline_obj.outline_slides) != num_slides:
        raise ValueError("Dàn ý chưa đủ đúng số mục được yêu cầu")
    from uuid import uuid4
    for idx, slide in enumerate(outline_obj.outline_slides, 1):
        slide.id = str(uuid4())
        slide.slide_index = slide.slide_number = idx
    outline_obj.topic = topic
    return outline_obj
