from pydantic import model_validator
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4
from lessonai.schemas.content_blocks import ContentBlock
from lessonai.schemas.provenance import GenerationMetadata
##
class ChartType(str, Enum):
    ARITHMETIC_SEQUENCE = "arithmetic_sequence"   # giữ lại cho dãy số dạng u_n = a + d*n
    FUNCTION_PLOT = "function_plot"                # TỔNG QUÁT — áp dụng mọi hàm số 1 biến
    INEQUALITY_SYSTEM = "inequality_system"        # Hệ bất phương trình bậc nhất 2 ẩn & Miền nghiệm Oxy
    NONE = "none"

class ChartSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    operation: str = "function"
    requirement_token: Optional[str] = None
    deck_id: Optional[str] = None
    slide_id: Optional[str] = None
    kind: ChartType = Field(
        default=ChartType.NONE,
        description=(
            "Chỉ chọn 'function_plot' hoặc 'inequality_system' đối với những slide thực sự cần minh họa trực quan "
            "(thường là 1-2 slide có layout 'IMAGE_TEXT' trong bài). "
            "BẮT BUỘC chọn 'none' đối với các slide Định nghĩa, Công thức (CONCEPT_HIGHLIGHT), "
            "Phương pháp giải & Ví dụ giải mẫu từng bước (TWO_COLUMN, SINGLE_COLUMN)."
        )
    )
    pedagogical_purpose: Optional[str] = Field(
        default=None,
        description="Lý do trực quan hóa. VD: 'Minh họa hình dáng đồ thị hàm số f(x) = 2x để học sinh có góc nhìn hình học'."
    )
    expression: Optional[str] = Field(
        default=None,
        description=(
            "Biểu thức hàm số theo biến x, cú pháp Python/Sympy chuẩn. "
            "VD: 'x**3 - 3*x', 'sin(x)', 'log(x)', 'sqrt(x)'. "
            "CHỈ dùng x và các hàm toán học cơ bản (sin, cos, tan, log, exp, sqrt, Abs). "
            "KHÔNG chứa code, ký tự đặc biệt hay hướng dẫn khác."
        )
    )
    boundary_lines: Optional[list] = Field(
        default=None,
        description="Danh sách đường biên cho hệ bất phương trình. VD: [{'expr': '8 - 2*x', 'label': '2x + y = 8'}]"
    )
    vertices: Optional[list] = Field(
        default=None,
        description="Tọa độ các đỉnh miền nghiệm đa giác trên Oxy. VD: [[0, 0], [4, 0], [2.67, 2.67], [0, 4]]"
    )
    x_min: float = Field(default= -4.0)
    x_max: float = Field(default=4.0)
    y_min: Optional[float] = Field(default=None)
    y_max: Optional[float] = Field(default=None)
    chart_title: Optional[str] = Field(
        default=None,
        description="Tiêu đề hiển thị trên đồ thị. VD: 'Đồ thị hàm số y = 2x'."
    )
class SlideType(str, Enum):
    """Phân loại các trang slide trong bài giảng"""
    TITLE_SLIDE = "TITLE_SLIDE"            # Slide tiêu đề bài học
    WARM_UP_SLIDE = "WARM_UP_SLIDE"        # Slide khởi động / mở đầu
    CONCEPT_SLIDE = "CONCEPT_SLIDE"        # Slide khái niệm / hình thành kiến thức
    EXERCISE_SLIDE = "EXERCISE_SLIDE"      # Slide bài tập / luyện tập
    TEACHER_NOTE_SLIDE = "TEACHER_NOTE_SLIDE" # Slide ghi chú / kịch bản lời thoại dành cho GV
    SUMMARY_SLIDE = "SUMMARY_SLIDE"        # Slide tóm tắt / dặn dò cuối bài

class SlideLayout(str, Enum):
    """Bố cục giao diện hiển thị slide"""
    TITLE_ONLY = "TITLE_ONLY"
    SINGLE_COLUMN = "SINGLE_COLUMN"
    TWO_COLUMN = "TWO_COLUMN"
    CONCEPT_HIGHLIGHT = "CONCEPT_HIGHLIGHT"
    IMAGE_TEXT = "IMAGE_TEXT"
    QUIZ_OPTION = "QUIZ_OPTION"

class QuizOptionDetail(BaseModel):
    label: str = Field(description="Nhãn phương án (A, B, C, D)")
    text: str = Field(description="Nội dung hiển thị của phương án")
    is_correct: bool = Field(default=False, description="Đáp án đúng (True) hay sai (False)")
    distractor_rationale: Optional[str] = Field(
        default=None,
        description="Giải thích vì sao phương án này SAI về mặt Toán học: chỉ ra cụ thể "
        "công thức, bước biến đổi, điều kiện hoặc phép tính bị sai và nêu kết quả/cách làm đúng. "
        "Không suy đoán tâm lý hay thái độ của học sinh."
    )

class SourceRef(BaseModel):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def migrate_source(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            value.setdefault("source_type", value.get("source"))
            value.setdefault("id", value.get("slide_id"))
        return value

    source_type: Optional[str] = Field(default=None, description="Nguồn trích xuất: curriculum, slide_kntt12, question_bank_rag")
    id: Optional[str] = Field(default=None, description="Mã định danh của tài liệu tham chiếu")
    title: Optional[str] = Field(default=None, description="Tiêu đề tài liệu")
    topic: Optional[str] = Field(default=None, description="Chủ đề toán học")
    activity_type: Optional[str] = Field(default=None, description="Hoạt động sư phạm")
    layout_hint: Optional[str] = Field(default=None, description="Gợi ý layout")
    difficulty: Optional[str] = Field(default=None, description="Độ khó câu hỏi")

class ClassProficiency(str, Enum):
    BASIC = "basic"         # Lớp yếu / cơ bản
    STANDARD = "standard"   # Lớp trung bình / chuẩn
    ADVANCED = "advanced"   # Lớp giỏi / nâng cao
class SlideSchema(BaseModel):
    """
    Schema định nghĩa cấu trúc dữ liệu cho một trang Slide trình chiếu.
    Tích hợp đầy đủ các loại Slide: Title, Khởi động, Khái niệm, Bài tập, Tóm tắt.
    """
    model_config = ConfigDict(extra="allow")
    slide_id: str = Field(default_factory=lambda: str(uuid4()))
    revision: int = Field(default=0, ge=0)
    source_outline_id: Optional[str] = None
    scene_spec: Optional[dict] = None
    blocks: List[ContentBlock] = Field(default_factory=list)
    question: Optional[str] = None
    generation_metadata: Optional[GenerationMetadata] = None

    table_data: Optional[dict] = None
    stage: Optional[str] = None
    key_message: Optional[str] = None
    slide_index: int = Field(default=1, ge=1, description="STT slide (bắt đầu từ 1)")

    @model_validator(mode="before")
    @classmethod
    def migrate_index(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            if "slide_number" in value:
                if "slide_index" in value and value["slide_index"] != value["slide_number"]:
                    raise ValueError("slide_number và slide_index không khớp")
                value["slide_index"] = value.pop("slide_number")
            if isinstance(value.get("polyhedron_type"), str):
                value["polyhedron_type"] = value["polyhedron_type"].strip().lower() or None
        return value

    type: SlideType = Field(default=SlideType.CONCEPT_SLIDE, description="Loại slide: TITLE_SLIDE, WARM_UP_SLIDE, CONCEPT_SLIDE, EXERCISE_SLIDE, SUMMARY_SLIDE")
    layout: Optional[SlideLayout] = Field(default=SlideLayout.SINGLE_COLUMN, description="Bố cục giao diện hiển thị slide: TITLE_ONLY, SINGLE_COLUMN, TWO_COLUMN, CONCEPT_HIGHLIGHT, IMAGE_TEXT, QUIZ_OPTION")
    title: str = Field(description="Tiêu đề chính của slide")
    subtitle: Optional[str] = Field(default=None, description="Tiêu đề phụ (nếu có)")
    bullet_points: List[str] = Field(default_factory=list, description="Danh sách các ý văn bản đầu dòng trên slide (công thức toán bọc bằng $...$)")
    main_definition_latex: Optional[str] = Field(default=None, description="Công thức toán trọng tâm dạng LaTeX thuần (không bọc $), VD: '\\int x^2 dx = \\frac{x^3}{3} + C'")
    teacher_note: Optional[str] = Field(default=None, description="Kịch bản lời thoại và hướng dẫn tổ chức giảng dạy dành riêng cho Giáo viên")
    image_prompt: Optional[str] = Field(default=None, description="Mô tả ý tưởng đồ thị / hình vẽ để sinh tự động")
    chart_spec: Optional[ChartSpec] = Field(default=None, description="Cấu hình vẽ đồ thị hàm số tự động")
    has_3d: Optional[bool] = Field(
        default=False,
        description="Bật khung mô hình Hình học không gian 3D tương tác (chỉ đặt True trên slide layout 'IMAGE_TEXT' của chủ đề Hình học không gian)"
    )
    polyhedron_type: Optional[str] = Field(
        default=None,
        description="Loại khối đa diện 3D chuẩn SGK (chỉ chọn khi khớp rõ giả thiết, ngược lại để null): 'cube' (Hình lập phương ABCD.A'B'C'D'), 'square_pyramid_regular' (Hình chóp tứ giác đều S.ABCD), 'square_pyramid_at_a' (Hình chóp tứ giác S.ABCD đáy hình vuông có SA vuông góc với đáy)"
    )
    snapshot_3d_base64: Optional[str] = Field(
        default=None,
        description="Task 14.2: Chuỗi Base64 Data URL (data:image/png;base64,...) chụp lại khung hình 3D WebGL hiện tại từ Frontend để xuất vào Slide PPTX"
    )
    worked_solution_steps: List[str] = Field(
        default_factory=list,
        description="Các bước giải mẫu tự luận chi tiết chuẩn SGK (Đề bài -> Bước 1 -> Bước 2 -> Kết luận) hiển thị ở cột phải của layout TWO_COLUMN"
    )
    quiz_options: List[QuizOptionDetail] = Field(default_factory=list, description="Danh sách các phương án trắc nghiệm")
    math_formulas: List[str] = Field(default=[], description="Danh sách các công thức toán phức tạp (phân số, tích phân). Mỗi công thức là một mã LaTex chuẩn.")
    class_proficiency: Optional[ClassProficiency] = Field(
    default=ClassProficiency.STANDARD,
    description="Trình độ học lực phân hóa của slide (basic, standard, advanced)"
    )
    target_outcome: Optional[str] = Field(
        default=None,
        description="Mục tiêu chuẩn đầu ra kiến thức/kỹ năng của học sinh"
    )
    activity_type: Optional[str] = Field(
        default=None,
        description="Loại hoạt động sư phạm CV 5512: khoi_dong, hinh_thanh_kien_thuc, luyen_tap, van_dung, tong_ket"
    )
    source_refs: Optional[List[SourceRef]] = Field(
        default=None,
        description="Tham chiếu nguồn gốc từ kho slide KNTT 12 hoặc ngân hàng câu hỏi RAG (VD: slide_id, question_id)"
    )
    pedagogical_mode: Optional[str] = Field(
        default=None,
        description="Chế độ sư phạm tổ chức hoạt động (Thảo luận cặp đôi, Thảo luận nhóm 4, Cá nhân suy ngẫm...)"
    )
class ThemeType(str, Enum):
    MATH_ACADEMIC = "math_academic"
    MATH_INFOGRAPHIC = "math_infographic"
    MATH_ESCAPE_ROOM = "math_escape_room"
    MODERN_BLUE = "modern_blue"

class SlideDeckSchema(BaseModel):
    """
    Schema tổng thể cho cả bộ Slide trình chiếu bài giảng.
    """
    model_config = ConfigDict(extra="allow")
    generation_metadata: Optional[GenerationMetadata] = None
    schema_version: int = Field(default=2, ge=1, le=2)
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    deck_id: str = Field(default_factory=lambda: str(uuid4()))
    revision: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_identity(self):
        ids = [s.slide_id for s in self.slides]
        if any(not value for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("ID slide trống hoặc bị trùng")
        for index, slide in enumerate(self.slides, 1):
            slide.slide_index = index
        return self

    presentation_title: str = Field(description="Tiêu đề bài giảng slide")
    subject: str = Field(description="Tên môn học")
    grade: int = Field(description="Khối lớp")
    theme: Optional[ThemeType] = Field(default=ThemeType.MATH_ACADEMIC, description="Chủ đề màu sắc thiết kế")
    slides: List[SlideSchema] = Field(max_length=200, description="Danh sách các trang slide trong bài giảng")
    snapshot_3d_base64: Optional[str] = Field(
        default=None,
        description="Task 14.2: Chuỗi Base64 Data URL dự phòng toàn cục cho cả bộ Slide"
    )
