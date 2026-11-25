"""Pydantic Schemas trung gian cho kiến trúc Role-Based Prompt Chaining.

Mỗi vai trò (Role) trong chuỗi sinh Giáo án 5512 và Bộ Slide có một schema đầu ra riêng,
nhỏ gọn và chặt chẽ để truyền làm đầu vào đã kiểm chứng cho vai trò tiếp theo.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from .schemas import LessonActivity
from .slide_schema import (
    ChartSpec,
    QuizOptionDetail,
    SlideLayout,
    SlideSchema,
    SlideType,
    ThemeType,
)


# ==============================================================================
# I. SCHEMAS TRUNG GIAN CHO CHUỖI SINH GIÁO ÁN 5512 (LESSON PLAN CHAIN)
# ==============================================================================

class ActivityBlueprintItem(BaseModel):
    """Khung kế hoạch cho 1 trong 4 hoạt động sư phạm Công văn 5512."""
    activity_number: int = Field(
        description="STT hoạt động: 1 (Khởi động), 2 (Hình thành kiến thức), 3 (Luyện tập), 4 (Vận dụng)"
    )
    title: str = Field(
        default="",
        description="Tên hoạt động sư phạm tương ứng"
    )
    time_minutes: int = Field(
        default=10,
        description="Thời lượng dự kiến (phút), tổng 4 hoạt động phải đúng 45 phút"
    )
    objective_summary: str = Field(
        default="",
        description="Tóm tắt mục tiêu cần đạt của hoạt động này"
    )
    core_task_outline: str = Field(
        default="",
        description="Định hướng nhiệm vụ học tập / bài toán trọng tâm sẽ giao cho học sinh"
    )
    rag_question_id: Optional[str] = Field(
        default=None,
        description="Mã câu hỏi/ví dụ RAG được chọn cho hoạt động này (nếu có)"
    )


class LessonBlueprintSchema(BaseModel):
    """
    Đầu ra của Vai trò 1 (`role.pedagogical_architect`):
    Xác lập toàn bộ mục tiêu YCCĐ, thiết bị học liệu và khung phân bổ 4 hoạt động 45 phút.
    """
    lesson_title: str = Field(description="Tên bài dạy")
    subject: str = Field(default="Toán học", description="Tên môn học")
    grade: int = Field(default=12, description="Khối lớp")
    knowledge_goals: List[str] = Field(
        default_factory=list,
        description="Danh sách các mục tiêu kiến thức bám sát YCCĐ"
    )
    competency_goals: List[str] = Field(
        default_factory=list,
        description="Danh sách mục tiêu năng lực chung và năng lực toán học"
    )
    skills_goals: List[str] = Field(
        default_factory=list,
        description="Danh sách mục tiêu kỹ năng"
    )
    character_goals: List[str] = Field(
        default_factory=list,
        description="Danh sách mục tiêu phẩm chất chủ yếu"
    )
    teaching_equipment: List[str] = Field(
        default_factory=list,
        description="Thiết bị dạy học và học liệu cho GV và HS"
    )
    activity_blueprints: List[ActivityBlueprintItem] = Field(
        default_factory=list,
        description="Khung thiết kế cho đúng 4 hoạt động (1, 2, 3, 4) với tổng thời gian 45 phút"
    )


class LessonActivitiesPayload(BaseModel):
    """
    Đầu ra của Vai trò 2 (`role.lesson_activity_author`):
    Chi tiết 4 hoạt động bài dạy với đầy đủ 4 bước tổ chức thực hiện Công văn 5512.
    """
    activities: List[LessonActivity] = Field(
        description="Danh sách 4 hoạt động bài dạy chi tiết theo khung Blueprint"
    )


class LessonRepairPayload(BaseModel):
    """
    Đầu ra của Vai trò 3 (`role.lesson_repair_reviewer` - có điều kiện):
    Bản vá cục bộ cho các hoạt động hoặc mục tiêu bị Validator 5512 báo lỗi.
    """
    patched_activities: List[LessonActivity] = Field(
        default_factory=list,
        description="Danh sách các hoạt động đã được sửa lỗi chuẩn 5512"
    )
    knowledge_goals: Optional[List[str]] = Field(
        default=None,
        description="Mục tiêu kiến thức đã bổ sung (nếu trước đó bị thiếu)"
    )
    competency_goals: Optional[List[str]] = Field(
        default=None,
        description="Mục tiêu năng lực đã bổ sung (nếu trước đó bị thiếu)"
    )
    character_goals: Optional[List[str]] = Field(
        default=None,
        description="Mục tiêu phẩm chất đã bổ sung (nếu trước đó bị thiếu)"
    )


# ==============================================================================
# II. SCHEMAS TRUNG GIAN CHO CHUỖI SINH BỘ SLIDE (SLIDE DECK CHAIN)
# ==============================================================================

class SlideNarrativeItem(BaseModel):
    """
    Khung nội dung kịch bản của một trang slide do Vai trò 1 (`role.slide_narrative_designer`) thiết kế.
    Chưa cần điền chi tiết cấu hình kỹ thuật SymPy `chart_spec` hay `quiz_options` đầy đủ.
    """
    slide_index: int = Field(description="STT slide (bắt đầu từ 1)")
    type: SlideType = Field(default=SlideType.CONCEPT_SLIDE)
    layout: SlideLayout = Field(default=SlideLayout.SINGLE_COLUMN)
    title: str = Field(description="Tiêu đề chính của slide")
    subtitle: Optional[str] = Field(default=None)
    bullet_points: List[str] = Field(default_factory=list)
    main_definition_latex: Optional[str] = Field(default=None)
    worked_solution_steps: List[str] = Field(default_factory=list)
    teacher_note: Optional[str] = Field(default=None)
    activity_type: Optional[str] = Field(default=None)
    pedagogical_mode: Optional[str] = Field(default=None)
    needs_chart: bool = Field(
        default=False,
        description="Đặt True nếu slide này cần vẽ đồ thị hàm số 2D (layout IMAGE_TEXT)"
    )
    needs_3d: bool = Field(
        default=False,
        description="Đặt True nếu slide này cần mô hình hình học không gian 3D (chỉ dùng cho chủ đề Hình học không gian)"
    )
    needs_quiz: bool = Field(
        default=False,
        description="Đặt True nếu slide này là câu hỏi trắc nghiệm tương tác (layout QUIZ_OPTION)"
    )
    visual_hint: Optional[str] = Field(
        default=None,
        description="Gợi ý ngắn về hàm số cần vẽ, khối đa diện 3D hoặc nội dung câu hỏi trắc nghiệm cho Vai trò 2"
    )

    @model_validator(mode="after")
    def sync_flags_with_layout(self) -> "SlideNarrativeItem":
        if self.layout == SlideLayout.QUIZ_OPTION or self.type == SlideType.EXERCISE_SLIDE and self.needs_quiz:
            self.needs_quiz = True
        return self


class SlideNarrativeDeckSchema(BaseModel):
    """Đầu ra của Vai trò 1 (`role.slide_narrative_designer`) trong chuỗi sinh Slide."""
    presentation_title: str = Field(description="Tiêu đề bài giảng slide")
    subject: str = Field(default="Toán học")
    grade: int = Field(default=12)
    theme: Optional[ThemeType] = Field(default=ThemeType.MATH_ACADEMIC)
    slides: List[SlideNarrativeItem] = Field(description="Danh sách kịch bản các trang slide")


class SlideVisualQuizItem(BaseModel):
    """
    Cấu hình trực quan (Đồ thị SymPy / Mô hình 3D) và Trắc nghiệm tương tác cho một slide cụ thể,
    do Vai trò 2 (`role.visual_and_quiz_specialist`) thiết kế.
    """
    slide_index: int = Field(description="STT slide cần gắn cấu hình trực quan / trắc nghiệm")
    chart_spec: Optional[ChartSpec] = Field(default=None)
    has_3d: bool = Field(default=False)
    polyhedron_type: Optional[str] = Field(default=None)
    quiz_options: List[QuizOptionDetail] = Field(default_factory=list)
    math_formulas: List[str] = Field(default_factory=list)


class SlideVisualQuizBatchSchema(BaseModel):
    """Đầu ra của Vai trò 2 (`role.visual_and_quiz_specialist`) trong chuỗi sinh Slide."""
    items: List[SlideVisualQuizItem] = Field(
        default_factory=list,
        description="Danh sách cấu hình đồ thị, 3D và câu hỏi trắc nghiệm gắn theo slide_index"
    )


class SlideRepairBatchSchema(BaseModel):
    """
    Đầu ra của Vai trò 3 (`role.slide_repair_reviewer` - có điều kiện):
    Chỉ chứa các trang slide đã được vá lỗi SymPy / Định lý SGK / Chart / Quiz.
    """
    patched_slides: List[SlideSchema] = Field(
        default_factory=list,
        description="Danh sách các trang slide đã được sửa lỗi theo đúng slide_index"
    )
