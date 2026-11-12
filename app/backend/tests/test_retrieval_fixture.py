import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from lessonai.services.retrieval_fixture import validate_fixture, run, aggregate_exit


def sample():
    ref = {"unit_id": "test-u1", "content_hash": "a" * 64, "rationale": "Same function and domain"}
    fixture = {
        "schema_version": "1",
        "config": {"algorithm": "lexical", "algorithm_version": "test-1",
                   "embedding": "none", "embedding_version": "none",
                   "index_data_sha256": "b" * 64, "top_k": 1,
                   "score_threshold": 0.0, "tie_break": "unit_id_ascending"},
        "cases": [{"case_id": "positive", "query": "domain", "required_ids": [ref]}],
    }
    return fixture, {"units": [{"unit_id": "test-u1", "content_hash": "a" * 64}]}


@pytest.mark.parametrize("code", ["FIXTURE_SCHEMA", "FIXTURE_DUPLICATE_ID", "FIXTURE_OVERLAP",
                                  "FIXTURE_UNKNOWN_ID", "FIXTURE_HASH_MISMATCH",
                                  "FIXTURE_APPROVAL_HASH", "FIXTURE_CAPACITY"])
def test_each_semantic_error_has_exact_code(code):
    fixture, manifest = sample()
    case = fixture["cases"][0]
    ref = case["required_ids"][0]
    if code == "FIXTURE_SCHEMA":
        fixture["config"]["top_k"] = "1"
    elif code == "FIXTURE_DUPLICATE_ID":
        manifest["units"].append(copy.deepcopy(manifest["units"][0]))
    elif code == "FIXTURE_OVERLAP":
        case["optional_relevant_ids"] = [copy.deepcopy(ref)]
    elif code == "FIXTURE_UNKNOWN_ID":
        ref["unit_id"] = "typo"
    elif code == "FIXTURE_HASH_MISMATCH":
        ref["content_hash"] = "c" * 64
    elif code == "FIXTURE_APPROVAL_HASH":
        case["required_ids"] = []
        case["forbidden_ids"] = [{**ref, "reason": "hash_changed", "approval_hash": ref["content_hash"]}]
    elif code == "FIXTURE_CAPACITY":
        manifest["units"].append({"unit_id": "test-u2", "content_hash": "a" * 64})
        case["required_ids"].append({**ref, "unit_id": "test-u2"})
    assert [e["code"] for e in validate_fixture(fixture, manifest)] == [code]


def test_stale_approval_is_valid_and_inputs_unchanged():
    fixture, manifest = sample()
    case = fixture["cases"][0]
    ref = case["required_ids"].pop()
    case["forbidden_ids"] = [{**ref, "reason": "hash_changed", "approval_hash": "c" * 64}]
    before = copy.deepcopy((fixture, manifest))
    assert validate_fixture(fixture, manifest) == []
    assert (fixture, manifest) == before


def test_cli_good_bad_and_environment(tmp_path):
    fixture, manifest = sample()
    fp, mp = tmp_path / "fixture.json", tmp_path / "manifest.json"
    mp.write_text(json.dumps(manifest))
    for invalid, expected in [(False, 0), (True, 2)]:
        if invalid:
            fixture["cases"][0]["required_ids"][0]["unit_id"] = "missing"
        fp.write_text(json.dumps(fixture))
        proc = subprocess.run([sys.executable, "-m", "lessonai.services.retrieval_fixture", str(fp), str(mp)], capture_output=True, text=True)
        assert proc.returncode == expected, proc.stderr
        assert json.loads(proc.stdout)["exit_code"] == expected
    fp.write_text("{")
    assert run(fp, mp)[1]["errors"][0]["code"] == "FIXTURE_JSON"
    assert run(fp, mp)[0] == 2
    mp.unlink()
    assert run(fp, mp)[0] == 3  # environmental error dominates malformed JSON
    assert aggregate_exit([0, 1, 2, 3]) == 3
    assert aggregate_exit([0, 1]) == 1


@pytest.fixture(scope="module", autouse=True)
def real_approvals_unchanged():
    approval = Path(__file__).resolve().parents[1] / "data/reviewed_sources.json"
    before = hashlib.sha256(approval.read_bytes()).hexdigest() if approval.exists() else None
    yield
    after = hashlib.sha256(approval.read_bytes()).hexdigest() if approval.exists() else None
    assert after == before, "Real approval store changed during fixture validation tests"
