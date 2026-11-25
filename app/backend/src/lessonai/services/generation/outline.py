from typing import Optional
from uuid import uuid4

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
    use_rag: bool = False,  # Retained for older API callers; generation does not use RAG.
    model_provider: Optional[str] = "gemini",
    model_id: Optional[str] = None,
    tone: Optional[str] = "academic",
    language: Optional[str] = "vi",
    session_id: Optional[str] = None,
) -> OutlineResponse:
    """
    Sinh Dàn ý (Outline) bài thuyết trình/bài giảng trước khi sinh slide chi tiết (Trạm 2).
    Tuân thủ nghiêm ngặt ADR 0001 (Zero-Fallback) và ghi nhận chuỗi Langfuse v5 (`chain.outline_generation`).
    """
    from lessonai.rag.curriculum_registry import infer_lesson_id

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
        },
    ) as chain_obs:
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
                model_provider=model_provider,
                model_id=model_id,
                role_name=OUTLINE_PLANNER_PROMPT.name,
                prompt_name=OUTLINE_PLANNER_PROMPT.name,
                prompt_version=OUTLINE_PLANNER_PROMPT.version,
            )
            role_obs.set_output({
                "slides_count": len(outline_obj.outline_slides) if outline_obj and outline_obj.outline_slides else 0
            })

        with tracing.observe_evaluator(
            "gate.outline_slide_count",
            input_data={"expected_num_slides": num_slides},
        ) as gate_obs:
            if not outline_obj or len(outline_obj.outline_slides) != num_slides:
                gate_obs.fail("Dàn ý chưa đủ đúng số mục được yêu cầu")
                tracing.record_trace_score("outline_valid", 0.0)
                raise ValueError("Dàn ý chưa đủ đúng số mục được yêu cầu")
            gate_obs.set_output({"is_valid": True, "num_slides": len(outline_obj.outline_slides)})

        for idx, slide in enumerate(outline_obj.outline_slides, 1):
            slide.id = str(uuid4())
            slide.slide_index = slide.slide_number = idx
        outline_obj.topic = topic
        outline_obj.session_id = session_id
        tracing.record_trace_score("outline_valid", 1.0)
        chain_obs.set_output({"title": outline_obj.title, "num_slides": len(outline_obj.outline_slides)})
        return outline_obj
