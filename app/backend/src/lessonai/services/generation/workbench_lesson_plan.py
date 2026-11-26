"""Generate a 5512 Kế hoạch bài dạy directly from an approved Bàn làm việc v3 Dàn ý in a single AI call (#50, ADR 0002), with Langfuse v5 role tracing."""
import json
from pydantic import BaseModel

from lessonai.llm import tracing
from lessonai.llm.gateway import llm_gateway
from lessonai.prompts.roles import WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.schemas.workbench_slides import WorkbenchApprovedOutlineItem, WorkbenchSlidesRequest
from lessonai.services.generation.outline_contract import normalize_outline_text
from lessonai.services.quality.validation import validate_5512_lesson_plan

ACTIVITY_NUM_BY_NAME = {
    "Khởi động": 1,
    "Hình thành kiến thức": 2,
    "Luyện tập": 3,
    "Vận dụng": 4,
}


class WorkbenchLessonPlanResponse(BaseModel):
    plan: LessonPlanSchema
    warnings: list[str] = []


def validate_workbench_plan_outline(
    plan: LessonPlanSchema,
    items: list[WorkbenchApprovedOutlineItem],
) -> list[str]:
    """Verify that every Mục dàn ý (its title and points) appears in order in the matching 5512 activity (#50)."""
    activities = plan.model_dump(mode="json").get("activities") or []
    by_number = {act["activity_number"]: act for act in activities if isinstance(act, dict) and "activity_number" in act}
    if [act.get("activity_number") for act in activities] != [1, 2, 3, 4]:
        raise ValueError("Kế hoạch bài dạy phải có đủ 4 hoạt động (1, 2, 3, 4) theo đúng thứ tự Công văn 5512.")

    cursors: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
    norm_cursors: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
    warnings: list[str] = []

    for item in items:
        act_num = ACTIVITY_NUM_BY_NAME.get(item.activity)
        if act_num is None or act_num not in by_number:
            raise ValueError(f"Mục «{item.title}» thuộc Hoạt động «{item.activity}» không khớp hoạt động 5512.")
        act = by_number[act_num]
        exec_steps = act.get("execution") or {}
        combined_text = "\n".join([
            str(act.get("goal") or ""),
            str(exec_steps.get("step_1_assign") or ""),
            str(exec_steps.get("step_2_excute") or ""),
            str(exec_steps.get("step_3_report") or ""),
            str(exec_steps.get("step_4_conclusion") or ""),
            str(act.get("expected_product") or ""),
        ])
        norm_text = normalize_outline_text(combined_text)

        # 1. Check item title in order within the activity
        title_pos = combined_text.find(item.title, cursors[act_num])
        if title_pos >= 0:
            cursors[act_num] = title_pos + len(item.title)
            nt = normalize_outline_text(item.title)
            np = norm_text.find(nt, norm_cursors[act_num]) if nt else -1
            if np >= 0:
                norm_cursors[act_num] = np + len(nt)
        else:
            nt = normalize_outline_text(item.title)
            np = norm_text.find(nt, norm_cursors[act_num]) if nt else -1
            if np < 0:
                raise ValueError(f"Kế hoạch bài dạy bỏ hoặc đổi thứ tự Mục dàn ý «{item.title}» ở Hoạt động {act_num}.")
            norm_cursors[act_num] = np + len(nt)
            warnings.append(f"Hoạt động {act_num}: tiêu đề Mục «{item.title}» khớp sau chuẩn hóa.")

        # 2. Check each point of the item within the activity
        for pt in item.points:
            if not pt or not pt.strip():
                continue
            if pt in combined_text:
                continue
            npt = normalize_outline_text(pt)
            if npt and npt in norm_text:
                warnings.append(f"Hoạt động {act_num}: ý «{pt}» khớp sau chuẩn hóa.")
            else:
                raise ValueError(f"Kế hoạch bài dạy bỏ sót ý «{pt}» của Mục «{item.title}» ở Hoạt động {act_num}.")

    return warnings


def generate_workbench_lesson_plan(request: WorkbenchSlidesRequest) -> WorkbenchLessonPlanResponse:
    """Generate a validated 5512 LessonPlanSchema from the v3 Dàn ý in a single AI call (#50)."""
    with tracing.trace_chain(
        "chain.workbench_lesson_plan_generation",
        lesson_id=request.lesson_id,
        topic=request.title,
        proficiency=request.level.value,
        input_data={"title": request.title, "sgk": request.sgk, "items_count": len(request.outline.items)},
    ) as chain_obs:
        prompt = json.dumps({
            "tiêu đề": request.title,
            "bài SGK": request.sgk,
            "trình độ lớp": request.level.value,
            "mục dàn ý": [
                {
                    "item_id": item.item_id,
                    "activity": item.activity,
                    "kind": item.kind,
                    "title": item.title,
                    "points": list(item.points),
                    "minutes": item.minutes,
                }
                for item in request.outline.items
            ],
        }, ensure_ascii=False)

        with tracing.observe_role(
            WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.name,
            prompt_name=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.name,
            prompt_version=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.version,
            input_data={"items_count": len(request.outline.items)},
        ) as role_obs:
            raw_plan = llm_gateway.generate_structured(
                prompt=prompt,
                system_prompt=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.system_prompt,
                response_schema=LessonPlanSchema,
                task_type="lesson_plan",
                model_provider=request.model_provider,
                model_id=request.model_id,
                single_attempt=True,
                role_name=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.name,
                prompt_name=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.name,
                prompt_version=WORKBENCH_LESSON_PLAN_AUTHOR_PROMPT.version,
            )
            plan = LessonPlanSchema.model_validate(raw_plan)
            role_obs.set_output({"activities_count": len(plan.activities)})

        with tracing.observe_evaluator(
            "gate.workbench_lesson_plan_5512_and_fidelity",
            input_data={"items_count": len(request.outline.items)},
        ) as gate_obs:
            val_5512 = validate_5512_lesson_plan(plan)
            if not val_5512.is_valid:
                gate_obs.fail("; ".join(val_5512.errors))
                raise ValueError("; ".join(val_5512.errors))
            fidelity_warnings = validate_workbench_plan_outline(plan, request.outline.items)
            all_warnings = [*val_5512.warnings, *fidelity_warnings]
            gate_obs.set_output({"warnings_count": len(all_warnings)})

        chain_obs.set_output({"activities_count": len(plan.activities), "warnings_count": len(all_warnings)})
        return WorkbenchLessonPlanResponse(plan=plan, warnings=all_warnings)
