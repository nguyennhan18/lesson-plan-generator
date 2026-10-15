from pydantic import model_validator
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
##
class ChartType(str, Enum):
    ARITHMETIC_SEQUENCE = "arithmetic_sequence"   # giữ lại cho dãy số dạng u_n = a + d*n
    FUNCTION_PLOT = "function_plot"                # TỔNG QUÁT — áp dụng mọi hàm số 1 biến
    NONE = "none"

class ChartSpec(BaseModel):
    kind: ChartType = Field(
        default=ChartType.FUNCTION_PLOT,
        description="BẮT BUỘC chọn 'function_plot' nếu nội dung slide có xuất hiện bất kỳ hàm số cụ thể nào (VD: f(x) = 2x, F(x) = x^3). Chỉ chọn 'none' đối với các slide thuần định nghĩa tổng quát."
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
    x_min: float = Field(default= -4.0)
    x_max: float = Field(default=4.0)
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

class ClassProficiency(str, Enum):
    BASIC = "basic"         # Lớp yếu / cơ bản
    STANDARD = "standard"   # Lớp trung bình / chuẩn
    ADVANCED = "advanced"   # Lớp giỏi / nâng cao
class SlideSchema(BaseModel):
    """
    Schema định nghĩa cấu trúc dữ liệu cho một trang Slide trình chiếu.
    Tích hợp đầy đủ các loại Slide: Title, Khởi động, Khái niệm, Bài tập, Tóm tắt.
    """
    slide_index: int = Field(description="STT slide (bắt đầu từ 1)")
    type: SlideType = Field(default=SlideType.CONCEPT_SLIDE, description="Loại slide: TITLE_SLIDE, WARM_UP_SLIDE, CONCEPT_SLIDE, EXERCISE_SLIDE, SUMMARY_SLIDE")
    layout: Optional[SlideLayout] = Field(default=SlideLayout.SINGLE_COLUMN, description="Bố cục giao diện hiển thị slide: TITLE_ONLY, SINGLE_COLUMN, TWO_COLUMN, CONCEPT_HIGHLIGHT, IMAGE_TEXT, QUIZ_OPTION")
    title: str = Field(description="Tiêu đề chính của slide")
    subtitle: Optional[str] = Field(default=None, description="Tiêu đề phụ (nếu có)")
    bullet_points: List[str] = Field(default_factory=list, description="Danh sách các ý văn bản đầu dòng trên slide (công thức toán bọc bằng $...$)")
    main_definition_latex: Optional[str] = Field(default=None, description="Công thức toán trọng tâm dạng LaTeX thuần (không bọc $), VD: '\\int x^2 dx = \\frac{x^3}{3} + C'")
    teacher_note: Optional[str] = Field(default=None, description="Kịch bản lời thoại và hướng dẫn tổ chức giảng dạy dành riêng cho Giáo viên")
    image_prompt: Optional[str] = Field(default=None, description="Mô tả ý tưởng đồ thị / hình vẽ để sinh tự động")
    chart_spec: Optional[ChartSpec] = Field(default=None, description="Cấu hình vẽ đồ thị hàm số tự động")
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
    @model_validator(mode = "after")
    def validate_quiz_options(self) -> "SlideSchema":
        is_quiz = self.layout == SlideLayout.QUIZ_OPTION
        has_options = bool(self.quiz_options)

        # Không phải slide trắc nghiệm và không có phương án -> bỏ qua
        if not is_quiz and not has_options:
            return self

        # Slide QUIZ_OPTION bắt buộc phải có phương án
        if not has_options:
            raise ValueError("Slide QUIZ_OPTION phải có quiz_options")

        # Đúng 1 đáp án đúng
        correct_count = sum(opt.is_correct for opt in self.quiz_options)
        if correct_count != 1:
            raise ValueError(
                f"Cần đúng 1 phương án đúng, hiện có {correct_count}"
            )

        # Mọi phương án sai phải có distractor_rationale
        missing = [
            opt.label
            for opt in self.quiz_options
            if not opt.is_correct
            and not (opt.distractor_rationale and opt.distractor_rationale.strip())
        ]
        if missing:
            raise ValueError(
                f"Phương án sai thiếu distractor_rationale: {', '.join(missing)}"
            )

        return self
class ThemeType(str, Enum):
    MATH_ACADEMIC = "math_academic"
    MATH_INFOGRAPHIC = "math_infographic"
    MATH_ESCAPE_ROOM = "math_escape_room"
    MODERN_BLUE = "modern_blue"

class SlideDeckSchema(BaseModel):
    """
    Schema tổng thể cho cả bộ Slide trình chiếu bài giảng.
    """
    presentation_title: str = Field(description="Tiêu đề bài giảng slide")
    subject: str = Field(description="Tên môn học")
    grade: int = Field(description="Khối lớp")
    theme: Optional[ThemeType] = Field(default=ThemeType.MATH_ACADEMIC, description="Chủ đề màu sắc thiết kế")
    slides: List[SlideSchema] = Field(description="Danh sách các trang slide trong bài giảng")

