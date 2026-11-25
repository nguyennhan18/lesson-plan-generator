"""Contracts and layout catalog for building Bàn làm việc slides from an approved Dàn ý (#40, #43)."""
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from lessonai.schemas.slide_schema import ClassProficiency
from lessonai.schemas.workbench_outline import Activity, Kind, LESSON_MINUTES, Text

LayoutName = Literal[
    "Mở đầu",
    "Tình huống",
    "Kiến thức trọng tâm",
    "Ví dụ (đề và lời giải)",
    "Chữ trái, hình phải",
    "Hình tương tác ở giữa",
    "Câu hỏi trắc nghiệm",
    "Tổng kết",
    "Nội dung",
]
LAYOUT_NAMES = get_args(LayoutName)
VisualKind = Literal["graph", "bbt", "oxyz", "solid"]
ElementType = Literal[
    "title", "paragraph", "text", "steps", "formula", "table", "image", "caption",
    "graph", "bbt", "oxyz", "solid", "quiz",
]


class WorkbenchVisualInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    visual_id: Text
    kind: VisualKind
    origin: Literal["ai", "teacher"] = "ai"
    status: Literal["proposed", "confirmed"] = "proposed"
    data: dict[str, Any] = Field(default_factory=dict)
    requirement_token: str | None = None
    source_fingerprint: str | None = None
    label: str | None = None


class WorkbenchApprovedOutlineItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    item_id: Text
    activity: Activity
    kind: Kind
    title: Text
    points: list[str] = Field(default_factory=list)
    slide_count: int = Field(strict=True, ge=1, le=4)
    minutes: int = Field(strict=True, ge=1, le=LESSON_MINUTES)
    visuals: list[WorkbenchVisualInput] = Field(default_factory=list)
    needs_review: bool = False


class WorkbenchApprovedOutline(BaseModel):
    model_config = ConfigDict(extra="allow")

    items: list[WorkbenchApprovedOutlineItem] = Field(min_length=1)


class WorkbenchSlidesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Text
    sgk: str | None = None
    lesson_id: str | None = None
    level: ClassProficiency = ClassProficiency.STANDARD
    outline: WorkbenchApprovedOutline
    model_provider: str | None = None
    model_id: str | None = None


class WorkbenchItemSlidesRequest(WorkbenchSlidesRequest):
    item_id: Text


class GeneratedQuizOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Literal["A", "B", "C", "D"]
    text: Text
    correct: bool = False
    why: Text


class GeneratedQuizContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: Text
    options: list[GeneratedQuizOption] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def check_options(self):
        if [opt.label for opt in self.options] != ["A", "B", "C", "D"]:
            raise ValueError("Câu hỏi trắc nghiệm phải có đủ 4 phương án A, B, C, D theo thứ tự.")
        if sum(1 for opt in self.options if opt.correct) != 1:
            raise ValueError("Câu hỏi trắc nghiệm phải có đúng một phương án đúng.")
        return self


class GeneratedTableContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headers: list[Text] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)


class GeneratedSlideContent(BaseModel):
    """AI chooses a layout and fills content slots; it never outputs x, y, w, h coordinates (ADR 0004)."""
    model_config = ConfigDict(extra="forbid")

    item_id: Text
    layout: LayoutName
    title: Text
    paragraph: str | None = None
    items: list[Text] = Field(default_factory=list)
    list_style: Literal["text", "steps"] | None = None
    formula: str | None = None
    caption: str | None = None
    table: GeneratedTableContent | None = None
    quiz: GeneratedQuizContent | None = None
    visual_id: str | None = None
    notes: str = ""


class GeneratedSlideDeck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slides: list[GeneratedSlideContent] = Field(min_length=1)


class WorkbenchSlideElement(BaseModel):
    model_config = ConfigDict(extra="allow")

    element_id: str
    type: ElementType
    x: int
    y: int
    w: int
    h: int
    reveal: int = 0
    parts: int = 1
    hero: bool | None = None
    text: str | None = None
    items: list[str] | None = None
    latex: str | None = None
    headers: list[str] | None = None
    rows: list[list[str]] | None = None
    src: str | None = None
    alt: str | None = None
    question: str | None = None
    options: list[GeneratedQuizOption] | None = None
    visual_id: str | None = None


class WorkbenchSlide(BaseModel):
    model_config = ConfigDict(extra="allow")

    slide_id: str
    item_id: str
    layout: LayoutName
    notes: str = ""
    elements: list[WorkbenchSlideElement]


class WorkbenchSlidesResponse(BaseModel):
    slides: list[WorkbenchSlide]
    prompt_chars: int
