"""Backend contract and behavioral tests for Bàn làm việc slide generation and item regeneration (#40, #43, #46)."""
import pytest
from fastapi.testclient import TestClient

from lessonai.main import app
from lessonai.services.generation import workbench_slides
from lessonai.rag.context_builder import PedagogicalContextBuilder

client = TestClient(app)
SLIDES_URL = "/api/v1/workbench/slides"
ITEM_SLIDES_URL = "/api/v1/workbench/slides/item"

OUTLINE_ITEMS = [
    {"item_id": "m1", "activity": "Khởi động", "kind": "Mở đầu", "title": "Khảo sát hàm số bậc ba", "points": ["Toán 12"], "slide_count": 1, "minutes": 5},
    {"item_id": "m2", "activity": "Hình thành kiến thức", "kind": "Kiến thức trọng tâm", "title": "Sơ đồ khảo sát", "points": ["Tập xác định", "Sự biến thiên"], "slide_count": 2, "minutes": 15},
    {
        "item_id": "m3", "activity": "Luyện tập", "kind": "Ví dụ", "title": "Ví dụ đồ thị $y = x^3 - 3x + 1$",
        "points": ["Vẽ đồ thị"], "slide_count": 1, "minutes": 15,
        "visuals": [{"visual_id": "v1", "kind": "graph", "origin": "ai", "status": "confirmed", "data": {"expression": "x^3 - 3*x + 1"}}],
    },
    {"item_id": "m4", "activity": "Vận dụng", "kind": "Tổng kết", "title": "Tổng kết", "points": ["Ba bước khảo sát"], "slide_count": 1, "minutes": 10},
]

REQUEST = {
    "title": "Khảo sát hàm số bậc ba",
    "sgk": "Toán 12, Chương I, Bài 4",
    "lesson_id": "M12-C1-B4",
    "level": "standard",
    "outline": {"items": OUTLINE_ITEMS},
}


@pytest.fixture
def fake_slide_ai(monkeypatch):
    generated = [
        {"item_id": "m1", "layout": "Mở đầu", "title": "Khảo sát hàm số bậc ba", "caption": "Toán 12, Chương I, Bài 4"},
        {"item_id": "m2", "layout": "Kiến thức trọng tâm", "title": "Sơ đồ khảo sát", "items": ["Tập xác định", "Sự biến thiên"]},
        {"item_id": "m2", "layout": "Kiến thức trọng tâm", "title": "Xét dấu đạo hàm", "items": ["Tính y'", "Lập BBT"], "formula": "f'(x) = 0"},
        {"item_id": "m3", "layout": "Chữ trái, hình phải", "title": "Đồ thị hàm số", "items": ["Đi qua (0; 1)"], "visual_id": "v1"},
        {"item_id": "m4", "layout": "Tổng kết", "title": "Tổng kết", "items": ["Ba bước khảo sát"]},
    ]
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return {"slides": generated}

    monkeypatch.setattr(workbench_slides.llm_gateway, "generate_structured", generate)
    monkeypatch.setattr(
        PedagogicalContextBuilder,
        "build_slide_deck_context",
        lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("RAG must not run")),
    )
    return generated, calls


def test_build_slides_uses_one_call_and_assigns_coordinates_from_layout_catalog(fake_slide_ai):
    _, calls = fake_slide_ai
    response = client.post(SLIDES_URL, json={**REQUEST, "model_provider": "groq", "model_id": "llama-3.3-70b-versatile"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(calls) == 1
    assert calls[0]["single_attempt"] is True
    assert calls[0]["model_provider"] == "groq"
    assert calls[0]["model_id"] == "llama-3.3-70b-versatile"
    assert "nguồn đã duyệt" not in calls[0]["prompt"]
    assert data["prompt_chars"] <= workbench_slides.DEFAULT_SLIDE_PROMPT_BUDGET
    slides = data["slides"]
    assert len(slides) == 5
    assert [s["item_id"] for s in slides] == ["m1", "m2", "m2", "m3", "m4"]
    # Vị trí lấy từ Bố cục mẫu (Mở đầu: title x=120, y=280, w=1360, h=220)
    first_title = slides[0]["elements"][0]
    assert (first_title["x"], first_title["y"], first_title["w"], first_title["h"]) == (120, 280, 1360, 220)
    # Hình đặt đúng Mục m3 ở Bố cục mẫu "Chữ trái, hình phải" (x=700, y=140, w=820, h=680)
    graph_el = next(el for el in slides[3]["elements"] if el["type"] == "graph")
    assert graph_el["visual_id"] == "v1"
    assert (graph_el["x"], graph_el["y"], graph_el["w"], graph_el["h"]) == (700, 140, 820, 680)


@pytest.mark.parametrize("problem", ["wrong_count", "unknown_item", "visual_wrong_item", "missing_visual", "has_coordinates"])
def test_build_slides_rejects_fidelity_violations_in_one_call(fake_slide_ai, problem):
    generated, calls = fake_slide_ai
    if problem == "wrong_count":
        generated.pop(1)
    elif problem == "unknown_item":
        generated[0]["item_id"] = "m-khong-co"
    elif problem == "visual_wrong_item":
        generated[0]["visual_id"] = "v1"
    elif problem == "missing_visual":
        generated[3]["visual_id"] = None
    elif problem == "has_coordinates":
        generated[0]["x"] = 100
    response = client.post(SLIDES_URL, json=REQUEST)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "invalid_ai_output"
    assert len(calls) == 1


def test_prompt_budget_blocks_overflow_without_sample_fallback(fake_slide_ai):
    _, calls = fake_slide_ai
    response = client.post(SLIDES_URL, json=REQUEST)
    assert response.status_code == 200
    assert response.json()["prompt_chars"] <= workbench_slides.DEFAULT_SLIDE_PROMPT_BUDGET
    assert len(calls[0]["prompt"]) <= workbench_slides.DEFAULT_SLIDE_PROMPT_BUDGET

    # Khi ngân sách quá nhỏ không thể chứa cả Dàn ý tối thiểu -> chặn gọi AI, không chèn bài mẫu
    with pytest.raises(ValueError, match="vượt ngân sách"):
        workbench_slides.generate_workbench_slides(
            workbench_slides.WorkbenchSlidesRequest.model_validate(REQUEST),
            budget=200,
        )
    assert len(calls) == 1


def test_regenerate_single_item_slides_replaces_only_target_item_in_one_call(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return {
            "slides": [
                {"item_id": "m2", "layout": "Kiến thức trọng tâm", "title": "Sơ đồ mới 1", "items": ["Ý 1"]},
                {"item_id": "m2", "layout": "Kiến thức trọng tâm", "title": "Sơ đồ mới 2", "items": ["Ý 2"]},
                {"item_id": "m2", "layout": "Nội dung", "title": "Sơ đồ mới 3", "items": ["Ý 3"]},
            ]
        }

    monkeypatch.setattr(workbench_slides.llm_gateway, "generate_structured", generate)
    updated_items = [
        {**item, "slide_count": 3} if item["item_id"] == "m2" else item
        for item in OUTLINE_ITEMS
    ]
    response = client.post(ITEM_SLIDES_URL, json={
        **REQUEST,
        "outline": {"items": updated_items},
        "item_id": "m2",
    })
    assert response.status_code == 200, response.text
    slides = response.json()["slides"]
    assert len(calls) == 1
    assert len(slides) == 3
    assert all(s["item_id"] == "m2" for s in slides)
