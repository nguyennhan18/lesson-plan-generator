import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.schemas import LessonRequest
from schemas.slide_schema import SlideType, SlideLayout
from services.fallback_service import get_curated_lesson_plan, get_curated_slide_deck
from services.validation import validate_5512_lesson_plan
from rag.curriculum_registry import infer_lesson_id

client = TestClient(app)


@pytest.fixture(autouse=True)
def speed_up_offline_tests(monkeypatch):
    """Giúp test chạy tức thì (< 1s) trong môi trường kiểm thử offline không có mạng"""
    def fast_mock_llm(*args, **kwargs):
        raise ConnectionError("Offline test mode: kích hoạt nhanh Retrieval Fallback")
    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", fast_mock_llm)


def test_retrieval_fallback_across_all_math12_chapters():
    """Kiểm tra Tầng Retrieval Fallback lắp ghép bài giảng chuẩn xác cho mọi chương Toán 12"""
    math12_test_topics = [
        ("Tính đơn điệu và cực trị của hàm số", "M12-C1-B1"),
        ("Hệ trục tọa độ trong không gian Oxyz", "M12-C2-B2"),
        ("Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm", "M12-C3-B1"),
        ("Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm", "M12-C3-B2"),
        ("Tích phân và công thức Newton - Leibniz", "M12-C4-B2"),
        ("Phương trình mặt phẳng trong không gian Oxyz", "M12-C5-B1"),
        ("Công thức xác suất toàn phần và công thức Bayes", "M12-C6-B2"),
    ]

    for topic, expected_lid in math12_test_topics:
        # 1. Kiểm tra Giáo án 5512
        plan = get_curated_lesson_plan(topic=topic, grade=12)
        val = validate_5512_lesson_plan(plan)
        
        assert val.is_valid, f"Kế hoạch bài dạy không đạt chuẩn 5512 cho bài: {topic}. Lỗi: {val.errors}"
        assert len(plan.activities) == 4, f"Bài {topic} không có đúng 4 hoạt động"
        assert sum(a.time_minutes for a in plan.activities) == 45, f"Tổng thời lượng không bằng 45 phút cho bài: {topic}"
        assert len(plan.knowledge_goals) > 0, f"Thiếu mục tiêu YCCĐ cho bài: {topic}"

        # 2. Kiểm tra SlideDeck
        deck = get_curated_slide_deck(topic=topic, grade=12, plan=plan)
        assert deck is not None
        assert len(deck.slides) == 8, f"SlideDeck bài {topic} phải có đúng 8 trang slide"
        assert deck.slides[0].type == SlideType.TITLE_SLIDE
        assert deck.slides[1].type == SlideType.WARM_UP_SLIDE
        assert deck.slides[4].layout == SlideLayout.TWO_COLUMN  # Slide ví dụ giải mẫu
        assert len(deck.slides[4].worked_solution_steps) > 0, f"Slide 5 bài {topic} thiếu worked_solution_steps"
        
        # Slide 6 trắc nghiệm
        assert deck.slides[5].layout == SlideLayout.QUIZ_OPTION
        assert len(deck.slides[5].quiz_options) == 4
        correct_count = sum(1 for opt in deck.slides[5].quiz_options if opt.is_correct)
        assert correct_count == 1, f"Slide trắc nghiệm bài {topic} phải có đúng 1 đáp án đúng"

        # Kiểm tra source_refs được gắn trên slide
        has_source_refs = any(bool(s.source_refs) for s in deck.slides)
        assert has_source_refs, f"Bài {topic} không có source_refs trên slide"


def test_backward_compatibility_grade10_and_11():
    """Bảo đảm tương thích ngược 100% cho các bài test Lớp 10 và 11 cũ"""
    # Lớp 10
    plan_10 = get_curated_lesson_plan(topic="Hệ bất phương trình bậc nhất hai ẩn", grade=10)
    deck_10 = get_curated_slide_deck(topic="Hệ bất phương trình bậc nhất hai ẩn", grade=10)
    assert plan_10.grade == 10
    assert "Hệ bất phương trình" in plan_10.lesson_title
    assert deck_10.grade == 10

    # Lớp 11
    plan_11 = get_curated_lesson_plan(topic="Cấp số cộng", grade=11)
    deck_11 = get_curated_slide_deck(topic="Cấp số cộng", grade=11)
    assert plan_11.grade == 11
    assert "Cấp số cộng" in plan_11.lesson_title
    assert deck_11.grade == 11


def test_api_endpoints_generate_lesson_plan_and_slide_with_rag():
    """Kiểm tra gọi qua FastAPI endpoint với tham số RAG"""
    # 1. API sinh Giáo án cho bài Chương 3
    req_body = {
        "topic": "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm",
        "subject": "Toán học",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "use_rag": True,
        "class_proficiency": "standard"
    }
    resp = client.post("/api/v1/lesson-plan/generate", json=req_body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert "plan" in data
    assert data["plan"]["lesson_title"] != ""
    assert len(data["plan"]["activities"]) == 4

    # 2. API sinh Slide
    slide_req_body = {
        "topic": "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm",
        "subject": "Toán học",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "use_rag": True,
        "plan": data["plan"]
    }
    resp_slide = client.post("/api/v1/slide/generate", json=slide_req_body)
    assert resp_slide.status_code == 200
    deck_data = resp_slide.json()
    assert "slides" in deck_data
    assert len(deck_data["slides"]) >= 5
    # Kiểm tra có ít nhất 1 slide gắn source_refs
    has_refs = any(bool(s.get("source_refs")) for s in deck_data["slides"])
    assert has_refs, "Thiếu source_refs trong kết quả Slide API"
