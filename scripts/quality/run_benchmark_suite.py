#!/usr/bin/env python3
"""
Thực thi Bộ đề chuẩn & Phản ví dụ Toán 12 (`data/fixtures/math12_benchmark_suite.json`)
qua đường sản phẩm thực (`math_worker`, `geometry_scene`, `visual_requirements`,
`/api/v1/chart/render`, `/api/v1/visuals/confirm`, `/api/v1/quality/check`, `/api/v1/quality/approve`).

Lưu ý: Toàn bộ ca kỹ thuật đạt (`technical_pass=True`) không thay thế chữ ký nghiệm thu
chuyên môn của giáo viên Toán 12 (`teacher_signoff_complete`).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from lessonai.core.jobs import get_runner
from lessonai.main import create_app
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.geometry_scene import build_scene
from lessonai.services.math_worker import verify_equality
from lessonai.services.visual_requirements import VisualError, confirm_requirement

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE_PATH = REPO_ROOT / "data" / "fixtures" / "math12_benchmark_suite.json"


def evaluate_benchmark_case(case: Dict[str, Any], api: TestClient) -> Dict[str, Any]:
    cid = case["case_id"]
    cat = case["category"]
    expected = case["expected_outcome"]
    deck_id = f"bench-{cid.lower()}"
    details: Dict[str, Any] = {}
    passed = True

    # 1. Kiểm tra đẳng thức trực tiếp nếu có equality_check
    if "equality_check" in case:
        eq = case["equality_check"]
        res = verify_equality(
            eq["lhs"],
            eq["rhs"],
            symbols=tuple(eq.get("symbols") or ("x",)),
            syntax=eq.get("syntax", "expression"),
        )
        details["equality_result"] = res
        if res.get("status") != expected.get("equality_status"):
            passed = False
        if "reason_contains" in expected and expected["reason_contains"] not in str(res.get("reason") or ""):
            passed = False

    # 2. Kiểm tra chặn biểu thức độc hại qua HTTP endpoint nếu có
    if "unsafe_plot_expression" in case:
        resp = api.post(
            "/api/v1/chart/render",
            json={"kind": "function_plot", "expression": case["unsafe_plot_expression"]},
        )
        details["unsafe_plot_http_status"] = resp.status_code
        if resp.status_code >= 400:
            details["unsafe_plot_error_message"] = resp.json().get("detail", {}).get("message", "")
        if resp.status_code != expected.get("unsafe_plot_http_status"):
            passed = False

    # 3. Kiểm tra các ca từ chối xác nhận hình học / đồ thị (under_specified, contradictory, out_of_scope)
    if expected.get("visual_confirmation_error"):
        spec_payload = copy.deepcopy(case.get("geometry_spec") or case.get("visual_spec") or {})
        spec_payload.update({"deck_id": deck_id, "slide_id": f"{cid.lower()}-s1", "source": {}})
        resp = api.post("/api/v1/visuals/confirm", json=spec_payload)
        details["visual_confirm_http_status"] = resp.status_code
        msg = resp.json().get("detail", {}).get("message", "")
        details["error_message"] = msg
        if resp.status_code != expected.get("http_status", 422):
            passed = False
        if "reason_contains" in expected:
            if expected["reason_contains"] not in msg:
                passed = False

    # 4. Kiểm tra ca thay đổi đề bài sau khi xác nhận hình (BM-CONTRA-02)
    if "slide_before_edit" in case and "slide_after_edit" in case:
        before_slide = copy.deepcopy(case["slide_before_edit"])
        after_slide = copy.deepcopy(case["slide_after_edit"])
        vspec = copy.deepcopy(case["visual_spec"])
        confirm_payload = {
            **vspec,
            "deck_id": deck_id,
            "slide_id": before_slide["slide_id"],
            "source": before_slide,
        }
        conf = confirm_requirement(confirm_payload)
        confirmed_chart_spec = {
            **vspec,
            **conf["requirement"]["spec"],
            "deck_id": deck_id,
            "slide_id": before_slide["slide_id"],
            "requirement_token": conf["requirement_token"],
        }
        after_slide["chart_spec"] = confirmed_chart_spec
        deck = SlideDeckSchema.model_validate({
            "deck_id": deck_id,
            "presentation_title": case["topic"],
            "subject": "Toán học",
            "grade": 12,
            "slides": [after_slide],
        }).model_dump(mode="json")

        q_resp = api.post("/api/v1/quality/check", json=deck).json()
        warning_ids = [i["issue_id"] for i in q_resp.get("issues", []) if i.get("severity") == "warning"]
        app_resp = api.post(
            "/api/v1/quality/approve",
            json={
                "deck": deck,
                "acknowledged": True,
                "reviewed_issue_ids": warning_ids,
                "content_fingerprint": q_resp.get("content_fingerprint"),
            },
        )
        err_count = sum(1 for i in q_resp.get("issues", []) if i.get("severity") == "error")
        details["quality_status"] = q_resp.get("status")
        details["blocking_error_count"] = err_count
        details["quality_issues"] = q_resp.get("issues", [])
        details["approve_http_status"] = app_resp.status_code
        if q_resp.get("status") != expected["quality_status"]:
            passed = False
        if err_count < expected.get("min_blocking_errors", 1):
            passed = False
        if (app_resp.status_code == 200) != expected["teacher_approval_allowed"]:
            passed = False

    # 5. Kiểm tra slide hoàn chỉnh (valid & faulty)
    if "slide" in case:
        slide = copy.deepcopy(case["slide"])
        slide_id = slide["slide_id"]

        if "visual_spec" in case and not expected.get("visual_confirmation_error"):
            vspec = copy.deepcopy(case["visual_spec"])
            plot_res = get_runner().run("math.plot", vspec)
            details["plot_status"] = plot_res.get("status")
            details["plot_segments_count"] = len(plot_res.get("segments") or [])
            if plot_res.get("status") != expected.get("plot_status"):
                passed = False
            if len(plot_res.get("segments") or []) < expected.get("min_plot_segments", 1):
                passed = False
            if "discontinuity_x" in expected:
                disc_x = float(expected["discontinuity_x"])
                # Đảm bảo không có đoạn nào nối trực tiếp qua điểm gián đoạn x = disc_x
                crosses = any(
                    seg[0][0] < disc_x < seg[-1][0]
                    for seg in (plot_res.get("segments") or [])
                    if len(seg) >= 2
                )
                details["crosses_discontinuity"] = crosses
                if crosses:
                    passed = False

            conf = confirm_requirement({
                **vspec,
                "deck_id": deck_id,
                "slide_id": slide_id,
                "source": slide,
            })
            slide["chart_spec"] = {
                **vspec,
                **conf["requirement"]["spec"],
                "deck_id": deck_id,
                "slide_id": slide_id,
                "requirement_token": conf["requirement_token"],
            }

        if "geometry_spec" in case and not expected.get("visual_confirmation_error"):
            gspec = copy.deepcopy(case["geometry_spec"])
            scene = build_scene(gspec)
            details["scene_status"] = scene.get("status")
            details["volume"] = scene["measurements"]["volume"]
            details["altitude_foot"] = scene["altitude_foot"]
            if scene.get("status") != expected.get("scene_status"):
                passed = False
            if not math.isclose(scene["measurements"]["volume"], expected["expected_volume"]):
                passed = False
            if scene["altitude_foot"] != expected["expected_altitude_foot"]:
                passed = False
            if "equal_lateral_edges" in expected:
                lengths = scene["measurements"]["edge_lengths"]
                all_equal = all(
                    math.isclose(lengths["S-A"], lengths[f"S-{v}"])
                    for v in ("B", "C", "D")
                )
                details["equal_lateral_edges"] = all_equal
                if all_equal != expected["equal_lateral_edges"]:
                    passed = False

            conf = confirm_requirement({
                **gspec,
                "deck_id": deck_id,
                "slide_id": slide_id,
                "source": slide,
            })
            slide["scene_spec"] = {
                **gspec,
                **conf["requirement"]["spec"],
                "deck_id": deck_id,
                "slide_id": slide_id,
                "requirement_token": conf["requirement_token"],
            }

        deck = SlideDeckSchema.model_validate({
            "deck_id": deck_id,
            "presentation_title": case["topic"],
            "subject": "Toán học",
            "grade": 12,
            "slides": [slide],
        }).model_dump(mode="json")

        q_resp = api.post("/api/v1/quality/check", json=deck).json()
        warning_ids = [i["issue_id"] for i in q_resp.get("issues", []) if i.get("severity") == "warning"]
        app_resp = api.post(
            "/api/v1/quality/approve",
            json={
                "deck": deck,
                "acknowledged": True,
                "reviewed_issue_ids": warning_ids,
                "content_fingerprint": q_resp.get("content_fingerprint"),
            },
        )
        err_count = sum(1 for i in q_resp.get("issues", []) if i.get("severity") == "error")

        details["quality_status"] = q_resp.get("status")
        details["blocking_error_count"] = err_count
        details["quality_issues"] = q_resp.get("issues", [])
        details["approve_http_status"] = app_resp.status_code

        if q_resp.get("status") != expected.get("quality_status"):
            passed = False
        if "blocking_error_count" in expected and err_count != expected["blocking_error_count"]:
            passed = False
        if "min_blocking_errors" in expected and err_count < expected["min_blocking_errors"]:
            passed = False
        if (app_resp.status_code == 200) != expected.get("teacher_approval_allowed"):
            passed = False

    return {
        "case_id": cid,
        "category": cat,
        "lesson_id": case["lesson_id"],
        "passed": passed,
        "details": details,
    }


def run_suite(suite_path: Path = DEFAULT_SUITE_PATH) -> Dict[str, Any]:
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases: List[Dict[str, Any]] = suite.get("cases") or []
    results: List[Dict[str, Any]] = []

    with TestClient(create_app()) as api:
        api.post("/api/v1/session")
        for case in cases:
            results.append(evaluate_benchmark_case(case, api))

    signoff = suite.get("teacher_signoff") or {}
    teacher_signed = bool(
        signoff.get("status") == "approved"
        and signoff.get("reviewer")
        and signoff.get("reviewed_at")
    )
    by_category: Dict[str, int] = {}
    for c in cases:
        cat = c["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "suite_id": suite.get("suite_id"),
        "total_cases": len(results),
        "passed_cases": sum(1 for r in results if r["passed"]),
        "technical_pass": all(r["passed"] for r in results),
        "categories": by_category,
        "teacher_signoff": signoff,
        "teacher_signoff_complete": teacher_signed,
        "handover_eligible": bool(all(r["passed"] for r in results) and teacher_signed),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE_PATH)
    parser.add_argument("--output", type=Path, required=True, help="Fresh output JSON path (opened with 'x').")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"Output path already exists: {args.output}")

    report = run_suite(args.suite)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "total_cases": report["total_cases"],
                "passed_cases": report["passed_cases"],
                "technical_pass": report["technical_pass"],
                "teacher_signoff_complete": report["teacher_signoff_complete"],
                "handover_eligible": report["handover_eligible"],
            },
            ensure_ascii=False,
        )
    )
    if not report["technical_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
