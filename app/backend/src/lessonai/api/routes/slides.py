from fastapi import HTTPException
from fastapi.responses import Response
from lessonai.schemas.schemas import LessonRequest
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.generation import generate_slide_deck
from lessonai.llm.gateway import classify_generation_error
from lessonai.exporters.graph_generator import generate_math_plot, is_plottable
from lessonai.core.feature_availability import ExpressionProcessingUnavailable
from fastapi import APIRouter
from lessonai.services.rendering import enrich_slide_deck_with_renders

router = APIRouter()

@router.post("/api/v1/slide/generate", response_model=SlideDeckSchema)
def generate_slide_endpoint(req: LessonRequest):
    """
    API 4: Nhận yêu cầu từ người dùng, gọi Gemini AI sinh cấu trúc JSON Slide bài giảng (SlideDeckSchema).
    Nếu req.plan có dữ liệu, Slide sẽ được đồng bộ chính xác theo Kế hoạch bài dạy 5512.
    Tự động kết xuất ảnh đồ thị Matplotlib để Front-end hiển thị đồng bộ 100% với file PowerPoint.
    """
    try:
        slide_deck = generate_slide_deck(
            approved_outline=req.approved_outline, model_provider=req.model_provider, model_id=req.model_id,
            topic=req.topic,
            subject=req.subject,
            grade=req.grade,
            lesson_id=req.lesson_id,
            use_rag=req.use_rag,
            plan=req.plan,
            class_proficiency=req.class_proficiency,
            target_outcome=req.target_outcome
        )
        deck_dict = slide_deck.model_dump()
        from lessonai.services.content_quality import evaluate_deck
        deck_dict["quality_report"] = evaluate_deck(deck_dict)
        return enrich_slide_deck_with_renders(deck_dict)
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "slide")) from error


@router.post("/api/v1/slide/enrich")
def enrich_slide_endpoint(deck: dict):
    """Bổ sung ảnh đồ thị và công thức vào dữ liệu slide deck bất kỳ để hiển thị đúng trên front-end"""
    try:
        return enrich_slide_deck_with_renders(deck)
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
