"""Canonical JSON digest shared by math claims and handoffs (D2, D8); RAG source hashes keep their own version."""
import hashlib
import json

# Bump only when canonical() or the digest changes; every stored claim/handoff hash carries this version.
CANONICAL_HASH_VERSION = 1


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()
