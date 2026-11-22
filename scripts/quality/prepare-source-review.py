#!/usr/bin/env python3
"""Produce a review inventory without modifying sources or inventing approvals."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from lessonai.rag.content_units import asset_manifest, source_hash, source_snapshot, unit
from lessonai.rag.retriever import Math12HybridRetriever
from lessonai.services.deck_lint import check_latex_syntax, lint_slide
from lessonai.services.slide_remediation import remediate_pdf2xml_slide


def _question_structural_issues(item: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for field in ("question", "solution"):
        for err in check_latex_syntax(str(item.get(field) or "")):
            if err not in issues:
                issues.append(err)
    for choice in item.get("choices") or []:
        for err in check_latex_syntax(str(choice or "")):
            if err not in issues:
                issues.append(err)
    for step in item.get("worked_solution_steps") or []:
        for err in check_latex_syntax(str(step or "")):
            if err not in issues:
                issues.append(err)
    return issues


def build_review_inventory(
    *,
    write_remediated_slides: Path | None = None,
) -> Dict[str, Any]:
    retriever = Math12HybridRetriever.get_instance()
    candidates = retriever.get_corpus_candidates_for_review()
    entries: List[Dict[str, Any]] = []
    remediated_slides: List[Dict[str, Any]] = []

    raw_clean_slides = 0
    remediated_clean_slides = 0
    clean_questions = 0

    for source_type in ("slide_kntt12", "question_bank_rag"):
        items = candidates.get(source_type) or []
        for item in items:
            entry = unit(item, source_type)
            record_id = (
                item.get("source_id")
                or item.get("id")
                or item.get("slide_id")
                or item.get("question_id")
            )
            doc_version = item.get("document_version") or item.get("version") or "unknown"
            entry.update(
                source_id=record_id,
                document_version=doc_version,
                lesson_id=item.get("lesson_id"),
                status="needs_review",
                reviewer=None,
                reviewed_at=None,
            )

            if source_type == "slide_kntt12":
                raw_errors = lint_slide(item, is_ingested_raw=True).get("errors", [])
                entry["structural_issues"] = raw_errors
                if not raw_errors:
                    raw_clean_slides += 1

                remediated = remediate_pdf2xml_slide(item)
                remediated_slides.append(remediated)
                rem_errors = lint_slide(remediated, is_ingested_raw=True).get("errors", [])
                if not rem_errors:
                    remediated_clean_slides += 1
                entry["remediated_candidate"] = {
                    "sha256": source_hash(remediated),
                    "structural_issues": rem_errors,
                    "content": source_snapshot(remediated),
                }
            else:
                q_errors = _question_structural_issues(item)
                entry["structural_issues"] = q_errors

            try:
                entry["asset_hashes"] = asset_manifest(item)
            except (OSError, ValueError, TypeError) as error:
                entry["asset_issue"] = str(error)

            if source_type == "question_bank_rag":
                if not entry["structural_issues"] and "asset_issue" not in entry:
                    clean_questions += 1

            effective_issues = (
                entry["remediated_candidate"]["structural_issues"]
                if source_type == "slide_kntt12"
                else entry["structural_issues"]
            )
            entry["review_ready"] = bool(not effective_issues and "asset_issue" not in entry)
            entries.append(entry)

    if write_remediated_slides is not None:
        write_remediated_slides.parent.mkdir(parents=True, exist_ok=True)
        with write_remediated_slides.open("x", encoding="utf-8") as handle:
            for slide in remediated_slides:
                handle.write(json.dumps(slide, ensure_ascii=False) + "\n")

    total_slides = len(candidates.get("slide_kntt12") or [])
    total_questions = len(candidates.get("question_bank_rag") or [])
    return {
        "schema_version": 1,
        "summary": {
            "total_units": len(entries),
            "approved": 0,
            "slides_total": total_slides,
            "slides_raw_lint_clean": raw_clean_slides,
            "slides_raw_lint_pass_rate_pct": round((raw_clean_slides * 100.0) / max(1, total_slides), 2),
            "slides_remediated_lint_clean": remediated_clean_slides,
            "slides_remediated_lint_pass_rate_pct": round((remediated_clean_slides * 100.0) / max(1, total_slides), 2),
            "questions_total": total_questions,
            "questions_review_ready": clean_questions,
            "questions_quarantined_by_assets": total_questions - clean_questions,
            "total_review_ready_for_teacher": remediated_clean_slides + clean_questions,
        },
        "sources": entries,
        "notice": "Lint sạch không chứng nhận đúng toán. Cần đối chiếu nguồn và giáo viên duyệt từng hash.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Fresh output JSON path (opened with 'x').")
    parser.add_argument(
        "--write-remediated-slides",
        type=Path,
        default=None,
        help="Optional fresh JSONL path to export structure-remediated pdf2xml slides.",
    )
    args = parser.parse_args()

    path = Path(args.output)
    if path.exists():
        parser.error(f"Output file already exists: {path}")
    if args.write_remediated_slides is not None and args.write_remediated_slides.exists():
        parser.error(f"Remediated slides file already exists: {args.write_remediated_slides}")

    payload = build_review_inventory(write_remediated_slides=args.write_remediated_slides)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "units": len(payload["sources"]),
                "approved": 0,
                "slides_raw_clean": payload["summary"]["slides_raw_lint_clean"],
                "slides_remediated_clean": payload["summary"]["slides_remediated_lint_clean"],
                "questions_review_ready": payload["summary"]["questions_review_ready"],
                "output": str(path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
