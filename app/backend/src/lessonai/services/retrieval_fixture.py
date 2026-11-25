"""Offline fixture validation. Never loads runtime approvals or runs retrieval.

Usage: python -m lessonai.services.retrieval_fixture FIXTURE MANIFEST
Manifest units contain unit_id and the current content_hash. Approval hashes
are deliberately separate, so a stale approval remains a valid test input.
"""
import argparse
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Unit(StrictModel):
    unit_id: Text
    content_hash: Hash


class Reference(Unit):
    rationale: Text


class Forbidden(Reference):
    reason: Literal["not_approved", "revoked", "hash_changed", "irrelevant_distractor"]
    approval_hash: Hash | None = None


class RetrievalConfig(StrictModel):
    algorithm: Text
    algorithm_version: Text
    embedding: Text
    embedding_version: Text
    index_data_sha256: Hash
    top_k: Annotated[int, Field(gt=0)]
    min_bm25: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None
    tie_break: Literal["unit_id_ascending"]


class Case(StrictModel):
    case_id: Text
    lesson_id: Text
    query: Text
    required_ids: list[Reference]
    optional_relevant_ids: list[Reference] = Field(default_factory=list)
    forbidden_ids: list[Forbidden] = Field(default_factory=list)


class Fixture(StrictModel):
    schema_version: Literal["1"]
    config: RetrievalConfig
    cases: Annotated[list[Case], Field(min_length=1)]


class Manifest(StrictModel):
    hash_version: Literal[2]
    units: list[Unit]


def validate_fixture(fixture, manifest):
    """Return stable machine-readable errors, before any retrieval can run."""
    try:
        data = Fixture.model_validate(fixture)
        inventory = Manifest.model_validate(manifest)
    except ValidationError as exc:
        return [{"code": "FIXTURE_SCHEMA", "message": str(exc)}]
    errors = []

    def error(code, detail):
        errors.append({"code": code, "message": detail})

    units = {}
    for unit in inventory.units:
        if unit.unit_id in units:
            error("FIXTURE_DUPLICATE_ID", f"manifest: {unit.unit_id}")
        units[unit.unit_id] = unit.content_hash
    seen_cases = set()
    for case in data.cases:
        if case.case_id in seen_cases:
            error("FIXTURE_DUPLICATE_ID", f"case: {case.case_id}")
        seen_cases.add(case.case_id)
        seen = set()
        for group in (case.required_ids, case.optional_relevant_ids, case.forbidden_ids):
            local = set()
            for ref in group:
                if ref.unit_id in local:
                    error("FIXTURE_DUPLICATE_ID", f"{case.case_id}: {ref.unit_id}")
                elif ref.unit_id in seen:
                    error("FIXTURE_OVERLAP", f"{case.case_id}: {ref.unit_id}")
                local.add(ref.unit_id)
                if ref.unit_id not in units:
                    error("FIXTURE_UNKNOWN_ID", f"{case.case_id}: {ref.unit_id}")
                elif ref.content_hash != units[ref.unit_id]:
                    error("FIXTURE_HASH_MISMATCH", f"{case.case_id}: {ref.unit_id}")
                if isinstance(ref, Forbidden) and ref.reason == "hash_changed":
                    if ref.approval_hash is None or ref.approval_hash == ref.content_hash:
                        error("FIXTURE_APPROVAL_HASH", f"{case.case_id}: stale approval required for {ref.unit_id}")
            seen.update(local)
        if len(case.required_ids) > data.config.top_k:
            error("FIXTURE_CAPACITY", f"{case.case_id}: required count exceeds top_k")
    return errors


def aggregate_exit(codes):
    """Environment > fixture > contract/invalid_baseline > success."""
    return max(codes, default=0)


def run(fixture_path, manifest_path):
    objects, errors, codes = [], [], []
    for path in (fixture_path, manifest_path):
        try:
            objects.append(json.loads(Path(path).read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeError) as exc:
            errors.append({"code": "FIXTURE_JSON", "message": str(exc)})
            codes.append(2)
        except OSError as exc:
            errors.append({"code": "ENVIRONMENT_IO", "message": str(exc)})
            codes.append(3)
    if not codes:
        errors = validate_fixture(*objects)
        codes.append(2 if errors else 0)
    code = aggregate_exit(codes)
    return code, {"stage": "fixture_validation", "exit_code": code, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    code, report = run(args.fixture, args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
