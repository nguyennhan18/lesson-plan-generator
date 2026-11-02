from fastapi import HTTPException
from lessonai.schemas.schemas import RAGPreviewRequest
from lessonai.rag.curriculum_registry import CurriculumRegistry
from lessonai.rag.retriever import Math12HybridRetriever
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/curriculum/math12")
def get_math12_curriculum_endpoint():
    """
    Trả về toàn bộ Khung Chương trình Toán 12 (CT GDPT 2018 - SGK Kết nối tri thức với cuộc sống),
    bao gồm danh mục Chương, Bài học, YCCĐ, từ khóa và số lượng slide / câu hỏi có sẵn trong kho RAG.
    """
    try:
        registry = CurriculumRegistry.get_instance()
        retriever = Math12HybridRetriever.get_instance()

        curriculum_data = registry.curriculum
        chapters = []
        for ch in curriculum_data.get("chapters", []):
            ch_copy = dict(ch)
            lessons = []
            for l in ch.get("lessons", []):
                l_copy = dict(l)
                lid = l.get("lesson_id")
                l_copy["available_slides_count"] = len(retriever.slides_by_lesson.get(lid, []))
                l_copy["available_questions_count"] = len(retriever.questions_by_lesson.get(lid, []))
                lessons.append(l_copy)
            ch_copy["lessons"] = lessons
            chapters.append(ch_copy)

        return {
            "subject": curriculum_data.get("subject", "Toán học"),
            "grade": curriculum_data.get("grade", 12),
            "curriculum_standard": curriculum_data.get("curriculum_standard", "GDPT 2018 (Kết nối tri thức với cuộc sống)"),
            "total_chapters": len(chapters),
            "total_lessons": len(registry.get_all_lessons()),
            "total_slides": len(retriever.slides),
            "total_questions": len(retriever.questions),
            "chapters": chapters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải Khung chương trình Toán 12: {str(e)}")


@router.post("/api/v1/rag/preview")
def preview_rag_materials_endpoint(req: RAGPreviewRequest):
    """
    Xem trước tài nguyên sư phạm được Pedagogical RAG truy xuất cho bài học Toán 12:
    bao gồm YCCĐ, Dàn ý bài giảng (Skeleton), Slide mẫu đẹp nhất và Câu hỏi bài tập thực tế.
    """
    try:
        retriever = Math12HybridRetriever.get_instance()
        skeleton = retriever.retrieve_lesson_skeleton(req.lesson_id)
        slides = retriever.retrieve_exemplar_slides(req.lesson_id, query=req.topic, k=req.k_slides)
        questions = retriever.retrieve_questions(req.lesson_id, proficiency=req.proficiency or "standard", query=req.topic, k=req.k_questions)

        cleaned_slides = []
        for s in slides:
            cleaned_slides.append({
                "slide_id": s.get("slide_id"),
                "title": s.get("title"),
                "activity_type": s.get("activity_type"),
                "layout_hint": s.get("layout_hint"),
                "bullet_points": s.get("bullet_points", []),
                "main_definition_latex": s.get("main_definition_latex"),
                "quality_score": s.get("quality_score", 0.5),
                "source": s.get("source_file", "KNTT12")
            })

        cleaned_questions = []
        for q in questions:
            cleaned_questions.append({
                "question_id": q.get("question_id"),
                "topic": q.get("topic"),
                "question": q.get("question"),
                "difficulty": q.get("difficulty", "medium"),
                "quiz_options": q.get("quiz_options", []),
                "worked_solution_steps": q.get("worked_solution_steps", []),
                "answer": q.get("answer")
            })

        return {
            "lesson_id": req.lesson_id,
            "topic": req.topic or skeleton.get("title"),
            "chapter_id": skeleton.get("chapter_id"),
            "chapter_title": skeleton.get("chapter_title"),
            "periods": skeleton.get("periods", 2),
            "yccd": skeleton.get("yccd", []),
            "keywords": skeleton.get("keywords", []),
            "deck_outline": skeleton.get("deck_outline", []),
            "slides_preview": cleaned_slides,
            "questions_preview": cleaned_questions,
            "total_available_slides": len(retriever.slides_by_lesson.get(req.lesson_id, [])),
            "total_available_questions": len(retriever.questions_by_lesson.get(req.lesson_id, []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xem trước tài nguyên RAG: {str(e)}")

