"""Create one validated outline from one structured LLM response with Langfuse v5 role tracing."""
import json
from lessonai.services.workbench_visuals import filter_grounded_outline_visuals

from lessonai.llm import tracing
from lessonai.llm.gateway import llm_gateway
from lessonai.prompts.roles import WORKBENCH_OUTLINE_PLANNER_PROMPT
from lessonai.rag.curriculum_registry import CurriculumRegistry
from lessonai.schemas.workbench_outline import (
    LESSON_MINUTES,
    GeneratedOutline,
    WorkbenchOutlineRequest,
    WorkbenchOutlineResponse,
)


def resolve_lesson(request: str, lesson_id: str | None = None) -> tuple[str | None, str | None]:
    registry = CurriculumRegistry.get_instance()
    selected = lesson_id if lesson_id is not None else registry.infer_lesson_id(request)
    entry = registry.get_lesson(selected) if selected else None
    return (selected, entry["title"]) if entry else (None, None)


def identify_lesson(request: str) -> dict:
    lesson_id, _ = resolve_lesson(request)
    return {"lesson_id": lesson_id, "lessons": CurriculumRegistry.get_instance().get_all_lessons()}


def generate_outline(request: WorkbenchOutlineRequest, lesson_id: str | None, title: str | None):
    with tracing.trace_chain(
        "chain.workbench_outline_generation",
        session_id=getattr(request, "session_id", None),
        lesson_id=lesson_id,
        topic=request.request,
        proficiency=request.level.value,
        input_data={
            "request": request.request,
            "lesson_id": lesson_id,
            "sgk": title,
            "level": request.level.value,
        },
    ) as chain_obs:
        prompt = json.dumps({
            "yêu cầu": request.request,
            "bài SGK": title,
            "trình độ lớp": request.level.value,
        }, ensure_ascii=False)

        with tracing.observe_role(
            WORKBENCH_OUTLINE_PLANNER_PROMPT.name,
            prompt_name=WORKBENCH_OUTLINE_PLANNER_PROMPT.name,
            prompt_version=WORKBENCH_OUTLINE_PLANNER_PROMPT.version,
            input_data={"lesson_id": lesson_id},
        ) as role_obs:
            generated = GeneratedOutline.model_validate(llm_gateway.generate_structured(
                prompt=prompt,
                system_prompt=WORKBENCH_OUTLINE_PLANNER_PROMPT.system_prompt,
                response_schema=GeneratedOutline,
                task_type="outline",
                model_provider=request.model_provider,
                model_id=request.model_id,
                single_attempt=True,
                role_name=WORKBENCH_OUTLINE_PLANNER_PROMPT.name,
                prompt_name=WORKBENCH_OUTLINE_PLANNER_PROMPT.name,
                prompt_version=WORKBENCH_OUTLINE_PLANNER_PROMPT.version,
            ))
            role_obs.set_output({
                "title": generated.title,
                "items_count": len(generated.items),
                "used_sources": generated.used_sources,
            })

        with tracing.observe_evaluator(
            "gate.workbench_outline_contract",
            input_data={"items_count": len(generated.items), "used_sources": generated.used_sources},
        ) as gate_obs:
            if generated.used_sources:
                gate_obs.fail("Không chấp nhận trích dẫn nguồn khi RAG tạm ngừng.")
                tracing.record_trace_score("workbench_outline_valid", 0.0)
                raise ValueError("Không chấp nhận trích dẫn nguồn khi RAG tạm ngừng.")
            minutes = sum(item.minutes for item in generated.items)
            warnings = [] if minutes == LESSON_MINUTES else [
                f"Dàn ý dự kiến {minutes} phút, chuẩn một tiết là {LESSON_MINUTES} phút."
            ]
            from uuid import uuid4
            assembled_items = []
            for item in generated.items:
                dumped = item.model_dump()
                kept_visuals, v_warnings = filter_grounded_outline_visuals(dumped)
                warnings.extend(v_warnings)
                assembled_items.append({**dumped, "item_id": str(uuid4()), "visuals": kept_visuals})
            gate_obs.set_output({"minutes": minutes, "warnings": warnings})

        tracing.record_trace_score("workbench_outline_valid", 1.0)
        tracing.record_trace_score("minutes_match_45", 1.0 if minutes == LESSON_MINUTES else 0.0)
        response = WorkbenchOutlineResponse(
            title=generated.title, lesson_id=lesson_id, sgk=title,
            outline={"items": assembled_items},
            source_refs=[],
            warnings=warnings,
        )
        chain_obs.set_output({"title": response.title, "items_count": len(response.outline.items), "minutes": minutes})
        return response
