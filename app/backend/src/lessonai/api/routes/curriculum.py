from fastapi import HTTPException
from lessonai.schemas.schemas import RAGPreviewRequest
from lessonai.rag.curriculum_registry import CurriculumRegistry
from lessonai.rag.retriever import Math12HybridRetriever
from fastapi import APIRouter
from lessonai.rag.content_units import approved_units

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
                l_copy["available_slides_count"] = len(approved_units(retriever.slides_by_lesson.get(lid, [])))
                l_copy["available_questions_count"] = len(approved_units(retriever.questions_by_lesson.get(lid, [])))
                lessons.append(l_copy)
            ch_copy["lessons"] = lessons
            chapters.append(ch_copy)

        return {
            "subject": curriculum_data.get("subject", "Toán học"),
            "grade": curriculum_data.get("grade", 12),
            "curriculum_standard": curriculum_data.get("curriculum_standard", "GDPT 2018 (Kết nối tri thức với cuộc sống)"),
            "total_chapters": len(chapters),
            "total_lessons": len(registry.get_all_lessons()),
            "total_slides": len(approved_units(retriever.slides)),
            "total_questions": len(approved_units(retriever.questions)),
            "chapters": chapters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải Khung chương trình Toán 12: {str(e)}")


@router.post("/api/v1/rag/preview")
def preview_rag_materials_endpoint(req: RAGPreviewRequest):
    """The sample browser was removed from the production authoring workflow."""
    raise HTTPException(status_code=410, detail={"code":"sample_preview_removed", "message":"Kho xem trước bài mẫu đã được gỡ. Hãy soạn bài từ dữ kiện của giáo viên."})
