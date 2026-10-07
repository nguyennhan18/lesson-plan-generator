import sys
import os
import pytest
from pydantic import ValidationError

# Thêm đường dẫn thư mục root/app vào sys.path để import các module schema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.slide_schema import (
    SlideDeckSchema,
    SlideSchema,
    SlideType,
    SlideLayout,
    QuizOptionDetail,
    ClassProficiency,
    ThemeType,
)
from app.schemas.schemas import LessonRequest


def test_quiz_slide_valid():
    """
    Test Case 1: Kiểm tra parse thành công slide trắc nghiệm hợp lệ.
    Bao gồm: đủ 4 lựa chọn (A, B, C, D), có 1 đáp án đúng và phân tích bẫy sai (distractor_rationale).
    """
    slide_deck = {
        "slide_index": 1,
        "type":  SlideType.EXERCISE_SLIDE,
        "layout": SlideLayout.QUIZ_OPTION,
        "title" : "Câu hỏi rèn luyện ",
        "subtitle" : "Chọn đáp án đúng nhất",
        "bullet_points" : ["Hãy xác định công thức số hạng tổng quát"],
        "class_proficiency": ClassProficiency.STANDARD,
        "target_outcome": "Học sinh ghi nhớ và áp dụng chính xác công thức",
        "quiz_options" : [
            {
                "label" : "A",
                "text" : "u_n = u_1 + (n-1)d",
                "is_correct": True,
                "distractor_rationale": None
            },
            {
                "label": "B",
                "text": "u_n = u_1 + nd",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm lẫn số hạng thứ n được cộng nd thay vì (n-1)d."
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm phép cộng công sai d thành phép trừ."
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm lẫn công thức Cấp số cộng sang Cấp số nhân."
            }
        ]
    }
    slide = SlideSchema(**slide_deck)
    assert slide.slide_index == 1
    assert slide.layout == SlideLayout.QUIZ_OPTION
    assert slide.class_proficiency == ClassProficiency.STANDARD
    assert len(slide.quiz_options) == 4

    assert slide.quiz_options[0].label == "A"
    assert slide.quiz_options[0].is_correct is True
    assert slide.quiz_options[0].distractor_rationale is None

    assert slide.quiz_options[1].label == "B"
    assert slide.quiz_options[1].is_correct is False
    assert slide.quiz_options[1].distractor_rationale == "Học sinh nhầm lẫn số hạng thứ n được cộng nd thay vì (n-1)d."


def test_quiz_slide_missing_distractor_rationale():
    """
    Test Case 2: Kiểm tra chốt chặn Validation (DoD).
    Pydantic bắt buộc phải ném ValidationError khi phương án sai bị thiếu distractor_rationale.
    """
    slide_dict = {
        "slide_index" : 2,
        "type" : SlideType.EXERCISE_SLIDE,
        "layout" : SlideLayout.QUIZ_OPTION,
        "title" : "Câu hỏi thiếu giải thích",
        "quiz_options" : [
            {
                "label": "A",
                "text": "u_n = u_1 + (n-1)d",
                "is_correct": True,
                "distractor_rationale": None
            },
            {
                "label": "B",
                "text": "u_n = u_1 + nd",
                "is_correct": False,
                "distractor_rationale": ""  # <--- Cố tình để chuỗi rỗng: Vi phạm DoD!
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "   "  # <--- Cố tình để khoảng trắng: Vi phạm DoD!
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": None  # <--- Cố tình để None ở đáp án sai: Vi phạm DoD!
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        SlideSchema(**slide_dict)
    error_messages = str(exc_info.value)

    assert "Phương án sai thiếu distractor_rationale: B" in error_messages
    assert "B" in error_messages
    assert "C" in error_messages
    assert "D" in error_messages




def test_quiz_slide_invalid_correct_count():
    """
    Test Case 3: Kiểm tra chốt chặn số lượng đáp án đúng.
    Pydantic ném ValidationError khi câu hỏi trắc nghiệm có 0 hoặc nhiều hơn 1 đáp án đúng.
    """
    slide_dict = {
        "slide_index" : 3,
        "type" : SlideType.EXERCISE_SLIDE,
        "layout" : SlideLayout.QUIZ_OPTION,
        "title" : "Câu hỏi có 2 đáp án đúng",
        "quiz_options" : [
            {
                "label": "A",
                "text": "u_n = u_1 + (n-1)d",
                "is_correct": True,  # <--- Đáp án đúng 1
                "distractor_rationale": None
            },
            {
                "label": "B",
                "text": "u_n = u_1 + (n-1)*d",
                "is_correct": True,  # <--- Cố tình vi phạm: Đáp án đúng 2 (Có 2 câu is_correct = True)!
                "distractor_rationale": None
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm phép cộng công sai d thành phép trừ."
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm công thức Cấp số cộng sang Cấp số nhân."
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        SlideSchema(**slide_dict)
    error_messages = str(exc_info.value)
    assert "Cần đúng 1 phương án đúng, hiện có 2" in error_messages


def test_lesson_request_with_proficiency():
    """
    Test Case 4: Kiểm tra LessonRequest tiếp nhận tham số phân loại học lực.
    Bao gồm: class_proficiency (basic, standard, advanced) và target_outcome.
    """
    request_dict = {
        "topic": "Cấp số cộng và ứng dụng",
        "subject": "Toán học",
        "grade": 11,
        "class_proficiency": ClassProficiency.ADVANCED,
        "target_outcome": "Học sinh vận dụng cao giải bài toán thực tế về Cấp số cộng"
    }
    req = LessonRequest(**request_dict)
    # 2. Kiểm tra Pydantic parse và lưu trữ chuẩn xác các trường phân loại học lực
    assert req.topic == "Cấp số cộng và ứng dụng"
    assert req.subject == "Toán học"
    assert req.grade == 11
    assert req.class_proficiency == ClassProficiency.ADVANCED
    assert req.class_proficiency.value == "advanced"
    assert req.target_outcome == "Học sinh vận dụng cao giải bài toán thực tế về Cấp số cộng"


if __name__ == "__main__":
    pytest.main([__file__])
