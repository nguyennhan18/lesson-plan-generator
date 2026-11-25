#!/usr/bin/env python3
"""Repeat the existing 15-case runner and record per-case elapsed time."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from lessonai.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if args.rounds < 2:
        parser.error("rounds must be at least 2")
    if args.output.exists():
        parser.error("output already exists")

    spec = importlib.util.spec_from_file_location("existing_benchmark_runner", args.runner)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    suite = json.loads(args.suite.read_text(encoding="utf-8"))
    cases = suite["cases"]
    if len(cases) != 15 or len({case["case_id"] for case in cases}) != 15:
        raise ValueError("Expected exactly 15 distinct cases in the existing suite")
    records = []
    rounds = []
    for round_number in range(1, args.rounds + 1):
        round_started = time.perf_counter()
        with TestClient(create_app()) as api:
            session_response = api.post("/api/v1/session")
            if session_response.status_code != 200:
                raise RuntimeError(f"session HTTP {session_response.status_code}")
            for case in cases:
                started = time.perf_counter()
                try:
                    result = module.evaluate_benchmark_case(case, api)
                except Exception as exc:
                    result = {
                        "case_id": case["case_id"],
                        "category": case["category"],
                        "lesson_id": case["lesson_id"],
                        "passed": False,
                        "exception": f"{type(exc).__name__}: {exc}",
                        "details": {},
                    }
                records.append({
                    "round": round_number,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                    **result,
                })
        rounds.append({
            "round": round_number,
            "elapsed_seconds": round(time.perf_counter() - round_started, 3),
        })
        print(json.dumps({
            "round": round_number,
            "passed": sum(r["passed"] for r in records if r["round"] == round_number),
            "total": len(cases),
        }))

    report = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "runner_sha256": hashlib.sha256(args.runner.read_bytes()).hexdigest(),
        "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
        "suite_id": suite.get("suite_id"),
        "case_count": len(cases),
        "rounds": rounds,
        "records": records,
        "metric_scope": "technical evaluator elapsed time; no LLM generation or file export",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
