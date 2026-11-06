"""Build deterministic, non-approval provenance inventories for legacy RAG data."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


INVENTORY_SCHEMA_VERSION = 1


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        records.append(record)
    return records


def _stable_id(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _asset_references(record: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    references: list[dict[str, Any]] = []
    seen_asset_fields = False
    for field in ("images", "assets", "media"):
        if field not in record:
            continue
        seen_asset_fields = True
        values = record[field]
        if values in (None, []):
            continue
        if not isinstance(values, list):
            references.append({
                "field": field,
                "reference": None,
                "reference_sha256": None,
                "content_sha256": None,
                "status": "invalid_asset_manifest",
            })
            continue
        for index, value in enumerate(values):
            reference = value if isinstance(value, str) else None
            references.append({
                "field": field,
                "index": index,
                "reference": reference,
                "reference_sha256": _sha256_bytes(reference.encode("utf-8")) if reference else None,
                "content_sha256": None,
                "status": "external_reference_unverified" if reference and reference.startswith(("http://", "https://"))
                else "local_asset_bytes_not_available",
            })
    if references:
        status = "references_unverified"
    elif seen_asset_fields:
        status = "no_references_in_record"
    else:
        status = "not_recorded"
    return references, status


def _source_record_hash(record: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(record))


def _document_version(
    source_id: str,
    source_metadata: dict[str, Any],
    records: list[dict[str, Any]],
    key_fields: tuple[str, ...],
) -> str:
    ordered = sorted(
        records,
        key=lambda record: (
            tuple(str(record.get(field) or "") for field in key_fields),
            _source_record_hash(record),
        ),
    )
    version_payload = {
        "version_algorithm": "canonical-json-sha256-v1",
        "source_id": source_id,
        "source_metadata": source_metadata,
        "records": [
            {
                "record_key": [record.get(field) for field in key_fields],
                "content_sha256": _source_record_hash(record),
            }
            for record in ordered
        ],
    }
    return f"sha256:{_sha256_bytes(_canonical_json(version_payload))}"


def _load_question_bank(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows = _read_json(path)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected a JSON array of objects")
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id:
            continue
        if record_id in by_id:
            duplicate_ids.append(record_id)
        by_id[record_id] = row
    return by_id, {
        "record_count": len(rows),
        "missing_id_count": sum(not isinstance(row.get("id"), str) or not row.get("id") for row in rows),
        "duplicate_ids": sorted(set(duplicate_ids)),
        "file_sha256": _sha256_bytes(path.read_bytes()),
    }


def build_provenance_inventory(data_dir: Path) -> dict[str, Any]:
    """Create an inventory snapshot; this function never writes to the input corpus."""
    data_dir = Path(data_dir)
    slides_path = data_dir / "slides_kntt12" / "slides_kntt12_cleaned.jsonl"
    slide_manifest_path = data_dir / "slides_kntt12" / "manifest.json"
    decks_path = data_dir / "slides_kntt12" / "decks_kntt12.json"
    questions_path = data_dir / "questions" / "questions_math12_rag.jsonl"
    question_bank_path = data_dir / "questions" / "question_bank.json"
    summary_path = data_dir / "dataset_summary.json"

    slides = _read_jsonl(slides_path)
    slide_manifest = _read_json(slide_manifest_path)
    decks = _read_json(decks_path)
    questions = _read_jsonl(questions_path)
    question_bank, question_bank_summary = _load_question_bank(question_bank_path)
    summary = _read_json(summary_path)

    if not isinstance(slide_manifest, list) or any(not isinstance(row, dict) for row in slide_manifest):
        raise ValueError(f"{slide_manifest_path}: expected a JSON array of objects")
    if not isinstance(decks, list) or any(not isinstance(row, dict) for row in decks):
        raise ValueError(f"{decks_path}: expected a JSON array of objects")

    manifest_counts = Counter(str(row.get("file_id")) for row in slide_manifest if row.get("file_id"))
    deck_counts = Counter(str(row.get("doc_id")) for row in decks if row.get("doc_id"))
    manifest_by_file_id = {
        str(row.get("file_id")): row
        for row in slide_manifest
        if row.get("file_id") and manifest_counts[str(row.get("file_id"))] == 1
    }
    deck_by_doc_id = {
        str(row.get("doc_id")): row
        for row in decks
        if row.get("doc_id") and deck_counts[str(row.get("doc_id"))] == 1
    }

    slides_by_doc: dict[str, list[dict[str, Any]]] = {}
    missing_slide_fields: dict[str, int] = {}
    for record in slides:
        doc_id = record.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            missing_slide_fields["doc_id"] = missing_slide_fields.get("doc_id", 0) + 1
            continue
        slides_by_doc.setdefault(doc_id, []).append(record)
        for field in ("file_id", "source_file", "slide_no", "lesson_id"):
            if record.get(field) in (None, ""):
                missing_slide_fields[field] = missing_slide_fields.get(field, 0) + 1

    source_documents: list[dict[str, Any]] = []
    slide_documents: dict[str, dict[str, Any]] = {}
    unmatched_slide_sources: list[str] = []
    for doc_id in sorted(slides_by_doc):
        records = slides_by_doc[doc_id]
        file_ids = sorted({str(record.get("file_id")) for record in records if record.get("file_id")})
        source_files = sorted({str(record.get("source_file")) for record in records if record.get("source_file")})
        source_id = _stable_id("kntt12-pdf", doc_id)
        manifest_entry = (
            manifest_by_file_id.get(file_ids[0])
            if len(file_ids) == 1 and manifest_counts[file_ids[0]] == 1
            else None
        )
        deck_entry = deck_by_doc_id.get(doc_id)
        metadata = {
            "doc_id": doc_id,
            "file_id": file_ids[0] if len(file_ids) == 1 else None,
            "source_file": source_files[0] if len(source_files) == 1 else None,
            "manifest_entry": {
                key: manifest_entry.get(key)
                for key in ("filename", "size", "status")
            } if manifest_entry else None,
            "deck_lesson_id": deck_entry.get("lesson_id") if deck_entry else None,
        }
        version = _document_version(source_id, metadata, records, ("slide_no", "slide_id"))
        row = {
            "source_id": source_id,
            "source_type": "slide_source_document",
            "document_version": version,
            "version_basis": "canonical_extracted_records_and_manifest_metadata",
            "source_document_sha256": None,
            "source_document_sha256_status": "original_pdf_bytes_not_present_in_runtime_data",
            "provenance_status": "identified_extraction_snapshot" if len(file_ids) == len(source_files) == 1 and manifest_entry else "ambiguous",
            "decision_status": "pending_review",
            "record_count": len(records),
            "record_ids": [
                str(record.get("slide_id") or f"{doc_id}#S{record.get('slide_no')}")
                for record in sorted(records, key=lambda item: (str(item.get("slide_no") or ""), str(item.get("slide_id") or "")))
            ],
            "asset_manifest": [],
            "asset_status": "not_recorded_in_cleaned_rows",
            "identity_metadata": metadata,
        }
        if row["provenance_status"] != "identified_extraction_snapshot":
            unmatched_slide_sources.append(doc_id)
        source_documents.append(row)
        slide_documents[doc_id] = row

    slide_records: list[dict[str, Any]] = []
    for record in slides:
        doc_id = record.get("doc_id")
        document = slide_documents.get(str(doc_id)) if doc_id else None
        slide_records.append({
            "record_id": record.get("slide_id") or (
                f"{doc_id}#S{record.get('slide_no')}" if doc_id else None
            ),
            "source_id": document["source_id"] if document else None,
            "document_version": document["document_version"] if document else None,
            "content_sha256": _source_record_hash(record),
            "lesson_id": record.get("lesson_id"),
            "slide_no": record.get("slide_no"),
            "provenance_status": document["provenance_status"] if document else "missing_source_document_id",
            "decision_status": "pending_review",
        })

    question_source_id = _stable_id("rag-corpus", "questions_math12_rag")
    question_metadata = {
        "dataset_file": questions_path.name,
        "question_bank_file": question_bank_path.name,
        "lineage_kind": "dataset-container-not-original-publisher-document",
    }
    question_version = _document_version(question_source_id, question_metadata, questions, ("id",))
    question_by_id = {
        record.get("id"): record for record in questions if isinstance(record.get("id"), str)
    }
    runtime_question_counts = Counter(
        record.get("id") for record in questions if isinstance(record.get("id"), str)
    )
    question_bank_by_id = question_bank
    duplicate_question_bank_ids = set(question_bank_summary["duplicate_ids"])
    unmatched_question_ids = sorted(set(question_by_id) - set(question_bank_by_id))
    duplicate_runtime_question_ids = sorted(
        record_id
        for record_id, count in Counter(
            record.get("id") for record in questions if record.get("id")
        ).items()
        if count > 1
    )
    missing_question_fields: dict[str, int] = {}
    question_records: list[dict[str, Any]] = []
    question_asset_count = 0
    question_asset_reference_count = 0
    question_sources: dict[str, int] = {}
    for record in sorted(questions, key=lambda item: str(item.get("id") or "")):
        record_id = record.get("id")
        duplicate_runtime_id = isinstance(record_id, str) and runtime_question_counts[record_id] > 1
        duplicate_bank_id = isinstance(record_id, str) and record_id in duplicate_question_bank_ids
        bank_record = (
            question_bank_by_id.get(record_id)
            if isinstance(record_id, str) and not duplicate_runtime_id and not duplicate_bank_id
            else None
        )
        if bank_record:
            source_label = bank_record.get("source")
            if isinstance(source_label, str) and source_label:
                question_sources[source_label] = question_sources.get(source_label, 0) + 1
        references, asset_status = _asset_references(record)
        if references:
            question_asset_count += 1
            question_asset_reference_count += len(references)
        for field in (
            "id",
            "lesson_id",
            "question",
            "answer",
            "solution",
            "source",
            "source_id",
            "source_type",
            "document_version",
        ):
            if record.get(field) in (None, ""):
                missing_question_fields[field] = missing_question_fields.get(field, 0) + 1
        matched = bank_record is not None
        if duplicate_runtime_id:
            question_provenance_status = "duplicate_runtime_record_id"
        elif duplicate_bank_id:
            question_provenance_status = "duplicate_question_bank_record_id"
        elif not matched:
            question_provenance_status = "unmatched_question_bank_record"
        else:
            question_provenance_status = "origin_document_unresolved"
        question_records.append({
            "record_id": record_id,
            "source_id": question_source_id,
            "document_version": question_version,
            "content_sha256": _source_record_hash(record),
            "lesson_id": record.get("lesson_id"),
            "question_bank_record_id": record_id if matched else None,
            "question_bank_source_label": bank_record.get("source") if matched else None,
            "origin_source_id": None,
            "provenance_status": question_provenance_status,
            "decision_status": "pending_review",
            "asset_manifest": references,
            "asset_status": asset_status,
        })

    source_documents.append({
        "source_id": question_source_id,
        "source_type": "rag_corpus_snapshot",
        "document_version": question_version,
        "version_basis": "canonical_runtime_question_records",
        "source_document_sha256": _sha256_bytes(questions_path.read_bytes()),
        "source_document_sha256_status": "runtime_jsonl_file_bytes",
        "provenance_status": "container_only_origin_documents_unresolved",
        "decision_status": "pending_review",
        "record_count": len(questions),
        "record_ids": [str(record.get("id")) for record in sorted(questions, key=lambda item: str(item.get("id") or ""))],
        "asset_manifest": [],
        "asset_status": "record_level_asset_references_unverified",
        "identity_metadata": question_metadata,
    })

    source_documents.sort(key=lambda item: item["source_id"])
    slide_records.sort(key=lambda item: str(item.get("record_id") or ""))
    inventory = {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "hash_algorithm": "sha256",
        "canonicalization": "UTF-8 JSON, sorted object keys, compact separators, no NaN",
        "approval_policy": "inventory_only_all_records_pending_review",
        "input_files": {
            path.name: _sha256_bytes(path.read_bytes())
            for path in (
                slides_path,
                slide_manifest_path,
                decks_path,
                questions_path,
                question_bank_path,
                summary_path,
            )
        },
        "counts": {
            "slide_records": len(slides),
            "slide_source_documents": len(slides_by_doc),
            "question_records": len(questions),
            "question_bank_records": question_bank_summary["record_count"],
            "question_records_matched_to_bank": len(set(question_by_id) & set(question_bank_by_id)),
            "question_records_unmatched_to_bank": len(unmatched_question_ids),
            "question_records_with_asset_references": question_asset_count,
            "question_asset_references": question_asset_reference_count,
            "approved_records": 0,
            "pending_review_slide_records": len(slides),
            "pending_review_question_records": len(questions),
        },
        "discrepancies": {
            "dataset_summary_total_questions_rag": summary.get("total_questions_rag"),
            "dataset_summary_questions_rag_count": summary.get("questions_rag_count"),
            "actual_runtime_question_records": len(questions),
            "question_bank_duplicate_ids": question_bank_summary["duplicate_ids"],
            "unmatched_question_ids": unmatched_question_ids,
            "duplicate_runtime_question_ids": duplicate_runtime_question_ids,
            "unmatched_slide_source_doc_ids": unmatched_slide_sources,
            "duplicate_slide_manifest_file_ids": sorted(
                file_id for file_id, count in manifest_counts.items() if count > 1
            ),
            "duplicate_slide_deck_doc_ids": sorted(
                doc_id for doc_id, count in deck_counts.items() if count > 1
            ),
            "missing_slide_metadata_counts": dict(sorted(missing_slide_fields.items())),
            "missing_question_metadata_counts": dict(sorted(missing_question_fields.items())),
            "runtime_question_source_labels_from_joined_bank": dict(sorted(question_sources.items())),
        },
        "question_bank": {
            **question_bank_summary,
            "unmatched_runtime_question_ids": unmatched_question_ids,
        },
        "source_documents": source_documents,
        "slide_records": slide_records,
        "question_records": question_records,
    }
    return inventory


def inventory_bytes(inventory: dict[str, Any]) -> bytes:
    return (json.dumps(inventory, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def synchronize_dataset_summary(data_dir: Path) -> bool:
    """Correct the legacy total question count from the runtime JSONL record count."""
    data_dir = Path(data_dir)
    questions_path = data_dir / "questions" / "questions_math12_rag.jsonl"
    summary_path = data_dir / "dataset_summary.json"
    actual_count = len(_read_jsonl(questions_path))
    summary = _read_json(summary_path)
    if not isinstance(summary, dict):
        raise ValueError(f"{summary_path}: expected a JSON object")
    if summary.get("total_questions_rag") == actual_count:
        return False
    summary["total_questions_rag"] = actual_count
    payload = (json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    _atomic_write_bytes(summary_path, payload)
    return True


def write_inventory(path: Path, inventory: dict[str, Any]) -> bool:
    """Atomically write deterministic inventory bytes; return whether bytes changed."""
    path = Path(path)
    payload = inventory_bytes(inventory)
    if path.exists() and path.read_bytes() == payload:
        return False
    _atomic_write_bytes(path, payload)
    return True
