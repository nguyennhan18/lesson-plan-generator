"""Expert Confirmation (Xác nhận chuyên môn) of one version of a Bộ slide or Kế hoạch bài dạy.

The token signs the version's content fingerprint with the machine key
(lessonai.core.signing). It never expires (ADR 0005): it stops counting once
that content changes or the key that signed it is no longer on this machine.
"""
import hashlib
import time
from lessonai.core import signing
from lessonai.core.hashing import fingerprint

METHOD = "issue_review_v1"
KEY_CHANGED_MESSAGE = ("Xác nhận chuyên môn đã lưu không còn hiệu lực vì được ký bằng khóa không có trên máy này (tệp khóa đã bị "
                       "xóa hoặc thay, hoặc xác nhận được tạo trên máy khác). Cần kiểm tra và lưu xác nhận lại.")


def sign_review(purpose, content, issue_ids, owner):
    """Sign the teacher's review of exactly this content; return the token and its record."""
    record = {"method": METHOD, "hash": fingerprint(content), "issues_hash": fingerprint(issue_ids),
              "reviewer": hashlib.sha256(owner.encode()).hexdigest()[:16], "confirmed_at": int(time.time())}
    return signing.sign(purpose, record), record


def review_state(purpose, token, content):
    """None without a token, else "valid" for exactly this content, "key_changed" or "invalid"."""
    if not token:
        return None
    try:
        record = signing.verify(purpose, token, max_length=4000)
    except signing.KeyChanged:
        return "key_changed"
    except signing.InvalidToken:
        return "invalid"
    return "valid" if record.get("method") == METHOD and record.get("hash") == fingerprint(content) else "invalid"


def apply_review(report, purpose, token, content, review_method):
    """Mark the report ready for a valid confirmation, or tell the teacher a lost key voided it."""
    state = review_state(purpose, token, content)
    if state == "valid" and report["status"] != "blocked":
        report["status"] = "ready"
        report["review_method"] = review_method
    if state == "key_changed":
        # Informational: the teacher re-approves by acknowledging the same warnings as before.
        notice = {"field": "review_token", "severity": "info", "code": signing.KeyChanged.code, "message": KEY_CHANGED_MESSAGE}
        report["issues"].append({**notice, "issue_id": fingerprint({"issue": notice, "position": len(report["issues"])})})
    return report
