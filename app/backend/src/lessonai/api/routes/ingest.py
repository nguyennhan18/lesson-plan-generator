import os
from fastapi import HTTPException, UploadFile, File
from lessonai.services.analytics import classify_grade_sheet
from lessonai.parsers.pptx_parser import parse_pptx
from lessonai.parsers.docx_parser import parse_docx
from lessonai.parsers.common import ParsedDocumentResponse
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/ingest', tags=['Ingest'])

@router.post("/parse-document", response_model = ParsedDocumentResponse)

async def parse_document_endpoint(
    file: UploadFile = File(..., description="File giáo án (.docx) or slide (.pptx) cần bóc tách")
):

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".pptx", ".docx"):
        raise HTTPException(
            status_code = 400,
            detail = f"định dạng '{ext}' không được hỗ trợ. Chỉ chấp nhận file .pptx or docx"
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code = 400,
                detail = "File tải lên rỗng"
            )
        if ext == ".pptx":
            parsed_result = parse_pptx(content)
        elif ext == ".docx":
            parsed_result = parse_docx(content)

        return {
            "filename" : filename,
            **parsed_result,

        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Loiox khi phân tích file '{filename}' : {str(e)}"
        )
    finally:
        await file.close()


@router.post("/classify-grades")
async def classify_grades_endpoint(
    file: UploadFile = File(..., description="File Excel/CSV chứa điểm số")
):


    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".xlsx", ".xlsm", ".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng '{ext}' không được hỗ trợ. Chỉ nhận file .xlsx, .xlsm hoặc .csv"
        )
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="File bảng điểm tải lên bị rỗng"
            )
        result = classify_grade_sheet(content, filename=filename)
        return {
            "filename": filename,
            **result.to_dict()
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code = 400,
            detail = str(ve)

        )
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Lỗi khi phân tích: '{filename}': {str(e)}"
        )
    finally:
        await file.close()

