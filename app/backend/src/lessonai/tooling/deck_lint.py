"""
Bộ kiểm tra chất lượng nội dung & sư phạm tự động cho Slide/Deck (`deck_lint.py` - Mục V plan_v3.md).

Hỗ trợ kiểm tra:
1. Slide đơn lẻ từ kho dữ liệu (`slides_kntt12_cleaned.jsonl` hoặc `slides_v2.jsonl`)
2. Slide/Deck hoàn chỉnh (`SlideSchema` / `SlideDeckSchema` cả v1 và v2 có `blocks`)
"""

import re
from typing import Any, Dict, List, Optional, Union

VALID_SHORT_LABEL_RE = re.compile(
    r"^(Giải\s*:?|Lời giải\s*:?|Chú ý\s*:?|Nhận xét\s*:?|Định lí\s*\d*\s*:?|"
    r"Định nghĩa\s*\d*\s*:?|Hệ quả\s*\d*\s*:?|Tính chất\s*\d*\s*:?|"
    r"Ví dụ\s*\d*\s*:?|Luyện tập\s*\d*\s*:?|Vận dụng\s*\d*\s*:?|"
    r"HĐ\s*\d+\s*:?|Hoạt động\s*\d*\s*:?|Bước\s*\d+\s*:?|"
    r"Kết luận\s*:?|Tóm tắt\s*:?|Trả lời\s*:?|Phương pháp\s*:?|"
    r"[a-dA-D][.)]|Câu\s*\d+\s*[.:]?|Bài\s*\d+\s*[.:]?)$",
    re.I,
)

MISSING_VISUAL_RE = re.compile(
    r"(như\s+hình\s+vẽ|hình\s+vẽ\s+bên|hình\s+bên|đồ\s+thị\s+bên|"
    r"đồ\s+thị\s+như\s+hình|bảng\s+biến\s+thiên\s+như\s+hình|"
    r"bảng\s+biến\s+thiên\s+bên|quan\s+sát\s+hình\s+vẽ|cho\s+bởi\s+hình\s+vẽ)",
    re.I,
)

DIVIDER_TOKEN_RE = re.compile(
    r"^(BÀI\s+HỌC|NỘI\s+DUNG\s+BÀI\s+HỌC|NỘI\s+DUNG|CHƯƠNG\s+[IVX\d]+|\d{1,2})$",
    re.I,
)

WARMUP_FORBIDDEN_TITLE_RE = re.compile(
    r"\b(vận\s+dụng|luyện\s+tập|bài\s+tập|củng\s+cố|trắc\s+nghiệm)\b",
    re.I,
)

DANGLING_SOL_RE = re.compile(
    r"^(Giải|Lời\s+giải|Hướng\s+dẫn\s+giải|Trả\s+lời)\s*:?\s*$",
    re.I,
)

FORBIDDEN_LATEX_RE = re.compile(r"(\\undefined|\\onerror|(?<!\\)\x00)")


def _to_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}


def is_divider_slide(slide: Union[Dict[str, Any], Any]) -> bool:
    """
    Bộ lọc slide chuyển mục theo Phụ lục A.4 (v3.1):
    Tối đa 25 từ và 6 dòng, không có công thức, và gần như toàn chữ IN HOA (hoặc chỉ là số thứ tự).
    Slide Định lí/Chú ý có chữ thường nên upper_ratio thấp và không bị loại.
    """
    s = _to_dict(slide)
    bullets = s.get("bullet_points") or []
    if not bullets and s.get("blocks"):
        bullets = [
            b.get("content", "")
            for b in s.get("blocks", [])
            if isinstance(b, dict) and b.get("content")
        ]
    texts = [
        t.strip()
        for t in [s.get("title", "")] + list(bullets)
        if t and isinstance(t, str) and t.strip()
    ]
    if not texts:
        return True
    letters = [c for t in texts for c in t if c.isalpha()]
    upper_ratio = sum(c.isupper() for c in letters) / max(1, len(letters))
    has_math = any("$" in t or re.search(r"[=<>′'^]", t) for t in texts)
    words = sum(len(t.split()) for t in texts)
    only_marks = all(re.fullmatch(r"\d{1,2}", t) or t.isupper() for t in texts)
    short_enough = words <= 25 and len(texts) <= 6
    return short_enough and not has_math and (upper_ratio > 0.85 or only_marks)


def check_latex_syntax(text: str) -> List[str]:
    """
    Kiểm tra cân bằng dấu `$` và cú pháp LaTeX cơ bản (ngoặc nhọn, \\frac, \\sqrt, \\left/\\right).
    """
    issues: List[str] = []
    if not text or not isinstance(text, str):
        return issues

    # Đếm dấu $ không bị escape
    unescaped_dollars = re.findall(r"(?<!\\)\$", text)
    if len(unescaped_dollars) % 2 != 0:
        issues.append("unbalanced_dollar: Số dấu '$' không cân bằng")
        return issues

    math_spans = re.findall(r"(?<!\\)\$([^$]+)(?<!\\)\$", text)
    for span in math_spans:
        s = span.strip()
        if not s:
            issues.append("empty_math_span: Cặp '$$' rỗng")
            continue
        # Kiểm tra cân bằng { và } (bỏ qua \{ và \})
        open_braces = len(re.findall(r"(?<!\\)\{", s))
        close_braces = len(re.findall(r"(?<!\\)\}", s))
        if open_braces != close_braces:
            issues.append(f"unbalanced_braces: Lệch ngoặc nhọn trong công thức '${s[:40]}$'")
        if FORBIDDEN_LATEX_RE.search(s):
            issues.append(f"invalid_latex_token: Token lỗi trong '${s[:40]}$'")
        if re.search(r"\\frac\s*(?!\{)", s):
            issues.append(f"malformed_frac: \\frac thiếu '{{' trong '${s[:40]}$'")
    return issues


def is_fragment_line(line: str) -> bool:
    """
    Kiểm tra dòng "mảnh vỡ": < 3 từ và không phải công thức toán hoặc nhãn hợp lệ.
    """
    s = (line or "").strip()
    if not s:
        return True
    words = s.split()
    if len(words) >= 3:
        return False
    # Hợp lệ nếu là công thức toán hoặc chứa toán tử/ký hiệu toán rõ ràng
    if "$" in s or re.search(r"[=<>≤≥±∓∞∫∑√^_′']", s):
        return False
    # Hợp lệ nếu là nhãn mục (Giải:, Định lí 1, a), ...)
    if VALID_SHORT_LABEL_RE.match(s):
        return False
    # Hợp lệ nếu là giá trị số có đơn vị
    if re.fullmatch(r"[-+]?\d+([.,]\d+)?(\s*[a-zA-Z%°²³]+)?", s):
        return False
    return True


def _slide_has_visual(s: Dict[str, Any]) -> bool:
    """Kiểm tra slide có hình ảnh, đồ thị, bảng biến thiên hoặc khối 3D đi kèm không."""
    chart_spec = s.get("chart_spec")
    if isinstance(chart_spec, dict) and chart_spec.get("kind") and chart_spec.get("kind") != "none":
        return True
    if s.get("has_3d") or s.get("snapshot_3d_base64"):
        return True
    if s.get("has_image") or s.get("image_assets"):
        return True
    for b in s.get("blocks") or []:
        bd = _to_dict(b)
        if bd.get("block_type") == "FIGURE" or bd.get("kind") == "picture":
            if bd.get("chart") or bd.get("figure_asset") or bd.get("table") or bd.get("asset"):
                return True
        if bd.get("table") or bd.get("chart") or bd.get("figure_asset"):
            return True
    return False


def lint_slide(slide: Union[Dict[str, Any], Any], *, is_ingested_raw: bool = False) -> Dict[str, List[str]]:
    """
    Kiểm tra một slide và trả về {"errors": [...], "warnings": [...]}.
    """
    s = _to_dict(slide)
    errors: List[str] = []
    warnings: List[str] = []

    slide_type = str(s.get("type") or "")
    layout = str(s.get("layout") or s.get("layout_hint") or "")
    activity_type = str(s.get("activity_type") or s.get("role") or "")
    title = (s.get("title") or "").strip()
    bullets = [str(b).strip() for b in (s.get("bullet_points") or []) if str(b).strip()]
    worked_steps = [str(w).strip() for w in (s.get("worked_solution_steps") or []) if str(w).strip()]
    blocks = [_to_dict(b) for b in (s.get("blocks") or [])]

    is_title_slide = slide_type == "TITLE_SLIDE" or layout == "TITLE_ONLY"

    # 1. Kiểm tra slide chuyển mục (S4)
    if not is_title_slide and is_divider_slide(s):
        errors.append("divider_slide: Slide chuyển mục/trang trí rời rạc không có nội dung học thuật")

    for t_line in [title] + bullets:
        if not is_title_slide and DIVIDER_TOKEN_RE.match(t_line.strip()):
            errors.append(f"divider_token: Chứa token chuyển mục rời rạc '{t_line.strip()}'")
            break

    # 2. Kiểm tra phân loại nhầm Khởi động (S2)
    if activity_type == "khoi_dong" or slide_type == "WARM_UP_SLIDE":
        if WARMUP_FORBIDDEN_TITLE_RE.search(title):
            errors.append(f"misclassified_warmup: Slide '{title}' bị gán nhầm làm Khởi động")

    # 3. Kiểm tra khung công thức chứa tên bài học (S3)
    main_latex = (s.get("main_definition_latex") or "").strip()
    if main_latex:
        stripped_text_cmd = re.sub(r"\\text\{[^}]*\}", "", main_latex)
        has_real_math_op = bool(
            re.search(
                r"([=<>≤≥+\-*/^_]|\\(?:int|sum|frac|sqrt|lim|vec|Rightarrow|Leftrightarrow|in|subset|cup|cap))",
                stripped_text_cmd,
            )
        )
        if "(SGK KNTT 12)" in main_latex or (r"\text{" in main_latex and not has_real_math_op):
            errors.append("title_in_formula_box: main_definition_latex chứa tên bài học thay vì công thức toán")
        for issue in check_latex_syntax(f"${main_latex}$" if "$" not in main_latex else main_latex):
            errors.append(issue)

    # 4. Kiểm tra cân bằng $ và cú pháp LaTeX trên toàn bộ văn bản
    all_texts: List[str] = [title] + bullets + worked_steps
    for b in blocks:
        if b.get("content"):
            all_texts.append(str(b["content"]))
        if b.get("text"):
            all_texts.append(str(b["text"]))
        if b.get("formula_latex"):
            fl = str(b["formula_latex"])
            all_texts.append(f"${fl}$" if "$" not in fl else fl)
        if b.get("latex"):
            fl = str(b["latex"])
            all_texts.append(f"${fl}$" if "$" not in fl else fl)

    for txt in all_texts:
        for issue in check_latex_syntax(txt):
            if issue not in errors:
                errors.append(issue)

    # 5. Kiểm tra dòng mảnh vỡ (< 3 từ) và dòng cụt "Giải:" ở cuối slide (S2)
    for b_line in bullets:
        if is_fragment_line(b_line):
            errors.append(f"fragment_line: Dòng mảnh vỡ '{b_line[:40]}'")

    if bullets and DANGLING_SOL_RE.match(bullets[-1]) and not worked_steps:
        errors.append(f"truncated_solution: Slide bị cắt cụt ngay sau '{bullets[-1]}' mà mất phần lời giải")

    # 6. Kiểm tra đề bài "như hình vẽ" nhưng thiếu hình (S5)
    combined_text = " ".join(all_texts)
    if MISSING_VISUAL_RE.search(combined_text) and not _slide_has_visual(s):
        errors.append("missing_visual: Đề bài tham chiếu 'như hình vẽ/đồ thị bên' nhưng không có FIGURE/đồ thị đi kèm")

    # 7. Kiểm tra câu tự luận chứa "Đáp án đúng là" hoặc lặp đáp án trắc nghiệm (S5)
    has_quiz_block = any(b.get("block_type") == "QUIZ" for b in blocks)
    is_quiz_slide = layout == "QUIZ_OPTION" or bool(s.get("quiz_options")) or has_quiz_block
    dap_an_matches = re.findall(r"Đáp\s+án\s+đúng\s+là\s+[A-D]", combined_text, flags=re.I)
    if not is_quiz_slide and dap_an_matches:
        errors.append("essay_with_mcq_answer: Slide tự luận/khái niệm chứa mẫu câu trắc nghiệm 'Đáp án đúng là X'")
    elif len(dap_an_matches) > 1:
        errors.append(f"repeated_mcq_answer: Cụm 'Đáp án đúng là X' bị lặp lại {len(dap_an_matches)} lần trên cùng 1 slide")

    # 8. Kiểm tra các quy tắc của Schema v2 (khi có blocks sư phạm)
    pedagogical_blocks = [b for b in blocks if b.get("block_type")]
    if pedagogical_blocks:
        reveal_orders = sorted({int(b.get("reveal_order", 0)) for b in pedagogical_blocks})
        expected_orders = list(range(len(reveal_orders)))
        if reveal_orders != expected_orders:
            errors.append(f"non_contiguous_reveal_order: reveal_order {reveal_orders} không liên tục từ 0")

        for b in pedagogical_blocks:
            btype = b.get("block_type")
            if btype == "WORKED_STEP" and not b.get("verified", True):
                errors.append(f"unverified_worked_step: Block WORKED_STEP '{b.get('block_id')}' có verified=False")
            has_body = any(
                bool(b.get(k))
                for k in ("content", "formula_latex", "table", "chart", "figure_asset", "quiz")
            )
            if not has_body:
                errors.append(f"empty_block: Block '{b.get('block_id')}' ({btype}) rỗng")
    elif not is_ingested_raw and not is_title_slide:
        # Với slide deck v1 chưa nâng cấp lên blocks, ghi nhận cảnh báo nếu chỉ có bullet_points thuần
        has_structured = bool(
            main_latex
            or worked_steps
            or s.get("quiz_options")
            or _slide_has_visual(s)
        )
        if not has_structured:
            warnings.append("bullets_only_slide: Slide chỉ có danh sách bullet_points (rơi vào lưới 4 hộp ở v1)")

    if not title and not bullets and not blocks:
        errors.append("empty_slide: Slide hoàn toàn rỗng")

    return {"errors": errors, "warnings": warnings}


def lint_deck(
    deck: Union[Dict[str, Any], Any],
    *,
    min_slides: int = 6,
    max_slides: int = 15,
) -> Dict[str, Any]:
    """
    Kiểm tra toàn bộ một SlideDeck và tổng hợp kết quả lint.
    """
    d = _to_dict(deck)
    slides = d.get("slides") or []
    slide_reports = []
    error_counts: Dict[str, int] = {}
    slides_with_errors = 0

    for idx, sl in enumerate(slides, 1):
        res = lint_slide(sl, is_ingested_raw=False)
        if res["errors"]:
            slides_with_errors += 1
            for err in res["errors"]:
                err_code = err.split(":", 1)[0]
                error_counts[err_code] = error_counts.get(err_code, 0) + 1
        slide_reports.append({
            "slide_index": _to_dict(sl).get("slide_index", idx),
            "title": _to_dict(sl).get("title", ""),
            "errors": res["errors"],
            "warnings": res["warnings"],
        })

    deck_errors: List[str] = []
    if not (min_slides <= len(slides) <= max_slides):
        deck_errors.append(
            f"slide_count_out_of_range: Số lượng slide ({len(slides)}) nằm ngoài khoảng [{min_slides}, {max_slides}]"
        )

    total_slides = len(slides)
    clean_slides = total_slides - slides_with_errors
    pass_rate_pct = round((clean_slides * 100.0) / max(1, total_slides), 2)

    return {
        "valid": slides_with_errors == 0 and len(deck_errors) == 0,
        "total_slides": total_slides,
        "clean_slides": clean_slides,
        "slides_with_errors": slides_with_errors,
        "pass_rate_pct": pass_rate_pct,
        "deck_errors": deck_errors,
        "error_counts_by_type": error_counts,
        "slides": slide_reports,
    }
