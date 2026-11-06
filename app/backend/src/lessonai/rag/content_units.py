"""Keep source units whole. Only an explicit, hash-matched review enables reuse."""
import base64
import copy
import hashlib
import json
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is not required for local-first POSIX runtime
    fcntl = None

from lessonai.core.config import DATA_DIR


REGISTRY_FILENAME = "reviewed_sources.json"
logger = logging.getLogger(__name__)


def _registry_path() -> Path:
    return Path(DATA_DIR) / REGISTRY_FILENAME


def _default_registry() -> Dict[str, Any]:
    return {"schema_version": 1, "updated_at": None, "sources": []}


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def _corrupt_backup_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return path.with_name(f"{path.name}.corrupt.{stamp}")


@contextmanager
def _registry_lock() -> Iterable[None]:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f"{path.name}.lock")
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = _backup_path(path)
        try:
            shutil.copy2(path, backup)
        except OSError:
            logger.warning("Approval registry backup skipped for %s", path)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _normalize_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(record, dict):
        return None
    status = str(record.get("status") or "").lower()
    sha256 = record.get("sha256")
    source_id = record.get("source_id")
    source_type = record.get("source_type")
    document_version = record.get("document_version")
    asset_hashes = record.get("asset_hashes") or {}
    if not sha256 or not isinstance(sha256, str):
        return None
    if status == "approved":
        if not any([source_id, source_type, document_version]):
            return None
        if not isinstance(asset_hashes, dict):
            return None
    reviewer = record.get("reviewer")
    reviewed_at = record.get("reviewed_at")
    if status == "approved" and (not reviewer or not reviewed_at):
        return None
    normalized = {
        "source_id": source_id,
        "source_type": source_type,
        "document_version": document_version,
        "status": status or "unapproved",
        "sha256": sha256,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "revoked": bool(record.get("revoked", False)),
        "revoked_at": record.get("revoked_at"),
        "revocation_reason": record.get("revocation_reason"),
        "asset_hashes": asset_hashes,
    }
    if normalized["status"] == "approved" and normalized["revoked"]:
        normalized["status"] = "revoked"
    return normalized


def _read_registry_contents(path: Path) -> Dict[str, Any]:
    if not path.exists():
        registry = _default_registry()
        _atomic_write_json(path, registry)
        return registry

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        backup = _corrupt_backup_path(path)
        try:
            shutil.copy2(path, backup)
        except OSError:
            logger.warning("Approval registry corruption preserved without backup due to I/O error: %s", exc)
        else:
            logger.warning("Approval registry corrupted; preserved original at %s", backup)
        return _default_registry()

    if not isinstance(raw, dict):
        backup = _corrupt_backup_path(path)
        try:
            shutil.copy2(path, backup)
        except OSError:
            logger.warning("Approval registry payload was malformed and could not be backed up: %s", path)
        else:
            logger.warning("Approval registry payload malformed; preserved original at %s", backup)
        return _default_registry()

    sources = raw.get("sources") or []
    if not isinstance(sources, list):
        backup = _corrupt_backup_path(path)
        try:
            shutil.copy2(path, backup)
        except OSError:
            logger.warning("Approval registry sources list invalid: %s", path)
        else:
            logger.warning("Approval registry sources list invalid; preserved original at %s", backup)
        return _default_registry()

    normalized = []
    for record in sources:
        cleaned = _normalize_record(record)
        if cleaned is not None:
            normalized.append(cleaned)
    return {
        "schema_version": int(raw.get("schema_version") or 1),
        "updated_at": raw.get("updated_at"),
        "sources": normalized,
    }


def load_approval_registry() -> Dict[str, Any]:
    """Load and normalize the approval registry. Missing or malformed files fail closed but are preserved for recovery."""
    path = _registry_path()
    with _registry_lock():
        return _read_registry_contents(path)


def save_approval_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    """Persist an approval registry to disk without auto-approving any records."""
    payload = {
        "schema_version": int((registry or {}).get("schema_version") or 1),
        "updated_at": (registry or {}).get("updated_at") or datetime.now(timezone.utc).isoformat(),
        "sources": [],
    }
    for record in (registry or {}).get("sources") or []:
        cleaned = _normalize_record(record)
        if cleaned is not None:
            payload["sources"].append(cleaned)
    with _registry_lock():
        _atomic_write_json(_registry_path(), payload)
    return payload


def register_source_approval(source: Dict[str, Any], reviewer: str, *, status: str = "approved", document_version: Optional[str] = None, revocation_reason: Optional[str] = None) -> Dict[str, Any]:
    """Add or update a single approval record. This function does not auto-approve anything."""
    if not isinstance(source, dict):
        raise ValueError("Source approval payload must be an object")
    checksum = source_hash(source)
    record = {
        "source_id": source.get("source_id") or source.get("id") or source.get("slide_id") or source.get("question_id"),
        "source_type": source.get("source_type"),
        "document_version": document_version or source.get("document_version") or source.get("version") or "unknown",
        "status": str(status or "approved").lower(),
        "sha256": checksum,
        "reviewer": reviewer,
        "reviewed_at": source.get("reviewed_at") or datetime.now(timezone.utc).isoformat(),
        "revoked": False,
        "revoked_at": None,
        "revocation_reason": revocation_reason,
        "asset_hashes": asset_manifest(source),
    }
    if record["status"] == "revoked":
        record["revoked"] = True
        record["revoked_at"] = datetime.now(timezone.utc).isoformat()
    with _registry_lock():
        registry = _read_registry_contents(_registry_path())
        new_sources = []
        replaced = False
        for existing in registry.get("sources") or []:
            if existing.get("sha256") == checksum:
                new_sources.append(record)
                replaced = True
            else:
                new_sources.append(existing)
        if not replaced:
            new_sources.append(record)
        registry["sources"] = new_sources
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_write_json(_registry_path(), registry)
    return record


def revoke_source_approval(source: Dict[str, Any], *, reason: str, reviewer: str) -> Dict[str, Any]:
    """Revoke an approval record. Revoked entries are explicitly excluded from approved retrieval."""
    checksum = source_hash(source)
    with _registry_lock():
        registry = _read_registry_contents(_registry_path())
        record = None
        for existing in registry.get("sources") or []:
            if existing.get("sha256") == checksum:
                record = dict(existing)
                break
        if not record:
            record = {
                "source_id": source.get("source_id") or source.get("id") or source.get("slide_id") or source.get("question_id"),
                "source_type": source.get("source_type"),
                "document_version": source.get("document_version") or source.get("version") or "unknown",
                "status": "revoked",
                "sha256": checksum,
                "reviewer": reviewer,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revocation_reason": reason,
                "asset_hashes": asset_manifest(source),
            }
        else:
            record["status"] = "revoked"
            record["revoked"] = True
            record["revoked_at"] = datetime.now(timezone.utc).isoformat()
            record["revocation_reason"] = reason
            record["reviewer"] = reviewer
        registry["sources"] = [
            existing if existing.get("sha256") != checksum else record
            for existing in (registry.get("sources") or [])
        ]
        if not any(existing.get("sha256") == checksum for existing in (registry.get("sources") or [])):
            registry["sources"].append(record)
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_write_json(_registry_path(), registry)
    return record


def source_snapshot(item):
    if not isinstance(item, dict):
        return {}
    return {key: value for key, value in sorted(item.items()) if key not in {"tokens", "quality_score", "retrieval_score"}}


def source_hash(item):
    payload = json.dumps(source_snapshot(item), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def asset_manifest(item):
    """Fingerprint referenced assets too; unavailable/opaque references quarantine the unit."""
    manifest = {}
    for field in ("images", "assets", "media"):
        values = item.get(field) or []
        if not isinstance(values, list):
            raise ValueError("Danh sách asset không hợp lệ")
        for index, value in enumerate(values):
            if isinstance(value, dict):
                reference = value.get("path") or value.get("source_part") or value.get("data_url")
                inline = value.get("data_base64")
            elif isinstance(value, str):
                reference = value
                inline = None
            else:
                reference = None
                inline = None
            if inline:
                raw = base64.b64decode(inline, validate=True)
            elif isinstance(reference, str) and reference.startswith("data:image/"):
                raw = base64.b64decode(reference.split(",", 1)[1], validate=True)
            elif reference:
                path = (DATA_DIR / reference).resolve()
                if not path.is_relative_to(DATA_DIR.resolve()) or not path.is_file():
                    raise ValueError("Asset thiếu hoặc nằm ngoài kho dữ liệu")
                raw = path.read_bytes()
            else:
                raise ValueError("Asset chưa có dữ liệu để đối chiếu")
            manifest[f"{field}[{index}]"] = hashlib.sha256(raw).hexdigest()
    return manifest


def approval_identity(item):
    item_dict = item if isinstance(item, dict) else {}
    content_hash = source_hash(item_dict)
    return {
        "source_id": item_dict.get("source_id") or item_dict.get("id") or item_dict.get("slide_id") or item_dict.get("question_id"),
        "source_type": item_dict.get("source_type"),
        "document_version": item_dict.get("document_version") or item_dict.get("version") or "unknown",
        "content_hash": content_hash,
        "asset_hashes": asset_manifest(item_dict),
    }


def approved_units(items):
    registry = load_approval_registry()
    records = registry.get("sources", []) if isinstance(registry, dict) else []
    if not isinstance(records, list):
        return []
    approved = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        status = str(record.get("status") or "").lower()
        if status != "approved":
            continue
        sha256 = record.get("sha256")
        if not sha256 or not isinstance(sha256, str):
            continue
        if record.get("revoked") is True:
            continue
        reviewer = record.get("reviewer")
        reviewed_at = record.get("reviewed_at")
        if not reviewer or not reviewed_at:
            continue
        if not any([record.get("source_id"), record.get("source_type"), record.get("document_version")]):
            continue
        if not isinstance(record.get("asset_hashes"), dict):
            continue
        approved[sha256] = record

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            item_identity = approval_identity(item)
        except (OSError, ValueError, TypeError):
            continue
        record = approved.get(item_identity["content_hash"])
        if record is None:
            continue
        if item_identity["document_version"] != record.get("document_version"):
            continue
        if item_identity["source_id"] and record.get("source_id") and item_identity["source_id"] != record.get("source_id"):
            continue
        if item_identity["source_type"] and record.get("source_type") and item_identity["source_type"] != record.get("source_type"):
            continue
        if item_identity["asset_hashes"] != record.get("asset_hashes", {}):
            continue
        result.append(copy.deepcopy(item))
    return result


def unit(item, source_type):
    raw = source_snapshot(item)
    return {
        "source_type": source_type,
        "id": item.get("slide_id") or item.get("id") or item.get("question_id"),
        "sha256": source_hash(item),
        "content": raw,
    }
