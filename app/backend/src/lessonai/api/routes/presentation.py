from fastapi import HTTPException
from lessonai.schemas.schemas import OutlineRequest, OutlineResponse
from lessonai.services.generation import generate_presentation_outline
from lessonai.llm.gateway import classify_generation_error
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/v1/presentation/outline", response_model=OutlineResponse)
@router.post("/api/presentation/outline", response_model=OutlineResponse)
def generate_outline_endpoint(req: OutlineRequest):
    """
    Trạm 2 Outline API theo FRONTEND_ARCHITECTURE.md (Mục 3.2 & Mục 7):
    Nhận chủ đề và cấu hình, sinh Dàn ý các slide (tiêu đề, hoạt động, visual_type, gạch đầu dòng)
    để giáo viên duyệt và chỉnh sửa trước khi sinh slide chi tiết.
    """
    try:
        return generate_presentation_outline(
            topic=req.topic,
            subject=req.subject,
            grade=req.grade,
            num_slides=req.num_slides,
            lesson_id=req.lesson_id,
            class_proficiency=req.class_proficiency,
            use_rag=req.use_rag,
            model_provider=req.model_provider,
            model_id=req.model_id,
            tone=req.tone,
            language=req.language
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=classify_generation_error(e, "dàn ý")) from e
