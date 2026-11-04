import pytest
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path
import copy

# Đảm bảo đường dẫn module

from lessonai.main import app
from lessonai.schemas.chat_schema import SlidePatchProposal, ApplyPatchRequest, ApplyPatchResponse
from lessonai.services.chat import apply_slide_patch, handle_copilot_chat

client = TestClient(app)

# Dữ liệu bài giảng mẫu 5 slide chuẩn Công văn 5512 môn Toán 11
SAMPLE_SLIDE_DECK = {
    "topic": "Hình Lập Phương & Đường Chéo Không Gian",
    "subject": "Toán học",
    "grade": 11,
    "slides": [
        {
            "index": 0,
            "title": "1. Khởi Động: Đặt Vấn Đề Khối Lập Phương",
            "bullet_points": ["Đáy ABCD là hình vuông cạnh a", "Các cạnh bên vuông góc với đáy"],
            "main_definition_latex": r"V = a^3"
        },
        {
            "index": 1,
            "title": "2. Khảo Sát & Tính Toán Đường Chéo AC'",
            "bullet_points": [
                "Xét tam giác vuông ACC' vuông tại C",
                "Độ dài đường chéo đáy: AC = a*sqrt(2)",
                "Áp dụng Pytago tính AC' = sqrt(AC^2 + CC'^2)"
            ],
            "main_definition_latex": r"AC' = \sqrt{2a^2 + a^2} = a\sqrt{3}"
        },
        {
            "index": 2,
            "title": "3. Dựng Đường Vuông Góc AH ⊥ B'D'",
            "bullet_points": ["Tam giác AB'D' đều cạnh a*sqrt(2)", "H là trung điểm B'D'"],
            "main_definition_latex": r"AH = \frac{a\sqrt{6}}{3}"
        },
        {
            "index": 3,
            "title": "4. Xác Định Thiết Diện Mặt Phẳng (A'BD)",
            "bullet_points": ["Mặt phẳng đi qua 3 đỉnh A', B, D", "Thiết diện là tam giác đều"],
            "main_definition_latex": r"S = \frac{a^2\sqrt{3}}{2}"
        },
        {
            "index": 4,
            "title": "5. Bài Tập Vận Dụng & Live Quiz",
            "bullet_points": ["Góc giữa hai đường thẳng AC và A'D bằng bao nhiêu độ?"],
            "main_definition_latex": r"\cos \alpha = \frac{1}{2}"
        }
    ]
}


def test_apply_slide_patch_unit_success():
    """
    Test Case 1: Kiểm thử đơn vị hàm apply_slide_patch cập nhật chính xác slide đích.

    Lý do thiết kế (Why):
    - Đảm bảo các trường bullet_points, main_definition_latex được thay thế đúng như bản vá.
    - Cờ is_ai_patch được kích hoạt để Front-end nhận diện.
    - Dữ liệu gốc SAMPLE_SLIDE_DECK không bị đột biến (Immutability).
    """
    original_deck = copy.deepcopy(SAMPLE_SLIDE_DECK)
    patch = SlidePatchProposal(
        target_slide_index=1,
        action="SIMPLIFY_SLIDE",
        bullet_points=[
            "Ý rút gọn 1: Đường chéo đáy AC = a*sqrt(2)",
            "Ý rút gọn 2: Chiều cao CC' = a",
            "Ý rút gọn 3: Đường chéo hộp AC' = a*sqrt(3)"
        ],
        main_definition_latex=r"AC' = a\sqrt{3}",
        preview_explanation="Đơn giản hóa công thức Pytago 2 bước cho học sinh cơ bản"
    )

    updated_deck = apply_slide_patch(original_deck, patch)

    # 1. Slide đích (index 1) phải thay đổi
    target_slide = updated_deck["slides"][1]
    assert len(target_slide["bullet_points"]) == 3
    assert target_slide["bullet_points"][0] == "Ý rút gọn 1: Đường chéo đáy AC = a*sqrt(2)"
    assert target_slide["main_definition_latex"] == r"AC' = a\sqrt{3}"
    assert target_slide["is_ai_patch"] is True
    assert target_slide["patch_action"] == "SIMPLIFY_SLIDE"

    # 2. Các slide khác (Slide 0, 2, 3, 4) phải giữ nguyên vẹn 100%
    assert updated_deck["slides"][0]["bullet_points"] == SAMPLE_SLIDE_DECK["slides"][0]["bullet_points"]
    assert updated_deck["slides"][2]["main_definition_latex"] == SAMPLE_SLIDE_DECK["slides"][2]["main_definition_latex"]
    assert updated_deck["slides"][4]["title"] == SAMPLE_SLIDE_DECK["slides"][4]["title"]

    # 3. Đảm bảo deck gốc không bị thay đổi (Deep Copy an toàn)
    assert original_deck["slides"][1]["bullet_points"] == SAMPLE_SLIDE_DECK["slides"][1]["bullet_points"]


def test_apply_slide_patch_quiz_action():
    """
    Test Case 2: Kiểm thử áp dụng bản vá dạng thêm câu hỏi trắc nghiệm (ADD_QUIZ).

    Lý do thiết kế (Why):
    - Đảm bảo cấu trúc quiz gồm câu hỏi, 4 phương án và đáp án đúng được gán chuẩn xác vào slide.
    """
    patch = SlidePatchProposal(
        target_slide_index=4,
        action="ADD_QUIZ",
        quiz={
            "question": "Tính góc giữa AC và A'D:",
            "options": ["A. 60°", "B. 90°", "C. 45°", "D. 30°"],
            "correct_answer": "A"
        },
        preview_explanation="Chèn câu hỏi trắc nghiệm củng cố vào Slide 5"
    )

    updated_deck = apply_slide_patch(SAMPLE_SLIDE_DECK, patch)
    target_slide = updated_deck["slides"][4]

    assert "quiz" in target_slide
    assert target_slide["quiz"]["correct_answer"] == "A"
    assert len(target_slide["quiz"]["options"]) == 4
    assert target_slide["patch_action"] == "ADD_QUIZ"


def test_apply_slide_patch_invalid_boundary():
    """
    Test Case 3: Kiểm tra xử lý lỗi khi chỉ số slide đích vượt ngoài phạm vi bài giảng.

    Lý do thiết kế (Why):
    - Ngăn chặn lỗi sập server (IndexError) khi giáo viên nhập số slide không tồn tại (vd: Slide 99 hoặc -1).
    """
    patch_overflow = SlidePatchProposal(
        target_slide_index=99,
        action="SIMPLIFY_SLIDE"
    )
    with pytest.raises(IndexError) as exc_info:
        apply_slide_patch(SAMPLE_SLIDE_DECK, patch_overflow)
    assert "nằm ngoài phạm vi" in str(exc_info.value)


def test_apply_slide_patch_invalid_deck_structure():
    """
    Test Case 4: Kiểm tra xử lý lỗi khi dữ liệu slide_deck bị khuyết thiếu cấu trúc.

    Lý do thiết kế (Why):
    - Đảm bảo tính toàn vẹn dữ liệu, ném lỗi ValueError rõ ràng nếu thiếu key 'slides'.
    """
    patch = SlidePatchProposal(target_slide_index=0, action="TEST")
    with pytest.raises(ValueError):
        apply_slide_patch({}, patch)






def test_m0_chat_does_not_offer_a_patch_or_modify_the_deck(monkeypatch):
    """Live proposals stay unavailable until M2 adds content and revision checks."""
    from lessonai.llm.gateway import llm_gateway
    monkeypatch.setattr(llm_gateway, "generate_text", lambda **kwargs: None)
    original = copy.deepcopy(SAMPLE_SLIDE_DECK)
    response = handle_copilot_chat(
        session_id="e2e_session_week1", user_message="Giải thích lại slide 2 đơn giản hơn",
        current_slide_index=1, slide_deck=SAMPLE_SLIDE_DECK,
    )
    assert response.suggested_patch is None
    assert "tạm ngắt" in response.ai_response
    assert SAMPLE_SLIDE_DECK == original


if __name__ == "__main__":
    import pytest
    print("=" * 70)
    print("ĐANG CHẠY BỘ TEST SUITE TASK 7.4 (E2E LIVE PATCHING & TUẦN 1)...")
    print("=" * 70)
    sys.exit(pytest.main(["-v", __file__]))
