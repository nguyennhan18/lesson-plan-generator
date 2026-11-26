"""Build validated Bàn làm việc slides from an approved Dàn ý in a single AI call (#40, #43)."""
import json
from uuid import uuid4

from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.workbench_slides import (
    GeneratedSlideContent,
    GeneratedSlideDeck,
    LAYOUT_NAMES,
    WorkbenchApprovedOutlineItem,
    WorkbenchItemSlidesRequest,
    WorkbenchSlide,
    WorkbenchSlideElement,
    WorkbenchSlidesRequest,
    WorkbenchSlidesResponse,
)

# ADR 0009 & Ticket #40: default 12,000-char prompt budget for a 10-slide outline (~half of legacy 24,600 chars).
DEFAULT_SLIDE_PROMPT_BUDGET = 12_000
PROMPT_SIZE_LOG: list[int] = []

# `points` trong Dàn ý là ý/câu hỏi gợi mở cho giáo viên, không phải nội dung trình chiếu.
# Không có câu này, LLM có xu hướng chép thẳng `points` vào paragraph/items của slide.
SLIDE_CONTENT_ELABORATION_INSTRUCTION = (
    "Mỗi points của Mục chỉ là ý/câu hỏi gợi mở cho giáo viên, không phải nội dung trình chiếu. "
    "Phải diễn giải và triển khai đầy đủ từng points thành nội dung thật (định nghĩa, công thức, lời giải, ví dụ cụ thể...), "
    "không chép lại nguyên văn points vào title/paragraph/items/caption."
)

# ADR 0004: Initial Bố cục mẫu catalog. Every coordinate is a multiple of 20 within 1600 × 900.
LAYOUT_CATALOG: dict[str, dict[str, dict]] = {
    "Mở đầu": {
        "title": {"x": 120, "y": 280, "w": 1360, "h": 220, "hero": True},
        "caption": {"x": 120, "y": 540, "w": 900, "h": 60},
        "paragraph": {"x": 120, "y": 540, "w": 1200, "h": 120},
    },
    "Tình huống": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "paragraph": {"x": 100, "y": 200, "w": 1400, "h": 120},
        "list": {"x": 100, "y": 240, "w": 1300, "h": 520, "default_style": "text"},
        "list_below_paragraph": {"x": 100, "y": 340, "w": 1300, "h": 440, "default_style": "text"},
        "caption": {"x": 100, "y": 780, "w": 1400, "h": 60},
    },
    "Kiến thức trọng tâm": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "paragraph": {"x": 100, "y": 200, "w": 1400, "h": 140},
        "list": {"x": 100, "y": 220, "w": 1400, "h": 400, "default_style": "text"},
        "list_below_paragraph": {"x": 100, "y": 360, "w": 1400, "h": 280, "default_style": "text"},
        "formula": {"x": 100, "y": 660, "w": 1400, "h": 140},
        "caption": {"x": 100, "y": 800, "w": 1400, "h": 60},
    },
    "Ví dụ (đề và lời giải)": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "paragraph": {"x": 100, "y": 200, "w": 1400, "h": 120},
        "list": {"x": 100, "y": 340, "w": 1400, "h": 480, "default_style": "steps"},
        "formula": {"x": 100, "y": 740, "w": 1400, "h": 120},
        "caption": {"x": 100, "y": 820, "w": 1400, "h": 60},
    },
    "Chữ trái, hình phải": {
        "title": {"x": 100, "y": 80, "w": 560, "h": 100},
        "paragraph": {"x": 100, "y": 200, "w": 560, "h": 200},
        "list": {"x": 100, "y": 220, "w": 560, "h": 540, "default_style": "text"},
        "list_below_paragraph": {"x": 100, "y": 420, "w": 560, "h": 340, "default_style": "text"},
        "caption": {"x": 100, "y": 780, "w": 560, "h": 60},
        "visual": {"x": 700, "y": 140, "w": 820, "h": 680},
    },
    "Hình tương tác ở giữa": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "visual": {"x": 200, "y": 200, "w": 1200, "h": 420},
        "paragraph": {"x": 200, "y": 660, "w": 1200, "h": 160},
        "caption": {"x": 200, "y": 820, "w": 1200, "h": 60},
    },
    "Câu hỏi trắc nghiệm": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "quiz": {"x": 100, "y": 200, "w": 1400, "h": 640},
    },
    "Tổng kết": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "list": {"x": 100, "y": 240, "w": 1400, "h": 440, "default_style": "steps"},
        "paragraph": {"x": 100, "y": 240, "w": 1400, "h": 220},
        "caption": {"x": 100, "y": 740, "w": 1400, "h": 60},
    },
    "Nội dung": {
        "title": {"x": 100, "y": 80, "w": 1400, "h": 100},
        "paragraph": {"x": 100, "y": 200, "w": 1400, "h": 140},
        "list": {"x": 100, "y": 240, "w": 1300, "h": 460, "default_style": "text"},
        "list_below_paragraph": {"x": 100, "y": 360, "w": 1300, "h": 340, "default_style": "text"},
        "table": {"x": 100, "y": 240, "w": 1400, "h": 460},
        "formula": {"x": 100, "y": 700, "w": 1400, "h": 120},
        "caption": {"x": 100, "y": 820, "w": 1400, "h": 60},
    },
}


def build_bounded_slide_prompt(
    *,
    title: str,
    sgk: str | None,
    level: str,
    items: list[WorkbenchApprovedOutlineItem],
    budget: int = DEFAULT_SLIDE_PROMPT_BUDGET,
) -> str:
    """Serialize the slide generation prompt within the character budget by trimming excess context first."""
    compact_items = [
        {
            "item_id": item.item_id,
            "activity": item.activity,
            "kind": item.kind,
            "title": item.title,
            "points": list(item.points),
            "slide_count": item.slide_count,
            "visuals": [
                {"visual_id": v.visual_id, "kind": v.kind, "label": v.label}
                for v in item.visuals
            ],
        }
        for item in items
    ]
    payload = {
        "tiêu đề": title,
        "bài SGK": sgk,
        "trình độ lớp": level,
        "bố cục mẫu": list(LAYOUT_NAMES),
        "mục dàn ý": compact_items,
    }
    prompt = json.dumps(payload, ensure_ascii=False)
    if len(prompt) > budget:
        for item in compact_items:
            item["points"] = [pt[:120] for pt in item["points"][:4]]
        prompt = json.dumps(payload, ensure_ascii=False)
    if len(prompt) > budget:
        raise ValueError(f"Prompt dựng Bộ slide ({len(prompt)} ký tự) vượt ngân sách {budget} ký tự.")
    return prompt


def _assemble_slide_elements(
    raw: GeneratedSlideContent,
    visual_lookup: dict[str, tuple[str, str]],
) -> list[WorkbenchSlideElement]:
    spec = LAYOUT_CATALOG[raw.layout]
    elements: list[WorkbenchSlideElement] = []
    step_cursor = 1

    def add_element(el_type: str, box: dict, **extra):
        elements.append(WorkbenchSlideElement(
            element_id=str(uuid4()),
            type=el_type,
            x=box["x"],
            y=box["y"],
            w=box["w"],
            h=box["h"],
            **extra,
        ))

    title_box = spec["title"]
    add_element(
        "title",
        title_box,
        reveal=0,
        parts=1,
        hero=title_box.get("hero"),
        text=raw.title,
    )

    if raw.visual_id is not None:
        if raw.visual_id not in visual_lookup:
            raise ValueError(f"Yêu cầu trực quan «{raw.visual_id}» không tồn tại trong Dàn ý.")
        owner_item_id, v_kind = visual_lookup[raw.visual_id]
        if owner_item_id != raw.item_id:
            raise ValueError(f"Hình «{raw.visual_id}» thuộc Mục «{owner_item_id}», không được đặt ở Mục «{raw.item_id}».")
        v_box = spec.get("visual") or LAYOUT_CATALOG["Chữ trái, hình phải"]["visual"]
        v_parts = 3 if v_kind == "bbt" else 1
        v_reveal = 1 if raw.layout == "Hình tương tác ở giữa" else 0
        add_element(v_kind, v_box, reveal=v_reveal, parts=v_parts, visual_id=raw.visual_id)
        if v_reveal > 0:
            step_cursor = v_reveal + v_parts

    if raw.paragraph and "paragraph" in spec:
        p_reveal = step_cursor if raw.layout == "Hình tương tác ở giữa" and raw.visual_id else (0 if raw.layout == "Ví dụ (đề và lời giải)" else 1)
        add_element("paragraph", spec["paragraph"], reveal=p_reveal, parts=1, text=raw.paragraph.strip())
        if p_reveal >= step_cursor:
            step_cursor = p_reveal + 1

    if raw.items:
        list_box = spec.get("list_below_paragraph") if (raw.paragraph and "list_below_paragraph" in spec) else spec.get("list")
        if list_box is None:
            list_box = LAYOUT_CATALOG["Nội dung"]["list"]
        style = raw.list_style or list_box.get("default_style", "text")
        parts = len(raw.items)
        add_element(style, list_box, reveal=step_cursor, parts=parts, items=list(raw.items))
        step_cursor += parts

    if raw.table and "table" in spec:
        add_element(
            "table",
            spec["table"],
            reveal=step_cursor,
            parts=1,
            headers=list(raw.table.headers),
            rows=[list(row) for row in raw.table.rows],
        )
        step_cursor += 1

    if raw.formula:
        f_box = spec.get("formula") or LAYOUT_CATALOG["Kiến thức trọng tâm"]["formula"]
        add_element("formula", f_box, reveal=step_cursor, parts=1, latex=raw.formula.strip())
        step_cursor += 1

    if raw.quiz:
        q_box = spec.get("quiz") or LAYOUT_CATALOG["Câu hỏi trắc nghiệm"]["quiz"]
        add_element(
            "quiz",
            q_box,
            reveal=0,
            parts=1,
            question=raw.quiz.question,
            options=list(raw.quiz.options),
        )

    if raw.caption and "caption" in spec:
        c_reveal = 0 if raw.layout == "Mở đầu" else step_cursor
        add_element("caption", spec["caption"], reveal=c_reveal, parts=1, text=raw.caption.strip())

    # If a slide has only a title and no body content at all, add its title or caption cleanly;
    # for quiz layout, quiz content is mandatory.
    if raw.layout == "Câu hỏi trắc nghiệm" and not raw.quiz:
        raise ValueError("Slide có Bố cục mẫu «Câu hỏi trắc nghiệm» nhưng thiếu dữ liệu câu hỏi trắc nghiệm.")

    return elements


def _validate_and_assemble_slides(
    generated_slides: list[GeneratedSlideContent],
    expected_items: list[WorkbenchApprovedOutlineItem],
) -> list[WorkbenchSlide]:
    expected_by_id = {item.item_id: item for item in expected_items}
    visual_lookup = {
        v.visual_id: (item.item_id, v.kind)
        for item in expected_items
        for v in item.visuals
    }
    grouped: dict[str, list[GeneratedSlideContent]] = {item.item_id: [] for item in expected_items}
    for raw in generated_slides:
        if raw.item_id not in expected_by_id:
            raise ValueError(f"Slide trỏ tới Mục «{raw.item_id}» không có trong Dàn ý đã duyệt.")
        grouped[raw.item_id].append(raw)

    for item in expected_items:
        actual_count = len(grouped[item.item_id])
        if actual_count != item.slide_count:
            raise ValueError(
                f"Mục «{item.item_id}» yêu cầu {item.slide_count} slide nhưng AI trả về {actual_count} slide."
            )
        placed_visuals = {s.visual_id for s in grouped[item.item_id] if s.visual_id}
        for v in item.visuals:
            if v.visual_id not in placed_visuals:
                raise ValueError(
                    f"Yêu cầu trực quan «{v.visual_id}» của Mục «{item.item_id}» chưa được đặt lên slide nào của Mục."
                )

    assembled: list[WorkbenchSlide] = []
    for item in expected_items:
        for raw in grouped[item.item_id]:
            elements = _assemble_slide_elements(raw, visual_lookup)
            assembled.append(WorkbenchSlide(
                slide_id=str(uuid4()),
                item_id=item.item_id,
                layout=raw.layout,
                notes=raw.notes,
                elements=elements,
            ))
    return assembled


def generate_workbench_slides(
    request: WorkbenchSlidesRequest,
    *,
    budget: int = DEFAULT_SLIDE_PROMPT_BUDGET,
) -> WorkbenchSlidesResponse:
    prompt = build_bounded_slide_prompt(
        title=request.title,
        sgk=request.sgk,
        level=request.level.value,
        items=request.outline.items,
        budget=budget,
    )
    prompt_chars = len(prompt)
    PROMPT_SIZE_LOG.append(prompt_chars)
    generated = GeneratedSlideDeck.model_validate(llm_gateway.generate_structured(
        prompt=prompt,
        system_prompt=(
            "Dựng Bộ slide Toán 12 bằng tiếng Việt từ Dàn ý đã duyệt. "
            "Mỗi slide thuộc đúng một Mục (item_id) và tổng số slide của mỗi Mục phải bằng đúng slide_count của Mục đó. "
            "Chọn Bố cục mẫu (layout) phù hợp với Loại mục trong danh mục được cung cấp, "
            "điền nội dung vào các ô (title, paragraph, items, formula, caption, table, quiz, visual_id), "
            "không tự sinh tọa độ. Mọi Yêu cầu trực quan của Mục phải xuất hiện trên ít nhất một slide của đúng Mục đó. "
            + SLIDE_CONTENT_ELABORATION_INSTRUCTION
        ),
        response_schema=GeneratedSlideDeck,
        task_type="slide",
        model_provider=request.model_provider,
        model_id=request.model_id,
        single_attempt=True,
    ))
    slides = _validate_and_assemble_slides(generated.slides, request.outline.items)
    return WorkbenchSlidesResponse(slides=slides, prompt_chars=prompt_chars)


def regenerate_workbench_item_slides(
    request: WorkbenchItemSlidesRequest,
    *,
    budget: int = DEFAULT_SLIDE_PROMPT_BUDGET,
) -> WorkbenchSlidesResponse:
    target = next((item for item in request.outline.items if item.item_id == request.item_id), None)
    if target is None:
        raise KeyError(f"Không tìm thấy Mục «{request.item_id}» trong Dàn ý.")
    prompt = build_bounded_slide_prompt(
        title=request.title,
        sgk=request.sgk,
        level=request.level.value,
        items=[target],
        budget=budget,
    )
    prompt_chars = len(prompt)
    PROMPT_SIZE_LOG.append(prompt_chars)
    generated = GeneratedSlideDeck.model_validate(llm_gateway.generate_structured(
        prompt=prompt,
        system_prompt=(
            "Sinh lại các slide của đúng Mục dàn ý được yêu cầu. "
            "Chỉ trả về đúng slide_count slide cho item_id này, chọn Bố cục mẫu trong danh mục và điền nội dung, không sinh tọa độ. "
            + SLIDE_CONTENT_ELABORATION_INSTRUCTION
        ),
        response_schema=GeneratedSlideDeck,
        task_type="slide",
        model_provider=request.model_provider,
        model_id=request.model_id,
        single_attempt=True,
    ))
    slides = _validate_and_assemble_slides(generated.slides, [target])
    return WorkbenchSlidesResponse(slides=slides, prompt_chars=prompt_chars)
