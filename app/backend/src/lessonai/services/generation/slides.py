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
    plan: Optional[LessonPlanSchema] = None
) -> SlideDeckSchema:
    """
    Soạn Slide bài giảng định tuyến qua LLM Gateway (Groq Llama 3.3 / Gemini 2.5 Flash).
    Tích hợp Pedagogical RAG Grounding & Curated Pedagogical Fallback chống lỗi 500 khi mạng rớt hoặc hết quota.
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

    try:
        # Gọi qua Gateway có Auto-Fallback
        slide_deck = llm_gateway.generate_structured(
            prompt=user_prompt,
            system_prompt=SLIDE_SYSTEM_PROMPT,
            response_schema=SlideDeckSchema,
            task_type="slide"
        )
        # Đảm bảo gán source_refs và activity_type cho các slide nếu cần
        if slide_deck and slide_deck.slides:
            for s in slide_deck.slides:
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
        return slide_deck
    except Exception as e:
        print(f"[AI Service] Kích hoạt Curated Fallback SlideDeck cho môn {subject}, lớp {grade}, bài '{topic}' do: {str(e)[:80]}")
        from lessonai.services.generation.fallback import get_curated_slide_deck
        return get_curated_slide_deck(topic=topic, subject=subject, grade=grade, lesson_id=resolved_lid, plan=plan)

