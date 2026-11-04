import pytest
import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta

# Đảm bảo đường dẫn module

from lessonai.main import app
from lessonai.schemas.chat_schema import (
    ChatInteractRequest,
    ChatInteractResponse,
    ChatMessage,
    SlidePatchProposal
)
from lessonai.services.chat import ChatSessionManager, handle_copilot_chat, session_manager


@pytest.fixture(autouse=True)
def offline_chat_gateway(monkeypatch):
    from lessonai.llm.gateway import llm_gateway
    monkeypatch.setattr(llm_gateway, "generate_text", lambda **kwargs: None)


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


def test_copilot_m0_explanation_keeps_draft_without_sample_patch():
    response = handle_copilot_chat(
        session_id="dod_session_test", user_message="Giải thích lại slide 2 đơn giản hơn",
        current_slide_index=1,
    )
    assert response.session_id == "dod_session_test"
    assert response.current_slide_index == 1
    assert "tạm ngắt" in response.ai_response
    assert response.suggested_action == "GENERAL_ADVICE"
    assert response.suggested_patch is None
    assert "AC'" not in response.ai_response


def test_copilot_m0_quiz_does_not_invent_a_question():
    response = handle_copilot_chat(
        session_id="quiz_proposal_test", user_message="Thêm câu hỏi trắc nghiệm kiểm tra nhanh",
        current_slide_index=0,
    )
    assert response.suggested_action == "GENERAL_ADVICE"
    assert response.suggested_patch is None
    assert "bản soạn được giữ nguyên" in response.ai_response








if __name__ == "__main__":
    import pytest
    print("=" * 70)
    print("ĐANG CHẠY TOÀN BỘ BỘ TEST CASE NGÀY 6 (CHAT CO-PILOT)...")
    print("=" * 70)
    sys.exit(pytest.main(["-v", __file__]))
