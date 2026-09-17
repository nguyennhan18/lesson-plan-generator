from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
##
class ChartType(str, Enum):
    ARITHMETIC_SEQUENCE = "arithmetic_sequence"   # giữ lại cho dãy số dạng u_n = a + d*n
    FUNCTION_PLOT = "function_plot"                # TỔNG QUÁT — áp dụng mọi hàm số 1 biến
    NONE = "none"

class ChartSpec(BaseModel):
    kind: ChartType = ChartType.NONE
    expression: Optional[str] = Field(
        default=None,
        description=(
            "Biểu thức hàm số theo biến x, cú pháp Python/Sympy chuẩn. "
            "VD: 'x**3 - 3*x', 'sin(x)', 'log(x)', 'sqrt(x)'. "
            "CHỈ dùng x và các hàm toán học cơ bản (sin, cos, tan, log, exp, sqrt, Abs). "
            "KHÔNG chứa code, ký tự đặc biệt hay hướng dẫn khác."
        )
    )
    x_min: float = -4
    x_max: float = 4
    chart_title: Optional[str] = Field(
        default=None,
        description="Tiêu đề hiển thị trên đồ thị (VD: 'Đồ thị hàm số y = sin(x)')"
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

class SlideSchema(BaseModel):
    """
    Schema định nghĩa cấu trúc dữ liệu cho một trang Slide trình chiếu.
    Tích hợp đầy đủ các loại Slide: Title, Khởi động, Khái niệm, Bài tập, Tóm tắt.
    """
    slide_index: int = Field(description="STT slide (bắt đầu từ 1)")
    type: SlideType = Field(default=SlideType.CONCEPT_SLIDE, description="Loại slide: TITLE_SLIDE, WARM_UP_SLIDE, CONCEPT_SLIDE, EXERCISE_SLIDE, SUMMARY_SLIDE")
    title: str = Field(description="Tiêu đề chính của slide")
    subtitle: Optional[str] = Field(default=None, description="Tiêu đề phụ (nếu có)")
    bullet_points: List[str] = Field(description="Danh sách các ý văn bản đầu dòng trên slide (công thức toán bọc bằng $...$)")
    main_definition_latex: Optional[str] = Field(default=None, description="Công thức toán trọng tâm dạng LaTeX thuần (không bọc $), VD: '\\int x^2 dx = \\frac{x^3}{3} + C'")
    teacher_note: Optional[str] = Field(default=None, description="Kịch bản lời thoại và hướng dẫn tổ chức giảng dạy dành riêng cho Giáo viên")
    image_prompt: Optional[str] = Field(default=None, description="Mô tả ý tưởng đồ thị / hình vẽ để sinh tự động")
    chart_spec: Optional[ChartSpec] = Field(default=None, description="Cấu hình vẽ đồ thị hàm số tự động")


class SlideDeckSchema(BaseModel):
    """
    Schema tổng thể cho cả bộ Slide trình chiếu bài giảng.
    """
    presentation_title: str = Field(description="Tiêu đề bài giảng slide")
    subject: str = Field(description="Tên môn học")
    grade: int = Field(description="Khối lớp")
    theme: Optional[str] = Field(default="modern_blue", description="Chủ đề màu sắc thiết kế")
    slides: List[SlideSchema] = Field(description="Danh sách các trang slide trong bài giảng")
