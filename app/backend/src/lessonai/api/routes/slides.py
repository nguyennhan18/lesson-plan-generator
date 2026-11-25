from fastapi import HTTPException
from fastapi.responses import Response
from lessonai.schemas.schemas import LessonRequest
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.generation import generate_slide_deck
from lessonai.llm.gateway import classify_generation_error
from lessonai.exporters.graph_generator import generate_math_plot, is_plottable
from lessonai.core.feature_availability import ExpressionProcessingUnavailable
from lessonai.core.signing import SigningKeyUnavailable
from fastapi import APIRouter
from lessonai.services.rendering import enrich_slide_deck_with_renders

router = APIRouter()

@router.post("/api/v1/slide/generate")
def generate_slide_endpoint():
    """Đã nghỉ hưu ở #59: thay bằng /api/v1/workbench/slides."""
    raise HTTPException(
        status_code=410,
        detail={
            "code": "legacy_slide_generation_retired",
            "message": "Endpoint sinh slide từ Kế hoạch bài dạy đã dừng; hãy dùng /api/v1/workbench/slides của Bàn làm việc.",
        },
    )


@router.post("/api/v1/slide/enrich")
def enrich_slide_endpoint(deck: dict):
    """Bổ sung ảnh đồ thị và công thức vào dữ liệu slide deck bất kỳ để hiển thị đúng trên front-end"""
    try:
        return enrich_slide_deck_with_renders(deck)
    except SigningKeyUnavailable:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý slide preview: {str(e)}")


@router.post("/api/v1/chart/render")
def render_chart_endpoint(spec: dict):
    """Render đồ thị từ cấu hình chart_spec và trả về file ảnh PNG trực tiếp"""
    from lessonai.services.visual_requirements import VisualError
    from lessonai.core.jobs import JobError
    from lessonai.services.math_expression import ExpressionError
    try:
        png_bytes = generate_math_plot(spec)
        return Response(content=png_bytes, media_type="image/png")
    except VisualError as error:
        raise HTTPException(409, detail={"code": error.code, "message": str(error)}) from error
    except ExpressionError as error:
        raise HTTPException(422, detail=error.detail()) from error
    except JobError as error:
        status = 503 if error.code == "job_busy" else 504 if error.code == "job_timeout" else 422
        raise HTTPException(status, detail={"code": error.code, "message": str(error)}) from error
    except (ValueError,KeyError,TypeError) as error:
        raise HTTPException(422, detail={"code": "chart_invalid", "message": str(error)}) from error
