"""Machine-local signing key for teacher confirmations (ADR 0005).

Figure confirmations and Expert Confirmations are signed with one key kept in
the app's config directory, outside the repository, so a confirmation made
today still verifies after the backend or the machine restarts.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import threading
from pathlib import Path
import lessonai.core.config  # noqa: F401  Loads app/backend/.env before LESSONAI_CONFIG_DIR is read.
from lessonai.core.hashing import canonical

KEY_FILE_NAME = "signing.key"
_KEY_BYTES = 32
_lock = threading.Lock()
_log = logging.getLogger("lessonai.signing")


class SigningKeyUnavailable(RuntimeError):
    """The key file exists but is unusable, or cannot be created. It is never silently replaced."""
    code = "signing_key_unavailable"
    message = ("Không đọc được khóa xác nhận trên máy (tệp khóa bị hỏng hoặc không truy cập được). Hãy khôi phục tệp khóa, "
               "hoặc xóa tệp để tạo khóa mới rồi xác nhận lại; đường dẫn tệp có trong nhật ký backend.")


class InvalidToken(ValueError):
    """The token is malformed, altered, or signed for another purpose."""


class KeyChanged(InvalidToken):
    """The token was signed by a key this machine does not have: its key file was deleted or replaced, or the token came from elsewhere."""
    code = "confirmation_key_changed"


def config_dir():
    """Per-user app config directory; LESSONAI_CONFIG_DIR overrides it."""
    override = os.getenv("LESSONAI_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "win32":
        return Path(os.getenv("APPDATA") or home / "AppData" / "Roaming") / "LessonAI"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LessonAI"
    return Path(os.getenv("XDG_CONFIG_HOME") or home / ".config") / "lessonai"


def key_path():
    return config_dir() / KEY_FILE_NAME


def _read(path):
    with open(path, "rb") as handle:
        return handle.read(_KEY_BYTES + 1)


def _create(path):
    """Write a new owner-only key; return None if another process created one first."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = secrets.token_bytes(_KEY_BYTES)
    staging = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(key)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(staging, path)  # Atomic, and never replaces a key that already exists.
        except FileExistsError:
            return None
    finally:
        staging.unlink(missing_ok=True)
    return key


def signing_key():
    """Read the key file on every use, creating it on the first run."""
    path = key_path()
    with _lock:
        try:
            try:
                key = _read(path)
            except FileNotFoundError:
                key = _create(path) or _read(path)
        except OSError as error:
            _log.error("Không dùng được tệp khóa xác nhận %s: %s", path, error)
            raise SigningKeyUnavailable(SigningKeyUnavailable.message) from error
    if len(key) != _KEY_BYTES:
        _log.error("Tệp khóa xác nhận %s bị hỏng: có %d byte, cần đúng %d", path, len(key), _KEY_BYTES)
        raise SigningKeyUnavailable(SigningKeyUnavailable.message)
    return key


def _key_id(key):
    return hashlib.sha256(b"lessonai-signing-key-id\0" + key).hexdigest()[:16]


def _mac(key, purpose, payload):
    return hmac.new(key, f"{purpose}\n{payload}".encode(), hashlib.sha256).hexdigest()


def sign(purpose, record):
    key = signing_key()
    payload = base64.urlsafe_b64encode(canonical({**record, "kid": _key_id(key)}).encode()).decode()
    return f"{payload}.{_mac(key, purpose, payload)}"


def verify(purpose, token, *, max_length):
    """Return the signed record, or raise KeyChanged or InvalidToken. Nothing expires by time."""
    if not isinstance(token, str) or not token or len(token) > max_length or token.count(".") != 1:
        raise InvalidToken()
    payload, signature = token.split(".")
    key = signing_key()
    if hmac.compare_digest(signature.encode(), _mac(key, purpose, payload).encode()):
        return json.loads(base64.urlsafe_b64decode(payload))
    try:
        claimed = json.loads(base64.urlsafe_b64decode(payload))
    except ValueError:
        raise InvalidToken() from None
    # The unsigned kid only picks the message: tokens from a lost or foreign key, including pre-#37 tokens with no kid, need re-confirmation.
    if isinstance(claimed, dict) and claimed.get("kid") != _key_id(key):
        raise KeyChanged()
    raise InvalidToken()
