from fastapi import HTTPException
from lessonai.schemas.chat_schema import ChatInteractRequest, ChatInteractResponse, ApplyPatchRequest, ApplyPatchResponse
from lessonai.services.chat import handle_copilot_chat, session_manager, apply_slide_patch
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/chat', tags=['Chat Co-pilot'])

@router.post("/interact", response_model=ChatInteractResponse)
def chat_interact_endpoint(req: ChatInteractRequest):
    """
    Task 6.1: Nhận tương tác hội thoại từ giáo viên, chuyển tới Trợ giảng AI
    phân tích ngữ cảnh slide hiện tại và trả về phản hồi kèm gợi ý.
    """
    try:
        response = handle_copilot_chat(
            session_id=req.session_id,
            user_message=req.user_message,
            current_slide_index=req.current_slide_index,
            slide_deck=req.slide_deck,
            subject=req.subject or "Toán học",
            grade=req.grade or 11,
            class_proficiency=req.class_proficiency or "standard"
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tương tác với Trợ giảng AI: {str(e)}"
        )


@router.get("/history/{session_id}")
def get_chat_history_endpoint(session_id: str):
    """Lấy danh sách các tin nhắn trong phiên hội thoại hiện tại"""
    return {
        "session_id": session_id,
        "history": session_manager.get_history(session_id)
    }


@router.delete("/session/{session_id}")
def clear_chat_session_endpoint(session_id: str):
    """Xóa lịch sử phiên hội thoại để bắt đầu phiên mới"""
    success = session_manager.clear_session(session_id)
    return {
        "session_id": session_id,
        "cleared": success
    }


@router.post("/apply-patch", response_model=ApplyPatchResponse)
def apply_patch_endpoint(req: ApplyPatchRequest):
    """
    Task 7.1: Nhận yêu cầu áp dụng bản vá đề xuất và trả về dữ liệu slide đã cập nhật.

    Lý do thiết kế (Why):
    - Đóng vai trò là API kiểm định và đồng bộ trạng thái giữa Front-end và Backend.
    - Cho phép kiểm thử tự động toàn diện luồng Live Patching bằng TestClient.
    """
    try:
        updated_deck = apply_slide_patch(
            slide_deck=req.slide_deck,
            patch=req.patch
        )
        target_idx = req.patch.target_slide_index
        updated_slide = updated_deck["slides"][target_idx]

        return ApplyPatchResponse(
            success=True,
            target_slide_index=target_idx,
            updated_slide=updated_slide,
            slide_deck=updated_deck,
            message=f"Đã áp dụng thành công bản vá cho Slide {target_idx + 1}"
        )
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi hợp nhất bản vá slide: {str(e)}")

