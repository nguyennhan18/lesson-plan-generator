from fastapi import HTTPException
from lessonai.services.validation import audit_slide_deck, DeckAuditResponse
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/validation', tags=['Validation & Pedagogical Linter'])

@router.post("/audit-deck", response_model=DeckAuditResponse)
def audit_deck_endpoint(deck_payload: dict):
    """
    Task 10.1: Endpoint kiểm duyệt sư phạm toàn bộ bộ Slide (AI Linter & Proofreader).
    Quét toàn bộ các trang slide để phát hiện lỗi chính tả tiếng Việt thường gặp
    và trả về danh sách cảnh báo để Giáo viên chủ động rà soát (Human-in-the-loop).
    """
    try:
        return audit_slide_deck(deck_payload)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi kiểm duyệt bộ Slide: {str(e)}"
        )

