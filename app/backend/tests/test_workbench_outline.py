from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

from lessonai.main import app
from lessonai.api.routes import presentation
from lessonai.services.generation import workbench_outline
from lessonai.rag.context_builder import PedagogicalContextBuilder

URL = "/api/v1/workbench/outline"
ACTIVITIES = ["Khởi động", "Hình thành kiến thức", "Luyện tập", "Vận dụng"]
REQUEST = {"request": "Soạn bài tích phân", "level": "standard"}


@pytest.fixture
def fake_ai(monkeypatch):
    items = [
        dict(activity=activity, kind=kind, title=kind, points=["Một ý"], minutes=12, slide_count=2)
        for activity, kind in zip(ACTIVITIES, ["Mở đầu", "Ví dụ", "Bài luyện tập", "Tổng kết"])
    ]
    calls = []
    claimed_sources = []

    def generate(**kwargs):
        calls.append(kwargs)
        return dict(title="Tích phân", items=items, used_sources=claimed_sources)

    monkeypatch.setattr(workbench_outline.llm_gateway, "generate_structured", generate)
    monkeypatch.setattr(presentation, "resolve_lesson", lambda *_: ("M12-C4-B2", "Tích phân"))
    monkeypatch.setattr(
        PedagogicalContextBuilder, "build_slide_deck_context",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("RAG must not run")),
    )
    return items, calls, claimed_sources


def test_outline_uses_one_call_without_rag_and_returns_duration_warning(fake_ai):
    _, calls, _ = fake_ai
    response = TestClient(app).post(URL, json=REQUEST)
    assert response.status_code == 200, response.json()
    result = response.json()
    assert len(calls) == 1
    assert calls[0]["single_attempt"] is True
    assert "nguồn đã duyệt" not in calls[0]["prompt"]
    assert result["source_refs"] == []
    assert "48" in result["warnings"][0]
    assert [item["activity"] for item in result["outline"]["items"]] == ACTIVITIES
    assert len({item["item_id"] for item in result["outline"]["items"]}) == 4


@pytest.mark.parametrize("problem", ["order", "missing", "slide_count", "kind", "placement", "source"])
def test_invalid_ai_response_is_rejected_without_another_call(fake_ai, problem):
    items, calls, _ = fake_ai
    if problem == "order":
        items[1], items[2] = items[2], items[1]
    elif problem == "missing":
        items.pop()
    elif problem == "source":
        fake_ai[2].append(1)
    else:
        field, value = {
            "slide_count": ("slide_count", 5), "kind": ("kind", "Lạ"), "placement": ("kind", "Tổng kết"),
        }[problem]
        items[0][field] = value
    response = TestClient(app).post(URL, json=REQUEST)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "invalid_ai_output"
    assert len(calls) == 1


@pytest.mark.parametrize("field", ["num_slides", "tone", "text_content", "aspect_ratio"])
def test_legacy_settings_do_not_trigger_ai(fake_ai, field):
    response = TestClient(app).post(URL, json={**REQUEST, field: "legacy"})
    assert response.status_code == 422
    assert not fake_ai[1]


def test_openapi_contract():
    fixture = Path(__file__).parent / "fixtures" / "api_contract.json"
    actual = app.openapi()
    assert {key: actual[key] for key in ("paths", "components")} == json.loads(fixture.read_text())


def test_identify_uses_curriculum_registry_without_ai(tmp_path, monkeypatch):
    from lessonai.rag import curriculum_registry

    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    (curriculum / "math12_ct2018.json").write_text(json.dumps({
        "chapters": [{"lessons": [{"lesson_id": "M12-C4-B2", "title": "Tích phân"}]}],
    }))
    monkeypatch.setattr(curriculum_registry, "DATA_DIR", tmp_path)
    monkeypatch.setattr(curriculum_registry.CurriculumRegistry, "_instance", curriculum_registry.CurriculumRegistry())
    response = TestClient(app).post(f"{URL}/identify", json={"request": REQUEST["request"]})
    assert response.status_code == 200
    assert response.json() == {
        "lesson_id": "M12-C4-B2", "lessons": [{"lesson_id": "M12-C4-B2", "title": "Tích phân"}],
    }


def test_no_reviewed_sources_can_return_empty_list(fake_ai, monkeypatch):
    response = TestClient(app).post(URL, json=REQUEST)
    assert response.status_code == 200
    assert response.json()["source_refs"] == []


def test_gateway_single_attempt_does_not_retry_groq_json_error(monkeypatch):
    from types import SimpleNamespace
    from lessonai.llm.gateway import LLMGateway, ProviderRoute

    gateway = LLMGateway()
    calls = []

    def fail(**kwargs):
        calls.append(kwargs["model"])
        raise RuntimeError("failed_generation")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fail)))
    client.with_options = lambda **_: client
    monkeypatch.setattr(gateway, "groq_client", client)
    monkeypatch.setattr(gateway, "get_active_routes", lambda _: [
        ProviderRoute("groq", "first"), ProviderRoute("groq", "second"),
    ])
    with pytest.raises(RuntimeError, match="failed_generation"):
        gateway.generate_structured(
            prompt="Dàn ý", system_prompt="", response_schema=workbench_outline.GeneratedOutline,
            single_attempt=True,
        )
    assert calls == ["first"]
