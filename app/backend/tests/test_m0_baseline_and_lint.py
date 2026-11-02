"""
Unit tests cho M0 (Kiểm kê dữ liệu, Golden Set, và bộ công cụ `deck_lint.py`).
"""

import json
import os
import sys
from pathlib import Path


from lessonai.services.deck_lint import (  # noqa: E402
    check_latex_syntax,
    is_divider_slide,
    is_fragment_line,
    lint_deck,
    lint_slide,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"


def test_is_divider_slide_v31_rules():
    """
    Kiểm tra quy tắc Phụ lục A.4 (v3.1):
    - Slide chuyển mục bị tách thành 4-5 dòng IN HOA (như Page 3, Page 4 Bài 1) phải trả về True.
    - Slide Định lí/Chú ý ngắn (có chữ thường hoặc ký hiệu toán) phải trả về False.
    """
    page4_s4_bug = {
        "title": "BÀI HỌC",
        "bullet_points": [
            "NỘI DUNG",
            "01",
            "TÍNH ĐƠN ĐIỆU CỦA HÀM SỐ",
            "02",
            "CỰC TRỊ CỦA HÀM SỐ",
        ],
    }
    assert is_divider_slide(page4_s4_bug) is True

    short_theorem_slide = {
        "title": "Định lí 1",
        "bullet_points": [
            "Nếu $f'(x) > 0$ với mọi $x \\in (a; b)$ thì hàm số đồng biến trên $(a; b)$."
        ],
    }
    assert is_divider_slide(short_theorem_slide) is False

    short_note_slide = {
        "title": "Chú ý",
        "bullet_points": [
            "Điểm cực trị của hàm số là giá trị $x_0$, còn $f(x_0)$ là giá trị cực trị."
        ],
    }
    assert is_divider_slide(short_note_slide) is False


def test_lint_slide_catches_s2_s3_s4_s5_errors():
    """Kiểm tra `lint_slide` bắt chính xác cả 5 loại lỗi S2-S5 mô tả trong المục I plan_v3.md."""
    # Lỗi S2: Vận dụng bị gán nhầm khoi_dong và cắt cụt ở chữ 'Giải:'
    s2_slide = {
        "type": "WARM_UP_SLIDE",
        "layout": "SINGLE_COLUMN",
        "activity_type": "khoi_dong",
        "title": "Khởi Động • Vận dụng 1 trang 9 SGK Toán 12",
        "bullet_points": [
            "Hãy giải bài toán trong tình huống mở đầu.",
            "Giải:",
        ],
    }
    res_s2 = lint_slide(s2_slide)
    err_codes_s2 = {e.split(":", 1)[0] for e in res_s2["errors"]}
    assert "misclassified_warmup" in err_codes_s2
    assert "truncated_solution" in err_codes_s2

    # Lỗi S3: main_definition_latex chứa tên bài học và bullet có mảnh vỡ
    s3_slide = {
        "type": "CONCEPT_SLIDE",
        "layout": "CONCEPT_HIGHLIGHT",
        "title": "1. Khái Niệm Trọng Tâm",
        "bullet_points": [
            "Cho hàm số $y=f(x)$ có đạo hàm trên khoảng $K$.",
            "khi",
        ],
        "main_definition_latex": r"\text{Bài 1: Tính đơn điệu và cực trị của hàm số} \quad (\text{SGK KNTT 12})",
    }
    res_s3 = lint_slide(s3_slide)
    err_codes_s3 = {e.split(":", 1)[0] for e in res_s3["errors"]}
    assert "title_in_formula_box" in err_codes_s3
    assert "fragment_line" in err_codes_s3

    # Lỗi S4: Slide chuyển mục rời rạc
    s4_slide = {
        "type": "CONCEPT_SLIDE",
        "layout": "SINGLE_COLUMN",
        "title": "NỘI DUNG BÀI HỌC",
        "bullet_points": ["01", "TÍNH ĐƠN ĐIỆU", "02", "CỰC TRỊ"],
    }
    res_s4 = lint_slide(s4_slide)
    err_codes_s4 = {e.split(":", 1)[0] for e in res_s4["errors"]}
    assert "divider_slide" in err_codes_s4 or "divider_token" in err_codes_s4

    # Lỗi S5: Đề bài "như hình vẽ" thiếu hình & câu tự luận lặp "Đáp án đúng là D"
    s5_slide = {
        "type": "EXERCISE_SLIDE",
        "layout": "TWO_COLUMN",
        "title": "Ví dụ giải mẫu",
        "bullet_points": [
            "Cho hàm số $y = f(x)$ có bảng xét dấu của đạo hàm như hình vẽ. Hàm số nghịch biến trên khoảng nào?"
        ],
        "worked_solution_steps": [
            "Bước 1: Đáp án đúng là D vì dựa vào bảng xét dấu.",
            "Bước 2: Đáp án đúng là D.",
        ],
    }
    res_s5 = lint_slide(s5_slide)
    err_codes_s5 = {e.split(":", 1)[0] for e in res_s5["errors"]}
    assert "missing_visual" in err_codes_s5
    assert "essay_with_mcq_answer" in err_codes_s5


def test_lint_slide_v2_blocks_validation():
    """Kiểm tra quy tắc lint cho Schema v2 (`blocks`, `reveal_order`, `verified`)."""
    bad_v2_slide = {
        "type": "EXERCISE_SLIDE",
        "layout": "TWO_COLUMN",
        "title": "Ví dụ 1",
        "blocks": [
            {
                "block_id": "s4-b1",
                "block_type": "PROBLEM_BOX",
                "content": "Xét chiều biến thiên của hàm số $y = x^3 - 3x^2 + 2$.",
                "reveal_order": 0,
                "verified": True,
            },
            {
                "block_id": "s4-b2",
                "block_type": "WORKED_STEP",
                "content": "Tập xác định $D = \\mathbb{R}$, đạo hàm $y' = 3x^2 - 6x$.",
                "reveal_order": 2,  # Nhảy cóc từ 0 lên 2 -> lỗi non_contiguous_reveal_order
                "verified": False,  # Lỗi unverified_worked_step
            },
        ],
    }
    res = lint_slide(bad_v2_slide)
    codes = {e.split(":", 1)[0] for e in res["errors"]}
    assert "non_contiguous_reveal_order" in codes
    assert "unverified_worked_step" in codes


def test_m0_artifacts_exist_and_valid():
    """Đảm bảo các báo cáo M0 (inventory, golden_set, baseline_lint) đã được tạo đầy đủ."""
    inv_path = REPO_ROOT / "reports" / "data" / "inventory_report.json"
    gs_path = REPO_ROOT / "data" / "fixtures" / "golden_set.json"
    base_path = REPO_ROOT / "reports" / "data" / "baseline_lint_report.json"

    assert inv_path.exists(), "Thiếu file data/inventory_report.json"
    assert gs_path.exists(), "Thiếu file data/golden_set.json"
    assert base_path.exists(), "Thiếu file data/baseline_lint_report.json"

    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    assert inv["pdf2xml_kntt12"]["file_count"] == 32
    assert inv["pptx_corpus"]["total_pptx_files"] == 193
    assert inv["pptx_corpus"]["total_slides"] == 3953

    gs = json.loads(gs_path.read_text(encoding="utf-8"))
    assert len(gs["golden_lessons"]) == 10
    assert len(gs["teacher_reference_decks"]) == 5
