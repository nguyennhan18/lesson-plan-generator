"""Trợ giảng AI trong Bàn làm việc: proposes text-only patches for the active slide (#45)."""
import json
from typing import Any
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.workbench_outline import Text
from lessonai.schemas.workbench_slides import GeneratedQuizOption, WorkbenchSlide

FIGURE_TYPES = {"graph", "bbt", "oxyz", "solid"}
EDITABLE_TEXT_TYPES = {"title", "paragraph", "text", "steps", "formula", "caption", "quiz", "table"}


class AssistantElementChange(BaseModel):
    """Proposed change for an existing element on the slide."""
    model_config = ConfigDict(extra="allow")

    element_id: Text
    type: str | None = None
    visual_id: str | None = None
    text: str | None = None
    items: list[str] | None = None
    latex: str | None = None
    headers: list[str] | None = None
    rows: list[list[str]] | None = None
    question: str | None = None
    options: list[GeneratedQuizOption] | None = None


class AssistantLLMOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    ai_response: Text = Field(max_length=16000)
    slide_id: Text
    changes: list[AssistantElementChange] = Field(default_factory=list)


class WorkbenchAssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: Text
    title: Text
    slide: WorkbenchSlide
    user_message: Text = Field(max_length=8000)
    model_provider: str | None = None
    model_id: str | None = None


class WorkbenchElementDiff(BaseModel):
    element_id: str
    type: str
    before: dict[str, Any]
    after: dict[str, Any]


class WorkbenchAssistantResponse(BaseModel):
    ai_response: str
    slide_id: str
    diffs: list[WorkbenchElementDiff]
    patched_slide: WorkbenchSlide


def _extract_content_fields(el_dict: dict[str, Any]) -> dict[str, Any]:
    fields = ("text", "items", "latex", "headers", "rows", "question", "options")
    return {k: el_dict[k] for k in fields if el_dict.get(k) is not None}


def propose_workbench_slide_edit(request: WorkbenchAssistantRequest) -> WorkbenchAssistantResponse:
    slide_dict = request.slide.model_dump(mode="json")
    elements_by_id = {el["element_id"]: el for el in slide_dict["elements"]}

    prompt = json.dumps({
        "bài giảng": request.title,
        "yêu cầu của giáo viên": request.user_message,
        "slide hiện tại": {
            "slide_id": slide_dict["slide_id"],
            "layout": slide_dict["layout"],
            "elements": [
                {
                    "element_id": el["element_id"],
                    "type": el["type"],
                    **_extract_content_fields(el),
                }
                for el in slide_dict["elements"]
                if el["type"] not in FIGURE_TYPES
            ],
        },
    }, ensure_ascii=False)

    raw_output = llm_gateway.generate_structured(
        prompt=prompt,
        system_prompt=(
            "Bạn là Trợ giảng AI trong Bàn làm việc Toán 12. "
            "Chỉ đề xuất sửa nội dung chữ/công thức của các phần tử văn bản có sẵn trên đúng slide đang chọn (giữ nguyên slide_id và element_id). "
            "Tuyệt đối không thêm, xóa hoặc sửa phần tử Hình tương tác (graph, bbt, oxyz, solid) và không gán hay đổi visual_id."
        ),
        response_schema=AssistantLLMOutput,
        task_type="chat",
        model_provider=request.model_provider,
        model_id=request.model_id,
        single_attempt=True,
    )
    output = AssistantLLMOutput.model_validate(raw_output)

    if output.slide_id != slide_dict["slide_id"]:
        raise HTTPException(422, detail={"code": "wrong_target_slide", "message": "Trợ giảng AI trả về sai slide đang chọn."})

    # Inspect raw output for any attempt to add/remove/modify figures or visual_id
    extra = output.model_extra or {}
    if any(k in extra for k in ("visual_id", "visuals", "added_elements", "removed_elements")):
        raise HTTPException(422, detail={
            "code": "visual_patch_forbidden",
            "message": "Trợ giảng AI không được thêm, xóa hoặc sửa phần tử hình hay visual_id.",
        })

    diffs: list[WorkbenchElementDiff] = []
    updated_elements = [dict(el) for el in slide_dict["elements"]]
    updated_by_id = {el["element_id"]: el for el in updated_elements}

    for change in output.changes:
        c_dict = change.model_dump(mode="json", exclude_none=True)
        if change.visual_id is not None or "visual_id" in (change.model_extra or {}) or change.type in FIGURE_TYPES:
            raise HTTPException(422, detail={
                "code": "visual_patch_forbidden",
                "message": "Trợ giảng AI không được thêm, xóa hoặc sửa phần tử hình hay visual_id.",
            })
        target_el = elements_by_id.get(change.element_id)
        if target_el is None:
            raise HTTPException(422, detail={
                "code": "visual_patch_forbidden",
                "message": f"Phần tử «{change.element_id}» không tồn tại trên slide hiện tại.",
            })
        if target_el["type"] in FIGURE_TYPES or target_el.get("visual_id") is not None:
            raise HTTPException(422, detail={
                "code": "visual_patch_forbidden",
                "message": "Trợ giảng AI không được sửa phần tử Hình tương tác trên slide.",
            })
        if change.type is not None and change.type != target_el["type"]:
            raise HTTPException(422, detail={
                "code": "visual_patch_forbidden",
                "message": "Trợ giảng AI không được đổi loại phần tử trên slide.",
            })

        before_fields = _extract_content_fields(target_el)
        mut_el = updated_by_id[change.element_id]
        for field in ("text", "items", "latex", "headers", "rows", "question", "options"):
            if field in c_dict and c_dict[field] is not None:
                mut_el[field] = c_dict[field]
                if field == "items" and isinstance(c_dict[field], list) and len(c_dict[field]) >= 1:
                    mut_el["parts"] = len(c_dict[field])
        after_fields = _extract_content_fields(mut_el)
        if before_fields != after_fields:
            diffs.append(WorkbenchElementDiff(
                element_id=change.element_id,
                type=target_el["type"],
                before=before_fields,
                after=after_fields,
            ))

    patched_slide = WorkbenchSlide.model_validate({
        **slide_dict,
        "edited": True,
        "elements": updated_elements,
    })
    return WorkbenchAssistantResponse(
        ai_response=output.ai_response,
        slide_id=slide_dict["slide_id"],
        diffs=diffs,
        patched_slide=patched_slide,
    )
