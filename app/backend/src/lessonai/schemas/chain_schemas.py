"""Pydantic Schemas trung gian cho kiến trúc Role-Based Prompt Chaining (feature/ban-lam-viec).

Mỗi vai trò (Role) trong chuỗi sinh Giáo án 5512 và Bộ Slide có một schema đầu ra riêng,
tương thích với `to_gemini_response_schema` và các hợp đồng `outline_contract.py` / `content_blocks.py`.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .content_blocks import ContentBlock
from .provenance import GenerationMetadata
from .schemas import LessonActivity
from .slide_schema import (
    ChartSpec,
    QuizOptionDetail,
    SlideLayout,
    SlideSchema,
    SlideType,
    SourceRef,
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
    title: str = Field(default="", description="Tên hoạt động sư phạm tương ứng")
    time_minutes: int = Field(
        default=10,
        description="Thời lượng dự kiến (phút), tổng 4 hoạt động phải đúng 45 phút"
    )
    objective_summary: str = Field(default="", description="Tóm tắt mục tiêu cần đạt của hoạt động này")
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
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

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
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

    activities: List[LessonActivity] = Field(
        description="Danh sách 4 hoạt động bài dạy chi tiết theo khung Blueprint và Dàn ý đã duyệt"
    )


class LessonRepairPayload(BaseModel):
    """
    Đầu ra của Vai trò 3 (`role.lesson_repair_reviewer` - có điều kiện):
    Bản vá cục bộ cho các hoạt động hoặc mục tiêu bị Validator 5512 / `validate_plan_outline` báo lỗi.
    """
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

    patched_activities: List[LessonActivity] = Field(
        default_factory=list,
        description="Danh sách các hoạt động đã được sửa lỗi chuẩn 5512 và khớp Dàn ý đã duyệt"
    )
    knowledge_goals: Optional[List[str]] = Field(default=None)
    competency_goals: Optional[List[str]] = Field(default=None)
    character_goals: Optional[List[str]] = Field(default=None)


# ==============================================================================
# II. SCHEMAS TRUNG GIAN CHO CHUỖI SINH BỘ SLIDE (SLIDE DECK CHAIN)
# ==============================================================================

class SlideNarrativeItem(BaseModel):
    """
    Khung nội dung kịch bản của một trang slide do Vai trò 1 (`role.slide_narrative_designer`) thiết kế.
    Giữ chặt `source_outline_id`, `title`, `activity_type`, `bullet_points` và `source_refs` từ Dàn ý đã duyệt.
    """
    slide_index: int = Field(default=1, ge=1, description="STT slide (bắt đầu từ 1)")
    source_outline_id: Optional[str] = Field(
        default=None,
        description="ID của thẻ dàn ý tương ứng trong `approved_outline` (bắt buộc giữ nguyên)"
    )
    type: SlideType = Field(default=SlideType.CONCEPT_SLIDE)
    layout: SlideLayout = Field(default=SlideLayout.SINGLE_COLUMN)
    title: str = Field(description="Tiêu đề chính của slide (giữ nguyên từ dàn ý đã duyệt nếu có)")
    subtitle: Optional[str] = Field(default=None)
    bullet_points: List[str] = Field(default_factory=list)
    main_definition_latex: Optional[str] = Field(default=None)
    worked_solution_steps: List[str] = Field(default_factory=list)
    teacher_note: Optional[str] = Field(default=None)
    activity_type: Optional[str] = Field(default=None)
    pedagogical_mode: Optional[str] = Field(default=None)
    question: Optional[str] = Field(default=None)
    source_refs: Optional[List[SourceRef]] = Field(default=None)
    needs_chart: bool = Field(default=False)
    needs_3d: bool = Field(default=False)
    needs_quiz: bool = Field(default=False)
    visual_hint: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def sync_flags_with_layout(self) -> "SlideNarrativeItem":
        if self.layout == SlideLayout.QUIZ_OPTION:
            self.needs_quiz = True
        return self


class SlideNarrativeDeckSchema(BaseModel):
    """Đầu ra của Vai trò 1 (`role.slide_narrative_designer`) trong chuỗi sinh Slide."""
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

    presentation_title: str = Field(description="Tiêu đề bài giảng slide")
    subject: str = Field(default="Toán học")
    grade: int = Field(default=12)
    theme: Optional[ThemeType] = Field(default=ThemeType.MATH_ACADEMIC)
    slides: List[SlideNarrativeItem] = Field(description="Danh sách kịch bản các trang slide")


class SlideVisualQuizItem(BaseModel):
    """
    Cấu hình trực quan (Đồ thị SymPy / Mô hình 3D thuộc KINDS / ContentBlocks) và Trắc nghiệm tương tác
    cho một slide cụ thể, do Vai trò 2 (`role.visual_and_quiz_specialist`) thiết kế.
    """
    slide_index: int = Field(description="STT slide cần gắn cấu hình trực quan / trắc nghiệm")
    chart_spec: Optional[ChartSpec] = Field(default=None)
    has_3d: bool = Field(default=False)
    polyhedron_type: Optional[str] = Field(
        default=None,
        description="Chỉ chọn trong {'cube', 'square_pyramid_regular', 'square_pyramid_at_a'} hoặc None"
    )
    scene_spec: Optional[dict] = Field(default=None)
    quiz_options: List[QuizOptionDetail] = Field(default_factory=list)
    math_formulas: List[str] = Field(default_factory=list)
    blocks: List[ContentBlock] = Field(default_factory=list)
    table_data: Optional[dict] = Field(default=None)


class SlideVisualQuizBatchSchema(BaseModel):
    """Đầu ra của Vai trò 2 (`role.visual_and_quiz_specialist`) trong chuỗi sinh Slide."""
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

    items: List[SlideVisualQuizItem] = Field(
        default_factory=list,
        description="Danh sách cấu hình đồ thị, 3D, blocks và câu hỏi trắc nghiệm gắn theo slide_index"
    )


class SlideRepairBatchSchema(BaseModel):
    """
    Đầu ra của Vai trò 3 (`role.slide_repair_reviewer` - có điều kiện):
    Chỉ chứa các trang slide đã được vá lỗi hợp đồng dàn ý / block / 3D / nguồn RAG.
    """
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None

    patched_slides: List[SlideSchema] = Field(
        default_factory=list,
        description="Danh sách các trang slide đã được sửa lỗi theo đúng slide_index"
    )
