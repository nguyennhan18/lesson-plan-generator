#!/usr/bin/env python3
"""Produce a non-mutating, review-ready triage report for RAG questions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lessonai.tooling.rag_question_triage import TRIAGE_SCHEMA_VERSION, summarize, triage_question


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "app/backend/data/questions/questions_math12_rag.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True, help="Must not already exist; evidence is append-only.")
    parser.add_argument("--id", dest="question_ids", action="append", help="Only triage one or more question IDs.")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Refusing to overwrite evidence: {args.output}")
    wanted = set(args.question_ids or [])
    rows = []
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        question = json.loads(line)
        if wanted and question.get("id") not in wanted:
            continue
        rows.append(triage_question(question))
    report = {"schema_version": TRIAGE_SCHEMA_VERSION, "input": str(args.input), "summary": summarize(rows), "results": rows}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
