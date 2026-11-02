from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from .slide_schema import ClassProficiency
# 4 bước dạy học CV 5512
class ExecutionSteps(BaseModel):
    step_1_assign: str = Field(description="Bước 1: Chuyển giao nhiệm vụ (GV giao bài)")
    step_2_excute: str = Field(description="Bước 2: Thực hiện nhiệm vụ (HS Trình bày)")
    step_3_report: str = Field(description="Bước 3: Báo cáo thảo luận (HS Trình bày)")
    step_4_conclusion: str = Field(description="Bước 4: Kết luận nhận đình (GV chốt kiến thức)")
# Định nghĩa hoạt động giảng dạy
class LessonActivity(BaseModel):
    activity_number: int = Field(description="STT hoạt động (1, 2, 3, hoặc 4)")
    time_minutes: int = Field(description="Thời lượng tính bằng phút (VD: 10)")
    goal: str = Field(description="Nội dung câu hỏi / bài tập giao cho HS")
    expected_product: str = Field(description="Đáp án / sản phẩm dự kiến của HS")
    execution: ExecutionSteps = Field(description="Chi tiết 4 bước tổ chức")
# Bản thiết kế giáo án
class LessonPlanSchema(BaseModel):
    lesson_title: str = Field(description="Tên bài dạy (VD: Bài 1: Tính đơn điệu và cực trị của hàm số)")
    subject: str = Field(default="Toán học", description="Tên môn học (Toán học)")
    grade: int = Field(default=12, description="Khối lớp (12)")
    knowledge_goals: List[str] = Field(description="Danh sách các mục tiêu kiến thức")
    competency_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu năng lực (Năng lực chung & đặc thù)")
    skills_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu kỹ năng")
    character_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu phẩm chất (Chăm chỉ, trung thực, trách nhiệm...)")
    teaching_equipment: List[str] = Field(default_factory=list, description="Thiết bị dạy học và học liệu dành cho GV và HS")
    activities: List[LessonActivity] = Field(description="Danh sách 4 hoạt động bài dạy")

class LessonRequest(BaseModel):
    topic: str = Field(
        description="Tên bài dạy / chủ đề",
        json_schema_extra={"example": "Tính đơn điệu và cực trị của hàm số"}
    )
    subject: str = Field(
        default="Toán học",
        description="Tên môn học (Mặc định: Toán học)",
        json_schema_extra={"example": "Toán học"}
    )
    grade: int = Field(
        default=12,
        description="Khối lớp (Mặc định: 12)",
        json_schema_extra={"example": 12}
    )
    lesson_id: Optional[str] = Field(
        default=None,
        description="Mã bài học Toán 12 CT GDPT 2018 (VD: M12-C1-B1). Nếu để trống sẽ tự động suy luận từ topic."
    )
    use_rag: bool = Field(
        default=True,
        description="Kích hoạt Pedagogical RAG truy xuất dữ liệu Toán 12 KNTT"
    )
    class_proficiency: Optional[ClassProficiency] = Field(
        default=ClassProficiency.STANDARD,
        description="Trình độ phân loại học lực của lớp (basic, standard, advanced)"
    )
    target_outcome: Optional[str] = Field(
        default=None,
        description="Mục tiêu chuẩn đầu ra mong muốn của bài dạy"
    )
    plan: Optional[LessonPlanSchema] = Field(default=None, description="Kế hoạch bài dạy đã có để đồng bộ Slide")

    @model_validator(mode="after")
    def validate_and_infer_scope(self) -> "LessonRequest":
        # 1. Scope lock: Chuẩn hóa môn học về Toán học nếu trống hoặc biến thể
        if not self.subject or "toán" not in self.subject.lower():
            self.subject = "Toán học"

        # 2. Scope lock & Tự động suy luận bài học nếu chưa có
        if not self.lesson_id:
            try:
                from lessonai.rag.curriculum_registry import infer_lesson_id
                self.lesson_id = infer_lesson_id(self.topic)
            except Exception:
                self.lesson_id = "M12-C1-B1"

        return self


class RAGPreviewRequest(BaseModel):
    lesson_id: Optional[str] = Field(
        default=None,
        description="Mã bài học Toán 12, VD: M12-C1-B1"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Tên bài dạy hoặc từ khóa cần preview"
    )
    proficiency: Optional[str] = Field(
        default="standard",
        description="Phân hóa học lực: basic, standard, advanced"
    )
    k_slides: int = Field(default=3, ge=1, le=10, description="Số lượng slide mẫu cần xem trước")
    k_questions: int = Field(default=3, ge=1, le=10, description="Số lượng câu hỏi cần xem trước")

    @model_validator(mode="after")
    def validate_lesson_id(self) -> "RAGPreviewRequest":
        if not self.lesson_id:
            try:
                from lessonai.rag.curriculum_registry import infer_lesson_id
                self.lesson_id = infer_lesson_id(self.topic)
            except Exception:
                self.lesson_id = "M12-C1-B1"
        return self


class OutlineSlideItem(BaseModel):
    id: str = Field(default="", description="ID duy nhất của slide trong dàn ý")
    slide_index: int = Field(default=1, description="STT slide")
    slide_number: Optional[int] = Field(default=None, description="Alias cho STT slide")
    title: str = Field(description="Tiêu đề slide")
    activity_type: str = Field(default="Hình thành kiến thức", description="Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng, Tổng kết")
    visual_type: str = Field(default="Concept Highlight", description="3D Geometry, 2D Function Plot, Interactive Quiz, Concept Highlight, Text & Formula")
    bullet_points: List[str] = Field(default_factory=list, description="Các gạch đầu dòng ý chính")
    key_points: Optional[List[str]] = Field(default=None, description="Alias cho bullet_points")
    math_focus: Optional[str] = Field(default=None, description="Công thức hoặc trọng tâm toán học")
    has_3d: bool = Field(default=False)
    polyhedron_type: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def sync_slide_item_aliases(self) -> "OutlineSlideItem":
        if self.slide_number is None:
            self.slide_number = self.slide_index
        elif self.slide_index == 1 and self.slide_number != 1:
            self.slide_index = self.slide_number

        if not self.key_points and self.bullet_points:
            self.key_points = self.bullet_points
        elif not self.bullet_points and self.key_points:
            self.bullet_points = self.key_points
        return self


class OutlineRequest(BaseModel):
    topic: str = Field(description="Tên bài dạy / Đề tài thuyết trình")
    subject: str = Field(default="Toán học")
    grade: int = Field(default=12)
    lesson_id: Optional[str] = Field(default=None)
    num_slides: int = Field(default=8, ge=4, le=16)
    class_proficiency: Optional[str] = Field(default="standard")
    use_rag: bool = Field(default=True)
    model_provider: Optional[str] = Field(default="gemini")
    model_id: Optional[str] = Field(default="gemini-2.5-flash")
    tone: Optional[str] = Field(default="academic")
    language: Optional[str] = Field(default="vi")

    @model_validator(mode="after")
    def validate_and_infer(self) -> "OutlineRequest":
        if not self.subject or "toán" not in self.subject.lower():
            self.subject = "Toán học"
        if not self.lesson_id:
            try:
                from lessonai.rag.curriculum_registry import infer_lesson_id
                self.lesson_id = infer_lesson_id(self.topic)
            except Exception:
                self.lesson_id = "M12-C1-B1"
        return self


class OutlineResponse(BaseModel):
    title: str
    topic: Optional[str] = None
    theme: str = "gallery_monochrome"
    num_slides: int
    subject: str
    grade: int
    class_proficiency: str
    lesson_id: Optional[str] = None
    outline_slides: List[OutlineSlideItem]

    @model_validator(mode="after")
    def sync_topic_and_title(self) -> "OutlineResponse":
        if not self.topic and self.title:
            self.topic = self.title
        elif not self.title and self.topic:
            self.title = self.topic
        return self


