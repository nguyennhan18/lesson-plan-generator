r"""
Automated Acceptance Test Suite — Day 10 (Xây dựng Bộ lọc Kiểm duyệt Sư phạm - AI Linter & Proofreader)
Kiểm tra toàn diện 5 hạng mục của Ngày 10 theo Ke_Hoach_Phat_Trien.pdf:
- Task 10.1: Endpoint POST /api/v1/validation/audit-deck trong validation.py — Quét toàn bộ slide tìm lỗi chính tả tiếng Việt thường gặp
- Task 10.2: Tích hợp SymPy kiểm tra biến đổi đại số cơ bản (đảm bảo hai vế phương trình / đẳng thức có tương đương không)
- Task 10.3: Prompt AI & Danh mục đối chiếu công thức với định lý SGK, trả về mảng warnings: [{slide_index, message, severity}]
- Task 10.4: Thiết kế giao diện "Danh sách Cảnh báo" — Hiển thị biểu tượng ⚠️ màu vàng trên slide có lỗi, click vào gợi ý cách sửa mà KHÔNG tự ý ghi đè bài của GV
- Task 10.5 (DoD): Đưa một slide cố tình gõ sai từ "học xinh" và công thức sai dấu -> Hệ thống hiện bảng cảnh báo vàng để GV tự sửa
"""

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from services.validation import (
    PEDAGOGICAL_THEOREM_AUDIT_SYSTEM_PROMPT,
    SlideWarningItem,
    DeckAuditResponse,
    audit_slide_deck,
    check_vietnamese_spelling_in_slide,
    verify_math_with_sympy_in_slide,
    check_textbook_theorems_in_slide,
)

MAIN_PY = BACKEND_SRC / "main.py"
VALIDATION_PY = BACKEND_SRC / "services" / "validation.py"
LINTER_CLIENT_JS = FRONTEND_DIR / "src" / "utils" / "pedagogicalLinterClient.js"
WARNING_MODAL_JSX = FRONTEND_DIR / "src" / "components" / "PedagogicalWarningModal.jsx"
PRESENTATION_STAGE_JSX = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
SLIDE_EDITOR_JSX = FRONTEND_DIR / "src" / "components" / "SlideEditorScreen.jsx"


def test_task_10_1_vietnamese_spelling_and_audit_endpoint():
    """
    Task 10.1: Kiểm tra endpoint /api/v1/validation/audit-deck và bộ quét lỗi chính tả Tiếng Việt
    trên toàn bộ các trường của Slide (tách bỏ vùng toán học $...$ để không bắt nhầm ký hiệu Toán).
    """
    main_code = MAIN_PY.read_text(encoding="utf-8")
    assert "/api/v1/validation" in main_code, "Thiếu prefix /api/v1/validation trong main.py"
    assert '"/audit-deck"' in main_code, "Thiếu route POST /api/v1/validation/audit-deck trong main.py"
    assert "audit_slide_deck" in main_code

    slide_with_typos = {
        "slide_number": 1,
        "title": "1. Khởi động cùng học xinh lớp 10",
        "bullet_points": [
            r"Giải phương chình bậc hai $x^2 - 5x + 6 = 0$ từ giả thuyết bài toán.",
            "Hàm số này là là hàm số bậc hai chuẩn.",
        ],
        "teacher_note": "Nhắc học sinh tránh kết luận vô ngiệm khi chưa tính Delta.",
    }
    warnings = check_vietnamese_spelling_in_slide(slide_with_typos, 1)
    detected_tokens = {w.detected_token.lower() for w in warnings if w.detected_token}

    assert "học xinh" in detected_tokens, "Phải phát hiện lỗi chính tả 'học xinh'"
    assert "phương chình" in detected_tokens, "Phải phát hiện lỗi chính tả 'phương chình'"
    assert "giả thuyết" in detected_tokens, "Phải phát hiện nhầm thuật ngữ 'giả thuyết' -> 'giả thiết'"
    assert "là là" in detected_tokens, "Phải phát hiện lỗi gõ lặp từ 'là là'"
    assert "vô ngiệm" in detected_tokens, "Phải phát hiện lỗi chính tả 'vô ngiệm'"


def test_task_10_2_sympy_algebraic_equivalence_verification():
    """
    Task 10.2: Kiểm tra tích hợp SymPy phát hiện các phép biến đổi đại số và phương trình/bất phương trình
    không tương đương, đồng thời KHÔNG báo lỗi giả trên phương trình điều kiện chuẩn.
    """
    # 1. Slide chứa 5 phép biến đổi đại số SAI
    slide_bad_algebra = {
        "slide_number": 2,
        "title": "Biến đổi đại số",
        "main_definition_latex": "(x - 2)^2 = x^2 - 4x - 4",
        "bullet_points": [
            r"Phân tích nhân tử: $x^2 - 5x + 6 = (x - 2)(x + 3)$",
            r"Tính biệt thức: $\Delta = (-2)^2 - 4 \cdot 1 \cdot (-3) = 4 - 12 = -8$",
            r"Chuyển vế phương trình: $2x - 6 = 0 \iff 2x = -6$",
            r"Chia bất phương trình cho số âm: $-2m + 4 > 0 \iff m > 2$",
        ],
    }
    bad_warnings = verify_math_with_sympy_in_slide(slide_bad_algebra, 2)
    assert len(bad_warnings) == 5, f"SymPy phải phát hiện đủ 5 lỗi đại số, thực tế: {len(bad_warnings)}"
    assert all(w.category == "algebra_sympy" for w in bad_warnings)

    # 2. Slide chứa các phương trình điều kiện & biến đổi ĐÚNG (Không được báo lỗi giả)
    slide_clean_algebra = {
        "slide_number": 3,
        "title": "Phương trình bậc hai chuẩn",
        "main_definition_latex": r"ax^2 + bx + c = 0 \quad (a \neq 0)",
        "bullet_points": [
            r"Quỹ đạo ném bóng: $h(t) = -0.5t^2 + 2t + 2.5 = 0$",
            r"Khai triển đúng: $(x - 2)^2 = x^2 - 4x + 4$",
            r"Phân tích đúng: $x^2 - 5x + 6 = (x - 2)(x - 3)$",
            r"Phương trình tương đương: $2x - 6 = 0 \iff 2x = 6 \iff x = 3$",
        ],
        "quiz_options": [
            {"label": "A", "text": "$x = 3$", "is_correct": True, "distractor_rationale": "Đúng."},
            {"label": "B", "text": "$(x - 2)^2 = x^2 - 4$", "is_correct": False, "distractor_rationale": "Bẫy sai lầm."},
        ],
    }
    clean_warnings = verify_math_with_sympy_in_slide(slide_clean_algebra, 3)
    assert len(clean_warnings) == 0, f"Slide chuẩn không được phép có cảnh báo giả: {clean_warnings}"


def test_task_10_3_textbook_theorem_cross_checking_and_schema():
    """
    Task 10.3: Kiểm tra Prompt AI và bộ quy tắc đối chiếu Định lý SGK Toán GDPT 2018,
    trả về mảng warnings: [{slide_index, message, severity, ...}].
    """
    assert "GDPT 2018" in PEDAGOGICAL_THEOREM_AUDIT_SYSTEM_PROMPT
    assert "warnings" in PEDAGOGICAL_THEOREM_AUDIT_SYSTEM_PROMPT

    slide_bad_theorems = {
        "slide_number": 1,
        "title": "Thể tích khối chóp và Phương trình bậc hai",
        "main_definition_latex": r"\Delta = b^2 + 4ac",
        "bullet_points": [
            r"Công thức nghiệm: $x_{1,2} = \frac{b \pm \sqrt{\Delta}}{2a}$",
            r"Hệ thức Vi-ét: $x_1 + x_2 = \frac{b}{a}$ và $x_1 x_2 = -\frac{c}{a}$",
            r"Thể tích khối chóp: $V = S_{\text{đáy}} \cdot h$",
        ],
    }
    warnings = check_textbook_theorems_in_slide(slide_bad_theorems, 1)
    assert len(warnings) == 5, f"Phải phát hiện đủ 5 lỗi định lý SGK, thực tế: {len(warnings)}"

    for w in warnings:
        dumped = w.model_dump()
        assert "slide_index" in dumped and dumped["slide_index"] == 1
        assert "message" in dumped and len(dumped["message"]) > 10
        assert "severity" in dumped and dumped["severity"] in ("warning", "error", "info")
        assert dumped["category"] == "textbook_theorem"


def test_task_10_4_frontend_yellow_warning_ui_human_in_the_loop():
    """
    Task 10.4: Kiểm tra giao diện "Danh sách Cảnh báo" (PedagogicalWarningModal.jsx),
    biểu tượng ⚠️ màu vàng trên PresentationStage.jsx & SlideEditorScreen.jsx,
    và nguyên tắc KHÔNG tự ý ghi đè bài của Giáo viên.
    """
    assert LINTER_CLIENT_JS.exists(), "Thiếu file pedagogicalLinterClient.js"
    assert WARNING_MODAL_JSX.exists(), "Thiếu component PedagogicalWarningModal.jsx"

    modal_code = WARNING_MODAL_JSX.read_text(encoding="utf-8")
    stage_code = PRESENTATION_STAGE_JSX.read_text(encoding="utf-8")
    editor_code = SLIDE_EDITOR_JSX.read_text(encoding="utf-8")

    # Kiểm tra nội dung giao diện "Danh sách Cảnh báo" và cam kết Human-in-the-Loop
    assert "Danh Sách Cảnh Báo Sư Phạm" in modal_code
    assert "KHÔNG tự ý ghi đè bài của Giáo viên" in modal_code
    assert "<MathText" in modal_code, "Gợi ý sửa công thức phải được hiển thị bằng <MathText />"

    # Kiểm tra tích hợp biểu tượng ⚠️ màu vàng và Modal trên cả 2 màn hình
    assert "PedagogicalWarningModal" in stage_code
    assert "⚠️" in stage_code
    assert "PedagogicalWarningModal" in editor_code
    assert "⚠️" in editor_code


def test_task_10_5_dod_hoc_xinh_and_sign_error_end_to_end():
    """
    Task 10.5 (DoD Ngày 10):
    Đưa một slide cố tình gõ sai từ "học xinh" và công thức sai dấu
    -> Hệ thống phát hiện chính xác ở cả Backend (Python/SymPy) lẫn Frontend (Node.js ESM Runtime),
    hiển thị bảng cảnh báo vàng kèm gợi ý sửa mà TUYỆT ĐỐI KHÔNG tự ý ghi đè dữ liệu Slide của GV.
    """
    dod_deck = {
        "presentation_title": "Bài giảng Phương trình bậc hai",
        "slides": [
            {
                "slide_number": 1,
                "title": "1. Bài tập khởi động dành cho học xinh lớp 10",
                "main_definition_latex": r"\Delta = b^2 + 4ac",
                "bullet_points": [
                    r"Khai triển hằng đẳng thức: $(x - 1)^2 = x^2 - 2x - 1$",
                ],
            }
        ],
    }
    original_snapshot = copy.deepcopy(dod_deck)

    # 1. Kiểm định phía Backend (audit_slide_deck)
    backend_res: DeckAuditResponse = audit_slide_deck(dod_deck)
    assert backend_res.is_clean is False
    assert backend_res.total_warnings == 3, (
        f"Backend phải phát hiện 3 cảnh báo ('học xinh', '\\Delta = b^2 + 4ac', '(x-1)^2 = x^2 - 2x - 1'), "
        f"thực tế: {backend_res.total_warnings}"
    )

    categories = {w.category for w in backend_res.warnings}
    assert categories == {"spelling", "textbook_theorem", "algebra_sympy"}, (
        f"Phải hội tụ đủ 3 tầng kiểm duyệt (spelling, textbook_theorem, algebra_sympy), nhận được: {categories}"
    )
    assert dod_deck == original_snapshot, "Backend audit_slide_deck tuyệt đối KHÔNG được làm biến đổi dữ liệu gốc của GV!"

    # 2. Kiểm định phía Frontend bằng Node.js ESM Runtime (pedagogicalLinterClient.js)
    node_script = r"""
import { auditSlideDeckLocal, mergeAuditWarnings } from './src/utils/pedagogicalLinterClient.js';

const teacherDeck = {
  presentation_title: 'Bài giảng Phương trình bậc hai',
  slides: [
    {
      slide_number: 1,
      title: '1. Bài tập khởi động dành cho học xinh lớp 10',
      main_definition_latex: '\\Delta = b^2 + 4ac',
      bullet_points: ['Khai triển hằng đẳng thức: $(x - 1)^2 = x^2 - 2x - 1$'],
    },
  ],
};

const beforeTitle = teacherDeck.slides[0].title;
const beforeLatex = teacherDeck.slides[0].main_definition_latex;

const localRes = auditSlideDeckLocal(teacherDeck);
const merged = mergeAuditWarnings(localRes.warnings, localRes.warnings);

console.log(JSON.stringify({
  isClean: localRes.is_clean,
  totalWarnings: localRes.total_warnings,
  dedupCount: merged.length,
  hasHocXinhWarning: localRes.warnings.some((w) => w.detected_token === 'học xinh' && w.category === 'spelling'),
  hasDeltaSignWarning: localRes.warnings.some((w) => w.category === 'textbook_theorem' && w.message.includes('Delta')),
  hasAlgebraSignWarning: localRes.warnings.some((w) => w.category === 'algebra_sympy'),
  teacherSlideUntouched:
    teacherDeck.slides[0].title === beforeTitle &&
    teacherDeck.slides[0].main_definition_latex === beforeLatex,
}));
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        check=True,
    )
    fe_payload = json.loads(proc.stdout.strip())

    assert fe_payload["isClean"] is False
    assert fe_payload["totalWarnings"] == 3
    assert fe_payload["dedupCount"] == 3, "Hàm mergeAuditWarnings phải khử trùng lặp chính xác"
    assert fe_payload["hasHocXinhWarning"] is True, "Frontend phải bắt được lỗi 'học xinh'"
    assert fe_payload["hasDeltaSignWarning"] is True, "Frontend phải bắt được lỗi sai dấu '\\Delta = b^2 + 4ac'"
    assert fe_payload["hasAlgebraSignWarning"] is True, "Frontend phải bắt được lỗi sai dấu hằng đẳng thức '(x-1)^2 = x^2 - 2x - 1'"
    assert fe_payload["teacherSlideUntouched"] is True, "Frontend tuyệt đối KHÔNG tự ý ghi đè bài của GV!"


class TestDay10PedagogicalLinter(unittest.TestCase):
    def test_10_1_vietnamese_spelling_audit(self):
        test_task_10_1_vietnamese_spelling_and_audit_endpoint()

    def test_10_2_sympy_algebra_verification(self):
        test_task_10_2_sympy_algebraic_equivalence_verification()

    def test_10_3_textbook_theorem_crosscheck(self):
        test_task_10_3_textbook_theorem_cross_checking_and_schema()

    def test_10_4_frontend_yellow_warning_ui(self):
        test_task_10_4_frontend_yellow_warning_ui_human_in_the_loop()

    def test_10_5_dod_hoc_xinh_and_sign_error(self):
        test_task_10_5_dod_hoc_xinh_and_sign_error_end_to_end()


if __name__ == "__main__":
    unittest.main()
