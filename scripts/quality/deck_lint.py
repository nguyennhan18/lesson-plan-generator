#!/usr/bin/env python3
"""
M0.3 - CLI đo Baseline chất lượng Slide & Deck bằng `deck_lint.py`.

Đo 3 lớp:
1. Toàn bộ 1.847 slide trong `data/slides_kntt12/slides_kntt12_cleaned.jsonl`
2. Các slide thuộc 6 bài Golden Set Toán 12 KNTT (CT 2018)
3. Các SlideDeck sinh bởi pipeline hiện tại (`get_retrieval_math12_slide_deck`) cho các bài trong Golden Set.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"

from lessonai.services.deck_lint import lint_deck, lint_slide  # noqa: E402
from lessonai.services.generation.fallback import get_retrieval_math12_slide_deck  # noqa: E402

DATA_DIR = REPO_ROOT / "app" / "backend" / "data"
CLEANED_SLIDES_PATH = DATA_DIR / "slides_kntt12" / "slides_kntt12_cleaned.jsonl"
GOLDEN_SET_PATH = REPO_ROOT / "data" / "fixtures" / "golden_set.json"
OUT_BASELINE_PATH = REPO_ROOT / "reports" / "data" / "baseline_lint_report.json"


def evaluate_jsonl_slides(slides: List[Dict[str, Any]]) -> Dict[str, Any]:
    error_counts: Dict[str, int] = {}
    slides_with_errors = 0
    sample_failures = []

    for sl in slides:
        res = lint_slide(sl, is_ingested_raw=True)
        if res["errors"]:
            slides_with_errors += 1
            for err in res["errors"]:
                code = err.split(":", 1)[0]
                error_counts[code] = error_counts.get(code, 0) + 1
            if len(sample_failures) < 15:
                sample_failures.append({
                    "slide_id": sl.get("slide_id"),
                    "lesson_id": sl.get("lesson_id"),
                    "page_number": sl.get("page_number"),
                    "title": sl.get("title"),
                    "activity_type": sl.get("activity_type"),
                    "errors": res["errors"],
                })

    total = len(slides)
    clean = total - slides_with_errors
    return {
        "total_slides": total,
        "clean_slides": clean,
        "slides_with_errors": slides_with_errors,
        "pass_rate_pct": round((clean * 100.0) / max(1, total), 2),
        "error_counts_by_type": dict(sorted(error_counts.items(), key=lambda x: -x[1])),
        "sample_failures": sample_failures,
    }


def evaluate_current_pipeline_decks(golden_lessons: List[Dict[str, Any]]) -> Dict[str, Any]:
    deck_reports = []
    agg_errors: Dict[str, int] = {}
    total_slides = 0
    total_clean_slides = 0

    seen_lids = set()
    for item in golden_lessons:
        lid = item.get("lesson_id")
        if not lid or not lid.startswith("M12-C") or lid in seen_lids:
            continue
        seen_lids.add(lid)
        deck = get_retrieval_math12_slide_deck(topic=item["title"], lesson_id=lid)
        rep = lint_deck(deck)
        total_slides += rep["total_slides"]
        total_clean_slides += rep["clean_slides"]
        for k, v in rep["error_counts_by_type"].items():
            agg_errors[k] = agg_errors.get(k, 0) + v
        deck_reports.append({
            "golden_id": item["id"],
            "lesson_id": lid,
            "title": item["title"],
            "total_slides": rep["total_slides"],
            "clean_slides": rep["clean_slides"],
            "slides_with_errors": rep["slides_with_errors"],
            "pass_rate_pct": rep["pass_rate_pct"],
            "error_counts_by_type": rep["error_counts_by_type"],
            "slides": rep["slides"],
        })

    return {
        "decks_evaluated": len(deck_reports),
        "total_slides": total_slides,
        "clean_slides": total_clean_slides,
        "slides_with_errors": total_slides - total_clean_slides,
        "pass_rate_pct": round((total_clean_slides * 100.0) / max(1, total_slides), 2),
        "error_counts_by_type": dict(sorted(agg_errors.items(), key=lambda x: -x[1])),
        "decks": deck_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy deck_lint đo Baseline (M0.3)")
    parser.add_argument("--output", type=str, default=str(OUT_BASELINE_PATH))
    args = parser.parse_args()

    all_slides = []
    if CLEANED_SLIDES_PATH.exists():
        for line in CLEANED_SLIDES_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                all_slides.append(json.loads(line))

    golden_data = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    golden_lessons = golden_data.get("golden_lessons", [])
    golden_lids = {
        g["lesson_id"]
        for g in golden_lessons
        if g.get("source_kind") == "pdf2xml" and g.get("lesson_id")
    }
    golden_ingested_slides = [s for s in all_slides if s.get("lesson_id") in golden_lids]

    corpus_eval = evaluate_jsonl_slides(all_slides)
    golden_ingested_eval = evaluate_jsonl_slides(golden_ingested_slides)
    generated_decks_eval = evaluate_current_pipeline_decks(golden_lessons)

    report = {
        "ingested_kntt12_corpus_baseline": corpus_eval,
        "golden_set_ingested_slides_baseline": golden_ingested_eval,
        "current_pipeline_generated_decks_baseline": generated_decks_eval,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== KẾT QUẢ ĐO BASELINE BẰNG DECK_LINT (M0.3) ===")
    print(f"1. Kho slide hiện tại (slides_kntt12_cleaned.jsonl):")
    print(
        f"   - Tổng số slide: {corpus_eval['total_slides']} | "
        f"Đạt: {corpus_eval['clean_slides']} ({corpus_eval['pass_rate_pct']}%) | "
        f"Lỗi: {corpus_eval['slides_with_errors']}"
    )
    print(f"   - Phân loại lỗi: {corpus_eval['error_counts_by_type']}")

    print(f"\n2. Tập Golden Set (6 bài pdf2xml KNTT 12 trong kho hiện tại):")
    print(
        f"   - Tổng số slide: {golden_ingested_eval['total_slides']} | "
        f"Đạt: {golden_ingested_eval['clean_slides']} ({golden_ingested_eval['pass_rate_pct']}%) | "
        f"Lỗi: {golden_ingested_eval['slides_with_errors']}"
    )
    print(f"   - Phân loại lỗi: {golden_ingested_eval['error_counts_by_type']}")

    print(f"\n3. Các Deck sinh bởi Pipeline v1 hiện tại (`get_retrieval_math12_slide_deck`):")
    print(
        f"   - Số deck: {generated_decks_eval['decks_evaluated']} | "
        f"Tổng số slide: {generated_decks_eval['total_slides']} | "
        f"Đạt: {generated_decks_eval['clean_slides']} ({generated_decks_eval['pass_rate_pct']}%) | "
        f"Lỗi: {generated_decks_eval['slides_with_errors']}"
    )
    print(f"   - Phân loại lỗi: {generated_decks_eval['error_counts_by_type']}")
    print(f"\nĐã lưu báo cáo baseline chi tiết tại: {out_path}")


if __name__ == "__main__":
    main()
