from typing import Optional
from lessonai.llm import tracing
from lessonai.llm.gateway import llm_gateway
from lessonai.prompts.roles import OUTLINE_PLANNER_PROMPT
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
    language: Optional[str] = "vi",
    session_id: Optional[str] = None,
) -> OutlineResponse:
    """
    Sinh Dàn ý (Outline) bài thuyết trình/bài giảng trước khi sinh slide chi tiết (Trạm 2).
    Tích hợp Langfuse Chain & Role Observation (`role.outline_planner`), gom chung `session_id`
    với chuỗi Giáo án 5512 và Bộ Slide tiếp theo.
    """
    from lessonai.rag.curriculum_registry import infer_lesson_id
    from lessonai.schemas.slide_schema import SlideType, SlideLayout, ChartType

    resolved_lid = lesson_id or infer_lesson_id(topic)

    with tracing.trace_chain(
        "chain.outline_generation",
        session_id=session_id,
        lesson_id=resolved_lid,
        topic=topic,
        proficiency=class_proficiency or "standard",
        input_data={
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "num_slides": num_slides,
            "lesson_id": resolved_lid,
            "class_proficiency": class_proficiency,
        },
    ) as chain_obs:
        prompt = (
            f"Hãy lập Dàn ý (Outline) bài thuyết trình {num_slides} slide cho bài học sau:\n"
            f"Chủ đề: {topic}\n"
            f"Môn học: {subject}, Lớp {grade} (Mã bài: {resolved_lid})\n"
            f"Trình độ học lực: {class_proficiency}\n"
            f"Ngôn ngữ: {language}, Phong cách: {tone}\n"
            f"Yêu cầu:\n"
            f"- Cấu trúc đúng 5 bước sư phạm (Khởi động -> Khái niệm -> Ví dụ/3D -> Luyện tập trắc nghiệm -> Tổng kết)\n"
            f"- Mỗi slide có 2-4 gạch đầu dòng ý chính trọng tâm.\n"
            f"- Đánh dấu loại trực quan (visual_type): '3D Geometry', '2D Function Plot', 'Interactive Quiz', 'Concept Highlight', hoặc 'Text & Formula'.\n"
            f"- Nếu chủ đề là hình học không gian, ghi rõ has_3d=True và polyhedron_type (cube, pyramid_square, pyramid_triangle, prism_triangle)."
        )

        try:
            with tracing.observe_role(
                OUTLINE_PLANNER_PROMPT.name,
                prompt_name=OUTLINE_PLANNER_PROMPT.name,
                prompt_version=OUTLINE_PLANNER_PROMPT.version,
                input_data={"topic": topic, "num_slides": num_slides, "lesson_id": resolved_lid},
            ) as role_obs:
                outline_obj = llm_gateway.generate_structured(
                    prompt=prompt,
                    system_prompt=OUTLINE_PLANNER_PROMPT.system_prompt,
                    response_schema=OutlineResponse,
                    task_type="outline",
                    role_name=OUTLINE_PLANNER_PROMPT.name,
                    prompt_name=OUTLINE_PLANNER_PROMPT.name,
                    prompt_version=OUTLINE_PLANNER_PROMPT.version,
                )
                if outline_obj and outline_obj.outline_slides:
                    for idx, s in enumerate(outline_obj.outline_slides):
                        if not s.id:
                            s.id = f"outline-slide-{idx + 1}"
                        s.slide_index = idx + 1
                    outline_obj.session_id = session_id
                    role_obs.set_output({"num_slides": len(outline_obj.outline_slides)})
                    chain_obs.set_output({"title": outline_obj.title, "num_slides": len(outline_obj.outline_slides)})
                    tracing.record_trace_score("outline_generated", 1.0)
                    tracing.record_trace_score("fallback_used", 0.0)
                    return outline_obj
        except Exception as e:
            print(f"[AI Service] LLM outline exception ({e}), kích hoạt Curated Outline Fallback...")
            chain_obs.mark_warning(f"Curated Outline Fallback: {str(e)[:120]}")

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

            slides_list.append(
                OutlineSlideItem(
                    id=f"outline-slide-{idx + 1}",
                    slide_index=idx + 1,
                    title=s.title or f"Nội dung #{idx + 1}",
                    activity_type=act_type,
                    visual_type=vis_type,
                    bullet_points=s.bullet_points if s.bullet_points else [f"Trọng tâm kiến thức mục {idx + 1}"],
                    math_focus=s.main_definition_latex,
                    has_3d=bool(s.has_3d),
                    polyhedron_type=s.polyhedron_type,
                )
            )

        while len(slides_list) < num_slides:
            curr_i = len(slides_list) + 1
            slides_list.append(
                OutlineSlideItem(
                    id=f"outline-slide-{curr_i}",
                    slide_index=curr_i,
                    title=f"Phần {curr_i}: Ứng dụng & Luyện tập mở rộng",
                    activity_type="Vận dụng & Mở rộng",
                    visual_type="Text & Formula",
                    bullet_points=[
                        f"Thực hành giải bài tập mức độ vận dụng cho chủ đề {topic}.",
                        "Thảo luận nhóm và phân tích kết quả tính toán.",
                    ],
                    math_focus=None,
                    has_3d=False,
                )
            )

        result = OutlineResponse(
            title=topic,
            theme="gallery_monochrome",
            num_slides=len(slides_list),
            subject=subject,
            grade=grade,
            class_proficiency=class_proficiency or "standard",
            lesson_id=resolved_lid,
            session_id=session_id,
            outline_slides=slides_list,
        )
        chain_obs.set_output({"title": result.title, "num_slides": result.num_slides, "fallback": True})
        tracing.record_trace_score("outline_generated", 1.0)
        tracing.record_trace_score("fallback_used", 1.0, comment="curated_outline_fallback")
        return result
