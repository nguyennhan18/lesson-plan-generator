import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta

# Đảm bảo đường dẫn module
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from main import app
from schemas.chat_schema import (
    ChatInteractRequest,
    ChatInteractResponse,
    ChatMessage,
    SlidePatchProposal
)
from services.chat_service import ChatSessionManager, handle_copilot_chat, session_manager


client = TestClient(app)


def test_chat_schema_validation():
    """Kiểm tra tính hợp lệ của các Pydantic schema Chat Co-pilot"""
    req = ChatInteractRequest(
        session_id="session_123",
        user_message="Giải thích lại slide 2 đơn giản hơn",
        current_slide_index=1
    )
    assert req.session_id == "session_123"
    assert req.user_message == "Giải thích lại slide 2 đơn giản hơn"
    assert req.current_slide_index == 1
    assert req.subject == "Toán học"
    assert req.grade == 11
    assert req.class_proficiency == "standard"
    assert req.slide_deck is None

    # Kiểm tra khởi tạo với hồ sơ học lực tùy biến từ Day 4
    req_advanced = ChatInteractRequest(
        session_id="session_adv",
        user_message="Mở rộng câu hỏi này",
        current_slide_index=3,
        subject="Hình học",
        grade=12,
        class_proficiency="advanced"
    )
    assert req_advanced.class_proficiency == "advanced"
    assert req_advanced.grade == 12

    # Kiểm tra khởi tạo bản vá đề xuất SlidePatchProposal cho Day 7
    patch = SlidePatchProposal(
        target_slide_index=1,
        action="SIMPLIFY_SLIDE",
        bullet_points=["Ý rút gọn 1", "Ý rút gọn 2"],
        main_definition_latex=r"AC' = a\sqrt{3}",
        preview_explanation="Rút gọn công thức đường chéo"
    )
    assert patch.target_slide_index == 1
    assert patch.slide_index == 1
    assert patch.action == "SIMPLIFY_SLIDE"
    assert len(patch.bullet_points) == 2

    res = ChatInteractResponse(
        session_id="session_123",
        ai_response="Đây là hướng dẫn chi tiết...",
        current_slide_index=1,
        suggested_action="SIMPLIFY_SLIDE",
        suggested_patch=patch
    )
    assert res.session_id == "session_123"
    assert res.suggested_action == "SIMPLIFY_SLIDE"
    assert res.suggested_patch is not None
    assert res.suggested_patch.target_slide_index == 1
    assert res.timestamp is not None


def test_chat_session_manager_sliding_window():
    """Kiểm tra cơ chế lưu lịch sử ngữ cảnh và cắt bớt theo cửa sổ trượt"""
    manager = ChatSessionManager(max_history_turns=3)
    sess_id = "test_window_session"

    # Thêm 4 lượt hội thoại (vượt quá 3 turns)
    for i in range(4):
        manager.add_turn(sess_id, "user", f"Câu hỏi {i+1}")
        manager.add_turn(sess_id, "assistant", f"Trả lời {i+1}")

    history = manager.get_history(sess_id)
    # Cửa sổ tối đa max_history_turns * 2 = 6 tin nhắn
    assert len(history) <= 6
    # Tin nhắn đầu tiên còn lưu là Câu hỏi 2 (Câu hỏi 1 đã bị trượt ra ngoài)
    assert history[-2]["content"] == "Câu hỏi 4"
    assert history[-1]["content"] == "Trả lời 4"

    # Xóa session
    cleared = manager.clear_session(sess_id)
    assert cleared is True
    assert len(manager.get_history(sess_id)) == 0


def test_chat_session_cleanup_expired():
    """
    Kiểm tra cơ chế thu hồi bộ nhớ RAM tự động (Session TTL Cleanup).

    Lý do thiết kế (Why):
    - Đảm bảo các phiên làm việc không còn tương tác quá 60 phút sẽ được tự động giải phóng,
      ngăn chặn hiện tượng tràn bộ nhớ khi hệ thống phục vụ nhiều giáo viên đồng thời.
    """
    manager = ChatSessionManager(max_history_turns=5)

    # Khởi tạo 2 phiên làm việc: 1 phiên đang hoạt động, 1 phiên hết hạn (cách đây 90 phút)
    manager.add_turn("session_active", "user", "Câu hỏi đang hoạt động", slide_index=0)
    manager.add_turn("session_stale", "user", "Câu hỏi cũ", slide_index=1)

    # Mô phỏng phiên session_stale không hoạt động trong 90 phút
    manager._session_last_active["session_stale"] = datetime.now() - timedelta(minutes=90)

    assert manager.session_count() == 2

    cleaned = manager.cleanup_expired_sessions(max_age_minutes=60)
    assert cleaned == 1
    assert manager.session_count() == 1
    assert len(manager.get_history("session_stale")) == 0
    assert len(manager.get_history("session_active")) == 1


def test_chat_session_slide_index_tracking():
    """
    Kiểm tra khả năng truy vết vị trí slide tương ứng cho từng tin nhắn trong phiên.

    Lý do thiết kế (Why):
    - Giáo viên có thể chuyển đổi qua lại giữa các slide trong tiết dạy, việc lưu trữ slide_index
      giúp hệ thống và AI tái hiện chính xác ngữ cảnh slide tại thời điểm phát sinh câu hỏi.
    """
    manager = ChatSessionManager(max_history_turns=5)
    sess_id = "test_slide_tracking"

    manager.add_turn(sess_id, "user", "Giải thích slide 0", slide_index=0)
    manager.add_turn(sess_id, "assistant", "Nội dung slide 0", slide_index=0)
    manager.add_turn(sess_id, "user", "Thêm câu hỏi slide 2", slide_index=2)

    # Kiểm tra truy xuất dạng từ điển phục vụ API
    history = manager.get_history(sess_id)
    assert len(history) == 3
    assert history[0]["slide_index"] == 0
    assert history[1]["slide_index"] == 0
    assert history[2]["slide_index"] == 2

    # Kiểm tra truy xuất dạng đối tượng ChatMessage phục vụ logic nội bộ
    messages = manager.get_session_messages(sess_id)
    assert isinstance(messages[0], ChatMessage)
    assert messages[2].slide_index == 2


def test_copilot_dod_explain_slide_2_simpler():
    """
    Kiểm tra tiêu chí DoD Ngày 6:
    'Gõ tin nhắn chat Giải thích lại slide 2 đơn giản hơn, AI trả lời đúng trọng tâm và gợi ý nội dung mới trong khung chat.'
    """
    session_id = "dod_session_test"
    response = handle_copilot_chat(
        session_id=session_id,
        user_message="Giải thích lại slide 2 đơn giản hơn",
        current_slide_index=1
    )

    assert response.session_id == session_id
    assert response.current_slide_index == 1
    # Phải có nội dung giải thích chi tiết
    assert len(response.ai_response) > 50
    # Phải có liên quan đến đường chéo AC' hoặc Pytago hoặc a\sqrt{3}
    assert any(term in response.ai_response for term in ["AC'", "đường chéo", "Pytago", "a\\sqrt{3}", "a\\sqrt{2}"])
    # Phải có hành động gợi ý SIMPLIFY_SLIDE
    assert response.suggested_action == "SIMPLIFY_SLIDE"
    # Phải có bản vá đề xuất SlidePatchProposal định kiểu mạnh cho Day 7
    assert response.suggested_patch is not None
    assert isinstance(response.suggested_patch, SlidePatchProposal)
    assert response.suggested_patch.target_slide_index == 1
    assert response.suggested_patch.action == "SIMPLIFY_SLIDE"
    assert response.suggested_patch.bullet_points is not None
    assert len(response.suggested_patch.bullet_points) == 3
    assert response.suggested_patch.main_definition_latex is not None


def test_copilot_add_quiz_proposal():
    """
    Kiểm tra Trợ giảng AI sinh đề xuất câu hỏi trắc nghiệm củng cố (ADD_QUIZ).

    Lý do thiết kế (Why):
    - Khi giáo viên yêu cầu kiểm tra bài trên lớp, AI phải tự động sinh câu hỏi trắc nghiệm
      4 phương án, đáp án đúng và lời giải thích vào SlidePatchProposal để hiển thị một chạm lên slide.
    """
    session_id = "quiz_proposal_test"
    response = handle_copilot_chat(
        session_id=session_id,
        user_message="Thêm câu hỏi trắc nghiệm kiểm tra nhanh",
        current_slide_index=0
    )

    assert response.suggested_action == "ADD_QUIZ"
    assert response.suggested_patch is not None
    assert isinstance(response.suggested_patch, SlidePatchProposal)
    assert response.suggested_patch.action == "ADD_QUIZ"
    assert response.suggested_patch.quiz is not None
    quiz = response.suggested_patch.quiz
    assert "question" in quiz
    assert len(quiz["options"]) == 4
    assert quiz["correct_answer"] == "B"


def test_api_chat_interact_endpoint():
    """Kiểm tra gọi trực tiếp API POST /api/v1/chat/interact qua HTTP client và tuần tự hóa SlidePatchProposal"""
    payload = {
        "session_id": "api_test_session_001",
        "user_message": "Giải thích lại slide 2 đơn giản hơn",
        "current_slide_index": 1,
        "slide_deck": None
    }
    res = client.post("/api/v1/chat/interact", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["session_id"] == "api_test_session_001"
    assert "ai_response" in data
    assert len(data["ai_response"]) > 0
    assert data["current_slide_index"] == 1
    assert "timestamp" in data
    # Kiểm tra tuần tự hóa SlidePatchProposal trả về trong JSON
    assert "suggested_patch" in data
    assert data["suggested_patch"] is not None
    assert data["suggested_patch"]["target_slide_index"] == 1
    assert data["suggested_patch"]["action"] == "SIMPLIFY_SLIDE"
    assert "bullet_points" in data["suggested_patch"]


def test_api_chat_conversation_continuity():
    """Kiểm tra tính liên tục của ngữ cảnh qua nhiều lượt gửi tin nhắn"""
    session_id = "api_multi_turn_session"

    # Lượt 1
    res1 = client.post("/api/v1/chat/interact", json={
        "session_id": session_id,
        "user_message": "Slide này đang nói về hình gì?",
        "current_slide_index": 0
    })
    assert res1.status_code == 200

    # Lượt 2
    res2 = client.post("/api/v1/chat/interact", json={
        "session_id": session_id,
        "user_message": "Giải thích lại slide 2 đơn giản hơn",
        "current_slide_index": 1
    })
    assert res2.status_code == 200

    # Kiểm tra endpoint lấy lịch sử
    res_hist = client.get(f"/api/v1/chat/history/{session_id}")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["session_id"] == session_id
    assert len(hist_data["history"]) >= 4  # 2 user messages + 2 AI responses
    assert hist_data["history"][0]["slide_index"] == 0
    assert hist_data["history"][2]["slide_index"] == 1

    # Kiểm tra endpoint xóa session
    res_del = client.delete(f"/api/v1/chat/session/{session_id}")
    assert res_del.status_code == 200
    assert res_del.json()["cleared"] is True

    # Kiểm tra lại lịch sử sau xóa
    res_hist_after = client.get(f"/api/v1/chat/history/{session_id}")
    assert len(res_hist_after.json()["history"]) == 0


def test_api_chat_empty_message_validation():
    """Kiểm tra xử lý khi thiếu trường bắt buộc"""
    # Thiếu user_message
    res = client.post("/api/v1/chat/interact", json={
        "session_id": "test_missing_field"
    })
    assert res.status_code == 422


if __name__ == "__main__":
    import pytest
    print("=" * 70)
    print("ĐANG CHẠY TOÀN BỘ BỘ TEST CASE NGÀY 6 (CHAT CO-PILOT)...")
    print("=" * 70)
    sys.exit(pytest.main(["-v", __file__]))
