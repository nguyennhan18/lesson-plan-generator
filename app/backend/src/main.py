"""Compatibility entry point; prefer lessonai.main:app."""
from lessonai.main import app, create_app

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("lessonai.main:app", host="0.0.0.0", port=8000, reload=True)
