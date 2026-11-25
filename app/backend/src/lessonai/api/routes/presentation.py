from fastapi import HTTPException
from lessonai.schemas.schemas import OutlineRequest, OutlineResponse
from lessonai.services.generation import generate_presentation_outline
from lessonai.llm.gateway import classify_generation_error
from fastapi import APIRouter

from lessonai.schemas.workbench_outline import (
    WorkbenchLessonMatch, WorkbenchOutlineRequest, WorkbenchOutlineResponse, WorkbenchRequestText,
)
from lessonai.services.generation.workbench_outline import generate_outline, identify_lesson, resolve_lesson

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


@router.post("/api/v1/workbench/outline/identify", response_model=WorkbenchLessonMatch)
def identify_workbench_lesson(req: WorkbenchRequestText):
    return identify_lesson(req.request)


@router.post("/api/v1/workbench/outline", response_model=WorkbenchOutlineResponse)
def generate_workbench_outline(req: WorkbenchOutlineRequest):
    lesson_id, title = resolve_lesson(req.request, req.lesson_id)
    if req.lesson_id is not None and lesson_id is None:
        raise HTTPException(422, detail={"code": "unknown_textbook_lesson", "message": "Không tìm thấy bài SGK đã chọn."})
    try:
        return generate_outline(req, lesson_id, title)
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "Dàn ý")) from error
