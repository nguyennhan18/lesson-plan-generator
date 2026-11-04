"""Scoped, expiring proposals built with the response and applied once."""
import copy
import json
import secrets
import threading
import time
from pydantic import BaseModel, Field
from fastapi import HTTPException
from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services.content_quality import evaluate_deck, content_snapshot
from lessonai.services.visual_requirements import fingerprint

_lock = threading.RLock()
_sessions = {}
_proposals = {}
ALLOWED = {"title", "subtitle", "bullet_points", "worked_solution_steps", "main_definition_latex", "math_formulas", "teacher_note", "quiz_options", "layout"}


class CopilotOutput(BaseModel):
    ai_response: str = Field(min_length=1, max_length=16000)
    slide_id: str
    changes: dict | None = None


def new_session(owner, deck):
    with _lock:
        now = time.monotonic()
        for sid in list(_sessions):
            if _sessions[sid]["expires"] <= now:
                del _sessions[sid]
        for pid in list(_proposals):
            if _proposals[pid]["expires"] <= now or _proposals[pid]["session_id"] not in _sessions:
                del _proposals[pid]
        if len(_sessions) >= 64:
            raise HTTPException(503, detail="Đã đạt giới hạn hội thoại")
        sid = secrets.token_urlsafe(24)
        _sessions[sid] = {"owner": owner, "project_id": deck.project_id, "deck_id": deck.deck_id,
                          "history": [], "expires": now + 3600}
        return sid


def session(owner, sid):
    with _lock:
        result = _sessions.get(sid)
        if not result or result["owner"] != owner or result["expires"] <= time.monotonic():
            raise HTTPException(404, detail="Không tìm thấy phiên hội thoại")
        return result


def history(owner, sid):
    with _lock:
        return copy.deepcopy(session(owner, sid)["history"])


def reset(owner, sid):
    with _lock:
        session(owner, sid)
        del _sessions[sid]
        for pid in list(_proposals):
            if _proposals[pid]["session_id"] == sid:
                del _proposals[pid]


def interact(owner, data):
    deck = SlideDeckSchema.model_validate(data["slide_deck"]).model_dump(mode="json")
    if len(json.dumps(deck,ensure_ascii=False).encode())>1024*1024:
        raise HTTPException(413,detail="Bài quá lớn cho hội thoại; cần chia nhỏ dự án")
    sid = data["session_id"]
    current = session(owner, sid)
    if (current["deck_id"], current["project_id"]) != (deck["deck_id"], deck["project_id"]):
        raise HTTPException(404, detail="Sai phạm vi dự án")
    target = next((s for s in deck["slides"] if s["slide_id"] == data.get("slide_id")), None)
    message = str(data.get("user_message") or "").strip()
    if not target or not message or len(message) > 8000:
        raise HTTPException(422, detail="Thiếu slide hoặc yêu cầu hợp lệ")
    output = llm_gateway.generate_structured(
        prompt=json.dumps({"request": message, "deck_title": deck["presentation_title"], "slide": target,
                           "history": history(owner, sid)[-8:]}, ensure_ascii=False),
        system_prompt="Trả lời và đề xuất sửa cùng một slide được cung cấp. Giữ đúng đề/giả thiết. Không đủ dữ kiện thì changes=null và nêu phần thiếu. Chỉ sửa các trường nội dung được yêu cầu; slide_id phải giữ nguyên. Không tự xác nhận đúng toán.",
        response_schema=CopilotOutput, task_type="chat")
    proposal = None
    if output.slide_id != target["slide_id"]:
        raise HTTPException(422, detail="AI trả sai slide đích")
    if output.changes:
        if not set(output.changes) <= ALLOWED or len(json.dumps(output.changes)) > 50000:
            raise HTTPException(422, detail="Đề xuất có trường ngoài phạm vi cho phép")
        candidate = {**target, **output.changes}
        checked = SlideDeckSchema.model_validate({**deck, "slides": [candidate]}).model_dump(mode="json")
        report = evaluate_deck(checked)
        if report["status"] != "blocked":
            pid = secrets.token_urlsafe(24)
            proposal = {"proposal_id": pid, "slide_id": target["slide_id"], "before": {k: target.get(k) for k in output.changes},
                        "changes": output.changes, "status": "needs_review", "report": report}
            with _lock:
                session(owner, sid)  # Reset during the LLM request invalidates this result.
                for expired in list(_proposals):
                    if _proposals[expired]["expires"]<=time.monotonic():del _proposals[expired]
                if len(_proposals) >= 64:
                    raise HTTPException(503, detail="Đã đạt giới hạn đề xuất")
                _proposals[pid] = {**proposal, "owner": owner, "session_id": sid, "base_hash": fingerprint(content_snapshot(deck)),
                                   "base_revision": deck["revision"], "deck_id": deck["deck_id"], "expires": time.monotonic()+900, "applied": None}
    with _lock:
        current = session(owner, sid)
        current["history"] = (current["history"] + [{"role":"user", "text":message}, {"role":"assistant", "text":output.ai_response}])[-40:]
    return {"ai_response": output.ai_response, "suggested_patch": proposal, "session_id": sid}


def apply(owner, data):
    deck = SlideDeckSchema.model_validate(data["slide_deck"]).model_dump(mode="json")
    with _lock:
        proposal = _proposals.get(data.get("proposal_id"))
        if not proposal or proposal["owner"] != owner or proposal["expires"] <= time.monotonic():
            raise HTTPException(404, detail="Đề xuất không tồn tại hoặc đã hết hạn")
        session(owner, proposal["session_id"])
        current_hash = fingerprint(content_snapshot(deck))
        if proposal["applied"] is not None:
            if current_hash not in {proposal["base_hash"], fingerprint(content_snapshot(proposal["applied"]))}:
                raise HTTPException(409, detail="Bài đã thay đổi")
            return copy.deepcopy(proposal["applied"])
        if current_hash != proposal["base_hash"] or deck["revision"] != proposal["base_revision"]:
            raise HTTPException(409, detail="Bài đã thay đổi; cần tạo lại đề xuất")
        if data.get("acknowledged") is not True:
            raise HTTPException(422, detail="Cần duyệt nội dung trước/sau trước khi áp dụng")
        for slide in deck["slides"]:
            if slide["slide_id"] == proposal["slide_id"]:
                slide.update(copy.deepcopy(proposal["changes"]))
                slide["revision"] += 1
                for key in ("chart_image_base64", "formula_image_base64", "snapshot_3d_base64", "snapshot_3d"):
                    slide.pop(key, None)
                for key in ("chart_spec", "scene_spec"):
                    if slide.get(key):
                        slide[key].pop("requirement_token", None)
        deck["revision"] += 1
        deck.pop("review_token", None)
        deck["quality_report"] = evaluate_deck(deck)
        proposal["applied"] = copy.deepcopy(deck)
        return deck
