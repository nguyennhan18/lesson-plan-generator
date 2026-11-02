import pytest
from fastapi.testclient import TestClient
from lessonai.main import app
from lessonai.services.generation import generate_presentation_outline
from lessonai.schemas.schemas import OutlineResponse, OutlineRequest

client = TestClient(app)

def test_generate_presentation_outline_service():
    """Kiểm tra hàm service generate_presentation_outline trả về đúng chuẩn OutlineResponse"""
    res = generate_presentation_outline(
        topic="Hệ trục tọa độ trong không gian Oxyz",
        subject="Toán học",
        grade=12,
        num_slides=6,
        class_proficiency="standard",
        use_rag=True
    )
    assert isinstance(res, OutlineResponse)
    assert res.topic == "Hệ trục tọa độ trong không gian Oxyz"
    assert res.grade == 12
    assert len(res.outline_slides) >= 3
    # Phải có ít nhất 1 slide chứa tiêu đề và key_points
    first_slide = res.outline_slides[0]
    assert first_slide.title
    assert len(first_slide.key_points) > 0


def test_api_v1_presentation_outline_endpoint():
    """Kiểm tra endpoint POST /api/v1/presentation/outline qua FastAPI TestClient"""
    payload = {
        "topic": "Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba",
        "subject": "Toán học",
        "grade": 12,
        "num_slides": 7,
        "class_proficiency": "advanced",
        "use_rag": True,
        "model_provider": "gemini",
        "model_id": "gemini-2.5-flash"
    }
    response = client.post("/api/v1/presentation/outline", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == payload["topic"]
    assert data["grade"] == 12
    assert "outline_slides" in data
    assert len(data["outline_slides"]) >= 4

    # Kiểm tra cấu trúc từng slide
    slides = data["outline_slides"]
    for s in slides:
        assert "slide_number" in s
        assert "title" in s
        assert "activity_type" in s
        assert "visual_type" in s
        assert "key_points" in s
        assert isinstance(s["key_points"], list)


def test_presentation_outline_alias_endpoint():
    """Kiểm tra alias route POST /api/presentation/outline"""
    payload = {
        "topic": "Thể tích khối chóp tứ giác đều S.ABCD",
        "subject": "Toán học",
        "grade": 12,
        "num_slides": 6
    }
    response = client.post("/api/presentation/outline", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["outline_slides"]) >= 3
