"""Create one validated outline from one structured LLM response."""
import json
from uuid import uuid4

from lessonai.llm.gateway import llm_gateway
from lessonai.rag.context_builder import PedagogicalContextBuilder
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
    context, refs = PedagogicalContextBuilder.build_slide_deck_context(
        lesson_id, topic=request.request, proficiency=request.level.value,
    )
    # Source identities come from the reviewed context, never from model-generated strings.
    sources = json.loads(context)["source_units"] if lesson_id else []
    prompt = json.dumps({
        "yêu cầu": request.request,
        "bài SGK": title,
        "trình độ lớp": request.level.value,
        "nguồn đã duyệt": [{"number": number, **unit} for number, unit in enumerate(sources, 1)],
    }, ensure_ascii=False)
    generated = GeneratedOutline.model_validate(llm_gateway.generate_structured(
        prompt=prompt,
        system_prompt=(
            "Soạn Dàn ý Toán 12 bằng tiếng Việt theo Công văn 5512. "
            "Có đủ bốn Hoạt động theo thứ tự: Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng. "
            "Mở đầu thuộc Khởi động, Tổng kết thuộc Vận dụng. Mỗi Mục có 1–4 slide, "
            "và tổng thời lượng dự kiến là 45 phút. Dùng nguồn đã duyệt được cung cấp khi có. "
            "Trong used_sources, ghi các số number của nguồn thực sự dùng, hoặc [] nếu không dùng. "
            "Không đề xuất Yêu cầu trực quan và không suy diễn nguồn."
        ),
        response_schema=GeneratedOutline,
        task_type="outline",
        single_attempt=True,
    ))
    if refs and not generated.used_sources:
        raise ValueError("Dàn ý chưa dùng nguồn đã duyệt được cung cấp.")
    if any(number > len(refs) for number in generated.used_sources):
        raise ValueError("Dàn ý trích dẫn nguồn không có trong ngữ cảnh đã duyệt.")
    minutes = sum(item.minutes for item in generated.items)
    return WorkbenchOutlineResponse(
        title=generated.title, lesson_id=lesson_id, sgk=title,
        outline={"items": [{**item.model_dump(), "item_id": str(uuid4())} for item in generated.items]},
        source_refs=[refs[number - 1] for number in dict.fromkeys(generated.used_sources)],
        warnings=[] if minutes == LESSON_MINUTES else [f"Dàn ý dự kiến {minutes} phút, chuẩn một tiết là {LESSON_MINUTES} phút."],
    )
