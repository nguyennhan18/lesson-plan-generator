"""FastAPI application composition. Run: uvicorn lessonai.main:app --app-dir src."""
from lessonai.core.config import FRONTEND_DIST_DIR, configure_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from lessonai.api.routes import (
    web, system, curriculum, presentation, lesson_plan, exports,
    slides, chat, ingest, validation, geometry,
)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="LessonAI-5512",
        description="Hệ thống tự động sinh Kế hoạch bài dạy theo Công văn 5512 và Slide bài giảng",
        version="0.1.0",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    assets = FRONTEND_DIST_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")
    for routes in (web, system, curriculum, presentation, lesson_plan, exports,
                   slides, chat, ingest, validation, geometry):
        app.include_router(routes.router)
    return app


app = create_app()
