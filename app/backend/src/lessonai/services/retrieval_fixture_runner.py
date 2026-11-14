"""Execute validated fixtures against the real retriever; no approval writes."""
import copy
import hashlib
import json

from lessonai.rag.content_units import source_hash
from lessonai.rag.retriever import QUESTION_RETRIEVAL_VERSION
from lessonai.services.retrieval_fixture import Fixture, validate_fixture

ALGORITHM = "lessonai-question-bm25-quality"
VERSION = QUESTION_RETRIEVAL_VERSION


def index_hash(rows):
    # Order matters for the built corpus, even though result ties use identity.
    return hashlib.sha256(json.dumps([source_hash(row) for row in rows], separators=(",", ":")).encode()).hexdigest()


def identity(row):
    return str(row.get("unit_id") or row.get("id") or row.get("question_id") or "")


def check_result(case, rows):
    ids = [identity(row) for row in rows]
    required = {r.unit_id for r in case.required_ids}
    allowed = required | {r.unit_id for r in case.optional_relevant_ids}
    forbidden = {r.unit_id: r.reason for r in case.forbidden_ids}
    errors = []
    if not allowed and ids:
        errors.append({"code": "EXPECTED_EMPTY"})
    if len(ids) != len(set(ids)):
        errors.append({"code": "DUPLICATE_ID"})
    for uid in sorted(required - set(ids)):
        errors.append({"code": "MISSING_REQUIRED", "unit_id": uid})
    for uid in sorted(set(ids)):
        if uid in forbidden:
            errors.append({"code": "FORBIDDEN_PRESENT", "unit_id": uid, "reason": forbidden[uid]})
        elif uid not in allowed:
            errors.append({"code": "UNEXPECTED_ID", "unit_id": uid})
    return errors


def mutations(case, baseline):
    """Output mutations always start from a clean result; exact error-code sets."""
    if check_result(case, baseline):
        return [{"status": "invalid_baseline"}]
    attempts = []
    for ref in case.forbidden_ids:
        expected = {"FORBIDDEN_PRESENT"}
        if not case.required_ids and not case.optional_relevant_ids:
            expected.add("EXPECTED_EMPTY")
        attempts.append((ref.reason, baseline + [{"id": ref.unit_id}], expected))
    if case.required_ids:
        uid = case.required_ids[0].unit_id
        attempts.append(("remove_required", [r for r in baseline if identity(r) != uid], {"MISSING_REQUIRED"}))
    if baseline:
        attempts.append(("duplicate", baseline + [copy.deepcopy(baseline[0])], {"DUPLICATE_ID"}))
    known = {r.unit_id for r in case.required_ids + case.optional_relevant_ids + case.forbidden_ids}
    unknown = "mutation-unknown"
    while unknown in known:
        unknown += "-x"
    expected = {"UNEXPECTED_ID"}
    if not case.required_ids and not case.optional_relevant_ids:
        expected.add("EXPECTED_EMPTY")
    attempts.append(("unexpected", baseline + [{"id": unknown}], expected))
    result = []
    for kind, rows, expected in attempts:
        actual = {e["code"] for e in check_result(case, rows)}
        status = "detected_correctly" if actual == expected else "detected_wrong_code" if actual else "survived"
        result.append({"kind": kind, "expected_error_codes": sorted(expected), "actual_error_codes": sorted(actual), "status": status})
    return result


def execute(fixture, manifest, retriever, *, mutate=False):
    errors = validate_fixture(fixture, manifest)
    if errors:
        return 2, {"stage": "fixture_validation", "errors": errors}
    data = Fixture.model_validate(fixture)
    c = data.config
    if (c.algorithm, c.algorithm_version, c.embedding, c.embedding_version, c.tie_break) != (ALGORITHM, VERSION, "none", "none", "unit_id_ascending"):
        return 2, {"errors": [{"code": "FIXTURE_CONFIG_UNSUPPORTED"}]}
    if c.index_data_sha256 != index_hash(retriever._questions):
        return 2, {"errors": [{"code": "FIXTURE_INDEX_HASH"}]}
    results = []
    for case in data.cases:
        rows = retriever.retrieve_questions(case.lesson_id, query=case.query, k=c.top_k, min_bm25=c.min_bm25)
        errors = check_result(case, rows)
        result = {"case_id": case.case_id, "ids": [identity(row) for row in rows], "errors": errors}
        if mutate:
            result["mutations"] = mutations(case, rows)
        results.append(result)
    failed = any(r["errors"] or any(m["status"] != "detected_correctly" for m in r.get("mutations", [])) for r in results)
    by_kind = {}
    invalid_baseline = 0
    for result in results:
        for mutation in result.get("mutations", []):
            if mutation["status"] == "invalid_baseline":
                invalid_baseline += 1
                continue
            counts = by_kind.setdefault(mutation["kind"], {"detected_correctly": 0, "detected_wrong_code": 0, "survived": 0})
            counts[mutation["status"]] += 1
    for counts in by_kind.values():
        counts["correct_detection_rate"] = counts["detected_correctly"] / sum(counts.values())
    return int(failed), {"stage": "retrieval", "results": results, "invalid_baseline": invalid_baseline, "mutations_by_kind": by_kind}


def main():
    import argparse
    from pathlib import Path
    from lessonai.core.config import DATA_DIR, BACKEND_DIR
    from lessonai.rag.retriever import Math12HybridRetriever
    from lessonai.services.retrieval_fixture import run
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--test-root", required=True, type=Path)
    parser.add_argument("--mutate", action="store_true")
    args = parser.parse_args()
    root = args.test_root.resolve()
    if not DATA_DIR.is_relative_to(root) or DATA_DIR == root or DATA_DIR == (BACKEND_DIR / "data").resolve():
        code, report = 3, {"errors": [{"code": "ENVIRONMENT_DATA_DIR"}]}
    else:
        code, report = run(args.fixture, args.manifest)
        if code == 0:
            try:
                corpus = DATA_DIR / "questions/questions_math12_rag.jsonl"
                lines = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
                if not all(isinstance(row, dict) for row in lines):
                    raise ValueError("Corpus must contain objects")
                import contextlib
                import sys
                with contextlib.redirect_stdout(sys.stderr):
                    retriever = Math12HybridRetriever()
                if len(retriever._questions) != len(lines):
                    raise ValueError("Corpus loader skipped records")
                code, report = execute(json.loads(args.fixture.read_text()), json.loads(args.manifest.read_text()), retriever, mutate=args.mutate)
            except (OSError, ValueError, TypeError) as exc:
                code, report = 3, {"errors": [{"code": "ENVIRONMENT_CORPUS", "message": str(exc)}]}
    print(json.dumps({**report, "exit_code": code}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
