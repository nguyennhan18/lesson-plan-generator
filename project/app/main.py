from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from urllib.parse import quote

import sys
import os
import json
import base64
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_cache"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas.schemas import LessonPlanSchema, LessonRequest
from schemas.slide_schema import SlideDeckSchema
from services.ai_service import generate_lesson_plan, generate_slide_deck
from exporters.docx_exporter import export_lesson_plan_to_docx
from exporters.slide_exporter import export_slide_deck_to_pptx, render_latex_to_bytes
from exporters.graph_generator import generate_math_plot, is_plottable

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

# Mount thư mục static cho giao diện Web
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="""
        <div style="font-family: sans-serif; padding: 40px; text-align: center;">
            <h2>🚀 LessonAI-5512 API Server</h2>
            <p>Server đang hoạt động bình thường.</p>
            <p><a href="/docs">Xem tài liệu API Swagger</a> | <a href="/ui">Giao diện Studio</a></p>
        </div>
    """)

@app.get("/ui", response_class=HTMLResponse)
def ui_page():
    return root()

@app.get("/style.css")
def get_root_css():
    css_file = os.path.join(static_dir, "style.css")
    if os.path.exists(css_file):
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/app.js")
def get_root_js():
    js_file = os.path.join(static_dir, "app.js")
    if os.path.exists(js_file):
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")

@app.get("/api/v1/health")
def health_check():
    """Kiểm tra trạng thái server và cấu hình API key"""
    return {
        "status": "online",
        "has_api_key": bool(os.getenv("GEMINI_API_KEY")),
        "version": "0.1.0"
    }

@app.get("/api/v1/test-cases")
def get_test_cases():
    """Trả về danh sách các ca kiểm thử mẫu để test nhanh trên giao diện"""
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"topic": "Cấp số cộng", "subject": "Toán học", "grade": 11},
        {"topic": "Đạo hàm và ứng dụng", "subject": "Toán học", "grade": 11},
        {"topic": "Phương trình bậc hai một ẩn", "subject": "Toán học", "grade": 9},
        {"topic": "Sóng cơ và sự truyền sóng cơ", "subject": "Vật lý", "grade": 12},
        {"topic": "Khảo sát và vẽ đồ thị hàm số", "subject": "Toán học", "grade": 12}
    ]

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
        raw_filename = f"Giao_An_{plan.lesson_title}.docx".replace(" ", "_")
        safe_filename = quote(raw_filename)
        
        return Response(
            content=docx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=utf-8''{safe_filename}"
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
        raw_filename = f"Slide_{deck.presentation_title}.pptx".replace(" ", "_")
        safe_filename = quote(raw_filename)
        
        return Response(
            content=pptx_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename*=utf-8''{safe_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file Slide PPTX: {str(e)}")

def enrich_slide_deck_with_renders(deck_dict: dict) -> dict:
    """
    Sinh trước ảnh đồ thị Matplotlib và ảnh công thức LaTeX (dưới dạng Base64 Data URL)
    cho từng slide để Front-end hiển thị CHÍNH XÁC 1:1 như khi tải file PowerPoint về.
    """
    slides = deck_dict.get("slides", [])
    for slide in slides:
        # 1. Đồ thị Matplotlib
        chart_spec = slide.get("chart_spec")
        if chart_spec and is_plottable(chart_spec):
            try:
                png_bytes = generate_math_plot(chart_spec, figsize=(4.6, 3.6))
                b64 = base64.b64encode(png_bytes).decode("utf-8")
                slide["chart_image_base64"] = f"data:image/png;base64,{b64}"
                slide["has_chart"] = True
            except Exception as e:
                print(f"Lỗi render đồ thị cho slide preview: {e}")
                slide["has_chart"] = False
        else:
            slide["has_chart"] = False

        # 2. Công thức toán LaTeX
        main_latex = slide.get("main_definition_latex")
        if main_latex:
            try:
                formula_png = render_latex_to_bytes(main_latex)
                b64_f = base64.b64encode(formula_png).decode("utf-8")
                slide["formula_image_base64"] = f"data:image/png;base64,{b64_f}"
            except Exception as e:
                print(f"Lỗi render công thức LaTeX cho slide preview: {e}")

    return deck_dict

@app.post("/api/v1/slide/generate")
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
            plan=req.plan
        )
        deck_dict = slide_deck.model_dump()
        return enrich_slide_deck_with_renders(deck_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh Slide: {str(e)}")

@app.post("/api/v1/slide/enrich")
def enrich_slide_endpoint(deck: dict):
    """Bổ sung ảnh đồ thị và công thức vào dữ liệu slide deck bất kỳ để hiển thị đúng trên front-end"""
    try:
        return enrich_slide_deck_with_renders(deck)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý slide preview: {str(e)}")

@app.post("/api/v1/chart/render")
def render_chart_endpoint(spec: dict):
    """Render đồ thị từ cấu hình chart_spec và trả về file ảnh PNG trực tiếp"""
    try:
        if not is_plottable(spec):
            raise HTTPException(status_code=400, detail="Cấu hình chart_spec không thể vẽ thành đồ thị hàm số")
        png_bytes = generate_math_plot(spec)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi vẽ đồ thị: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print("🚀 Đang khởi chạy Server FastAPI tại http://localhost:8000 ...")
    print("📖 Xem tài liệu Swagger UI thử nghiệm API tại: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, app_dir=app_dir)
