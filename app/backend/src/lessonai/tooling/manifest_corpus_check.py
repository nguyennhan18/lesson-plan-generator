"""Read-only hash-v2 corpus verification; never reads/writes approval registry."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError
from lessonai.rag import content_units
from lessonai.tooling.retrieval_fixture import Manifest


def unit_id(row):
    return row.get("unit_id") or row.get("id") or row.get("slide_id") or row.get("question_id")


def verify(manifest, rows):
    try:
        parsed = Manifest.model_validate(manifest)
    except ValidationError as exc:
        return [{"code": "FIXTURE_SCHEMA", "message": str(exc)}]
    current, errors = {}, []
    for row in rows:
        uid = unit_id(row)
        if not uid or uid in current:
            errors.append({"code": "FIXTURE_CORPUS_ID", "unit_id": uid})
        else:
            current[uid] = content_units.source_hash(row)
    seen = set()
    for unit in parsed.units:
        if unit.unit_id in seen:
            errors.append({"code": "FIXTURE_DUPLICATE_ID", "unit_id": unit.unit_id})
        seen.add(unit.unit_id)
        actual = current.get(unit.unit_id)
        if actual != unit.content_hash:
            errors.append({"code": "FIXTURE_MANIFEST_STALE", "unit_id": unit.unit_id,
                           "expected": unit.content_hash, "actual": actual,
                           "reason": "missing_unit" if actual is None else "content_changed"})
    return errors


def check_files(manifest_path, corpus_paths):
    errors, objects, rows, fingerprints = [], [], [], []
    exit_code = 0
    for path in [manifest_path, *corpus_paths]:
        try:
            raw = Path(path).read_bytes()
            fingerprints.append({"path": str(path), "sha256_bytes": hashlib.sha256(raw).hexdigest()})
            if path == manifest_path:
                objects.append(json.loads(raw))
            else:
                parsed = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
                if not all(isinstance(row, dict) for row in parsed):
                    raise ValueError("JSONL corpus must contain objects")
                rows.extend(parsed)
        except OSError as exc:
            exit_code = 3
            errors.append({"code": "ENVIRONMENT_IO", "message": str(exc)})
        except (ValueError, UnicodeError) as exc:
            exit_code = max(exit_code, 2)
            errors.append({"code": "FIXTURE_JSON", "message": str(exc)})
    if not errors:
        errors = verify(objects[0], rows)
        exit_code = 2 if errors else 0
    repo = Path(__file__).resolve().parents[4]
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True)
    code_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), Path(content_units.__file__), Path(__file__).with_name("retrieval_fixture.py")]}
    report = {"stage": "manifest_corpus", "hash_version": 2, "created_at": datetime.now(timezone.utc).isoformat(),
              "commit": commit.stdout.strip() if commit.returncode == 0 else None, "code_sha256": code_hashes,
              "files": fingerprints, "corpus_units": len(rows), "manifest_units": len(objects[0].get("units", [])) if objects and isinstance(objects[0], dict) else None,
              "exit_code": exit_code, "errors": errors}
    return exit_code, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--corpus", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    code, report = check_files(args.manifest, args.corpus)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(json.dumps({"exit_code": 3, "errors": [{"code": "ENVIRONMENT_OUTPUT", "message": str(exc)}]}))
        return 3
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
