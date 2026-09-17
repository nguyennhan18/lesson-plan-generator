from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

import sys
import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas.schemas import LessonPlanSchema, LessonRequest
from schemas.slide_schema import SlideDeckSchema
from services.ai_service import generate_lesson_plan, generate_slide_deck
from exporters.docx_exporter import export_lesson_plan_to_docx
from exporters.slide_exporter import export_slide_deck_to_pptx

app = FastAPI(
    title="LessonAI-5512",
    description="Hệ thống tự động sinh Kế hoạch bài dạy theo Công văn 5512 và Slide bài giảng",
    version="0.1.0"
)

# Cấu hình CORS để giao diện Web dễ dàng gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Chào mừng bạn đến với LessonAI-5512 API Server",
        "docs_url": "/docs"
    }

@app.post("/api/v1/lesson-plan/generate")
def generate_lesson_plan_endpoint(req: LessonRequest):
    """
    API 1: Nhận bài dạy từ người dùng, gọi AI Gemini sinh Giáo án & kiểm tra qua Validator 5512.
    """
    try:
        plan, val_result = generate_lesson_plan(
            topic=req.topic,
            subject=req.subject,
            grade=req.grade
        )
        return {
            "is_valid": val_result.is_valid,
            "errors": val_result.errors,
            "warnings": val_result.warnings,
            "plan": plan.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh giáo án: {str(e)}")

@app.post("/api/v1/lesson-plan/export-docx")
def export_docx_endpoint(plan: LessonPlanSchema):
    """
    API 2: Nhận dữ liệu Giáo án JSON và trả về file Word (.docx) cho người dùng tải xuống.
    """
    try:
        docx_stream = export_lesson_plan_to_docx(plan)
        filename = f"Giao_An_{plan.lesson_title}.docx".replace(" ", "_")
        
        return Response(
            content=docx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file Word: {str(e)}")

@app.post("/api/v1/lesson-plan/export-slide")
def export_slide_endpoint(deck: SlideDeckSchema):
    """
    API 3: Nhận dữ liệu SlideDeck JSON và trả về file PowerPoint (.pptx) sinh qua python-pptx Hybrid (OMML + Matplotlib).
    """
    try:
        pptx_stream = export_slide_deck_to_pptx(deck)
        filename = f"Slide_{deck.presentation_title}.pptx".replace(" ", "_")
        
        return Response(
            content=pptx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file Slide PPTX: {str(e)}")

@app.post("/api/v1/slide/generate")
def generate_slide_endpoint(req: LessonRequest):
    """
    API 4: Nhận yêu cầu từ người dùng, gọi Gemini AI sinh cấu trúc JSON Slide bài giảng (SlideDeckSchema).
    """
    try:
        slide_deck = generate_slide_deck(
            topic=req.topic,
            subject=req.subject,
            grade=req.grade
        )
        return slide_deck.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh Slide: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print("🚀 Đang khởi chạy Server FastAPI tại http://localhost:8000 ...")
    print("📖 Xem tài liệu Swagger UI thử nghiệm API tại: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, app_dir=app_dir)
