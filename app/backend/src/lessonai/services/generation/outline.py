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
    model_id: Optional[str] = "gemini-2.5-flash",
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
        f"- Nếu chủ đề là hình học không gian, ghi rõ has_3d=True và polyhedron_type (cube, pyramid_square, pyramid_triangle, prism_triangle)."
    )

    try:
        outline_obj = llm_gateway.generate_structured(
            prompt=prompt,
            system_prompt=(
                "Bạn là chuyên gia sư phạm THPT. Hãy lập dàn ý bài giảng thuyết trình súc tích, chuẩn mực."
            ),
            response_schema=OutlineResponse,
            task_type="outline"
        )
        if outline_obj and outline_obj.outline_slides:
            for idx, s in enumerate(outline_obj.outline_slides):
                if not s.id:
                    s.id = f"outline-slide-{idx + 1}"
                s.slide_index = idx + 1
            return outline_obj
    except Exception as e:
        print(f"[AI Service] LLM outline exception ({e}), kích hoạt Curated Outline Fallback...")

    from lessonai.services.generation.fallback import get_curated_slide_deck
    fallback_deck = get_curated_slide_deck(topic=topic, subject=subject, grade=grade, lesson_id=resolved_lid)
    slides_list = []
    deck_slides = fallback_deck.slides if (fallback_deck and fallback_deck.slides) else []

    for idx, s in enumerate(deck_slides[:num_slides]):
        act_type = "Hình thành kiến thức"
        vis_type = "Concept Highlight"
        if s.type == SlideType.WARM_UP_SLIDE:
            act_type = "Khởi động"
            vis_type = "Title & Overview"
        elif s.type == SlideType.EXERCISE_SLIDE or s.layout == SlideLayout.QUIZ_OPTION:
            act_type = "Luyện tập & Trắc nghiệm"
            vis_type = "Interactive Quiz"
        elif s.has_3d:
            vis_type = "3D Geometry"
        elif s.chart_spec and s.chart_spec.kind != ChartType.NONE:
            vis_type = "2D Function Plot"
        elif s.type == SlideType.SUMMARY_SLIDE:
            act_type = "Tổng kết & Dặn dò"
            vis_type = "Summary List"

        slides_list.append(OutlineSlideItem(
            id=f"outline-slide-{idx + 1}",
            slide_index=idx + 1,
            title=s.title or f"Nội dung #{idx + 1}",
            activity_type=act_type,
            visual_type=vis_type,
            bullet_points=s.bullet_points if s.bullet_points else [f"Trọng tâm kiến thức mục {idx + 1}"],
            math_focus=s.main_definition_latex,
            has_3d=bool(s.has_3d),
            polyhedron_type=s.polyhedron_type
        ))

    while len(slides_list) < num_slides:
        curr_i = len(slides_list) + 1
        slides_list.append(OutlineSlideItem(
            id=f"outline-slide-{curr_i}",
            slide_index=curr_i,
            title=f"Phần {curr_i}: Ứng dụng & Luyện tập mở rộng",
            activity_type="Vận dụng & Mở rộng",
            visual_type="Text & Formula",
            bullet_points=[
                f"Thực hành giải bài tập mức độ vận dụng cho chủ đề {topic}.",
                "Thảo luận nhóm và phân tích kết quả tính toán."
            ],
            math_focus=None,
            has_3d=False
        ))

    return OutlineResponse(
        title=topic,
        theme="gallery_monochrome",
        num_slides=len(slides_list),
        subject=subject,
        grade=grade,
        class_proficiency=class_proficiency or "standard",
        lesson_id=resolved_lid,
        outline_slides=slides_list
    )

