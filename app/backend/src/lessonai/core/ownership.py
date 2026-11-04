"""Single-process local ownership. No claim of multi-user authentication."""
import secrets
import threading
import time
from fastapi import Request, HTTPException, Response, APIRouter

router = APIRouter()
_owners = {}
_lock = threading.RLock()


def require_owner(request: Request):
    token = request.cookies.get("lessonai_owner")
    with _lock:
        if not token or _owners.get(token, 0) <= time.monotonic():
            raise HTTPException(401, detail={"code": "session_expired", "message": "Phiên đã hết hạn. Hãy kết nối lại."})
        _owners[token] = time.monotonic() + 86400
    return token


@router.post("/api/v1/session")
def create_owner(request: Request, response: Response):
    with _lock:
        now = time.monotonic()
        for key in list(_owners):
            if _owners[key] <= now:
                del _owners[key]
        token = request.cookies.get("lessonai_owner")
        if token not in _owners:
            if len(_owners) >= 256:
                raise HTTPException(503, detail="Đã đạt giới hạn phiên")
            token = secrets.token_urlsafe(32)
        _owners[token] = now + 86400
    response.set_cookie("lessonai_owner", token, httponly=True, samesite="strict", max_age=86400)
    return {"status": "connected", "mode": "local_single_process"}
