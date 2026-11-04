---
name: prepare-and-approve-rag-sources
description: Inventory, lint, stage, and generate hash-locked review manifests for Grade 12 Math pedagogical RAG sources. Activate this skill WHENEVER inspecting or updating curriculum files in app/backend/data, running slide deck quality lint, or preparing source units for teacher approval in app/backend/data/reviewed_sources.json.
---
# Prepare and Approve Pedagogical RAG Sources (`prepare-and-approve-rag-sources`)

## When to Use (Khi nào dùng)
Activate this skill whenever you need to:
- Inspect or update the local RAG corpus (`slides_kntt12_cleaned.jsonl`, `questions_math12_rag.jsonl`, `math12_ct2018.json`) under `app/backend/data/`.
- Run structural/pedagogical slide deck lint (`deck_lint.py`).
- Generate a hash-locked source review manifest (`prepare-source-review.py`) or record human teacher approvals in `app/backend/data/reviewed_sources.json`.

## Prerequisites (Điều kiện tiên quyết)
- Python virtual environment at `app/backend/venv` with `lessonai` installed in editable mode.
- Runtime data present in `app/backend/data/` (or `LESSONAI_DATA_DIR` set to an absolute path).

## Steps (Các bước)
1. **Run corpus inventory and baseline deck lint:**
   ```bash
   make inventory
   make lint-data
   ```
2. **(Optional) Stage a packaged dataset into a new temporary directory:**
   ```bash
   app/backend/venv/bin/python scripts/data/build_packaged_data.py --output /tmp/lessonai-data-stage-001
   ```
   *Note:* `build_packaged_data.py` refuses to write into a non-empty directory and never overwrites `app/backend/data` automatically.
3. **Generate a hash-locked source review manifest (without auto-approving):**
   ```bash
   make prepare-source-review REVIEW_OUTPUT=/tmp/lessonai-review-001
   ```
   This invokes `scripts/quality/prepare-source-review.py` to write `/tmp/lessonai-review-001-sources.json` with `status: "needs_review"`, `sha256` (computed by `lessonai/rag/content_units.py:source_hash`), and `structural_issues` from `lint_slide`.
4. **Record human-verified approvals in `app/backend/data/reviewed_sources.json`:**
   Only after a human teacher/reviewer verifies the mathematical and pedagogical accuracy of specific units, add their records to `app/backend/data/reviewed_sources.json`:
   ```json
   {
     "sources": [
       {
         "id": "M12-C1-B1-S01",
         "source_type": "slide_kntt12",
         "sha256": "<exact_sha256_from_source_hash>",
         "status": "approved",
         "reviewer": "<reviewer_identifier>",
         "reviewed_at": "2026-11-04T10:00:00Z"
       }
     ]
   }
   ```
5. **Verify RAG filtering behavior:** `lessonai/rag/content_units.py:approved_units()` only releases items whose canonical JSON `sha256` (excluding volatile fields `tokens`, `quality_score`, `retrieval_score`) matches an `"approved"` entry with non-empty `reviewer` and `reviewed_at`.

## Reference Examples (Ví dụ mẫu)
- Hash computation & approval gate: `app/backend/src/lessonai/rag/content_units.py` (`source_snapshot`, `source_hash`, `approved_units`).
- Review manifest generator: `scripts/quality/prepare-source-review.py`.
- Hybrid BM25 + pedagogical retriever: `app/backend/src/lessonai/rag/retriever.py` (`Math12HybridRetriever`).
- Pedagogical slide linter: `app/backend/src/lessonai/services/deck_lint.py`.

## Verification (Cách kiểm tra đã làm đúng)
```bash
GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_phase3_pedagogical_rag.py app/backend/tests/test_phase4_rag_pipeline_and_fallback.py app/backend/tests/test_remediation_workflows.py
```

## Common Pitfalls (Lỗi thường gặp)
- **Bulk-approving unreviewed sources:** Never script mass updates setting `status: "approved"` in `reviewed_sources.json` just to increase available slide counts; this violates project remediation rules (`README.md`, `R08`).
- **Reusing an existing `REVIEW_OUTPUT` path:** `prepare-source-review.py` opens the output file with `open('x')` and raises `FileExistsError` if the file already exists.
- **Modifying a source unit after approval:** Any edit to a slide or question changes its `source_hash(item)`, automatically revoking its approval until re-reviewed.
