from typing import Union, Dict, Any
from urllib.parse import quote
from fastapi import HTTPException
from fastapi.responses import Response
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.exporters.docx_exporter import export_lesson_plan_to_docx
from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
from lessonai.exporters.dual_package_exporter import export_dual_package, sanitize_filename
from lessonai.utils.temp_file_cleaner import cleanup_memory_and_figures
from fastapi import APIRouter
from pydantic import ValidationError

router = APIRouter()

@router.post("/api/v1/lesson-plan/export-docx")
def export_docx_endpoint(payload: Union[Dict[str, Any], LessonPlanSchema]):
    """
    API 2: Nhận dữ liệu Giáo án JSON (và tùy chọn SlideDeck để đồng bộ) và trả về file Word (.docx) chuẩn CV 5512.
    """
    try:
        actual_plan = payload
        slide_deck = None
        if isinstance(payload, dict):
            if "plan" in payload or "lesson_plan" in payload:
                actual_plan = payload.get("plan") or payload.get("lesson_plan")
            slide_deck = payload.get("slide_deck")

        if actual_plan is None:
            raise HTTPException(status_code=400, detail="Không tìm thấy nội dung giáo án hợp lệ để xuất file Word")

        docx_stream = export_lesson_plan_to_docx(actual_plan, slide_deck=slide_deck)

        title = "Giao_An_5512"
        if isinstance(actual_plan, LessonPlanSchema):
            title = actual_plan.lesson_title or title
        elif isinstance(actual_plan, dict):
            title = actual_plan.get("lesson_title") or title
        elif slide_deck and isinstance(slide_deck, dict):
            title = slide_deck.get("presentation_title") or title

        safe_title = sanitize_filename(title, max_length=50)
        safe_filename = f"Giao_An_5512_{safe_title}.docx"
        url_encoded_filename = quote(safe_filename)

        return Response(
            content=docx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"; filename*=utf-8\'\'{url_encoded_filename}'
            }
        )
    except HTTPException:
        raise
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors(include_context=False)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Không thể xuất Word. Nội dung bản soạn được giữ nguyên.") from error


@router.post("/api/v1/lesson-plan/export-slide")
def export_slide_endpoint(deck: SlideDeckSchema):
    """
    API 3: Nhận dữ liệu SlideDeck JSON và trả về file PowerPoint (.pptx) sinh qua python-pptx Hybrid (OMML + Matplotlib).
    """
    try:
        pptx_stream = export_slide_deck_to_pptx(deck)
        deck_title = deck.presentation_title or "Bai_Giang"
        safe_title = sanitize_filename(deck_title, max_length=50)
        safe_filename = f"Slide_{safe_title}.pptx"
        url_encoded_filename = quote(safe_filename)

        return Response(
            content=pptx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"; filename*=utf-8\'\'{url_encoded_filename}'
            }
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Không thể xuất PowerPoint. Nội dung bản soạn được giữ nguyên.") from error
    finally:
        cleanup_memory_and_figures()


@router.post("/api/v1/lesson-plan/export-dual-package")
def export_dual_package_endpoint(payload: Dict[str, Any]):
    """
    API 3B (Dual-Package): Xuất trọn bộ Kế hoạch bài dạy Word (.docx) & Bài giảng Slide (.pptx)
    đã được đồng bộ hóa nội dung (Sync Dual-Mode) đóng gói trong định dạng .zip chuẩn nén,
    kèm mã băm SHA-256 xác thực và hướng dẫn sư phạm chi tiết.
    """
    try:
        plan_raw = payload.get("plan") or payload.get("lesson_plan")
        deck_raw = payload.get("slide_deck") or payload.get("deck")

        if not plan_raw and not deck_raw:
            raise HTTPException(
                status_code=400,
                detail="Cần cung cấp ít nhất Kế hoạch bài dạy ('plan') hoặc Slide ('slide_deck') để xuất gói ZIP."
            )

        result = export_dual_package(payload)
        url_encoded_filename = quote(result.filename)

        return Response(
            content=result.zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{result.filename}"; filename*=utf-8\'\'{url_encoded_filename}',
                "X-Dual-Package-Docs-Count": str(result.file_count),
                "X-Dual-Package-SHA256": result.zip_sha256,
                "X-Docx-SHA256": result.docx_sha256,
                "X-Pptx-SHA256": result.pptx_sha256,
            }
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất trọn bộ Dual-Package ZIP: {str(e)}")
    finally:
        cleanup_memory_and_figures()
