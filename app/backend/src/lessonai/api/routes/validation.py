from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/api/v1/validation', tags=['Validation & Pedagogical Linter'])


@router.post("/audit-deck")
def audit_deck_endpoint():
    """Đã nghỉ hưu sau #59: giao diện cũ gọi endpoint này đã bị gỡ.

    Engine kiểm duyệt (`audit_slide_deck` trong services/quality/validation.py)
    vẫn còn để có thể nối vào cổng Kiểm tra bài của Bàn làm việc; chỉ bề mặt HTTP
    này dừng lại vì không còn client nào gọi.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "code": "legacy_deck_audit_retired",
            "message": "Endpoint kiểm duyệt bộ slide đã dừng; hãy dùng cổng Kiểm tra bài của Bàn làm việc (/api/v1/quality/workbench/check).",
        },
    )
