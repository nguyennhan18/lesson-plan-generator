import copy
import hashlib
import json
import subprocess
import sys
import os
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
                   "min_bm25": 0.0, "tie_break": "unit_id_ascending"},
        "cases": [{"case_id": "positive", "lesson_id": "test-domain", "query": "domain", "required_ids": [ref]}],
    }
    return fixture, {"hash_version": 2, "units": [{"unit_id": "test-u1", "content_hash": "a" * 64}]}


def test_content_hash_v2_normalizes_text_without_changing_source():
    from lessonai.rag.content_units import source_hash, HASH_VERSION
    left = {"question": "Toán\r\n12\rA", "nested": [{"text": "e\u0301"}]}
    right = {"nested": [{"text": "é"}], "question": "Toán\n12\nA"}
    original = copy.deepcopy(left)
    assert HASH_VERSION == 2
    assert source_hash(left) == source_hash(right)
    assert left == original
    assert source_hash(right) != source_hash({**right, "question": "Toán\n11\nA"})


def test_stale_manifest_even_when_fixture_still_matches(tmp_path):
    from lessonai.rag.content_units import source_hash
    from lessonai.services.manifest_corpus_check import verify, check_files
    fixture, manifest = sample()
    original = {"id": "test-u1", "question": "x khác 3"}
    digest = source_hash(original)
    manifest["units"][0]["content_hash"] = digest
    fixture["cases"][0]["required_ids"][0]["content_hash"] = digest
    assert validate_fixture(fixture, manifest) == []
    assert verify(manifest, [original]) == []
    changed = {**original, "question": "x khác -3"}
    assert validate_fixture(fixture, manifest) == []
    assert verify(manifest, [changed])[0]["code"] == "FIXTURE_MANIFEST_STALE"
    assert verify(manifest, [])[0]["reason"] == "missing_unit"
    mp, cp = tmp_path / "manifest.json", tmp_path / "corpus.jsonl"
    mp.write_text(json.dumps(manifest))
    cp.write_text(json.dumps(changed))
    code, report = check_files(mp, [cp])
    assert code == 2 and report["corpus_units"] == 1
    assert report["code_sha256"] and len(report["files"]) == 2
    cp.unlink()
    assert check_files(mp, [cp])[0] == 3


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


@pytest.mark.parametrize("version", [None, 1, "2"])
def test_manifest_requires_current_hash_version(version):
    fixture, manifest = sample()
    if version is None:
        manifest.pop("hash_version")
    else:
        manifest["hash_version"] = version
    assert validate_fixture(fixture, manifest)[0]["code"] == "FIXTURE_SCHEMA"


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
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in approval.parent.glob("reviewed_sources.json*") if p.is_file()}
    yield
    after = hashlib.sha256(approval.read_bytes()).hexdigest() if approval.exists() else None
    assert after == before, "Real approval store changed during fixture validation tests"
    assert artifacts == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in approval.parent.glob("reviewed_sources.json*") if p.is_file()}


def test_real_retrieval_in_isolated_subprocess(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    env = {**os.environ, "LESSONAI_DATA_DIR": str(root)}
    code = r'''
import json, sys
from pathlib import Path
from lessonai.core.config import DATA_DIR, BACKEND_DIR
root = Path(sys.argv[1]).resolve()
if DATA_DIR != root / "corpus" or not DATA_DIR.is_relative_to(root) or DATA_DIR == (BACKEND_DIR / "data").resolve():
    sys.exit(3)
from lessonai.rag.content_units import register_source_approval, revoke_source_approval
rows = [{"id": f"isolation-test-{i:02}", "lesson_id": "test-domain", "question": "miền xác định hàm phân thức", "solution": "loại nghiệm mẫu số", "difficulty": "medium"} for i in range(24)]
register_source_approval(rows[0], "TEST ONLY")
register_source_approval(rows[1], "TEST ONLY")
revoke_source_approval(rows[1], reason="test", reviewer="TEST ONLY")
register_source_approval(rows[2], "TEST ONLY")
rows[2]["solution"] = "changed after approval"
(DATA_DIR / "questions").mkdir()
(DATA_DIR / "questions/questions_math12_rag.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
from lessonai.rag.retriever import Math12HybridRetriever
r = Math12HybridRetriever()
assert [q["id"] for q in r.retrieve_questions("test-domain", query="miền xác định", k=4)] == [rows[0]["id"]]
assert r.retrieve_questions("absent", query="miền xác định", k=4) == []
assert r.retrieve_questions("test-domain", query="zzznomatch", min_bm25=0.0) == []
assert r.retrieve_questions("test-domain", query=None, min_bm25=0.0)
assert r.retrieve_questions("test-domain", query="zzznomatch")  # None preserves legacy filtering
try:
    r.retrieve_questions("test-domain", score_threshold=0.1)
except TypeError:
    pass
else:
    raise AssertionError("Unknown runtime configuration was silently ignored")
for invalid in [float("nan"), float("inf"), -1]:
    try:
        r.retrieve_questions("test-domain", min_bm25=invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid BM25 threshold accepted")

# Same quality, same lesson, overlapping keywords, different mathematical condition.
target = {"id": "z-target", "lesson_id": "test-domain", "question": "miền xác định hàm phân thức mẫu x trừ ba", "difficulty": "medium"}
distractor = {"id": "a-distractor", "lesson_id": "test-domain", "question": "miền xác định hàm phân thức mẫu x cộng năm", "difficulty": "medium"}
for row in [target, distractor]:
    register_source_approval(row, "TEST ONLY")
corpus_path = DATA_DIR / "questions/questions_math12_rag.jsonl"
corpus_path.write_text("\n".join(json.dumps(row) for row in [distractor, target]))
r = Math12HybridRetriever()
config = {"k": 1, "min_bm25": 0.0}
found = r.retrieve_questions("test-domain", query="miền xác định phân thức mẫu x trừ ba", **config)
assert [q["id"] for q in found] == [target["id"]]
assert distractor["id"] not in [q["id"] for q in found]
assert r.retrieve_questions("test-domain", query="trừ ba", min_bm25=1e9) == []
for order in [[target, distractor], [distractor, target]]:
    corpus_path.write_text("\n".join(json.dumps(row) for row in order))
    tied = Math12HybridRetriever().retrieve_questions("test-domain", query=None, k=2)
    assert [q["id"] for q in tied] == ["a-distractor", "z-target"]

from lessonai.rag.content_units import load_approval_registry, save_approval_registry, approved_units
from lessonai.rag.content_units import source_hash
from lessonai.services.retrieval_fixture_runner import execute, index_hash, mutations, ALGORITHM, VERSION
from lessonai.services.retrieval_fixture import Case
ref = lambda row: {"unit_id": row["id"], "content_hash": source_hash(row), "rationale": "same function domain"}
fixture = {"schema_version": "1", "config": {"algorithm": ALGORITHM, "algorithm_version": VERSION, "embedding": "none", "embedding_version": "none", "index_data_sha256": index_hash(r._questions), "top_k": 1, "min_bm25": 0.0, "tie_break": "unit_id_ascending"}, "cases": [{"case_id": "ranking", "lesson_id": "test-domain", "query": "miền xác định phân thức mẫu x trừ ba", "required_ids": [ref(target)], "forbidden_ids": [{**ref(distractor), "reason": "irrelevant_distractor"}]}]}
manifest = {"hash_version": 2, "units": [{"unit_id": row["id"], "content_hash": source_hash(row)} for row in [target, distractor]]}
exit_code, report = execute(fixture, manifest, r, mutate=True)
assert exit_code == 0, report
assert all(m["status"] == "detected_correctly" for m in report["results"][0]["mutations"])
import subprocess
fixture_path, manifest_path = root / "fixture.json", root / "manifest.json"
fixture_path.write_text(json.dumps(fixture))
manifest_path.write_text(json.dumps(manifest))
cli = subprocess.run([sys.executable, "-m", "lessonai.services.retrieval_fixture_runner", str(fixture_path), str(manifest_path), "--test-root", str(root), "--mutate"], capture_output=True, text=True, timeout=15)
assert cli.returncode == 0, cli.stdout + cli.stderr
assert json.loads(cli.stdout)["exit_code"] == 0
bad_root = subprocess.run([sys.executable, "-m", "lessonai.services.retrieval_fixture_runner", str(fixture_path), str(manifest_path), "--test-root", str(root / "elsewhere")], capture_output=True, text=True, timeout=15)
assert bad_root.returncode == 3
fixture["config"]["top_k"] = 2
assert execute(fixture, manifest, r)[0] == 1  # actual runtime top_k admits distractor
fixture["config"]["top_k"] = 1
fixture["config"]["min_bm25"] = 1e9
assert execute(fixture, manifest, r)[0] == 1  # actual runtime threshold removes required
fixture["config"]["min_bm25"] = 0.0
for key, value in [("algorithm", "unsupported"), ("algorithm_version", "old"), ("embedding", "external"), ("embedding_version", "old"), ("index_data_sha256", "0"*64), ("tie_break", "corpus_order"), ("score_threshold", 0.0)]:
    changed = json.loads(json.dumps(fixture))
    changed["config"][key] = value
    assert execute(changed, manifest, r)[0] == 2, key
case = Case.model_validate(fixture["cases"][0])
assert mutations(case, [])[0]["status"] == "invalid_baseline"
for reason in ["not_approved", "revoked", "hash_changed", "irrelevant_distractor"]:
    case.forbidden_ids[0].reason = reason
    assert all(m["status"] == "detected_correctly" for m in mutations(case, [target]))
case.required_ids = []
assert all(m["status"] == "detected_correctly" for m in mutations(case, []))
registry = load_approval_registry()
for version in [None, 1, "2"]:
    for record in registry["sources"]:
        if version is None:
            record.pop("hash_version", None)
        else:
            record["hash_version"] = version
    save_approval_registry(registry)
    reasons = []
    assert approved_units([target, distractor], rejection_reasons=reasons) == []
    assert reasons and all(item["reason"] == "hash_version_mismatch" for item in reasons)
'''
    proc = subprocess.run([sys.executable, "-c", code, str(tmp_path)], env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
