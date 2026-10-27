import pytest
from schemas.schemas import LessonRequest
from schemas.slide_schema import SlideSchema, SlideType, SlideLayout
from rag.curriculum_registry import infer_lesson_id, CurriculumRegistry
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_lesson_request_defaults_and_scope_lock():
    """Kiểm tra LessonRequest mặc định là Toán 12 và use_rag=True"""
    req = LessonRequest(topic="Tính đơn điệu và cực trị của hàm số")
    assert req.subject == "Toán học"
    assert req.grade == 12
    assert req.use_rag is True
    assert req.lesson_id == "M12-C1-B1"


def test_auto_infer_lesson_id_across_curriculum():
    """Kiểm tra tự động suy luận lesson_id từ topic tự do"""
    test_mappings = [
        ("Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba", "M12-C1-B4"),
        ("Đường tiệm cận của đồ thị hàm số", "M12-C1-B3"),
        ("Giá trị lớn nhất và giá trị nhỏ nhất của hàm số", "M12-C1-B2"),
        ("Vectơ trong không gian và quy tắc hình hộp", "M12-C2-B1"),
        ("Hệ trục tọa độ trong không gian Oxyz", "M12-C2-B2"),
        ("Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm", "M12-C3-B1"),
        ("Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm", "M12-C3-B2"),
        ("Tích phân và định lý Newton - Leibniz", "M12-C4-B2"),
        ("Phương trình mặt phẳng trong không gian Oxyz", "M12-C5-B1"),
        ("Công thức xác suất toàn phần và công thức Bayes", "M12-C6-B2"),
        ("Chủ đề bất kỳ chưa xác định", "M12-C1-B1"),  # Fallback an toàn
    ]

    for topic, expected_lid in test_mappings:
        req = LessonRequest(topic=topic)
        assert req.lesson_id == expected_lid, f"Failed for topic: {topic}"


def test_slide_schema_source_refs_and_pedagogical_mode():
    """Kiểm tra SlideSchema hỗ trợ source_refs và pedagogical_mode"""
    slide = SlideSchema(
        slide_index=1,
        type=SlideType.CONCEPT_SLIDE,
        layout=SlideLayout.TWO_COLUMN,
        title="Tính đơn điệu của hàm số",
        bullet_points=["Định lý điều kiện đủ của tính đơn điệu"],
        source_refs=[{"source": "slides_kntt12", "slide_id": "M12-C1-B1-S05"}],
        pedagogical_mode="Hoạt động thảo luận cặp đôi (3 phút)"
    )
    assert slide.source_refs is not None
    assert len(slide.source_refs) == 1
    assert slide.source_refs[0]["slide_id"] == "M12-C1-B1-S05"
    assert slide.pedagogical_mode == "Hoạt động thảo luận cặp đôi (3 phút)"


def test_api_test_cases_endpoint_returns_math12():
    """Kiểm tra API /api/v1/test-cases trả về danh sách 10 bài test chuẩn Toán 12"""
    resp = client.get("/api/v1/test-cases")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 10
    
    # 100% test cases phải thuộc Toán 12
    for tc in data:
        assert tc["subject"] == "Toán học"
        assert tc["grade"] == 12
        assert tc["lesson_id"].startswith("M12-")
