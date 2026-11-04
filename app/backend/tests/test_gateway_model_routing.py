from types import SimpleNamespace
from unittest.mock import Mock
from pydantic import BaseModel
from lessonai.llm import gateway as module


class Result(BaseModel):
    value: str


def test_selected_missing_model_falls_back_and_is_skipped(monkeypatch, capsys):
    gateway = module.LLMGateway()
    gateway.gemini_key = "test"
    gateway.google_client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(
        side_effect=[RuntimeError("404 NOT_FOUND"), SimpleNamespace(text='{"value":"ok"}'),
                     SimpleNamespace(text='{"value":"again"}')]
    )))
    monkeypatch.setattr(gateway, "get_active_routes", lambda task: [
        module.ProviderRoute("google", "available")
    ])
    result = gateway.generate_structured("", "", Result, model_provider="gemini", model_id="missing")
    assert result.value == "ok"
    assert "google:missing" in gateway._dead_models
    gateway.generate_structured("", "", Result, model_provider="gemini", model_id="missing")
    assert [call.kwargs["model"] for call in gateway.google_client.models.generate_content.call_args_list] == [
        "missing", "available", "available"
    ]


def test_exhausted_route_does_not_announce_fallback(monkeypatch, capsys):
    import pytest
    gateway = module.LLMGateway()
    gateway.google_client = SimpleNamespace(models=SimpleNamespace(
        generate_content=Mock(side_effect=RuntimeError("404 NOT_FOUND"))
    ))
    monkeypatch.setattr(gateway, "get_active_routes", lambda task: [module.ProviderRoute("google", "missing")])
    with pytest.raises(RuntimeError):
        gateway.generate_structured("", "", Result)
    output = capsys.readouterr().out
    assert "Đã hết tuyến khả dụng" in output
    assert "Đang tự động chuyển mạch" not in output
