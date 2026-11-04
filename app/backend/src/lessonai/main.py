"""FastAPI application composition. Run: uvicorn lessonai.main:app --app-dir src."""
from contextlib import asynccontextmanager
from lessonai.core.jobs import close_runner
from lessonai.core.config import FRONTEND_DIST_DIR, configure_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from lessonai.api.routes import (
    web, system, curriculum, presentation, lesson_plan, exports,
    slides, chat, ingest, validation, geometry, visuals, quality,
)


@asynccontextmanager
async def lifespan(app):
    yield
    close_runner()


def create_app() -> FastAPI:
    configure_logging()
    import os
    from urllib.parse import urlsplit
    allowed = {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"}
    for origin in filter(None, os.getenv("LESSONAI_LOCAL_ORIGINS", "").split(",")):
        parsed = urlsplit(origin)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("LESSONAI_LOCAL_ORIGINS chỉ nhận HTTP origin cục bộ")
        allowed.add(origin)
    app = FastAPI(
        title="LessonAI-5512",
        description="Hệ thống tự động sinh Kế hoạch bài dạy theo Công văn 5512 và Slide bài giảng",
        version="0.2.0", lifespan=lifespan,
    )
    app.add_middleware(CORSMiddleware, allow_origins=sorted(allowed), allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    from lessonai.core.ownership import router as owner_router
    app.include_router(owner_router)
    from uuid import uuid4
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        request.state.request_id = str(uuid4())
        origin = request.headers.get("origin")
        if origin and origin not in allowed:
            return JSONResponse({"detail": {"code":"origin_forbidden", "message":"Origin không được phép", "request_id":request.state.request_id}}, status_code=403,headers={"X-Request-ID":request.state.request_id})
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        detail = error.detail if isinstance(error.detail, dict) else {"code": f"http_{error.status_code}", "message": str(error.detail)}
        detail = {**detail, "request_id": getattr(request.state, "request_id", None)}
        return JSONResponse({"detail": detail}, status_code=error.status_code, headers=error.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse({"detail": {"code":"validation_error", "message":"Dữ liệu không đúng cấu trúc", "request_id":getattr(request.state,"request_id",None),
            "field_errors":[{"loc":list(e["loc"]),"msg":e["msg"],"type":e["type"]} for e in error.errors()]}}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected_error(request,error):
        import logging
        logging.getLogger("lessonai").error("Unhandled request %s",getattr(request.state,"request_id",None),exc_info=error)
        return JSONResponse({"detail":{"code":"internal_error","message":"Không xử lý được yêu cầu. Bản soạn được giữ nguyên.","request_id":getattr(request.state,"request_id",None)}},status_code=500)

    from lessonai.core.ingress import BodyLimitMiddleware
    app.add_middleware(BodyLimitMiddleware)
    assets = FRONTEND_DIST_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")
    for routes in (web, system, curriculum, presentation, lesson_plan, exports,
                   slides, chat, ingest, validation, geometry, visuals, quality):
        app.include_router(routes.router)
    return app


app = create_app()
