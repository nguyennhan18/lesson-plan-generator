import os
from fastapi.responses import HTMLResponse
from fastapi import APIRouter
from lessonai.core.config import FRONTEND_DIST_DIR
react_dist_dir = str(FRONTEND_DIST_DIR)

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def root():
    # Phục vụ giao diện React 19 + Three.js nếu đã build (npm run build trong app/frontend)
    react_index = os.path.join(react_dist_dir, "index.html")
    if os.path.exists(react_index):
        with open(react_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse(content="""
        <div style="font-family: sans-serif; padding: 40px; text-align: center;">
            <h2>LessonAI-5512 API Server</h2>
            <p>Server đang hoạt động bình thường.</p>
            <p><a href="/docs">Xem tài liệu API Swagger</a> | <a href="/ui">Giao diện Studio</a></p>
        </div>
    """)


@router.get("/ui", response_class=HTMLResponse)
def ui_page():
    return root()

