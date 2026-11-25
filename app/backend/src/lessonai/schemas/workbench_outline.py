"""Contracts for creating a Dàn ý in the Bàn làm việc."""
from typing import Annotated, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from lessonai.schemas.slide_schema import ClassProficiency

Activity = Literal["Khởi động", "Hình thành kiến thức", "Luyện tập", "Vận dụng"]
Kind = Literal[
    "Mở đầu", "Tình huống khởi động", "Kiến thức trọng tâm", "Ví dụ",
    "Bài luyện tập", "Câu hỏi trắc nghiệm", "Tổng kết",
]
ACTIVITIES = get_args(Activity)
LESSON_MINUTES = 45
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class WorkbenchRequestText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: Text = Field(max_length=4000)


class WorkbenchOutlineRequest(WorkbenchRequestText):
    lesson_id: str | None = None
    level: ClassProficiency


class WorkbenchLessonOption(BaseModel):
    lesson_id: str
    title: str


class WorkbenchLessonMatch(BaseModel):
    lesson_id: str | None
    lessons: list[WorkbenchLessonOption]


class GeneratedOutlineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity: Activity
    kind: Kind
    title: Text
    points: list[Text]
    slide_count: int = Field(strict=True, ge=1, le=4)
    minutes: int = Field(strict=True, ge=1, le=LESSON_MINUTES)

    @model_validator(mode="after")
    def check_placement(self):
        required = {"Mở đầu": "Khởi động", "Tổng kết": "Vận dụng"}.get(self.kind)
        if required and self.activity != required:
            raise ValueError(f"{self.kind} phải thuộc {required}.")
        return self


class GeneratedOutline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Text
    items: list[GeneratedOutlineItem]
    used_sources: list[Annotated[int, Field(strict=True, ge=1)]]

    @model_validator(mode="after")
    def check_activities(self):
        activities = [item.activity for item in self.items]
        if tuple(dict.fromkeys(activities)) != ACTIVITIES or activities != sorted(activities, key=ACTIVITIES.index):
            raise ValueError("Dàn ý phải có đủ bốn Hoạt động theo đúng thứ tự.")
        return self


class WorkbenchOutlineItem(GeneratedOutlineItem):
    item_id: str


class WorkbenchOutline(BaseModel):
    items: list[WorkbenchOutlineItem]


class WorkbenchSourceRef(BaseModel):
    source_type: str
    id: str
    sha256: str


class WorkbenchOutlineResponse(BaseModel):
    schema_version: Literal[3] = 3
    title: str
    sgk: str | None
    lesson_id: str | None
    outline: WorkbenchOutline
    source_refs: list[WorkbenchSourceRef]
    warnings: list[str]
