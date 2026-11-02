from fastapi import HTTPException
from fastapi.responses import Response
from lessonai.schemas.schemas import LessonRequest
from lessonai.services.generation import generate_slide_deck
from lessonai.exporters.graph_generator import generate_math_plot, is_plottable
from lessonai.core.feature_availability import ExpressionProcessingUnavailable
from fastapi import APIRouter
from lessonai.services.rendering import enrich_slide_deck_with_renders

router = APIRouter()

@router.post("/api/v1/slide/generate")
def generate_slide_endpoint(req: LessonRequest):
    """
    API 4: Nhận yêu cầu từ người dùng, gọi Gemini AI sinh cấu trúc JSON Slide bài giảng (SlideDeckSchema).
    Nếu req.plan có dữ liệu, Slide sẽ được đồng bộ chính xác theo Kế hoạch bài dạy 5512.
    Tự động kết xuất ảnh đồ thị Matplotlib để Front-end hiển thị đồng bộ 100% với file PowerPoint.
    """
    try:
        slide_deck = generate_slide_deck(
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
        return enrich_slide_deck_with_renders(deck_dict)
    except Exception as e:
        print(f"[API] Sự cố sinh slide ({e}). Tự động kích hoạt Curated Fallback SlideDeck...")
        from lessonai.services.generation.fallback import get_curated_slide_deck
        fallback_deck = get_curated_slide_deck(
            topic=req.topic,
            subject=req.subject,
            grade=req.grade,
            lesson_id=req.lesson_id,
            plan=req.plan
        )
        return enrich_slide_deck_with_renders(fallback_deck.model_dump())


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
    try:
        from lessonai.exporters.graph_generator import expression_chart_is_disabled
        if expression_chart_is_disabled(spec):
            raise ExpressionProcessingUnavailable()
        if not is_plottable(spec):
            raise HTTPException(status_code=400, detail="Cấu hình chart_spec không thể vẽ thành đồ thị hàm số")
        png_bytes = generate_math_plot(spec)
        return Response(content=png_bytes, media_type="image/png")
    except HTTPException:
        raise
    except ExpressionProcessingUnavailable as error:
        raise HTTPException(status_code=503, detail={"code": error.code, "message": str(error)}) from error
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi vẽ đồ thị: {str(e)}")

