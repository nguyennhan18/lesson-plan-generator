"""Kiểm tra bài và Xác nhận chuyên môn for Bàn làm việc v3 (#49, ADR 0005)."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from lessonai.core import signing
from lessonai.core.hashing import fingerprint
from lessonai.schemas.workbench_slides import WorkbenchApprovedOutline, WorkbenchSlide
from lessonai.services.quality.content_quality import _walk, check_formula
from lessonai.services.quality.expert_confirmation import METHOD, apply_review, sign_review
from lessonai.services.quality.visual_requirements import (
    ITEM_SOURCE_FIELDS,
    ConfirmationKeyChanged,
    VisualError,
    checked_requirement,
    visual_source,
)

_PURPOSE = "deck_review"


class WorkbenchDeckPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    revision: int = 0
    review_token: str | None = None
    slides: list[WorkbenchSlide] = Field(default_factory=list)


class WorkbenchQualityCheckRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    project_id: str
    title: str
    outline: WorkbenchApprovedOutline
    deck: WorkbenchDeckPayload


class WorkbenchQualityApproveRequest(WorkbenchQualityCheckRequest):
    acknowledged: bool = False
    content_fingerprint: str
    reviewed_issue_ids: list[str] | None = None


def workbench_deck_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Canonical snapshot of a v3 Bài giảng deck and its outline items for Expert Confirmation signing."""
    items = []
    for item in (payload.get("outline") or {}).get("items") or []:
        items.append({
            "item_id": item.get("item_id"),
            "activity": item.get("activity"),
            "kind": item.get("kind"),
            "title": item.get("title"),
            "points": list(item.get("points") or []),
            "visuals": [
                {
                    "visual_id": v.get("visual_id"),
                    "kind": v.get("kind"),
                    "status": v.get("status"),
                    "data": v.get("data"),
                    "requirement_token": v.get("requirement_token"),
                }
                for v in (item.get("visuals") or [])
            ],
        })
    slides = []
    for slide in (payload.get("deck") or {}).get("slides") or []:
        slides.append({
            "slide_id": slide.get("slide_id"),
            "item_id": slide.get("item_id"),
            "layout": slide.get("layout"),
            "notes": slide.get("notes") or "",
            "edited": bool(slide.get("edited")),
            "elements": slide.get("elements") or [],
        })
    return {
        "project_id": payload.get("project_id"),
        "title": payload.get("title"),
        "items": items,
        "slides": slides,
    }


def evaluate_workbench_deck(payload: dict[str, Any]) -> dict[str, Any]:
    """Inspect a v3 Bài giảng for unconfirmed figures, overflowing elements, manual edits, and formula checks (#49)."""
    issues: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    unconfirmed_visuals: list[dict[str, Any]] = []
    overflow_elements: list[dict[str, Any]] = []
    edited_slides: list[dict[str, Any]] = []

    project_id = str(payload.get("project_id") or "")
    items = (payload.get("outline") or {}).get("items") or []
    slides = (payload.get("deck") or {}).get("slides") or []
    items_by_id = {item["item_id"]: item for item in items if isinstance(item, dict) and item.get("item_id")}

    if not str(payload.get("title") or "").strip():
        issues.append({"field": "title", "severity": "error", "message": "Thiếu tên Bài giảng"})
    if not slides:
        issues.append({"field": "slides", "severity": "error", "message": "Bộ slide rỗng"})

    # 1. Inspect visuals across outline items
    for idx, item in enumerate(items, 1):
        item_id = item.get("item_id")
        expected_fp = fingerprint(visual_source(item, ITEM_SOURCE_FIELDS))
        for visual in item.get("visuals") or []:
            vid = visual.get("visual_id")
            vkind = visual.get("kind")
            vstatus = visual.get("status")
            reason = None
            code = None
            if vstatus != "confirmed" or not visual.get("requirement_token"):
                reason = "Hình chưa được xác nhận dữ kiện"
            else:
                try:
                    spec_check = {
                        **(visual.get("data") or {}),
                        "kind": vkind,
                        "project_id": project_id,
                        "item_id": item_id,
                        "source_fingerprint": expected_fp,
                        "requirement_token": visual.get("requirement_token"),
                    }
                    rec = checked_requirement(spec_check)
                    if rec["spec"].get("source_fingerprint") != expected_fp:
                        reason = "Nội dung Mục dàn ý đã đổi sau khi xác nhận hình"
                except ConfirmationKeyChanged as err:
                    reason = str(err)
                    code = err.code
                except VisualError as err:
                    reason = str(err)
                    code = err.code
            if reason:
                entry = {
                    "visual_id": vid,
                    "kind": vkind,
                    "item_id": item_id,
                    "item_number": idx,
                    "item_title": item.get("title"),
                    "label": visual.get("label"),
                    "reason": reason,
                    **({"code": code} if code else {}),
                }
                unconfirmed_visuals.append(entry)
                issues.append({
                    "field": f"visuals.{vid}",
                    "severity": "warning",
                    "message": f"Mục {idx} ({vkind}): {reason}",
                    **({"code": code} if code else {}),
                })

    # 2. Inspect slides for overflow, manual edits, and math equalities
    for s_idx, slide in enumerate(slides, 1):
        sid = slide.get("slide_id") or str(s_idx)
        if slide.get("edited"):
            edited_slides.append({
                "slide_id": sid,
                "slide_number": s_idx,
                "item_id": slide.get("item_id"),
                "layout": slide.get("layout"),
            })
            issues.append({
                "slide_id": sid,
                "slide_index": s_idx,
                "field": "edited",
                "severity": "warning",
                "message": f"Slide {s_idx} đã được sửa tay trên canvas; cần kiểm tra lại nội dung và bố cục.",
            })
        for el in slide.get("elements") or []:
            eid = el.get("element_id")
            etype = el.get("type")
            if el.get("overflow"):
                overflow_elements.append({
                    "slide_id": sid,
                    "slide_number": s_idx,
                    "element_id": eid,
                    "type": etype,
                    "message": f"Slide {s_idx}: phần tử «{etype}» bị tràn chữ.",
                })
                issues.append({
                    "slide_id": sid,
                    "slide_index": s_idx,
                    "field": f"elements.{eid}.overflow",
                    "severity": "warning",
                    "message": f"Slide {s_idx}: phần tử «{etype}» bị tràn chữ.",
                })
            # Check math formulas inside elements
            for field_name in ("text", "items", "latex", "question"):
                val = el.get(field_name)
                if not val:
                    continue
                for path, formula in _walk(val, f"elements.{eid}.{field_name}", raw=(field_name == "latex")):
                    if len(checks) >= 100:
                        break
                    res = check_formula(formula)
                    checks.append({"slide_id": sid, "field": path, "formula": formula, **res})
                    if res["status"] == "failed":
                        issues.append({
                            "slide_id": sid,
                            "slide_index": s_idx,
                            "field": path,
                            "severity": "error",
                            "message": res["reason"],
                        })

    issues.append({
        "field": "content",
        "severity": "warning",
        "message": "Cần giáo viên đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của phiên bản này.",
    })
    for index, entry in enumerate(issues):
        entry["issue_id"] = fingerprint({"issue": entry, "position": index})

    snapshot = workbench_deck_snapshot(payload)
    status = "blocked" if any(i["severity"] == "error" for i in issues) else "needs_review"
    return {
        "status": status,
        "issues": issues,
        "checks": checks,
        "unconfirmed_visuals": unconfirmed_visuals,
        "overflow_elements": overflow_elements,
        "edited_slides": edited_slides,
        "content_fingerprint": fingerprint(snapshot),
        "scope": "Hình chưa xác nhận dữ kiện, phần tử tràn chữ, slide đã sửa tay và đẳng thức số học.",
    }


def check_workbench_deck(payload: dict[str, Any]) -> dict[str, Any]:
    report = evaluate_workbench_deck(payload)
    token = (payload.get("deck") or {}).get("review_token")
    snapshot = workbench_deck_snapshot(payload)
    return apply_review(report, _PURPOSE, token, snapshot, "teacher_confirmation_for_this_revision")


def approve_workbench_deck(payload: dict[str, Any], owner: str) -> dict[str, Any]:
    from fastapi import HTTPException
    if payload.get("acknowledged") is not True:
        raise HTTPException(422, detail="Cần xác nhận đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của phiên bản này")
    report = evaluate_workbench_deck(payload)
    if report["status"] == "blocked":
        raise HTTPException(409, detail={"code": "content_blocked", "message": "Cần sửa lỗi toán học đã phát hiện trước khi xác nhận chuyên môn", "report": report})
    if payload.get("content_fingerprint") != report["content_fingerprint"]:
        raise HTTPException(409, detail={"code": "review_incomplete", "message": "Nội dung Bộ slide đã thay đổi; hãy kiểm tra lại phiên bản hiện tại trước khi lưu xác nhận", "report": report})
    required = sorted(issue["issue_id"] for issue in report["issues"] if issue["severity"] == "warning")
    supplied = payload.get("reviewed_issue_ids")
    if supplied is not None and sorted(supplied) != required:
        raise HTTPException(409, detail={"code": "review_incomplete", "message": "Cần đối chiếu đầy đủ các mục cảnh báo của phiên bản hiện tại", "report": report})
    snapshot = workbench_deck_snapshot(payload)
    token, record = sign_review(_PURPOSE, snapshot, required, owner)
    return {
        "review_token": token,
        "report": {
            **report,
            "status": "ready",
            "review_method": "teacher_confirmation_for_this_revision",
            "review_record": {
                "method": METHOD,
                "reviewed_issue_ids": required,
                "content_fingerprint": report["content_fingerprint"],
                "reviewer": record["reviewer"],
                "confirmed_at": record["confirmed_at"],
            },
        },
    }
