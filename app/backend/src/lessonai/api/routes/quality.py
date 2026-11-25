import base64
import hashlib
import hmac
import json
import secrets
import time
from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException
from lessonai.core.ownership import require_owner
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.content_quality import evaluate_deck, content_snapshot
from lessonai.services.visual_requirements import canonical, fingerprint

router = APIRouter(prefix="/api/v1/quality", tags=["Content acceptance"])
_KEY = secrets.token_bytes(32)


def reviewed(deck):
    try:
        token = deck.get("review_token", "")
        if len(token) > 4000:
            return False
        payload, signature = token.split(".")
        if not hmac.compare_digest(signature, hmac.new(_KEY, payload.encode(), hashlib.sha256).hexdigest()):
            return False
        record = json.loads(base64.urlsafe_b64decode(payload))
        return record.get("method") == "issue_review_v1" and record["hash"] == fingerprint(content_snapshot(deck)) and record["expires"] > time.time()
    except (ValueError, KeyError, TypeError):
        return False


def check_deck(deck):
    report = evaluate_deck(deck)
    if report["status"] != "blocked" and reviewed(deck):
        report["status"] = "ready"
        report["review_method"] = "teacher_confirmation_for_this_revision"
    return report


@router.post("/check")
def check(deck: SlideDeckSchema, owner=Depends(require_owner)):
    return check_deck(deck.model_dump(mode="json"))


@router.post("/approve")
def approve(payload: dict, owner=Depends(require_owner)):
    if payload.get("acknowledged") is not True:
        raise HTTPException(422, detail="Cần xác nhận duyệt nội dung")
    try:
        deck = SlideDeckSchema.model_validate(payload["deck"]).model_dump(mode="json")
    except (KeyError, ValidationError) as error:
        raise HTTPException(422, detail="Bộ slide không hợp lệ") from error
    report = evaluate_deck(deck)
    if report["status"] == "blocked":
        raise HTTPException(409, detail={"code": "content_blocked", "message": "Cần sửa lỗi đã xác định trước khi xác nhận", "report": report})
    required = sorted(issue["issue_id"] for issue in report["issues"] if issue["severity"] == "warning")
    supplied = payload.get("reviewed_issue_ids")
    if not isinstance(supplied, list) or any(not isinstance(value, str) for value in supplied) or sorted(supplied) != required or payload.get("content_fingerprint") != report["content_fingerprint"]:
        raise HTTPException(409, detail={"code": "review_incomplete", "message": "Cần đối chiếu từng mục cần duyệt của đúng phiên bản bài", "report": report})
    review = {"method": "issue_review_v1", "reviewed_issue_ids": required,
              "content_fingerprint": report["content_fingerprint"]}
    record = {"method": "issue_review_v1", "issues_hash": fingerprint(required), "hash": fingerprint(content_snapshot(deck)), "expires": int(time.time())+86400, "reviewer": hashlib.sha256(owner.encode()).hexdigest()[:16], "confirmed_at": int(time.time())}
    encoded = base64.urlsafe_b64encode(canonical(record).encode()).decode()
    token = encoded + "." + hmac.new(_KEY, encoded.encode(), hashlib.sha256).hexdigest()
    return {"review_token": token, "report": {**report, "status": "ready", "review_method": "teacher_confirmation_for_this_revision", "review_record": {**review, "reviewer": record["reviewer"], "confirmed_at": record["confirmed_at"]}}}


from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.lesson_review import LessonReviewRequest, LessonQualityReport, LessonReviewResponse
from lessonai.services.lesson_quality import evaluate_plan, check_plan, sign_plan_review


@router.post('/lesson-plan/check', response_model=LessonQualityReport)
def check_lesson_plan(plan: LessonPlanSchema, owner=Depends(require_owner)):
    return check_plan(plan.model_dump(mode='json'))


@router.post('/lesson-plan/approve', response_model=LessonReviewResponse)
def approve_lesson_plan(payload: LessonReviewRequest, owner=Depends(require_owner)):
    if not payload.acknowledged:
        raise HTTPException(422, detail='Cần xác nhận đã đối chiếu giáo án')
    plan = payload.plan.model_dump(mode='json')
    report = evaluate_plan(plan)
    if report['status'] == 'blocked':
        raise HTTPException(409, detail={'code': 'content_blocked', 'message': 'Cần sửa lỗi giáo án trước khi xác nhận', 'report': report})
    required = sorted(i['issue_id'] for i in report['issues'] if i['severity'] == 'warning')
    if payload.content_fingerprint != report['content_fingerprint'] or sorted(payload.reviewed_issue_ids) != required:
        raise HTTPException(409, detail={'code': 'review_incomplete', 'message': 'Cần đối chiếu từng mục của đúng phiên bản giáo án', 'report': report})
    return sign_plan_review(plan, report, owner)
