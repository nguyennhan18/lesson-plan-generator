from fastapi import HTTPException
from lessonai.schemas.schemas import OutlineRequest, OutlineResponse
from lessonai.services.generation import generate_presentation_outline
from lessonai.llm.gateway import classify_generation_error
from fastapi import APIRouter

from lessonai.schemas.workbench_outline import (
    WorkbenchLessonMatch, WorkbenchOutlineRequest, WorkbenchOutlineResponse, WorkbenchRequestText,
)
from lessonai.schemas.workbench_slides import (
    WorkbenchItemSlidesRequest, WorkbenchSlidesRequest, WorkbenchSlidesResponse,
)
from lessonai.services.generation.workbench_outline import generate_outline, identify_lesson, resolve_lesson
from lessonai.services.generation.workbench_slides import (
    generate_workbench_slides, regenerate_workbench_item_slides,
)
from lessonai.services.generation.workbench_lesson_plan import (
    WorkbenchLessonPlanResponse, generate_workbench_lesson_plan,
)

router = APIRouter()

@router.post("/api/v1/presentation/outline")
@router.post("/api/presentation/outline")
def generate_outline_endpoint():
    """Đã nghỉ hưu ở #59: thay bằng /api/v1/workbench/outline."""
    raise HTTPException(
        status_code=410,
        detail={
            "code": "legacy_outline_retired",
            "message": "Endpoint sinh dàn ý theo num_slides đã dừng; hãy dùng /api/v1/workbench/outline của Bàn làm việc.",
        },
    )


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


@router.post("/api/v1/workbench/slides", response_model=WorkbenchSlidesResponse)
def build_workbench_slides(req: WorkbenchSlidesRequest):
    try:
        return generate_workbench_slides(req)
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "Bộ slide")) from error


@router.post("/api/v1/workbench/slides/item", response_model=WorkbenchSlidesResponse)
def regenerate_workbench_item(req: WorkbenchItemSlidesRequest):
    try:
        return regenerate_workbench_item_slides(req)
    except KeyError as error:
        raise HTTPException(422, detail={"code": "unknown_outline_item", "message": str(error)}) from error
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "slide của Mục")) from error


@router.post("/api/v1/workbench/lesson-plan", response_model=WorkbenchLessonPlanResponse)
def build_workbench_lesson_plan(req: WorkbenchSlidesRequest):
    try:
        return generate_workbench_lesson_plan(req)
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "Kế hoạch bài dạy")) from error
