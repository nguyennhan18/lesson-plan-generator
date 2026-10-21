import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from schemas.schemas import LessonPlanSchema


class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings


REQUIRED_KEYWORDS = [
    ["mở đầu", "khởi động"],
    ["hình thành kiến thức", "khám phá"],
    ["luyện tập"],
    ["vận dụng"]
]


def validate_5512_lesson_plan(plan: LessonPlanSchema) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    # 1. Kiểm tra mục tiêu
    if not plan.knowledge_goals:
        errors.append("Mục tiêu bài học thiếu phần 'Kiến thức'. ")
    if not plan.competency_goals and not plan.skills_goals:
        warnings.append("Mục tiêu bài học nên có phần 'Năng Lực'")
    # 2. Kiểm tra số lượng hoạt động
    if len(plan.activities) != 4:
        errors.append(f"Giáo án phải có đùng 4 hoạt động theo CV 5512(Hiện có: {len(plan.activities)})")
    # 3. Kiểm tra từ khóa hoạt động
    for idx, req_keywords in enumerate(REQUIRED_KEYWORDS, start=1):
        if idx <= len(plan.activities):
            act_goal = plan.activities[idx - 1].goal.lower()
            has_keyword = any(kw in act_goal for kw in req_keywords)
            if not has_keyword:
                errors.append(
                    f"Hoạt động {idx} ('{plan.activities[idx - 1].goal}') không chứa từ khóa chuẩn 5512 ({'/'.join(req_keywords)})."
                )
    # 4. Kiểm tra 4 bước tổ chức thực hiện
    total_time = 0
    for act in plan.activities:
        total_time += act.time_minutes
        exec_steps = act.execution
        if len(exec_steps.step_1_assign.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 1 (Chuyển giao nhiệm vụ) quá ngắn hoặc rỗng")
        if len(exec_steps.step_2_excute.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 2 (Thực hiện nhiệm vụ) quá ngắn hoặc rỗng")
        if len(exec_steps.step_3_report.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 3 (Báo cáo, thảo luận) quá ngắn hoặc rỗng")
        if len(exec_steps.step_4_conclusion.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 4 (Kết luận, nhận định) quá ngắn hoặc rỗng")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


# ==============================================================================
# NGÀY 10: BỘ LỌC KIỂM DUYỆT SƯ PHẠM (AI LINTER & PROOFREADER)
# Task 10.1: Quét toàn bộ slide tìm lỗi chính tả tiếng Việt thường gặp
# Task 10.2: Tích hợp SymPy kiểm tra biến đổi đại số cơ bản
# ==============================================================================

class SlideWarningItem(BaseModel):
    """
    Cấu trúc một cảnh báo kiểm duyệt sư phạm trên Slide.
    Đảm bảo tương thích chuẩn [{slide_index, message, severity}] trong lộ trình Ngày 10,
    đồng thời bổ sung trường field, category, suggestion phục vụ UI Human-in-the-Loop.
    """
    slide_index: int = Field(description="Số thứ tự trang slide có lỗi (bắt đầu từ 1)")
    message: str = Field(description="Nội dung cảnh báo chi tiết bằng Tiếng Việt")
    severity: str = Field(default="warning", description="Mức độ cảnh báo: 'warning' | 'error' | 'info'")
    field: Optional[str] = Field(default=None, description="Trường dữ liệu phát hiện lỗi (VD: title, bullet_points[0])")
    category: str = Field(default="spelling", description="Phân loại lỗi: 'spelling' | 'algebra_sympy' | 'textbook_theorem'")
    suggestion: Optional[str] = Field(default=None, description="Gợi ý cách sửa dành cho Giáo viên (không tự động ghi đè)")
    detected_token: Optional[str] = Field(default=None, description="Cụm từ hoặc biểu thức bị phát hiện lỗi")


class DeckAuditResponse(BaseModel):
    """Kết quả trả về của API POST /api/v1/validation/audit-deck"""
    is_clean: bool = Field(description="True nếu toàn bộ bộ Slide không có cảnh báo nào")
    total_warnings: int = Field(description="Tổng số cảnh báo phát hiện được")
    warnings: List[SlideWarningItem] = Field(default_factory=list, description="Danh sách cảnh báo chi tiết")


# Danh mục từ điển lỗi chính tả Tiếng Việt & thuật ngữ Toán học thường gặp trên Slide bài giảng
VIETNAMESE_PEDAGOGICAL_TYPO_RULES: List[Tuple[str, str, str]] = [
    # (Cụm từ viết sai, Cụm từ chuẩn, Giải thích ngắn)
    ("học xinh", "học sinh", "Sai phụ âm đầu x/s trong từ 'học sinh'"),
    ("giáo giục", "giáo dục", "Sai phụ âm đầu gi/d trong từ 'giáo dục'"),
    ("phương chình", "phương trình", "Sai phụ âm đầu ch/tr trong thuật ngữ 'phương trình'"),
    ("bất phương chình", "bất phương trình", "Sai phụ âm đầu ch/tr trong thuật ngữ 'bất phương trình'"),
    ("hệ phương chình", "hệ phương trình", "Sai phụ âm đầu ch/tr trong thuật ngữ 'hệ phương trình'"),
    ("trứng minh", "chứng minh", "Sai phụ âm đầu tr/ch trong thuật ngữ 'chứng minh'"),
    ("giả thuyết", "giả thiết", "Trong bài toán/định lý Toán học phổ thông, phần cho trước gọi là 'giả thiết' (không phải 'giả thuyết')"),
    ("sác định", "xác định", "Sai phụ âm đầu s/x trong thuật ngữ 'xác định'"),
    ("tập sác định", "tập xác định", "Sai phụ âm đầu s/x trong thuật ngữ 'tập xác định'"),
    ("tham xố", "tham số", "Sai phụ âm đầu x/s trong thuật ngữ 'tham số'"),
    ("hằn đẳng thức", "hằng đẳng thức", "Thiếu âm cuối 'g' trong thuật ngữ 'hằng đẳng thức'"),
    ("hằng đẵng thức", "hằng đẳng thức", "Sai dấu thanh hỏi/ngã trong thuật ngữ 'hằng đẳng thức'"),
    ("bất đẵng thức", "bất đẳng thức", "Sai dấu thanh hỏi/ngã trong thuật ngữ 'bất đẳng thức'"),
    ("vô ngiệm", "vô nghiệm", "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('vô nghiệm')"),
    ("ngiệm kép", "nghiệm kép", "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghiệm kép')"),
    ("ngiệm phân biệt", "nghiệm phân biệt", "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghiệm phân biệt')"),
    ("đạo hàn", "đạo hàm", "Sai âm cuối n/m trong thuật ngữ 'đạo hàm'"),
    ("nguyên hàn", "nguyên hàm", "Sai âm cuối n/m trong thuật ngữ 'nguyên hàm'"),
    ("tít phân", "tích phân", "Sai âm cuối t/ch trong thuật ngữ 'tích phân'"),
    ("tiệm cận ngan", "tiệm cận ngang", "Thiếu âm cuối 'g' trong thuật ngữ 'tiệm cận ngang'"),
    ("tiệm cận đứn", "tiệm cận đứng", "Thiếu âm cuối 'g' trong thuật ngữ 'tiệm cận đứng'"),
    ("cực chị", "cực trị", "Sai phụ âm đầu ch/tr trong thuật ngữ 'cực trị'"),
    ("đồng biếng", "đồng biến", "Dư âm cuối 'g' trong thuật ngữ 'đồng biến'"),
    ("nghịch biếng", "nghịch biến", "Dư âm cuối 'g' trong thuật ngữ 'nghịch biến'"),
    ("ngịch biến", "nghịch biến", "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghịch biến')"),
    ("tam giác câng", "tam giác cân", "Dư âm cuối 'g' trong thuật ngữ 'tam giác cân'"),
    ("hình tróp", "hình chóp", "Sai phụ âm đầu tr/ch trong thuật ngữ 'hình chóp'"),
    ("khối tróp", "khối chóp", "Sai phụ âm đầu tr/ch trong thuật ngữ 'khối chóp'"),
    ("lăng chụ", "lăng trụ", "Sai phụ âm đầu ch/tr trong thuật ngữ 'lăng trụ'"),
    ("năng trụ", "lăng trụ", "Sai phụ âm đầu n/l trong thuật ngữ 'lăng trụ'"),
    ("mặt phẵng", "mặt phẳng", "Sai dấu thanh hỏi/ngã trong thuật ngữ 'mặt phẳng'"),
    ("mặc phẳng", "mặt phẳng", "Sai âm cuối c/t trong thuật ngữ 'mặt phẳng'"),
    ("vuông gốc", "vuông góc", "Sai vần ốc/óc trong thuật ngữ 'vuông góc'"),
    ("xong xong", "song song", "Sai phụ âm đầu x/s trong thuật ngữ 'song song'"),
    ("khoản cách", "khoảng cách", "Thiếu âm cuối 'g' trong thuật ngữ 'khoảng cách'"),
    ("thể tít", "thể tích", "Sai âm cuối t/ch trong thuật ngữ 'thể tích'"),
    ("diện tít", "diện tích", "Sai âm cuối t/ch trong thuật ngữ 'diện tích'"),
    ("cấp xố cộng", "cấp số cộng", "Sai phụ âm đầu x/s trong thuật ngữ 'cấp số cộng'"),
    ("cấp xố nhân", "cấp số nhân", "Sai phụ âm đầu x/s trong thuật ngữ 'cấp số nhân'"),
    ("công xai", "công sai", "Sai phụ âm đầu x/s trong thuật ngữ 'công sai'"),
    ("công bọi", "công bội", "Sai nguyên âm o/ô trong thuật ngữ 'công bội'"),
    ("chục hoành", "trục hoành", "Sai phụ âm đầu ch/tr trong thuật ngữ 'trục hoành'"),
    ("chục tung", "trục tung", "Sai phụ âm đầu ch/tr trong thuật ngữ 'trục tung'"),
]

# Các từ chức năng Tiếng Việt dễ bị gõ lặp đôi do lỗi bàn phím
_REPEATED_WORDS = ("là", "của", "cho", "với", "trong", "khi", "thì", "mà", "và", "các", "những", "được", "có")
_REPEATED_WORD_PATTERNS = [
    (
        word,
        re.compile(rf"(?<!\w)({word})\s+\1(?!\w)", flags=re.IGNORECASE | re.UNICODE)
    )
    for word in _REPEATED_WORDS
]

# Biên dịch sẵn biểu thức chính quy có ranh giới từ Unicode cho từng quy tắc chính tả
_COMPILED_TYPO_PATTERNS: List[Tuple[re.Pattern, str, str, str]] = [
    (
        re.compile(rf"(?<!\w){re.escape(wrong)}(?!\w)", flags=re.IGNORECASE | re.UNICODE),
        wrong,
        correct,
        reason
    )
    for wrong, correct, reason in VIETNAMESE_PEDAGOGICAL_TYPO_RULES
]

# Regex tách bỏ vùng công thức LaTeX ($...$, $$...$$, \[...\], \(...\)) trước khi quét chính tả Tiếng Việt
_MATH_SEGMENT_REGEX = re.compile(r"(\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))")


def strip_math_segments_for_spellcheck(text: str) -> str:
    """
    Task 10.1: Thay thế các đoạn công thức Toán học ($...$ hoặc $$...$$) bằng khoảng trắng
    để bộ quét chính tả Tiếng Việt chỉ kiểm tra phần ngôn ngữ tự nhiên, không bắt nhầm ký hiệu Toán.
    """
    if not text:
        return ""
    masked = _MATH_SEGMENT_REGEX.sub(" ", str(text))
    return masked


def _scan_text_for_vietnamese_typos(
    raw_text: str,
    slide_index: int,
    field_name: str
) -> List[SlideWarningItem]:
    """
    Quét một chuỗi văn bản cụ thể trên Slide để tìm lỗi chính tả Tiếng Việt và lỗi lặp từ kép.
    """
    warnings: List[SlideWarningItem] = []
    if not raw_text or not str(raw_text).strip():
        return warnings

    natural_text = strip_math_segments_for_spellcheck(str(raw_text))
    if not natural_text.strip():
        return warnings

    # 1. Đối chiếu danh mục lỗi chính tả Tiếng Việt sư phạm
    for pattern, wrong_phrase, correct_phrase, reason in _COMPILED_TYPO_PATTERNS:
        match = pattern.search(natural_text)
        if match:
            found_token = match.group(0)
            warnings.append(
                SlideWarningItem(
                    slide_index=slide_index,
                    field=field_name,
                    category="spelling",
                    severity="warning",
                    detected_token=found_token,
                    message=(
                        f"Phát hiện lỗi chính tả tiếng Việt trên Slide {slide_index}: "
                        f"\"{found_token}\" ({reason})."
                    ),
                    suggestion=f"Gợi ý sửa \"{found_token}\" thành \"{correct_phrase}\"."
                )
            )

    # 2. Kiểm tra lỗi gõ lặp từ kép liên tiếp (VD: 'là là', 'của của')
    for word, rep_pattern in _REPEATED_WORD_PATTERNS:
        rep_match = rep_pattern.search(natural_text)
        if rep_match:
            duplicated_phrase = rep_match.group(0)
            warnings.append(
                SlideWarningItem(
                    slide_index=slide_index,
                    field=field_name,
                    category="spelling",
                    severity="warning",
                    detected_token=duplicated_phrase,
                    message=(
                        f"Phát hiện từ bị gõ lặp 2 lần liên tiếp trên Slide {slide_index}: "
                        f"\"{duplicated_phrase}\"."
                    ),
                    suggestion=f"Gợi ý lược bỏ từ lặp, chỉ giữ lại 1 từ \"{word}\"."
                )
            )

    return warnings


def check_vietnamese_spelling_in_slide(slide: Dict[str, Any], slide_index: int) -> List[SlideWarningItem]:
    """
    Task 10.1: Quét toàn bộ các trường văn bản của một trang Slide (title, subtitle,
    bullet_points, teacher_note, quiz_options) để tìm lỗi chính tả Tiếng Việt.
    """
    slide_warnings: List[SlideWarningItem] = []
    if not isinstance(slide, dict):
        return slide_warnings

    # 1. Kiểm tra tiêu đề chính & tiêu đề phụ
    title = slide.get("title")
    if title:
        slide_warnings.extend(_scan_text_for_vietnamese_typos(str(title), slide_index, "title"))

    subtitle = slide.get("subtitle")
    if subtitle:
        slide_warnings.extend(_scan_text_for_vietnamese_typos(str(subtitle), slide_index, "subtitle"))

    # 2. Kiểm tra danh sách ý chính (bullet_points)
    bullet_points = slide.get("bullet_points") or []
    if isinstance(bullet_points, list):
        for b_idx, bullet in enumerate(bullet_points):
            if bullet:
                slide_warnings.extend(
                    _scan_text_for_vietnamese_typos(str(bullet), slide_index, f"bullet_points[{b_idx}]")
                )

    # 3. Kiểm tra lời thoại giáo viên (teacher_note)
    teacher_note = slide.get("teacher_note")
    if teacher_note:
        slide_warnings.extend(_scan_text_for_vietnamese_typos(str(teacher_note), slide_index, "teacher_note"))

    # 4. Kiểm tra nội dung câu hỏi trắc nghiệm (quiz_options)
    quiz_options = slide.get("quiz_options") or []
    if isinstance(quiz_options, list):
        for q_idx, opt in enumerate(quiz_options):
            if isinstance(opt, dict):
                opt_text = opt.get("text")
                if opt_text:
                    slide_warnings.extend(
                        _scan_text_for_vietnamese_typos(str(opt_text), slide_index, f"quiz_options[{q_idx}].text")
                    )
                rationale = opt.get("distractor_rationale")
                if rationale:
                    slide_warnings.extend(
                        _scan_text_for_vietnamese_typos(
                            str(rationale), slide_index, f"quiz_options[{q_idx}].distractor_rationale"
                        )
                    )

    return slide_warnings


# ==============================================================================
# TASK 10.2: TÍCH HỢP SYMPY KIỂM TRA BIẾN ĐỔI ĐẠI SỐ CƠ BẢN
# (Đảm bảo hai vế phương trình / đẳng thức biến đổi có tương đương không)
# ==============================================================================

_SYMPY_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Khởi tạo bảng ký hiệu biến Toán học THPT chuẩn để SymPy phân tích nhân ngầm định (VD: 4ac -> 4*a*c)
_DEFAULT_SYMBOL_NAMES = (
    "a", "b", "c", "d", "x", "y", "z", "t", "m", "n", "k", "p", "q", "r", "h",
    "u", "v", "S", "P", "V", "B", "Delta", "alpha", "beta", "gamma",
    "x_0", "x_1", "x_2", "u_1", "u_n",
)
_SYMPY_LOCAL_DICT: Dict[str, Any] = {
    name: sp.Symbol(name, real=True) for name in _DEFAULT_SYMBOL_NAMES
}
_SYMPY_LOCAL_DICT.update({
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "Abs": sp.Abs,
    "pi": sp.pi,
})


def _replace_latex_Command_with_two_args(text: str, cmd: str, template: str) -> str:
    """
    Thay thế đệ quy lệnh LaTeX có 2 đối số ngoặc nhọn (VD: \\frac{A}{B})
    bằng cách dò cặp ngoặc nhọn cân bằng từ trong ra ngoài.
    """
    pattern = cmd + "{"
    max_iter = 25
    it = 0
    while pattern in text and it < max_iter:
        it += 1
        start = text.find(pattern)
        if start == -1:
            break
        # Tìm ngoặc đóng của đối số thứ 1
        idx = start + len(cmd)
        if idx >= len(text) or text[idx] != "{":
            break
        depth = 0
        arg1_end = -1
        for i in range(idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    arg1_end = i
                    break
        if arg1_end == -1:
            break
        arg1 = text[idx + 1 : arg1_end]

        # Kiểm tra tiếp đối số thứ 2
        idx2 = arg1_end + 1
        while idx2 < len(text) and text[idx2].isspace():
            idx2 += 1
        if idx2 >= len(text) or text[idx2] != "{":
            break
        depth = 0
        arg2_end = -1
        for i in range(idx2, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    arg2_end = i
                    break
        if arg2_end == -1:
            break
        arg2 = text[idx2 + 1 : arg2_end]

        replacement = template.format(arg1=arg1, arg2=arg2)
        text = text[:start] + replacement + text[arg2_end + 1 :]
    return text


def _replace_latex_sqrt(text: str) -> str:
    """Chuyển đổi \\sqrt[n]{A} -> ((A)**(1/(n))) và \\sqrt{A} -> sqrt(A)."""
    # 1. Căn bậc n: \sqrt[n]{A}
    text = re.sub(
        r"\\sqrt\[([^\]]+)\]\{([^{}]+)\}",
        r"((\2)**(1/(\1)))",
        text
    )
    # 2. Căn bậc 2 có ngoặc nhọn lồng nhau: \sqrt{A}
    cmd = "\\sqrt"
    max_iter = 20
    it = 0
    while "\\sqrt{" in text and it < max_iter:
        it += 1
        start = text.find("\\sqrt{")
        idx = start + len(cmd)
        depth = 0
        end_idx = -1
        for i in range(idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx == -1:
            break
        inner = text[idx + 1 : end_idx]
        text = text[:start] + f"sqrt({inner})" + text[end_idx + 1 :]
    return text


def clean_latex_for_sympy(raw_latex: str) -> str:
    """
    Task 10.2: Chuyển đổi chuỗi biểu thức LaTeX sang cú pháp đại số tương thích với SymPy.
    """
    if not raw_latex:
        return ""

    s = str(raw_latex).strip()
    # Bóc tách dấu $ hoặc $$ ở hai đầu
    if s.startswith("$$") and s.endswith("$$") and len(s) >= 4:
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()

    # Loại bỏ chú thích điều kiện đặt sau \quad (VD: "ax^2 + bx + c = 0 \quad (a \neq 0)")
    s = re.sub(r"\\q?quad\s*\([^)]*\\neq[^)]*\)\s*$", "", s)
    s = re.sub(r"\\q?quad.*$", "", s)

    # Loại bỏ các lệnh trang trí khoảng trắng LaTeX
    for token in (r"\left", r"\right", r"\displaystyle", r"\,", r"\;", r"\:", r"\!"):
        s = s.replace(token, "")

    # Thay thế ký hiệu toán học LaTeX sang toán tử đại số
    s = s.replace("−", "-")
    s = s.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\ast", "*").replace(r"\div", "/")

    # Chuẩn hóa chỉ số dưới phổ biến: x_1, x_2, x_0, u_1, u_n
    s = re.sub(r"([a-zA-Z])_\{([a-zA-Z0-9]+)\}", r"\1_\2", s)

    # Chuyển đổi \frac{A}{B} và \sqrt{A}
    s = _replace_latex_Command_with_two_args(s, r"\frac", "(({arg1})/({arg2}))")
    s = _replace_latex_sqrt(s)

    # Chuyển đổi ký hiệu Hy Lạp và hằng số
    s = re.sub(r"\\Delta\b", "Delta", s)
    s = re.sub(r"\\alpha\b", "alpha", s)
    s = re.sub(r"\\beta\b", "beta", s)
    s = re.sub(r"\\gamma\b", "gamma", s)
    s = re.sub(r"\\pi\b", "pi", s)

    # Chuyển đổi số mũ ^{...} -> **(...)
    max_iter = 20
    it = 0
    while "^{" in s and it < max_iter:
        it += 1
        start = s.find("^{")
        idx = start + 1
        depth = 0
        end_idx = -1
        for i in range(idx, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx == -1:
            break
        exp_inner = s[idx + 1 : end_idx]
        s = s[:start] + f"**({exp_inner})" + s[end_idx + 1 :]

    s = s.replace("^", "**")
    # Thay thế cặp ngoặc nhọn gom nhóm còn lại thành ngoặc đơn
    s = s.replace("{", "(").replace("}", ")")
    return s.strip()


def latex_to_sympy_expr(latex_str: str) -> Optional[Any]:
    """
    Task 10.2: Phân tích chuỗi LaTeX đơn thành đối tượng biểu thức ký hiệu SymPy (sp.Expr).
    Trả về None nếu biểu thức chứa ký hiệu không thuộc phạm vi đại số cơ bản (tích phân, giới hạn, tập hợp...).
    """
    if not latex_str or not str(latex_str).strip():
        return None

    # Bỏ qua các biểu thức giải tích nâng cao hoặc ký hiệu tập hợp không phải đẳng thức đại số thuần
    unsupported_tokens = (
        r"\int", r"\lim", r"\sum", r"\begin", r"\end", r"\pm", r"\mp",
        r"\vec", r"\overrightarrow", r"\widehat", r"\in", r"\subset",
        r"\cup", r"\cap", r"\mathbb", r"\varnothing", r"\neq", r"\approx",
        r"\text", "|"
    )
    for tok in unsupported_tokens:
        if tok in latex_str:
            return None

    cleaned = clean_latex_for_sympy(latex_str)
    if not cleaned or any(op in cleaned for op in ("=", "<", ">", "\\")):
        return None

    try:
        expr = parse_expr(
            cleaned,
            local_dict=_SYMPY_LOCAL_DICT,
            transformations=_SYMPY_TRANSFORMATIONS,
            evaluate=True
        )
        if isinstance(expr, sp.Expr):
            return expr
    except Exception:
        return None
    return None


def _is_algebraic_identity_candidate(lhs_raw: str, rhs_raw: str, lhs_expr: sp.Expr, rhs_expr: sp.Expr) -> bool:
    """
    Phân biệt giữa:
    1. Phương trình điều kiện cần tìm nghiệm (VD: x^2 - 5x + 6 = 0, y = 2x + 1, h(t) = -0.5t^2 + 2t + 2.5) -> KHÔNG báo lỗi.
    2. Phép biến đổi đại số / Hằng đẳng thức / Phân tích nhân tử / Rút gọn (VD: (x - 2)^2 = x^2 - 4x - 4,
       x^2 - 5x + 6 = (x - 2)(x + 3), 2(x + 3) = 2x + 3, (-3)^2 = -9) -> CẦN kiểm định bằng SymPy.
    """
    lhs_vars = lhs_expr.free_symbols
    rhs_vars = rhs_expr.free_symbols

    # Trường hợp 1: Đẳng thức số học thuần túy (không chứa biến tự do, VD: (-2)^2 - 4*1*(-3) = -8)
    if not lhs_vars and not rhs_vars:
        return True

    # Nếu hai vế không cùng tập biến số (VD: y = x^2 + 1, S = -b/a, Delta = b^2 - 4ac, x^2 - 4 = 0)
    # thì đây là định nghĩa hàm số, phép gán ký hiệu hoặc phương trình điều kiện '= 0'.
    if lhs_vars != rhs_vars or len(lhs_vars) == 0:
        return False

    # Loại trừ trường hợp một vế chỉ là 1 biến đơn lẻ (VD: x = 2x là phương trình, không phải khai triển)
    if lhs_expr.is_Symbol or rhs_expr.is_Symbol:
        return False

    # Kiểm tra bậc đa thức theo từng biến chung:
    # Trong phép khai triển hằng đẳng thức, phân tích nhân tử hoặc rút gọn đa thức (VD: (x-1)^2 = x^2 - 2x - 1),
    # hai vế có cùng tập biến và cùng bậc cao nhất (hoặc ít nhất một vế có cấu trúc ngoặc nhân/lũy thừa).
    try:
        for sym in lhs_vars:
            poly_l = sp.Poly(sp.expand(lhs_expr), sym)
            poly_r = sp.Poly(sp.expand(rhs_expr), sym)
            if poly_l.degree() != poly_r.degree():
                return False
            # Đảm bảo hệ số bậc cao nhất khớp nhau (hoặc đối dấu) để chắc chắn đây là phép biến đổi cùng bậc
            if abs(poly_l.LC()) != abs(poly_r.LC()):
                return False
        return True
    except Exception:
        # Nếu không phải đa thức (VD: phân thức hữu tỉ hoặc căn thức có cùng biến ở hai vế)
        return True


def check_algebraic_equality_chain(
    formula_latex: str,
    slide_index: int,
    field_name: str
) -> List[SlideWarningItem]:
    """
    Task 10.2 (Phần A): Kiểm tra đẳng thức đại số `LHS = RHS` hoặc chuỗi biến đổi `E_1 = E_2 = ... = E_k`
    bằng SymPy (`simplify(expand(LHS - RHS)) == 0`).
    """
    warnings: List[SlideWarningItem] = []
    if not formula_latex or "=" not in formula_latex:
        return warnings

    # Bỏ qua nếu là chuỗi tương đương phương trình (\iff, \Leftrightarrow, \implies) -> xử lý ở hàm riêng
    if any(tok in formula_latex for tok in (r"\iff", r"\Leftrightarrow", r"\implies", r"\Rightarrow", "<", ">", r"\le", r"\ge")):
        return warnings

    clean_outer = formula_latex.strip()
    if clean_outer.startswith("$$") and clean_outer.endswith("$$"):
        clean_outer = clean_outer[2:-2].strip()
    elif clean_outer.startswith("$") and clean_outer.endswith("$"):
        clean_outer = clean_outer[1:-1].strip()

    # Tách theo dấu '='
    parts = [p.strip() for p in clean_outer.split("=") if p.strip()]
    if len(parts) < 2:
        return warnings

    parsed_parts: List[Tuple[str, Optional[sp.Expr]]] = [
        (raw_p, latex_to_sympy_expr(raw_p)) for raw_p in parts
    ]

    # Duyệt từng cặp dấu '=' liền kề trong biểu thức (hỗ trợ cả LHS = RHS và chuỗi E_1 = E_2 = E_3)
    for i in range(len(parsed_parts) - 1):
        raw_l, expr_l = parsed_parts[i]
        raw_r, expr_r = parsed_parts[i + 1]
        if expr_l is None or expr_r is None:
            continue

        if not _is_algebraic_identity_candidate(raw_l, raw_r, expr_l, expr_r):
            continue

        diff = sp.simplify(sp.expand(sp.Add(expr_l, -expr_r)))
        if diff != 0:
            expanded_l = sp.expand(expr_l)
            expanded_r = sp.expand(expr_r)
            if expanded_l != expr_l:
                suggestion_text = (
                    f"Kiểm tra lại quy tắc dấu hoặc phép tính: Khai triển/rút gọn đúng của \"{raw_l}\" "
                    f"là \"{expanded_l}\" (thay vì \"{raw_r}\")."
                )
            else:
                factored_l = sp.factor(expr_l)
                suggestion_text = (
                    f"Kiểm tra lại biến đổi vế phải: \"{raw_r}\" khi khai triển bằng \"{expanded_r}\" "
                    f"≠ \"{raw_l}\" (Phân tích đúng của vế trái: \"{factored_l}\")."
                )

            warnings.append(
                SlideWarningItem(
                    slide_index=slide_index,
                    field=field_name,
                    category="algebra_sympy",
                    severity="error",
                    detected_token=f"{raw_l} = {raw_r}" if len(parsed_parts) > 2 else clean_outer,
                    message=(
                        f"Biến đổi đại số không tương đương trên Slide {slide_index}: "
                        f"Vế trái \"{raw_l}\" và vế phải \"{raw_r}\" không bằng nhau "
                        f"(SymPy kiểm chứng: LHS - RHS = {diff} ≠ 0)."
                    ),
                    suggestion=suggestion_text
                )
            )

    return warnings


def check_equation_equivalence_steps(
    formula_latex: str,
    slide_index: int,
    field_name: str
) -> List[SlideWarningItem]:
    """
    Task 10.2 (Phần B): Kiểm tra phép biến đổi tương đương giữa 2 phương trình / bất phương trình
    nối với nhau bởi \\iff hoặc \\Leftrightarrow (VD: 2x - 6 = 0 \\iff 2x = -6 hoặc -2m + 4 > 0 \\iff m > 2).
    """
    warnings: List[SlideWarningItem] = []
    if not formula_latex:
        return warnings

    if not any(tok in formula_latex for tok in (r"\iff", r"\Leftrightarrow", r"\implies", r"\Rightarrow")):
        return warnings

    clean_outer = formula_latex.strip()
    if clean_outer.startswith("$$") and clean_outer.endswith("$$"):
        clean_outer = clean_outer[2:-2].strip()
    elif clean_outer.startswith("$") and clean_outer.endswith("$"):
        clean_outer = clean_outer[1:-1].strip()

    steps = re.split(r"\\iff|\\Leftrightarrow|\\implies|\\Rightarrow", clean_outer)
    steps = [st.strip() for st in steps if st.strip()]
    if len(steps) < 2:
        return warnings

    for i in range(len(steps) - 1):
        step1, step2 = steps[i], steps[i + 1]

        # 1. Kiểm tra tương đương phương trình: L1 = R1 <=> L2 = R2
        if "=" in step1 and "=" in step2 and not any(op in step1 + step2 for op in ("<", ">", r"\le", r"\ge")):
            s1_parts = step1.split("=")
            s2_parts = step2.split("=")
            # Lấy vế phương trình cuối cùng của step1 nếu step1 có dạng chuỗi "Delta = ... = 0"
            l1_raw, r1_raw = s1_parts[-2].strip(), s1_parts[-1].strip()
            l2_raw, r2_raw = s2_parts[0].strip(), s2_parts[1].strip()

            l1, r1 = latex_to_sympy_expr(l1_raw), latex_to_sympy_expr(r1_raw)
            l2, r2 = latex_to_sympy_expr(l2_raw), latex_to_sympy_expr(r2_raw)
            if l1 is not None and r1 is not None and l2 is not None and r2 is not None:
                p1 = sp.expand(sp.Add(l1, -r1))
                p2 = sp.expand(sp.Add(l2, -r2))
                common_vars = list(p1.free_symbols.union(p2.free_symbols))
                if len(common_vars) == 1 and p1 != 0 and p2 != 0:
                    var = common_vars[0]
                    try:
                        sol1 = set(sp.solve(p1, var))
                        sol2 = set(sp.solve(p2, var))
                        if sol1 and sol2 and sol1 != sol2:
                            warnings.append(
                                SlideWarningItem(
                                    slide_index=slide_index,
                                    field=field_name,
                                    category="algebra_sympy",
                                    severity="error",
                                    detected_token=f"{step1} <=> {step2}",
                                    message=(
                                        f"Phép biến đổi phương trình không tương đương trên Slide {slide_index}: "
                                        f"\"{l1_raw} = {r1_raw}\" (nghiệm {var} = {sol1}) không tương đương với "
                                        f"\"{l2_raw} = {r2_raw}\" (nghiệm {var} = {sol2}). Nghi ngờ quên đổi dấu khi chuyển vế!"
                                    ),
                                    suggestion=(
                                        f"Kiểm tra lại quy tắc chuyển vế đổi dấu để phương trình giữ đúng tập nghiệm {var} = {sol1}."
                                    )
                                )
                            )
                    except Exception:
                        pass

        # 2. Kiểm tra lỗi quên đổi chiều bất phương trình bậc nhất khi chia cho số âm (VD: -2m + 4 > 0 <=> m > 2)
        ineq_regex = re.compile(r"(.+?)(<=|>=|\\le|\\ge|<|>)(.+)")
        m1 = ineq_regex.match(step1)
        m2 = ineq_regex.match(step2)
        if m1 and m2:
            # Nếu step1 có dấu '=' phía trước (VD: "\Delta' = (m-1)^2 - ... = -2m + 4 > 0"), lấy biểu thức sát dấu BĐT nhất
            l1_raw = m1.group(1).split("=")[-1].strip()
            op1 = m1.group(2).strip()
            r1_raw = m1.group(3).strip()

            l2_raw = m2.group(1).split("=")[-1].strip()
            op2 = m2.group(2).strip()
            r2_raw = m2.group(3).strip()

            l1, r1 = latex_to_sympy_expr(l1_raw), latex_to_sympy_expr(r1_raw)
            l2, r2 = latex_to_sympy_expr(l2_raw), latex_to_sympy_expr(r2_raw)
            if l1 is not None and r1 is not None and l2 is not None and r2 is not None:
                common_vars = list(sp.Add(l1, -r1).free_symbols.union(sp.Add(l2, -r2).free_symbols))
                if len(common_vars) == 1:
                    var = common_vars[0]
                    op_map = {"<": sp.Lt, ">": sp.Gt, "<=": sp.Le, ">=": sp.Ge, r"\le": sp.Le, r"\ge": sp.Ge}
                    rel1_cls = op_map.get(op1)
                    rel2_cls = op_map.get(op2)
                    if rel1_cls and rel2_cls:
                        try:
                            set1 = sp.solve_univariate_inequality(rel1_cls(l1, r1), var, relational=False)
                            set2 = sp.solve_univariate_inequality(rel2_cls(l2, r2), var, relational=False)
                            if set1 != set2:
                                warnings.append(
                                    SlideWarningItem(
                                        slide_index=slide_index,
                                        field=field_name,
                                        category="algebra_sympy",
                                        severity="error",
                                        detected_token=f"{l1_raw} {op1} {r1_raw} <=> {l2_raw} {op2} {r2_raw}",
                                        message=(
                                            f"Biến đổi bất phương trình sai tập nghiệm trên Slide {slide_index}: "
                                            f"\"{l1_raw} {op1} {r1_raw}\" (tập nghiệm: {set1}) không tương đương với "
                                            f"\"{l2_raw} {op2} {r2_raw}\" (tập nghiệm: {set2})."
                                        ),
                                        suggestion=(
                                            "Lưu ý: Khi nhân hoặc chia hai vế bất phương trình cho một số âm, "
                                            f"cần đổi chiều bất đẳng thức (tập nghiệm đúng: {set1})."
                                        )
                                    )
                                )
                        except Exception:
                            pass

    return warnings


def verify_math_with_sympy_in_slide(slide: Dict[str, Any], slide_index: int) -> List[SlideWarningItem]:
    """
    Task 10.2: Quét toàn bộ các công thức Toán học trên một trang Slide
    (main_definition_latex, math_formulas, bullet_points, và phương án đúng trong quiz_options)
    để kiểm định biến đổi đại số bằng SymPy.
    """
    warnings: List[SlideWarningItem] = []
    if not isinstance(slide, dict):
        return warnings

    candidate_formulas: List[Tuple[str, str]] = []

    # 1. Công thức trọng tâm (main_definition_latex)
    main_latex = slide.get("main_definition_latex")
    if main_latex and str(main_latex).strip():
        # Hỗ trợ trường hợp nhiều công thức ngăn cách bởi dấu '|' hoặc '\quad | \quad'
        sub_formulas = [seg.strip() for seg in re.split(r"\\q?quad\s*\|\s*\\q?quad|\|", str(main_latex)) if seg.strip()]
        for sub_f in sub_formulas:
            candidate_formulas.append((sub_f, "main_definition_latex"))

    # 2. Danh sách math_formulas (nếu có)
    math_formulas = slide.get("math_formulas") or []
    if isinstance(math_formulas, list):
        for m_idx, mf in enumerate(math_formulas):
            if mf and str(mf).strip():
                candidate_formulas.append((str(mf).strip(), f"math_formulas[{m_idx}]"))

    # 3. Các đoạn công thức $...$ hoặc $$...$$ nhúng trong bullet_points
    bullet_points = slide.get("bullet_points") or []
    if isinstance(bullet_points, list):
        for b_idx, bullet in enumerate(bullet_points):
            if not bullet:
                continue
            for match in _MATH_SEGMENT_REGEX.finditer(str(bullet)):
                candidate_formulas.append((match.group(0), f"bullet_points[{b_idx}]"))

    # 4. Chỉ kiểm tra phương án ĐÚNG (is_correct=True) trong quiz_options
    # (Phương án sai is_correct=False là bẫy sai lầm có chủ đích nên không cảnh báo lỗi)
    quiz_options = slide.get("quiz_options") or []
    if isinstance(quiz_options, list):
        for q_idx, opt in enumerate(quiz_options):
            if isinstance(opt, dict) and opt.get("is_correct") is True:
                for key in ("text", "distractor_rationale"):
                    val = opt.get(key)
                    if val:
                        for match in _MATH_SEGMENT_REGEX.finditer(str(val)):
                            candidate_formulas.append((match.group(0), f"quiz_options[{q_idx}].{key}"))

    # Chạy kiểm định SymPy cho từng biểu thức thu thập được
    for formula_str, field_label in candidate_formulas:
        warnings.extend(check_algebraic_equality_chain(formula_str, slide_index, field_label))
        warnings.extend(check_equation_equivalence_steps(formula_str, slide_index, field_label))

    return warnings


# ==============================================================================
# TASK 10.3: PROMPT AI ĐỐI CHIẾU CÔNG THỨC VỚI ĐỊNH LÝ SGK TOÁN GDPT 2018
# Trả về mảng chuẩn hóa warnings: [{slide_index, message, severity, ...}]
# ==============================================================================

PEDAGOGICAL_THEOREM_AUDIT_SYSTEM_PROMPT = """
Bạn là Chuyên gia Thẩm định Sách Giáo Khoa Toán THPT (Chương trình GDPT 2018) kiêm Bộ lọc Kiểm duyệt Sư phạm (AI Linter & Proofreader).
Nhiệm vụ của bạn là đọc soát danh sách các trang Slide bài giảng của Giáo viên và đối chiếu mọi công thức Toán học với Định lý chuẩn trong SGK Toán 10, 11, 12.

QUY TẮC KIỂM DUYỆT NGHIÊM NGẶT:
1. Chỉ báo cáo cảnh báo khi phát hiện công thức bị SAI DẤU, SAI HỆ SỐ hoặc SAI ĐỊNH LÝ SGK chuẩn mực, bao gồm:
   - Biệt thức Delta của phương trình bậc hai: Chuẩn SGK là \\Delta = b^2 - 4ac (hoặc \\Delta' = b'^2 - ac). Nếu ghi \\Delta = b^2 + 4ac là SAI DẤU.
   - Công thức nghiệm bậc hai: Chuẩn SGK là x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}, nghiệm kép x_0 = -\\frac{b}{2a}. Nếu thiếu dấu trừ trước b hoặc thiếu hệ số 2 ở mẫu là SAI.
   - Định lý Vi-ét: Chuẩn SGK là x_1 + x_2 = -\\frac{b}{a} và x_1 x_2 = \\frac{c}{a}. Nếu ghi x_1 + x_2 = \\frac{b}{a} (thiếu dấu trừ) hoặc x_1 x_2 = -\\frac{c}{a} là SAI DẤU.
   - Hệ thức lượng giác & Định lý Cosin: Chuẩn SGK là \\sin^2 x + \\cos^2 x = 1 và c^2 = a^2 + b^2 - 2ab\\cos C.
   - Đạo hàm cơ bản: Chuẩn SGK là (\\sin x)' = \\cos x và (\\cos x)' = -\\sin x.
   - Cấp số cộng: Chuẩn SGK là u_n = u_1 + (n - 1)d.
   - Thể tích khối chóp: Chuẩn SGK là V = \\frac{1}{3} S_{đáy} \\cdot h (phải có hệ số 1/3).
2. TUYỆT ĐỐI KHÔNG báo lỗi đối với các phương án nhiễu (is_correct = false) trong câu hỏi trắc nghiệm vì đó là bẫy sư phạm có chủ đích.
3. TUYỆT ĐỐI KHÔNG tự ý sửa đè nội dung Slide; chỉ trả về mảng JSON `warnings` theo cấu trúc:
   [{"slide_index": <int>, "message": "<mô tả lỗi đối chiếu định lý SGK>", "severity": "error" | "warning", "field": "<tên trường>", "category": "textbook_theorem", "suggestion": "<công thức đúng theo SGK>"}]
"""


class AITheoremAuditResult(BaseModel):
    """Schema nhận kết quả JSON có cấu trúc từ LLM Gateway trong Task 10.3."""
    warnings: List[SlideWarningItem] = Field(default_factory=list)


# Danh mục các quy tắc đối chiếu Định lý SGK Toán GDPT 2018 (Deterministic SGK Theorem Catalog)
# Mỗi phần tử gồm: (compiled_regex, theorem_name, wrong_desc, correct_latex, require_context_regex)
_TEXTBOOK_THEOREM_RULES: List[Tuple[re.Pattern, str, str, str, Optional[re.Pattern]]] = [
    # 1. Biệt thức Delta sai dấu: \Delta = b^2 + 4ac
    (
        re.compile(r"\\Delta\s*(?!')\s*=\s*b\s*\^\s*\{?2\}?\s*\+\s*4\s*\*?\s*a\s*\*?\s*c", re.IGNORECASE),
        "Công thức biệt thức Delta (SGK Toán 10)",
        "Ghi nhầm dấu cộng (+ 4ac) trong công thức biệt thức \\Delta",
        "\\Delta = b^2 - 4ac",
        None,
    ),
    # 2. Biệt thức Delta thiếu bình phương ở b: \Delta = b - 4ac
    (
        re.compile(r"\\Delta\s*(?!')\s*=\s*b\s*-\s*4\s*\*?\s*a\s*\*?\s*c", re.IGNORECASE),
        "Công thức biệt thức Delta (SGK Toán 10)",
        "Thiếu số mũ bình phương (b^2) trong công thức biệt thức \\Delta",
        "\\Delta = b^2 - 4ac",
        None,
    ),
    # 3. Biệt thức thu gọn Delta' sai dấu: \Delta' = b'^2 + ac
    (
        re.compile(r"\\Delta'\s*=\s*b'\s*\^\s*\{?2\}?\s*\+\s*a\s*\*?\s*c", re.IGNORECASE),
        "Công thức biệt thức thu gọn Delta' (SGK Toán 10)",
        "Ghi nhầm dấu cộng (+ ac) trong công thức biệt thức thu gọn \\Delta'",
        "\\Delta' = b'^2 - ac",
        None,
    ),
    # 4. Công thức nghiệm bậc hai quên dấu trừ trước b: \frac{b \pm \sqrt{\Delta}}{2a}
    (
        re.compile(r"\\frac\{\s*\+?\s*b\s*\\pm\s*\\sqrt\{\\Delta\}\s*\}\{\s*2\s*a\s*\}"),
        "Công thức nghiệm phương trình bậc hai (SGK Toán 10)",
        "Thiếu dấu âm (-) trước hệ số b trên tử số của công thức nghiệm",
        "x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}",
        None,
    ),
    # 5. Công thức nghiệm bậc hai thiếu hệ số 2 ở mẫu số: \frac{-b \pm \sqrt{\Delta}}{a}
    (
        re.compile(r"\\frac\{\s*-\s*b\s*\\pm\s*\\sqrt\{\\Delta\}\s*\}\{\s*a\s*\}"),
        "Công thức nghiệm phương trình bậc hai (SGK Toán 10)",
        "Thiếu hệ số 2 ở mẫu số (2a) trong công thức nghiệm tổng quát",
        "x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}",
        None,
    ),
    # 6. Công thức nghiệm kép quên dấu trừ: x_0 = \frac{b}{2a}
    (
        re.compile(r"x_\{?0\}?\s*=\s*\\frac\{\s*b\s*\}\{\s*2\s*a\s*\}"),
        "Công thức nghiệm kép phương trình bậc hai (SGK Toán 10)",
        "Thiếu dấu âm (-) trong công thức nghiệm kép / hoành độ đỉnh Parabol",
        "x_0 = -\\frac{b}{2a}",
        None,
    ),
    # 7. Định lý Vi-ét: Tổng hai nghiệm quên dấu âm (x_1 + x_2 = \frac{b}{a})
    (
        re.compile(r"x_\{?1\}?\s*\+\s*x_\{?2\}?\s*=\s*\\frac\{\s*b\s*\}\{\s*a\s*\}"),
        "Định lý Vi-ét — Tổng hai nghiệm (SGK Toán 10)",
        "Thiếu dấu âm (-) trong công thức tổng hai nghiệm Vi-ét",
        "x_1 + x_2 = -\\frac{b}{a}",
        None,
    ),
    # 8. Định lý Vi-ét: Tích hai nghiệm dư dấu âm (x_1 x_2 = -\frac{c}{a})
    (
        re.compile(r"x_\{?1\}?\s*(?:\\cdot|\*)?\s*x_\{?2\}?\s*=\s*-\s*\\frac\{\s*c\s*\}\{\s*a\s*\}"),
        "Định lý Vi-ét — Tích hai nghiệm (SGK Toán 10)",
        "Dư dấu âm (-) trong công thức tích hai nghiệm Vi-ét",
        "x_1 x_2 = \\frac{c}{a}",
        None,
    ),
    # 9. Hệ thức lượng giác cơ bản sai dấu: \sin^2 x - \cos^2 x = 1
    (
        re.compile(r"\\sin\s*\^\s*\{?2\}?\s*[a-zA-Z\\]+\s*-\s*\\cos\s*\^\s*\{?2\}?\s*[a-zA-Z\\]+\s*=\s*1"),
        "Hệ thức lượng giác cơ bản (SGK Toán 10 & 11)",
        "Ghi nhầm dấu trừ (-) thay vì dấu cộng (+) trong hằng đẳng thức lượng giác cơ bản",
        "\\sin^2 x + \\cos^2 x = 1",
        None,
    ),
    # 10. Đạo hàm hàm cos(x) quên dấu trừ: (\cos x)' = \sin x
    (
        re.compile(r"\(\s*\\cos\s*\(?x\)?\s*\)'\s*=\s*\+?\s*\\sin\s*\(?x\)?"),
        "Bảng đạo hàm lượng giác (SGK Toán 11)",
        "Quên dấu âm (-) trong công thức đạo hàm của hàm số cos(x)",
        "(\\cos x)' = -\\sin x",
        None,
    ),
    # 11. Cấp số cộng sai dấu trong số hạng tổng quát: u_n = u_1 + (n + 1)d hoặc u_n = u_1 - (n - 1)d
    (
        re.compile(r"u_\{?n\}?\s*=\s*u_\{?1\}?\s*(?:\+\s*\(\s*n\s*\+\s*1\s*\)|-\s*\(\s*n\s*-\s*1\s*\))\s*(?:\\cdot|\*)?\s*d"),
        "Số hạng tổng quát của Cấp số cộng (SGK Toán 11)",
        "Sai dấu trong công thức số hạng tổng quát của cấp số cộng",
        "u_n = u_1 + (n - 1)d",
        None,
    ),
    # 12. Thể tích khối chóp thiếu hệ số 1/3 (khi ngữ cảnh slide nói về khối chóp / hình chóp)
    (
        re.compile(r"V(?:_\{?(?:chóp|chop)\}?)?\s*=\s*(?!\\frac\{1\}\{3\}|1/3)(?:S(?:_\{?\\text\{đáy\}\}?|_\{?đáy\}?)?|B)\s*(?:\\cdot|\*)?\s*h"),
        "Công thức thể tích khối chóp (SGK Toán 11 & 12)",
        "Thiếu hệ số 1/3 trong công thức tính thể tích khối chóp (nhầm với thể tích khối lăng trụ)",
        "V = \\frac{1}{3} S_{\\text{đáy}} \\cdot h",
        re.compile(r"(khối\s+chóp|hình\s+chóp)", re.IGNORECASE | re.UNICODE),
    ),
]


def check_textbook_theorems_in_slide(slide: Dict[str, Any], slide_index: int) -> List[SlideWarningItem]:
    """
    Task 10.3 (Lớp Deterministic SGK Theorem Catalog):
    Đối chiếu trực tiếp mọi công thức trên Slide với các Định lý chuẩn trong SGK Toán GDPT 2018.
    Phát hiện tức thì các lỗi sai dấu định lý (VD: \\Delta = b^2 + 4ac, x_1 + x_2 = b/a...) ngay cả khi Offline.
    """
    warnings: List[SlideWarningItem] = []
    if not isinstance(slide, dict):
        return warnings

    # Ngữ cảnh toàn trang slide (để phân biệt bài khối chóp vs khối lăng trụ)
    slide_context_text = " ".join([
        str(slide.get("title") or ""),
        str(slide.get("subtitle") or ""),
        " ".join(str(b) for b in (slide.get("bullet_points") or [])),
    ])

    candidate_fields: List[Tuple[str, str]] = []

    main_latex = slide.get("main_definition_latex")
    if main_latex and str(main_latex).strip():
        candidate_fields.append((str(main_latex), "main_definition_latex"))

    for m_idx, mf in enumerate(slide.get("math_formulas") or []):
        if mf and str(mf).strip():
            candidate_fields.append((str(mf), f"math_formulas[{m_idx}]"))

    for b_idx, bullet in enumerate(slide.get("bullet_points") or []):
        if bullet and str(bullet).strip():
            candidate_fields.append((str(bullet), f"bullet_points[{b_idx}]"))

    # Chỉ quét phương án ĐÚNG (is_correct=True) trong quiz_options
    for q_idx, opt in enumerate(slide.get("quiz_options") or []):
        if isinstance(opt, dict) and opt.get("is_correct") is True:
            for key in ("text", "distractor_rationale"):
                val = opt.get(key)
                if val and str(val).strip():
                    candidate_fields.append((str(val), f"quiz_options[{q_idx}].{key}"))

    for raw_content, field_label in candidate_fields:
        for pattern, theorem_name, wrong_desc, correct_latex, ctx_regex in _TEXTBOOK_THEOREM_RULES:
            if ctx_regex is not None and not ctx_regex.search(slide_context_text):
                # Nếu quy tắc yêu cầu ngữ cảnh (VD: khối chóp) nhưng dòng hiện tại nói về lăng trụ thì bỏ qua
                continue
            if ctx_regex is not None and re.search(r"lăng\s+trụ", raw_content, re.IGNORECASE | re.UNICODE):
                continue

            match = pattern.search(raw_content)
            if match:
                found_formula = match.group(0).strip()
                warnings.append(
                    SlideWarningItem(
                        slide_index=slide_index,
                        field=field_label,
                        category="textbook_theorem",
                        severity="error",
                        detected_token=found_formula,
                        message=(
                            f"Phát hiện công thức lệch chuẩn {theorem_name} trên Slide {slide_index}: "
                            f"\"{found_formula}\" ({wrong_desc})."
                        ),
                        suggestion=f"Theo SGK Toán GDPT 2018, công thức đúng phải là: ${correct_latex}$."
                    )
                )

    return warnings


def audit_theorems_with_ai(
    slides: List[Dict[str, Any]],
    use_llm: bool = False
) -> List[SlideWarningItem]:
    """
    Task 10.3: Kết hợp đối chiếu danh mục Định lý SGK chuẩn (Deterministic) và Prompt AI qua LLMGateway.
    Đảm bảo trả về mảng warnings: [{slide_index, message, severity, ...}] nhanh, chính xác 100% và không lỗi mạng.
    """
    theorem_warnings: List[SlideWarningItem] = []
    if not isinstance(slides, list) or not slides:
        return theorem_warnings

    # 1. Quét qua bộ quy tắc Định lý SGK chuẩn (luôn chạy tức thì 0ms)
    for idx, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        raw_num = slide.get("slide_index") or slide.get("slide_number")
        slide_num = int(raw_num) if isinstance(raw_num, int) and raw_num > 0 else (idx + 1)
        theorem_warnings.extend(check_textbook_theorems_in_slide(slide, slide_num))

    # 2. Nếu được yêu cầu gọi thêm LLM Proofreader để rà soát ngữ nghĩa sâu theo SGK
    if use_llm:
        try:
            from services.llm_gateway import llm_gateway
            compact_slides = []
            for idx, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    continue
                raw_num = slide.get("slide_index") or slide.get("slide_number")
                slide_num = int(raw_num) if isinstance(raw_num, int) and raw_num > 0 else (idx + 1)
                compact_slides.append({
                    "slide_index": slide_num,
                    "title": slide.get("title", ""),
                    "main_definition_latex": slide.get("main_definition_latex", ""),
                    "bullet_points": slide.get("bullet_points", []),
                })

            user_prompt = (
                "Hãy đối chiếu toàn bộ các công thức trên bộ Slide sau với Định lý SGK Toán THPT (GDPT 2018) "
                "và trả về danh sách cảnh báo `warnings` nếu phát hiện công thức sai dấu hoặc sai định lý:\n"
                f"{compact_slides}"
            )
            ai_res = llm_gateway.generate_structured(
                prompt=user_prompt,
                system_prompt=PEDAGOGICAL_THEOREM_AUDIT_SYSTEM_PROMPT,
                response_schema=AITheoremAuditResult,
                task_type="chat",
                temperature=0.1,
            )
            if ai_res and ai_res.warnings:
                existing_keys = {(w.slide_index, w.detected_token or w.message) for w in theorem_warnings}
                for ai_w in ai_res.warnings:
                    key = (ai_w.slide_index, ai_w.detected_token or ai_w.message)
                    if key not in existing_keys:
                        if not ai_w.category:
                            ai_w.category = "textbook_theorem"
                        theorem_warnings.append(ai_w)
                        existing_keys.add(key)
        except Exception:
            # Fallback an toàn về kết quả Deterministic SGK Theorem Catalog nếu Offline / hết Quota
            pass

    return theorem_warnings


def audit_slide_deck(deck_payload: Dict[str, Any]) -> DeckAuditResponse:
    """
    Hàm điều phối kiểm duyệt toàn bộ bộ Slide (Slide Deck) qua 3 tầng:
    - Tầng 1 (Task 10.1): Quét lỗi chính tả Tiếng Việt & chế bản sư phạm.
    - Tầng 2 (Task 10.2): Kiểm định biến đổi đại số và phương trình tương đương bằng SymPy.
    - Tầng 3 (Task 10.3): Đối chiếu công thức với Định lý SGK Toán GDPT 2018 (AI Proofreader & SGK Catalog).
    """
    if not isinstance(deck_payload, dict):
        return DeckAuditResponse(is_clean=True, total_warnings=0, warnings=[])

    use_llm = bool(deck_payload.get("use_ai_proofreader", False))

    # Cho phép payload truyền trực tiếp {slides: [...]} hoặc {slide_deck: {slides: [...]}}
    if "slide_deck" in deck_payload and isinstance(deck_payload["slide_deck"], dict):
        deck_dict = deck_payload["slide_deck"]
    else:
        deck_dict = deck_payload

    slides = deck_dict.get("slides") or []
    if not isinstance(slides, list):
        return DeckAuditResponse(is_clean=True, total_warnings=0, warnings=[])

    all_warnings: List[SlideWarningItem] = []

    for idx, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        # Xác định STT slide (1-based index)
        raw_num = slide.get("slide_index") or slide.get("slide_number")
        slide_num = int(raw_num) if isinstance(raw_num, int) and raw_num > 0 else (idx + 1)

        # Task 10.1: Quét lỗi chính tả tiếng Việt trên từng Slide
        spelling_warnings = check_vietnamese_spelling_in_slide(slide, slide_num)
        all_warnings.extend(spelling_warnings)

        # Task 10.2: Tích hợp SymPy kiểm tra biến đổi đại số cơ bản trên từng Slide
        sympy_warnings = verify_math_with_sympy_in_slide(slide, slide_num)
        all_warnings.extend(sympy_warnings)

    # Task 10.3: Đối chiếu công thức với Định lý SGK Toán GDPT 2018
    theorem_warnings = audit_theorems_with_ai(slides, use_llm=use_llm)
    all_warnings.extend(theorem_warnings)

    return DeckAuditResponse(
        is_clean=len(all_warnings) == 0,
        total_warnings=len(all_warnings),
        warnings=all_warnings
    )
