"""Teacher confirmations outlive restarts and time, but not a lost key (issue #37, ADR 0005)."""
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import lessonai
from lessonai.main import create_app
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.slide_schema import SlideDeckSchema

pytestmark = pytest.mark.critical_regressions

SOURCE_ROOT = Path(lessonai.__file__).resolve().parents[1]
NO_LLM = {"GEMINI_API_KEY": "", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""}
RESTARTED_BACKEND = """
import json, sys
from fastapi.testclient import TestClient
from lessonai.main import create_app
calls = json.load(sys.stdin)
with TestClient(create_app()) as client:
    assert client.post("/api/v1/session").status_code == 200
    replies = [client.post(path, json=body) for path, body in calls]
    print(json.dumps([{"status": reply.status_code, "body": reply.json()} for reply in replies]))
"""


@pytest.fixture(autouse=True)
def config_dir(tmp_path, monkeypatch):
    """Never touch the real per-user key while testing."""
    path = tmp_path / "config"
    monkeypatch.setenv("LESSONAI_CONFIG_DIR", str(path))
    for name, value in NO_LLM.items():
        monkeypatch.setenv(name, value)
    return path


@pytest.fixture
def api():
    with TestClient(create_app()) as client:
        assert client.post("/api/v1/session").status_code == 200
        yield client


@pytest.fixture
def deck():
    return SlideDeckSchema.model_validate({"subject": "Toán học", "grade": 12, "presentation_title": "Thể tích khối lập phương", "slides": [
        {"slide_index": 1, "title": "Ví dụ", "bullet_points": ["Tính thể tích khối lập phương cạnh $2$."], "worked_solution_steps": ["$2^3=8$"]}]}).model_dump(mode="json")


@pytest.fixture
def plan():
    steps = {"step_1_assign": "Giáo viên giao nhiệm vụ.", "step_2_excute": "Học sinh tính thể tích.",
             "step_3_report": "Học sinh báo cáo kết quả.", "step_4_conclusion": "Giáo viên chốt công thức."}
    return LessonPlanSchema.model_validate({
        "lesson_title": "Thể tích khối lập phương", "knowledge_goals": ["Tính thể tích khối lập phương"],
        "competency_goals": ["Trình bày lời giải"],
        "activities": [{"activity_number": number, "time_minutes": minutes, "goal": name + ": tính thể tích khối lập phương cạnh 2",
                        "expected_product": "$2^3=8$", "execution": steps}
                       for number, (name, minutes) in enumerate(zip(["Khởi động", "Hình thành kiến thức", "Luyện tập", "Vận dụng"], [5, 20, 10, 10]), 1)],
    }).model_dump(mode="json")


def post_to_restarted_backend(*calls, **env):
    """Send requests to a backend in a new process, as after restarting the machine or the backend."""
    variables = {**os.environ, **NO_LLM, **env, "PYTHONPATH": os.pathsep.join(filter(None, [str(SOURCE_ROOT), os.environ.get("PYTHONPATH")]))}
    run = subprocess.run([sys.executable, "-c", RESTARTED_BACKEND], input=json.dumps(calls), env=variables,
                         capture_output=True, text=True, timeout=180)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout.strip().splitlines()[-1])


def figure_request(deck, **data):
    slide = deck["slides"][0]
    data = data or {"kind": "geometry", "polyhedron_type": "cube", "base_edge": 2, "height": 2}
    return {**data, "deck_id": deck["deck_id"], "slide_id": slide["slide_id"], "source": slide}


def confirm_figure(api, deck, **data):
    request = figure_request(deck, **data)
    spec = {key: value for key, value in request.items() if key != "source"}
    response = api.post("/api/v1/visuals/confirm", json=request)
    assert response.status_code == 200, response.text
    confirmed = response.json()
    return {**spec, **confirmed["requirement"]["spec"], "requirement_token": confirmed["requirement_token"]}


def confirm_plot(api, deck):
    return confirm_figure(api, deck, kind="function_plot", expression="x^3 - 3*x", operation="function", x_min=-3, x_max=3)


def delete_key(path):
    path.unlink()


def replace_key(path):
    path.write_bytes(os.urandom(32))


LOSE_KEY = pytest.mark.parametrize("lose_key", [delete_key, replace_key], ids=["deleted", "replaced"])
FIGURES = pytest.mark.parametrize("confirm, endpoint", [(confirm_figure, "/api/v1/visuals/scene"), (confirm_plot, "/api/v1/chart/render")],
                                  ids=["geometry", "function_plot"])


def save_expert_confirmation(api, check_path, approve_path, field, content):
    report = api.post(check_path, json=content).json()
    assert report["status"] == "needs_review", report
    response = api.post(approve_path, json={field: content, "acknowledged": True, "content_fingerprint": report["content_fingerprint"],
                                            "reviewed_issue_ids": [i["issue_id"] for i in report["issues"] if i["severity"] == "warning"]})
    assert response.status_code == 200, response.text
    return {**content, "review_token": response.json()["review_token"]}


def approve_deck(api, deck):
    return save_expert_confirmation(api, "/api/v1/quality/check", "/api/v1/quality/approve", "deck", deck)


def approve_plan(api, plan):
    return save_expert_confirmation(api, "/api/v1/quality/lesson-plan/check", "/api/v1/quality/lesson-plan/approve", "plan", plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows has no POSIX mode bits; the key stays in the per-user %APPDATA% profile")
def test_first_confirmation_creates_an_owner_only_key_file(api, deck, config_dir):
    confirm_figure(api, deck)
    assert stat.S_IMODE((config_dir / "signing.key").stat().st_mode) == 0o600


def test_key_defaults_to_the_user_config_dir_outside_the_repository(tmp_path, deck):
    home = tmp_path / "home"
    [confirmed] = post_to_restarted_backend(("/api/v1/visuals/confirm", figure_request(deck)), HOME=str(home), USERPROFILE=str(home),
                                            APPDATA=str(home / "AppData" / "Roaming"), XDG_CONFIG_HOME="", LESSONAI_CONFIG_DIR="")
    assert confirmed["status"] == 200, confirmed
    assert len(list(home.rglob("signing.key"))) == 1


def test_figure_confirmation_survives_backend_restart(api, deck):
    scene_spec = confirm_figure(api, deck)
    [scene] = post_to_restarted_backend(("/api/v1/visuals/scene", scene_spec))
    assert scene["status"] == 200, scene


def test_expert_confirmations_survive_backend_restart(api, deck, plan):
    deck_report, plan_report = post_to_restarted_backend(("/api/v1/quality/check", approve_deck(api, deck)),
                                                         ("/api/v1/quality/lesson-plan/check", approve_plan(api, plan)))
    assert [deck_report["body"]["status"], plan_report["body"]["status"]] == ["ready", "ready"], (deck_report, plan_report)


def test_changing_the_figure_data_voids_its_confirmation(api, deck):
    scene_spec = confirm_figure(api, deck)
    response = api.post("/api/v1/visuals/scene", json={**scene_spec, "base_edge": 3, "height": 3})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "visual_needs_review"


def test_changing_the_slide_formula_voids_the_figure_on_it(api, deck):
    slide = deck["slides"][0]
    slide.update(has_3d=True, scene_spec=confirm_figure(api, deck))
    assert api.post("/api/v1/quality/check", json=deck).json()["status"] == "needs_review"
    slide["math_formulas"] = ["V = a^3"]
    report = api.post("/api/v1/quality/check", json=deck).json()
    assert [issue["field"] for issue in report["issues"] if issue["severity"] == "error"] == ["scene_spec"], report


def test_editing_approved_content_voids_the_expert_confirmation(api, deck, plan):
    approved_deck, approved_plan = approve_deck(api, deck), approve_plan(api, plan)
    approved_deck["slides"][0]["title"] = "Ví dụ khác"
    approved_plan["lesson_title"] = "Bài khác"
    assert [api.post("/api/v1/quality/check", json=approved_deck).json()["status"],
            api.post("/api/v1/quality/lesson-plan/check", json=approved_plan).json()["status"]] == ["needs_review", "needs_review"]


@FIGURES
@LOSE_KEY
def test_losing_the_key_asks_to_reconfirm_figures(api, deck, config_dir, confirm, endpoint, lose_key):
    spec = confirm(api, deck)
    lose_key(config_dir / "signing.key")
    response = api.post(endpoint, json=spec)
    detail = response.json()["detail"]
    assert response.status_code == 409 and detail["code"] == "confirmation_key_changed" and "xác nhận lại" in detail["message"], detail


def test_losing_the_key_flags_the_figure_in_the_deck_check(api, deck, config_dir):
    deck["slides"][0].update(has_3d=True, scene_spec=confirm_figure(api, deck))
    delete_key(config_dir / "signing.key")
    report = api.post("/api/v1/quality/check", json=deck).json()
    assert [(issue["field"], issue.get("code")) for issue in report["issues"] if issue["severity"] == "error"] == [("scene_spec", "confirmation_key_changed")], report


@LOSE_KEY
def test_losing_the_key_asks_to_reconfirm_expert_confirmations(api, deck, plan, config_dir, lose_key):
    approved = [("/api/v1/quality/check", approve_deck(api, deck)), ("/api/v1/quality/lesson-plan/check", approve_plan(api, plan))]
    lose_key(config_dir / "signing.key")
    for path, content in approved:
        report = api.post(path, json=content).json()
        notices = [issue for issue in report["issues"] if issue.get("code") == "confirmation_key_changed"]
        assert report["status"] == "needs_review" and len(notices) == 1 and "xác nhận lại" in notices[0]["message"], report


def test_teacher_can_confirm_again_after_the_key_is_lost(api, deck, plan, config_dir):
    stale_deck, stale_plan = approve_deck(api, deck), approve_plan(api, plan)
    (config_dir / "signing.key").unlink()
    scene_spec = confirm_figure(api, deck)
    assert [api.post("/api/v1/visuals/scene", json=scene_spec).status_code,
            api.post("/api/v1/quality/check", json=approve_deck(api, stale_deck)).json()["status"],
            api.post("/api/v1/quality/lesson-plan/check", json=approve_plan(api, stale_plan)).json()["status"]] == [200, "ready", "ready"]


def test_an_unusable_key_file_is_reported_and_never_overwritten(api, deck, plan, config_dir):
    plotted = {**deck, "slides": [{**deck["slides"][0], "chart_spec": confirm_plot(api, deck)}]}
    approved_deck, approved_plan = approve_deck(api, deck), approve_plan(api, plan)
    key = config_dir / "signing.key"
    key.write_bytes(b"not a key")
    replies = [api.post(path, json=body) for path, body in [
        ("/api/v1/visuals/confirm", figure_request(deck)), ("/api/v1/quality/check", approved_deck),
        ("/api/v1/slide/enrich", plotted), ("/api/v1/lesson-plan/export-slide", approved_deck),
        ("/api/v1/lesson-plan/export-docx", approved_plan), ("/api/v1/lesson-plan/export-dual-package", {"plan": approved_plan, "slide_deck": approved_deck})]]
    assert [(reply.status_code, reply.json()["detail"]["code"]) for reply in replies] == [(503, "signing_key_unavailable")] * 6
    assert key.read_bytes() == b"not a key"


def test_confirmations_saved_weeks_ago_still_hold(api, deck, plan, monkeypatch):
    weeks_ago = time.time() - 30 * 86400
    with monkeypatch.context() as past:
        past.setattr(time, "time", lambda: weeks_ago)
        scene_spec, approved_deck, approved_plan = confirm_figure(api, deck), approve_deck(api, deck), approve_plan(api, plan)
    assert [api.post("/api/v1/visuals/scene", json=scene_spec).status_code,
            api.post("/api/v1/quality/check", json=approved_deck).json()["status"],
            api.post("/api/v1/quality/lesson-plan/check", json=approved_plan).json()["status"]] == [200, "ready", "ready"]
