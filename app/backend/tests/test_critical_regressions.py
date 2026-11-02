"""M0 containment checks, not acceptance of the disabled M1/M2 features."""

import builtins
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from fastapi.testclient import TestClient
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from pptx import Presentation
import pytest

from lessonai.main import app
from lessonai.core.feature_availability import ExpressionProcessingUnavailable
from lessonai.exporters.graph_generator import generate_math_plot, is_plottable, safe_eval_expression
from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx, render_latex_to_bytes
from lessonai.services.chat import handle_copilot_chat, session_manager
from lessonai.services.rendering import enrich_slide_deck_with_renders
from lessonai.services.validation import audit_slide_deck, latex_to_sympy_expr
from lessonai.utils.temp_file_cleaner import cleanup_memory_and_figures

pytestmark = pytest.mark.critical_regressions
client = TestClient(app)
ROOT = Path(__file__).resolve().parents[3]
MARKER = "(__import__('builtins').setattr(__import__('builtins'), 'lessonM0Marker', 731), x)[1]"


def deck_with_chart(expression=MARKER):
    return {
        "presentation_title": "Nguyên hàm", "subject": "Toán học", "grade": 12,
        "slides": [{"slide_index": 1, "title": "Họ nguyên hàm", "bullet_points": ["Tìm nguyên hàm của 2x."],
                    "chart_spec": {"kind": "function_plot", "expression": expression}}],
    }


@pytest.fixture(autouse=True)
def marker_guard():
    assert not hasattr(builtins, "lessonM0Marker")
    yield
    marker_set = hasattr(builtins, "lessonM0Marker")
    if marker_set:
        delattr(builtins, "lessonM0Marker")
    assert not marker_set, "An expression executed Python before being rejected"


@pytest.mark.parametrize("kind", ["function_plot", "function", "inequality_system", "linear_programming", "arithmetic_sequence"])
def test_m0_rejects_expression_before_all_graph_entry_points(kind):
    spec = {"kind": kind, "expression": MARKER, "boundary_lines": [{"expr": MARKER}]}
    assert is_plottable(spec) is False
    with pytest.raises(ExpressionProcessingUnavailable):
        safe_eval_expression(MARKER)
    with pytest.raises(ExpressionProcessingUnavailable):
        generate_math_plot(spec)
    response = client.post("/api/v1/chart/render", json=spec)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "expression_processing_temporarily_unavailable"


def test_m0_enrich_keeps_draft_and_removes_stale_chart():
    deck = deck_with_chart()
    deck["slides"][0]["chart_image_base64"] = "data:image/png;base64,stale"
    response = client.post("/api/v1/slide/enrich", json=deck)
    assert response.status_code == 200
    slide = response.json()["slides"][0]
    assert slide["chart_spec"] == deck["slides"][0]["chart_spec"]
    assert slide["bullet_points"] == deck["slides"][0]["bullet_points"]
    assert slide["chart_render_status"] == "temporarily_unavailable"
    assert "chart_image_base64" not in slide
    assert slide["has_chart"] is False


def test_m0_export_keeps_lesson_and_labels_unavailable_chart():
    deck = deck_with_chart()
    original = deepcopy(deck)
    stream = export_slide_deck_to_pptx(deck)
    pptx = Presentation(stream)
    text = " ".join(shape.text for shape in pptx.slides[0].shapes if shape.has_text_frame)
    assert "Họ nguyên hàm" in text
    assert "BẢN NHÁP" in text and "Đồ thị đang tạm ngắt" in text
    assert deck == original


def test_m0_validator_reports_unverified_without_parsing():
    assert latex_to_sympy_expr(MARKER) is None
    deck = {"slides": [{"slide_index": 1, "main_definition_latex": MARKER,
                        "worked_solution_steps": ["$1+1=3$"]}]}
    original = deepcopy(deck)
    response = audit_slide_deck(deck)
    assert response.is_clean is False
    assert any(item.category == "algebra_unverified" for item in response.warnings)
    assert deck == original
    # A worked solution alone must not be reported clean while verification is off.
    response = audit_slide_deck({"slides": [{"worked_solution_steps": ["$1+1=3$"]}]})
    assert response.is_clean is False


@pytest.mark.parametrize("message,index", [("Giải thích đơn giản hơn", 1), ("Giải thích lại slide 3", 2), ("Thêm câu hỏi trắc nghiệm", 0)])
@pytest.mark.parametrize("gateway_fails", [False, True])
def test_m0_copilot_never_pairs_live_text_with_sample_patch(monkeypatch, message, index, gateway_fails):
    from lessonai.llm.gateway import llm_gateway
    seen = []
    def gateway(**kwargs):
        seen.append(kwargs["prompt"])
        if gateway_fails:
            raise RuntimeError("offline")
        return "Nguyên hàm của 2x là x^2 + C."
    monkeypatch.setattr(llm_gateway, "generate_text", gateway)
    deck = deck_with_chart("x")
    original = deepcopy(deck)
    try:
        response = handle_copilot_chat("m0-copilot", message, current_slide_index=index, slide_deck=deck, grade=12)
        assert seen and "Họ nguyên hàm" in seen[0]
        assert response.suggested_patch is None
        assert response.suggested_action == "GENERAL_ADVICE"
        assert "lập phương" not in response.ai_response.lower()
        if gateway_fails:
            assert "tạm ngắt" in response.ai_response
        else:
            assert response.ai_response == "Nguyên hàm của 2x là x^2 + C."
        assert deck == original
    finally:
        session_manager.clear_session("m0-copilot")


@pytest.mark.parametrize("payload", [{"plan": None}, {"lesson_plan": None}])
def test_m0_missing_word_content_returns_json_error(payload):
    response = client.post("/api/v1/lesson-plan/export-docx", json=payload)
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert "content-disposition" not in response.headers


@pytest.mark.parametrize("endpoint,target,payload", [
    ("export-docx", "export_lesson_plan_to_docx", {"plan": {"lesson_title": "Nguyên hàm"}}),
    ("export-slide", "export_slide_deck_to_pptx", deck_with_chart("x")),
])
def test_m0_export_failure_never_retries_with_another_lesson(monkeypatch, endpoint, target, payload):
    from lessonai.api.routes import exports
    calls = []
    def fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("conversion failed")
    monkeypatch.setattr(exports, target, fail)
    response = client.post(f"/api/v1/lesson-plan/{endpoint}", json=payload)
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert "content-disposition" not in response.headers
    assert len(calls) == 1


def test_m0_word_synchronization_does_not_replace_invalid_plan():
    from pydantic import ValidationError
    from lessonai.exporters.docx_exporter import synchronize_lesson_and_slide_deck
    invalid = {"lesson_title": "Giữ nguyên bài này", "grade": "invalid", "activities": []}
    original = deepcopy(invalid)
    with pytest.raises(ValidationError):
        synchronize_lesson_and_slide_deck(invalid, None)
    assert invalid == original


def test_m0_matplotlib_jobs_keep_their_own_content_and_cleanup(monkeypatch):
    held = plt.figure()
    before = set(plt.get_fignums())
    original_save = Figure.savefig
    original_subplots = plt.subplots
    original_close = plt.close
    gate = threading.Barrier(2)
    observations = []
    local = threading.local()
    active = set()
    maximum_active = [0]
    observation_lock = threading.Lock()
    def subplots(*args, **kwargs):
        with observation_lock:
            figure, axes = original_subplots(*args, **kwargs)
            active.add(figure.number)
            maximum_active[0] = max(maximum_active[0], len(active))
        time.sleep(0.03)
        return figure, axes
    def close(figure=None):
        try:
            return original_close(figure)
        finally:
            with observation_lock:
                active.discard(getattr(figure, "number", figure))
    def save(figure, *args, **kwargs):
        # This observes actual figure content, not merely different PNG bytes.
        if local.kind == "chart":
            assert [patch.get_height() for patch in figure.axes[0].patches] == [2, 6]
        else:
            assert figure.axes[0].texts[0].get_text() == "$x^2+1$"
        observations.append(local.kind)
        cleanup_memory_and_figures()
        assert plt.fignum_exists(figure.number)
        assert plt.fignum_exists(held.number)
        time.sleep(0.03)
        return original_save(figure, *args, **kwargs)
    monkeypatch.setattr(Figure, "savefig", save)
    monkeypatch.setattr(plt, "subplots", subplots)
    monkeypatch.setattr(plt, "close", close)
    def render(kind):
        local.kind = kind
        gate.wait(timeout=10)
        if kind == "chart":
            return generate_math_plot({"kind": "chart", "labels": ["A", "B"], "values": [2, 6]})
        return render_latex_to_bytes("x^2+1")
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            images = list(executor.map(render, ["chart", "formula"]))
        assert sorted(observations) == ["chart", "formula"]
        assert maximum_active[0] == 1
        assert not active
        assert all(image.startswith(b"\x89PNG") for image in images)
        assert set(plt.get_fignums()) == before
    finally:
        plt.close(held)


def test_m0_render_failure_releases_only_its_figures(monkeypatch):
    held = plt.figure()
    before = set(plt.get_fignums())
    def fail(*args, **kwargs):
        raise RuntimeError("save failed")
    monkeypatch.setattr(Figure, "savefig", fail)
    try:
        with pytest.raises(RuntimeError, match="save failed"):
            generate_math_plot({"kind": "chart", "labels": ["A"], "values": [1]})
        assert set(plt.get_fignums()) == before
    finally:
        plt.close(held)


def test_review_clis_run_acceptance_without_overwriting_history(tmp_path):
    backend_output = tmp_path / "backend.json"
    frontend_output = tmp_path / "frontend.json"
    env = {**os.environ, "GEMINI_API_KEY": "", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""}
    backend = [sys.executable, str(ROOT / "scripts/quality/project-review-probes.py"), "--mode", "acceptance", "--output", str(backend_output)]
    frontend = ["node", str(ROOT / "scripts/quality/project-review-frontend-probes.mjs"), "--mode", "acceptance", "--input", str(backend_output), "--output", str(frontend_output)]
    for command in (backend, frontend):
        result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads(frontend_output.read_text())
    assert all(evidence["m0_checks"].values())
    assert all(evidence["frontend_m0_checks"].values())
    assert evidence["editor_add_slide_export"]["status"] == 422  # R05 is still open.
    for command, output in ((backend, backend_output), (frontend, frontend_output)):
        previous = output.read_bytes()
        result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
        assert result.returncode != 0
        assert "already exists" in result.stderr
        assert output.read_bytes() == previous
