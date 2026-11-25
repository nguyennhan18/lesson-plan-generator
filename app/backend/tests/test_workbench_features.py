"""Comprehensive backend tests for Bàn làm việc features (#44, #45, #49, #50, #51–#57, #59)."""
import io
import json
import zipfile
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from pptx import Presentation

from lessonai.main import create_app
from lessonai.parsers.pptx_parser import parse_pptx

pytestmark = pytest.mark.critical_regressions


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSONAI_CONFIG_DIR", str(tmp_path / "signing-config"))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with TestClient(create_app()) as client:
        assert client.post("/api/v1/session").status_code == 200
        yield client


def _sample_lesson_payload():
    return {
        "project_id": "proj-wb-1",
        "title": "Khảo sát hàm số bậc ba $y = x^3 - 3x + 1$",
        "sgk": "Toán 12, Chương I, Bài 4",
        "level": "standard",
        "outline": {
            "items": [
                {"item_id": "m1", "activity": "Khởi động", "kind": "Mở đầu", "title": "Khảo sát hàm số bậc ba", "points": ["Toán 12"], "slide_count": 1, "minutes": 5, "visuals": []},
                {
                    "item_id": "m2", "activity": "Hình thành kiến thức", "kind": "Ví dụ", "title": "Ví dụ khảo sát $y = x^3 - 3x + 1$",
                    "points": ["Đạo hàm và cực trị", "Vẽ đồ thị $y = x^3 - 3x + 1$"], "slide_count": 1, "minutes": 15,
                    "visuals": [
                        {"visual_id": "v-graph", "kind": "graph", "origin": "ai", "status": "proposed", "label": "$y = x^3 - 3x + 1$", "data": {"expression": "x^3 - 3*x + 1", "x_min": -3, "x_max": 3}},
                        {"visual_id": "v-bbt", "kind": "bbt", "origin": "ai", "status": "proposed", "label": "$y = x^3 - 3x + 1$", "data": {"expression": "x^3 - 3*x + 1"}},
                    ],
                },
                {"item_id": "m3", "activity": "Luyện tập", "kind": "Câu hỏi trắc nghiệm", "title": "Cực trị hàm số", "points": ["Chọn đáp án đúng"], "slide_count": 1, "minutes": 15, "visuals": []},
                {"item_id": "m4", "activity": "Vận dụng", "kind": "Tổng kết", "title": "Tổng kết", "points": ["Ba bước khảo sát"], "slide_count": 1, "minutes": 10, "visuals": []},
            ]
        },
        "deck": {
            "revision": 1,
            "slides": [
                {
                    "slide_id": "s1",
                    "item_id": "m1",
                    "layout": "Mở đầu",
                    "notes": "Ghi chú giáo viên slide 1",
                    "elements": [
                        {"element_id": "e1", "type": "title", "hero": True, "x": 120, "y": 280, "w": 1360, "h": 220, "reveal": 0, "parts": 1, "text": "Khảo sát hàm số bậc ba"},
                        {"element_id": "e2", "type": "formula", "x": 120, "y": 540, "w": 900, "h": 120, "reveal": 1, "parts": 1, "latex": r"\frac{x^2 + 1}{x - 1}"},
                        {"element_id": "e3", "type": "table", "x": 120, "y": 680, "w": 900, "h": 180, "reveal": 1, "parts": 1, "headers": ["x", "y"], "rows": [["0", "1"], ["1", "-1"]]},
                    ],
                },
                {
                    "slide_id": "s2",
                    "item_id": "m2",
                    "layout": "Chữ trái, hình phải",
                    "notes": "",
                    "edited": True,
                    "elements": [
                        {"element_id": "e4", "type": "title", "x": 100, "y": 80, "w": 560, "h": 100, "reveal": 0, "parts": 1, "text": "Ví dụ khảo sát", "overflow": True},
                        {"element_id": "e5", "type": "graph", "x": 700, "y": 140, "w": 820, "h": 680, "reveal": 0, "parts": 1, "visual_id": "v-graph"},
                    ],
                },
            ],
        },
    }


def test_quality_check_and_expert_confirmation_for_workbench_deck(api):
    payload = _sample_lesson_payload()
    report = api.post("/api/v1/quality/workbench/check", json=payload).json()
    assert report["status"] == "needs_review"
    assert len(report["unconfirmed_visuals"]) == 2
    assert len(report["overflow_elements"]) == 1
    assert len(report["edited_slides"]) == 1

    # Approve expert confirmation
    approve_res = api.post("/api/v1/quality/workbench/approve", json={
        **payload,
        "acknowledged": True,
        "content_fingerprint": report["content_fingerprint"],
    })
    assert approve_res.status_code == 200, approve_res.text
    token = approve_res.json()["review_token"]
    payload["deck"]["review_token"] = token

    checked = api.post("/api/v1/quality/workbench/check", json=payload).json()
    assert checked["status"] == "ready"

    # Modifying slide content invalidates the expert confirmation token
    payload["deck"]["slides"][0]["elements"][0]["text"] = "Tiêu đề đã sửa"
    stale = api.post("/api/v1/quality/workbench/check", json=payload).json()
    assert stale["status"] == "needs_review"


def test_pptx_export_from_workbench_canvas_omml_table_visuals_and_draft_stamp(api):
    payload = _sample_lesson_payload()
    # 1. Export without expert confirmation and with unconfirmed visual -> has Bản nháp stamp, no picture for unconfirmed graph
    res_draft = api.post("/api/v1/workbench/export-pptx", json=payload)
    assert res_draft.status_code == 200, res_draft.text
    prs_draft = Presentation(io.BytesIO(res_draft.content))
    assert round(prs_draft.slide_width.inches, 2) == 13.33
    assert round(prs_draft.slide_height.inches, 2) == 7.50
    parsed_draft = parse_pptx(io.BytesIO(res_draft.content))
    assert "Bản nháp" in parsed_draft["raw_text"]
    assert r"\frac" in parsed_draft["raw_text"]
    assert len(parsed_draft["slides"][0]["tables"]) == 1
    # Unconfirmed graph on slide 2 is omitted (no picture shape on slide 2)
    assert not any(sh.shape_type == 13 for sh in prs_draft.slides[1].shapes)

    # 2. Confirm both visuals on item m2 and approve expert confirmation -> no Bản nháp stamp, static PNG embedded on slide 2
    m2 = payload["outline"]["items"][1]
    conf_g = api.post("/api/v1/visuals/confirm", json={
        "project_id": payload["project_id"],
        "item_id": m2["item_id"],
        "kind": "graph",
        "data": m2["visuals"][0]["data"],
        "source": m2,
    }).json()
    m2["visuals"][0]["status"] = "confirmed"
    m2["visuals"][0]["requirement_token"] = conf_g["requirement_token"]

    conf_b = api.post("/api/v1/visuals/confirm", json={
        "project_id": payload["project_id"],
        "item_id": m2["item_id"],
        "kind": "bbt",
        "data": m2["visuals"][1]["data"],
        "source": m2,
    }).json()
    m2["visuals"][1]["status"] = "confirmed"
    m2["visuals"][1]["requirement_token"] = conf_b["requirement_token"]

    report = api.post("/api/v1/quality/workbench/check", json=payload).json()
    token = api.post("/api/v1/quality/workbench/approve", json={
        **payload,
        "acknowledged": True,
        "content_fingerprint": report["content_fingerprint"],
    }).json()["review_token"]
    payload["deck"]["review_token"] = token

    res_ready = api.post("/api/v1/workbench/export-pptx", json=payload)
    assert res_ready.status_code == 200, res_ready.text
    prs_ready = Presentation(io.BytesIO(res_ready.content))
    parsed_ready = parse_pptx(io.BytesIO(res_ready.content))
    assert "Bản nháp" not in parsed_ready["raw_text"]
    assert any(sh.shape_type == 13 for sh in prs_ready.slides[1].shapes)


def test_workbench_ai_assistant_allows_text_edits_and_rejects_visual_patches(api):
    payload = _sample_lesson_payload()
    slide = payload["deck"]["slides"][1]

    # 1. Valid text-only edit proposal
    valid_llm = {
        "ai_response": "Đã rút gọn tiêu đề ngắn gọn hơn.",
        "slide_id": slide["slide_id"],
        "changes": [{"element_id": "e4", "text": "Khảo sát hàm bậc ba"}],
    }
    with patch("lessonai.services.assistant.workbench_assistant.llm_gateway.generate_structured", return_value=valid_llm):
        res = api.post("/api/v1/chat/workbench/assistant", json={
            "project_id": payload["project_id"],
            "title": payload["title"],
            "slide": slide,
            "user_message": "Rút gọn tiêu đề",
        })
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["diffs"]) == 1
    assert body["patched_slide"]["elements"][0]["text"] == "Khảo sát hàm bậc ba"

    # 2. Forbidden patch targeting a figure element or visual_id -> 422 visual_patch_forbidden
    forbidden_llm = {
        "ai_response": "Sửa hình",
        "slide_id": slide["slide_id"],
        "changes": [{"element_id": "e5", "type": "graph", "visual_id": "v-other"}],
    }
    with patch("lessonai.services.assistant.workbench_assistant.llm_gateway.generate_structured", return_value=forbidden_llm):
        res_bad = api.post("/api/v1/chat/workbench/assistant", json={
            "project_id": payload["project_id"],
            "title": payload["title"],
            "slide": slide,
            "user_message": "Đổi đồ thị",
        })
    assert res_bad.status_code == 422
    assert res_bad.json()["detail"]["code"] == "visual_patch_forbidden"


def test_workbench_lesson_plan_from_outline_and_dual_package_zip(api):
    payload = _sample_lesson_payload()
    steps = {
        "step_1_assign": "Giáo viên chuyển giao nhiệm vụ học tập cho học sinh.",
        "step_2_excute": "Học sinh thảo luận nhóm và thực hiện nhiệm vụ.",
        "step_3_report": "Đại diện nhóm báo cáo kết quả trước lớp.",
        "step_4_conclusion": "Giáo viên nhận xét và chốt kiến thức chuẩn.",
    }
    valid_plan = {
        "lesson_title": payload["title"],
        "subject": "Toán học",
        "grade": 12,
        "knowledge_goals": ["Khảo sát hàm số bậc ba"],
        "competency_goals": ["Tư duy và lập luận toán học"],
        "skills_goals": ["Vẽ đồ thị"],
        "character_goals": ["Chăm chỉ"],
        "teaching_equipment": ["SGK Toán 12"],
        "activities": [
            {"activity_number": 1, "time_minutes": 5, "goal": "Hoạt động 1 (Khởi động): Khảo sát hàm số bậc ba - Toán 12", "expected_product": "Trả lời câu hỏi mở đầu", "execution": steps},
            {"activity_number": 2, "time_minutes": 15, "goal": "Hoạt động 2 (Hình thành kiến thức): Ví dụ khảo sát $y = x^3 - 3x + 1$", "expected_product": "Đạo hàm và cực trị; Vẽ đồ thị $y = x^3 - 3x + 1$", "execution": steps},
            {"activity_number": 3, "time_minutes": 15, "goal": "Hoạt động 3 (Luyện tập): Cực trị hàm số", "expected_product": "Chọn đáp án đúng", "execution": steps},
            {"activity_number": 4, "time_minutes": 10, "goal": "Hoạt động 4 (Vận dụng): Tổng kết", "expected_product": "Ba bước khảo sát", "execution": steps},
        ],
    }
    req = {
        "title": payload["title"],
        "sgk": payload["sgk"],
        "lesson_id": "M12-C1-B4",
        "level": "standard",
        "outline": payload["outline"],
    }
    with patch("lessonai.services.generation.workbench_lesson_plan.llm_gateway.generate_structured", return_value=valid_plan) as mock_gen:
        res = api.post("/api/v1/workbench/lesson-plan", json=req)
    assert res.status_code == 200, res.text
    assert mock_gen.call_count == 1
    assert mock_gen.call_args.kwargs["single_attempt"] is True

    # Missing outline item in generated plan -> rejected with 503 invalid_ai_output
    broken_plan = copy.deepcopy(valid_plan) if "copy" in globals() else json.loads(json.dumps(valid_plan))
    broken_plan["activities"][2]["goal"] = "Hoạt động 3 (Luyện tập): Nội dung hoàn toàn khác"
    broken_plan["activities"][2]["expected_product"] = "Không khớp"
    with patch("lessonai.services.generation.workbench_lesson_plan.llm_gateway.generate_structured", return_value=broken_plan):
        res_bad = api.post("/api/v1/workbench/lesson-plan", json=req)
    assert res_bad.status_code == 503
    assert res_bad.json()["detail"]["code"] == "invalid_ai_output"

    # Export Dual-Package ZIP with v3 canvas deck + 5512 plan
    zip_res = api.post("/api/v1/lesson-plan/export-dual-package", json={
        "plan": valid_plan,
        "slide_deck": payload,
    })
    assert zip_res.status_code == 200, zip_res.text
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        assert len(zf.namelist()) == 3


def test_graph_sampling_shaded_area_special_points_bbt_solid_and_oxyz(api):
    source = {"title": "Khảo sát $y = x^3 - 3x + 1$ và $y = (2x + 1)/(x - 1)$", "points": ["Tính diện tích từ -1 đến 1"]}

    # 1. Confirm cubic graph with shaded area [a, b] = [-1, 1] (#51, #52, #56, #57)
    conf_cubic = api.post("/api/v1/visuals/confirm", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "graph",
        "data": {
            "expression": "x^3 - 3*x + 1",
            "x_min": -3,
            "x_max": 3,
            "area": {"target": "ox", "a": -1, "b": 1},
        },
        "source": source,
    })
    assert conf_cubic.status_code == 200, conf_cubic.text
    cubic_token = conf_cubic.json()["requirement_token"]

    # Invalid area bounds a >= b rejected (#56)
    bad_area = api.post("/api/v1/visuals/confirm", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "graph",
        "data": {"expression": "x^3 - 3*x + 1", "x_min": -3, "x_max": 3, "area": {"target": "ox", "a": 2, "b": 1}},
        "source": source,
    })
    assert bad_area.status_code == 422

    sampled_cubic = api.post("/api/v1/visuals/graph/sample", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "graph",
        "expression": "x^3 - 3*x + 1",
        "x_min": -3,
        "x_max": 3,
        "area": {"target": "ox", "a": -1, "b": 1},
        "requirement_token": cubic_token,
        "viewport_x_min": -4,
        "viewport_x_max": 4,
    })
    assert sampled_cubic.status_code == 200, sampled_cubic.text
    s_data = sampled_cubic.json()
    assert len(s_data["area_polygons"]) >= 1
    sp = s_data["special_points"]
    assert sp["extrema"]["supported"] is True
    assert [it["display"] for it in sp["extrema"]["items"]] == ["CĐ(−1; 3)", "CT(1; −1)"]
    assert all(it["status"] == "verified" for it in sp["extrema"]["items"])
    assert sp["asymptotes"]["has_asymptotes"] is False
    assert "không có đường tiệm cận" in sp["asymptotes"]["disabled_reason"]

    # 2. Rational function graph & BBT (#55, #57)
    for expr, expected_family in [
        ("x^3 - 3*x + 1", "cubic"),
        ("(2*x + 1)/(x - 1)", "rational_1_1"),
        ("(x^2 - x + 1)/(x - 1)", "rational_2_1"),
    ]:
        conf_bbt = api.post("/api/v1/visuals/confirm", json={
            "project_id": "p1",
            "item_id": "m1",
            "kind": "bbt",
            "data": {"expression": expr},
            "source": source,
        })
        assert conf_bbt.status_code == 200, (expr, conf_bbt.text)
        bbt_res = api.post("/api/v1/visuals/bbt", json={
            "project_id": "p1",
            "item_id": "m1",
            "kind": "bbt",
            "expression": expr,
            "requirement_token": conf_bbt.json()["requirement_token"],
        })
        assert bbt_res.status_code == 200, bbt_res.text
        bbt_json = bbt_res.json()
        assert bbt_json["family"] == expected_family
        assert bbt_json["status"] == "verified"
        assert all(c["status"] == "verified" for c in bbt_json["claims"])

    # Unsupported BBT function family (e.g. sin(x) or degree 4) rejected with clear message (#55)
    bad_bbt = api.post("/api/v1/visuals/confirm", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "bbt",
        "data": {"expression": "sin(x)"},
        "source": source,
    })
    assert bad_bbt.status_code == 422
    assert "chưa hỗ trợ lập bảng biến thiên" in bad_bbt.json()["detail"]["message"]

    # 3. Hình Oxyz confirmation and degenerate rejection (#54)
    conf_oxyz = api.post("/api/v1/visuals/confirm", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "oxyz",
        "data": {
            "objects": [
                {"id": "A", "type": "point", "label": "A", "coords": [1, 2, 3]},
                {"id": "u", "type": "vector", "label": "u", "coords": [1, 0, -1]},
                {"id": "d", "type": "line", "label": "d", "point": [0, 0, 0], "direction": [1, 2, 1]},
                {"id": "P", "type": "plane", "label": "(P)", "coeffs": [1, -1, 2, -4]},
                {"id": "S", "type": "sphere", "label": "(S)", "center": [1, 1, 1], "radius": 2},
            ]
        },
        "source": source,
    })
    assert conf_oxyz.status_code == 200, conf_oxyz.text
    oxyz_scene = api.post("/api/v1/visuals/scene", json={
        "project_id": "p1",
        "item_id": "m1",
        "kind": "oxyz",
        "objects": conf_oxyz.json()["requirement"]["spec"]["objects"],
        "requirement_token": conf_oxyz.json()["requirement_token"],
    })
    assert oxyz_scene.status_code == 200, oxyz_scene.text
    assert oxyz_scene.json()["kind"] == "oxyz"
    assert len(oxyz_scene.json()["objects"]) == 5

    # Degenerate Oxyz objects rejected (zero vector, zero normal plane, non-positive radius) (#54)
    for bad_obj in [
        {"type": "vector", "label": "u", "coords": [0, 0, 0]},
        {"type": "plane", "label": "P", "coeffs": [0, 0, 0, 5]},
        {"type": "sphere", "label": "S", "center": [0, 0, 0], "radius": 0},
    ]:
        res_deg = api.post("/api/v1/visuals/confirm", json={
            "project_id": "p1",
            "item_id": "m1",
            "kind": "oxyz",
            "data": {"objects": [bad_obj]},
            "source": source,
        })
        assert res_deg.status_code == 422, bad_obj
