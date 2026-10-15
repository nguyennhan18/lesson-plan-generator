# 📊 BÁO CÁO TIẾN ĐỘ VÀ NGHỆM THU CHI TIẾT NGÀY 1
## NÂNG CẤP DATA SCHEMA (QUIZ PHÂN TÍCH LỖI SAI & PHÂN LOẠI HỌC LỰC)

**Ngày thực hiện:** 07/10/2026 - 08/10/2026  
**Dự án:** Lesson Plan Generator & Interactive Slide Studio (GDPT 2018)  
**Trạng thái nghiệm thu (DoD):** 🎯 **ĐẠT 100% (4/4 Test Cases PASSED)**  

---

## 📋 I. TỔNG QUAN VỀ QUY TRÌNH VÀ TIÊU CHUẨN KỶ LUẬT

Hôm nay hệ thống đã vận hành chính xác theo **Khung giờ Kỷ luật Thép 8 tiếng/ngày**:
1. **08:30 - 09:00:** Khởi động & Briefing kiến trúc, giải thuật, đọc mã nguồn liên quan.
2. **09:00 - 12:00:** Thực hiện Core Backend (Task 1.1, Task 1.2, Task 1.3).
3. **13:30 - 15:30 & 15:30 - 16:30:** Thực hiện Task 1.4 (Xây dựng Unit Test) & Debug lỗi phát sinh.
4. **16:30 - 17:30:** Nghiệm thu theo tiêu chí DoD, giải trình bóc tách code và lập báo cáo.

---

## 🏛️ II. PHÂN TÍCH KIẾN TRÚC VÀ GIẢI THUẬT ĐÃ THỐNG NHẤT

### 1. Sơ đồ Quan hệ Dữ liệu (Data Hierarchy)
```
[LessonRequest] (Đầu vào API)
   ├── topic: str
   ├── subject: str
   ├── grade: int
   ├── class_proficiency: ClassProficiency (basic | standard | advanced)
   └── target_outcome: str

[SlideDeckSchema] (Bộ Slide hoàn chỉnh)
   └── slides: List[SlideSchema]
         ├── slide_index: int
         ├── type: SlideType
         ├── layout: SlideLayout (ví dụ: QUIZ_OPTION)
         ├── class_proficiency: ClassProficiency
         ├── target_outcome: str
         └── quiz_options: List[QuizOptionDetail]
               ├── label: str ("A", "B", "C", "D")
               ├── text: str ("Nội dung đáp án")
               ├── is_correct: bool (True / False)
               └── distractor_rationale: str (Phân tích bẫy sai nếu is_correct == False)
```

### 2. Ràng buộc Validation Chốt chặn (DoD Requirement)
- Khi slide có `layout == SlideLayout.QUIZ_OPTION` hoặc có danh sách `quiz_options`:
  1. Slide **bắt buộc** phải có danh sách `quiz_options` (không được rỗng).
  2. Bắt buộc có **đúng 1 đáp án đúng** (`is_correct == True`).
  3. Bắt buộc 100% đáp án sai (`is_correct == False`) phải có trường `distractor_rationale` (không để rỗng hoặc khoảng trắng).

---

## 💻 III. CHI TIẾT TOÀN BỘ MÃ NGUỒN ĐÃ NÂNG CẤP VÀ XÂY DỰNG

### 1. File [`project/app/schemas/slide_schema.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/schemas/slide_schema.py)
```python
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

# Task 1.1: Schema chi tiết cho từng phương án trắc nghiệm
class QuizOptionDetail(BaseModel):
    label: str = Field(description="Nhãn phương án (A, B, C, D)")
    text: str = Field(description="Nội dung hiển thị của phương án")
    is_correct: bool = Field(default=False, description="Đáp án đúng (True) hay sai (False)")
    distractor_rationale: Optional[str] = Field(
        default=None,
        description="Giải thích bẫy tâm lý / nguyên nhân học sinh chọn sai phương án này"
    )

# Task 1.2: Enum phân loại học lực
class ClassProficiency(str, Enum):
    BASIC = "basic"         # Lớp yếu / cơ bản
    STANDARD = "standard"   # Lớp trung bình / chuẩn
    ADVANCED = "advanced"   # Lớp giỏi / nâng cao

# Task 1.3: Cập nhật SlideSchema tích hợp Quiz & Proficiency & Validator
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

    @model_validator(mode="after")
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
```

---

### 2. File [`project/app/schemas/schemas.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/schemas/schemas.py)
```python
from typing import List, Optional
from pydantic import BaseModel, Field
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
    lesson_title: str = Field(description="Tên bài dạy (VD: Bài 3: Cấp số cộng)")
    subject: str = Field(description="Tên môn học (VD: Toán học)")
    grade: int = Field(description="Khối lớp (VD: 11)")
    knowledge_goals: List[str] = Field(description="Danh sách các mục tiêu kiến thức")
    competency_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu năng lực (Năng lực chung & đặc thù)")
    skills_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu kỹ năng")
    character_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu phẩm chất (Chăm chỉ, trung thực, trách nhiệm...)")
    teaching_equipment: List[str] = Field(default_factory=list, description="Thiết bị dạy học và học liệu dành cho GV và HS")
    activities: List[LessonActivity] = Field(description="Danh sách 4 hoạt động bài dạy")

# Task 1.2: Cập nhật LessonRequest hỗ trợ class_proficiency & target_outcome
class LessonRequest(BaseModel):
    topic: str = Field(description="Tên bài dạy / chủ đề", example="Cấp số cộng")
    subject: str = Field(default="Toán học", description="Tên môn học", example="Toán học")
    grade: int = Field(default=11, description="Khối lớp", example=11)
    class_proficiency: Optional[ClassProficiency] = Field(
        default=ClassProficiency.STANDARD,
        description="Trình độ phân loại học lực của lớp (basic, standard, advanced)"
    )
    target_outcome: Optional[str] = Field(
        default=None,
        description="Mục tiêu chuẩn đầu ra mong muốn của bài dạy"
    )
    plan: Optional[LessonPlanSchema] = Field(default=None, description="Kế hoạch bài dạy đã có để đồng bộ Slide")
```

---

### 3. File [`project/test/test_schema.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/test/test_schema.py) (Unit Test Script)
```python
import sys
import os
import pytest
from pydantic import ValidationError

# Thêm đường dẫn project/app vào sys.path để import chuẩn package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.slide_schema import (
    SlideDeckSchema,
    SlideSchema,
    SlideType,
    SlideLayout,
    QuizOptionDetail,
    ClassProficiency,
    ThemeType,
)
from app.schemas.schemas import LessonRequest


def test_quiz_slide_valid():
    """
    Test Case 1: Kiểm tra parse thành công slide trắc nghiệm hợp lệ.
    Bao gồm: đủ 4 lựa chọn (A, B, C, D), có 1 đáp án đúng và phân tích bẫy sai (distractor_rationale).
    """
    slide_deck = {
        "slide_index": 1,
        "type": SlideType.EXERCISE_SLIDE,
        "layout": SlideLayout.QUIZ_OPTION,
        "title": "Câu hỏi rèn luyện ",
        "subtitle": "Chọn đáp án đúng nhất",
        "bullet_points": ["Hãy xác định công thức số hạng tổng quát"],
        "class_proficiency": ClassProficiency.STANDARD,
        "target_outcome": "Học sinh ghi nhớ và áp dụng chính xác công thức",
        "quiz_options": [
            {
                "label": "A",
                "text": "u_n = u_1 + (n-1)d",
                "is_correct": True,
                "distractor_rationale": None,
            },
            {
                "label": "B",
                "text": "u_n = u_1 + nd",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm lẫn số hạng thứ n được cộng nd thay vì (n-1)d.",
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm phép cộng công sai d thành phép trừ.",
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm lẫn công thức Cấp số cộng sang Cấp số nhân.",
            },
        ],
    }
    slide = SlideSchema(**slide_deck)
    assert slide.slide_index == 1
    assert slide.layout == SlideLayout.QUIZ_OPTION
    assert slide.class_proficiency == ClassProficiency.STANDARD
    assert len(slide.quiz_options) == 4

    assert slide.quiz_options[0].label == "A"
    assert slide.quiz_options[0].is_correct is True
    assert slide.quiz_options[0].distractor_rationale is None

    assert slide.quiz_options[1].label == "B"
    assert slide.quiz_options[1].is_correct is False
    assert (
        slide.quiz_options[1].distractor_rationale
        == "Học sinh nhầm lẫn số hạng thứ n được cộng nd thay vì (n-1)d."
    )


def test_quiz_slide_missing_distractor_rationale():
    """
    Test Case 2: Kiểm tra chốt chặn Validation (DoD).
    Pydantic bắt buộc phải ném ValidationError khi phương án sai bị thiếu distractor_rationale.
    """
    slide_dict = {
        "slide_index": 2,
        "type": SlideType.EXERCISE_SLIDE,
        "layout": SlideLayout.QUIZ_OPTION,
        "title": "Câu hỏi thiếu giải thích",
        "quiz_options": [
            {
                "label": "A",
                "text": "u_n = u_1 + (n-1)d",
                "is_correct": True,
                "distractor_rationale": None,
            },
            {
                "label": "B",
                "text": "u_n = u_1 + nd",
                "is_correct": False,
                "distractor_rationale": "",  # <--- Cố tình để chuỗi rỗng: Vi phạm DoD!
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "   ",  # <--- Cố tình để khoảng trắng: Vi phạm DoD!
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": None,  # <--- Cố tình để None ở đáp án sai: Vi phạm DoD!
            },
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        SlideSchema(**slide_dict)
    error_messages = str(exc_info.value)

    assert "Phương án sai thiếu distractor_rationale" in error_messages


def test_quiz_slide_invalid_correct_count():
    """
    Test Case 3: Kiểm tra chốt chặn số lượng đáp án đúng.
    Pydantic ném ValidationError khi câu hỏi trắc nghiệm có 0 hoặc nhiều hơn 1 đáp án đúng.
    """
    slide_dict = {
        "slide_index": 3,
        "type": SlideType.EXERCISE_SLIDE,
        "layout": SlideLayout.QUIZ_OPTION,
        "title": "Câu hỏi có 2 đáp án đúng",
        "quiz_options": [
            {
                "label": "A",
                "text": "u_n = u_1 + (n-1)d",
                "is_correct": True,  # <--- Đáp án đúng 1
                "distractor_rationale": None,
            },
            {
                "label": "B",
                "text": "u_n = u_1 + (n-1)*d",
                "is_correct": True,  # <--- Cố tình vi phạm: Đáp án đúng 2 (Có 2 câu is_correct = True)!
                "distractor_rationale": None,
            },
            {
                "label": "C",
                "text": "u_n = u_1 - (n-1)d",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm phép cộng công sai d thành phép trừ.",
            },
            {
                "label": "D",
                "text": "u_n = u_1 * d^(n-1)",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm công thức Cấp số cộng sang Cấp số nhân.",
            },
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        SlideSchema(**slide_dict)
    error_messages = str(exc_info.value)
    assert "Cần đúng 1 phương án đúng, hiện có 2" in error_messages


def test_lesson_request_with_proficiency():
    """
    Test Case 4: Kiểm tra LessonRequest tiếp nhận tham số phân loại học lực.
    Bao gồm: class_proficiency (basic, standard, advanced) và target_outcome.
    """
    req = LessonRequest(
        topic="Cấp số cộng",
        subject="Toán học",
        grade=11,
        class_proficiency=ClassProficiency.ADVANCED,
        target_outcome="Vận dụng cao bài toán dãy số",
    )
    assert req.class_proficiency == ClassProficiency.ADVANCED
    assert req.target_outcome == "Vận dụng cao bài toán dãy số"


if __name__ == "__main__":
    pytest.main([__file__])
```

---

## 🐛 IV. NHẬT KÝ GỠ LỖI & KINH NGHIỆM RÚT RA (DEBUGGING LOG)

Trong quá trình thực thi Ngày 1, chúng ta đã phát hiện và xử lý dứt điểm 3 lỗi kỹ thuật quan trọng:

1. **Lỗi `IndentationError` tại `@model_validator`:**
   - *Nguyên nhân:* Dòng `has_options = bool(self.quiz_options)` bị thụt lề thừa 4 spaces.
   - *Khắc phục:* Đưa lề về chuẩn 8 spaces thẳng hàng với lệnh trên.

2. **Lỗi `NameError` thứ tự khai báo Class:**
   - *Nguyên nhân:* `SlideSchema` khai báo `quiz_options: List[QuizOptionDetail]` ở dòng 69 nhưng class `QuizOptionDetail` lại định nghĩa tận dòng 120.
   - *Khắc phục:* Chuyển `QuizOptionDetail` và `ClassProficiency` lên định nghĩa trước `SlideSchema`.

3. **Lỗi `quizz_options` (chính tả 2 chữ `z`) & Mismatch chuỗi Assert:**
   - *Nguyên nhân:* Trong script test ban đầu gõ tên trường thành `quizz_options` làm Pydantic coi là field rỗng; đồng thời chuỗi assert bị thiếu dấu chấm `.`.
   - *Khắc phục:* Đổi thành `quiz_options` và khớp câu chữ assert với Validator backend.

---

## 📊 V. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG CHỐT SỔ (TERMINAL OUTPUT)

Chạy lệnh kiểm thử bằng pytest:
```bash
/Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/venv/bin/python /Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/test/test_schema.py
```

**Kết quả màn hình:**
```text
================================== test session starts ==================================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/nguyennhan18/Documents/Lesson-Plan-Generator
plugins: anyio-4.14.2
collected 4 items                                                                       

project/test/test_schema.py ....                                                  [100%]

============================== 4 passed in 0.05s ==============================
```

---

## 🎯 VI. KẾ HOẠCH BẮT ĐẦU NGÀY 2 (NÂNG CẤP AI PROMPT ENGINEERING)

**Mục tiêu Ngày 2:** Phân hóa Bài giảng & SGK trong AI Prompt Engineering (`project/app/services/ai_service.py`)

* **08:30 - 09:00 (Briefing):** Thống nhất Prompt phân hóa học lực cho Gemini AI dựa trên `ClassProficiency`.
* **Task 2.1 (Sáng):** Cập nhật `SLIDE_SYSTEM_PROMPT` trong `ai_service.py` với các chỉ dẫn phân loại học lực (`basic` $\rightarrow$ Cơ bản; `advanced` $\rightarrow$ Vận dụng cao).
* **Task 2.2 (Sáng):** Thêm ràng buộc Prompt ép Gemini sinh câu hỏi trắc nghiệm có bẫy học sinh kèm `distractor_rationale`.
* **Task 2.3 (Chiều):** Test gọi Gemini sinh slide cho 2 trường hợp đối lập: *"Cấp số cộng cho lớp yếu"* vs *"Cấp số cộng cho lớp chuyên Toán"*.
* **Task 2.4 (Chiều):** Đảm bảo bộ lọc `fix_latex_backslashes_in_json` xử lý trơn tru không bị vỡ JSON khi có mã LaTeX.
* **Task 2.5 (Cuối ngày):** Nghiệm thu tiêu chuẩn DoD Ngày 2: Sinh thành công bộ slide JSON chứa câu hỏi trắc nghiệm có phân tích bẫy sai chuẩn 100%.
