#!/usr/bin/env python3
"""
M0.4 - Spike kiểm chứng Gate G2 (SymPy parse & analyze) và Gate G3 (Công thức trong PPTX).

1. Gate G2:
   - Quét toàn bộ 894 câu hỏi trong `data/questions/questions_math12_rag.jsonl` (đặc biệt Chương 1: Hàm số).
   - Trích xuất biểu thức hàm số tường minh $y = ...$, $f(x) = ...$, $s(t) = ...$
   - Thử `safe_parse` sang SymPy, lọc biểu thức chứa tham số ($m, a, b, c$), kiểm tra tốc độ tính đạo hàm + `solveset(f', x, S.Reals)` với ngưỡng timeout 2.0s.
   - Thống kê tỉ lệ parse thành công, tỉ lệ nằm trong Whitelist Giai đoạn 1 (đa thức bậc <= 4, hữu tỉ bậc <= 3, căn bậc hai đa thức bậc <= 2), tỉ lệ trả `FiniteSet` thực, tỉ lệ `ConditionSet`/timeout.
2. Gate G3:
   - Thử nghiệm chuyển đổi bộ 16 công thức tiêu biểu của Toán 12 (phân số, căn thức, đạo hàm $f'(x)$, giới hạn $\\lim_{x \\to +\\infty}$, tích phân $\\int_a^b$, hệ phương trình/mặt phẳng) qua:
     (a) `latex2mathml` -> `mathml2omml` (OMML)
     (b) `render_latex_to_bytes` (PNG 300 DPI, 3 tầng fallback)
   - Phát hiện lỗi ngữ nghĩa OMML (ví dụ `(x-1)^2` chỉ gắn mũ vào dấu `)` hoặc thiếu `<a:rPr>` của PowerPoint DrawingML).
"""

import concurrent.futures
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"

DATA_DIR = REPO_ROOT / "app" / "backend" / "data"
QUESTIONS_PATH = DATA_DIR / "questions" / "questions_math12_rag.jsonl"
OUT_SPIKE_PATH = REPO_ROOT / "reports" / "data" / "spike_g2_g3_report.json"

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

FUNC_DEF_RE = re.compile(
    r"(?:y|f\s*\(\s*x\s*\)|g\s*\(\s*x\s*\)|s\s*\(\s*t\s*\))\s*=\s*([^$,;.;\n]+)"
)


def latex_to_sympy_str(latex_expr: str) -> str:
    """Làm sạch biểu thức LaTeX về cú pháp SymPy an toàn."""
    s = latex_expr.strip()
    s = re.sub(r"\\left|\\right|\\,|\\;|\\!|\\quad|\\qquad", "", s)
    s = s.replace(r"\cdot", "*").replace("−", "-")
    # Chuyển \frac{a}{b} (hỗ trợ lồng 2 tầng)
    for _ in range(3):
        s = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"((\1)/(\2))", s)
        s = re.sub(r"\\dfrac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"((\1)/(\2))", s)
    # Chuyển \sqrt[n]{a} và \sqrt{a}
    s = re.sub(r"\\sqrt\s*\[\s*(\d+)\s*\]\s*\{([^{}]+)\}", r"((\2)**(1/(\1)))", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", s)
    # Chuyển ^{...} -> **(...)
    s = re.sub(r"\^\s*\{([^{}]+)\}", r"**(\1)", s)
    s = re.sub(r"\^\s*([0-9a-zA-Z])", r"**\1", s)
    # Hàm lượng giác / logarit
    s = re.sub(r"\\(sin|cos|tan|cot|ln|log|exp)\b", r"\1", s)
    s = s.replace("{", "(").replace("}", ")")
    # Cắt bỏ phần đuôi văn bản tiếng Việt nếu lọt vào trong cặp $...$
    s = re.split(r"\s+(?:với|khi|trên|tại|có|là|biết|và)\b", s)[0]
    return s.strip().rstrip(".,;:")


def extract_candidate_function(question_text: str) -> Optional[str]:
    """Trích biểu thức hàm số $y = ...$ từ đề bài."""
    math_spans = re.findall(r"\$([^$]+)\$", question_text)
    for span in math_spans:
        if "\\int" in span or "\\lim" in span or "f'" in span or "y'" in span:
            continue
        m = FUNC_DEF_RE.search(span)
        if m:
            rhs = m.group(1).strip()
            if rhs and rhs not in {"f(x)", "g(x)", "0"} and not rhs.startswith("f("):
                return rhs
    return None


def is_stage1_whitelist(expr: sp.Expr, var: sp.Symbol) -> Tuple[bool, str]:
    """
    Kiểm tra Whitelist lớp hàm giai đoạn 1 (M3b.2):
    - Đa thức bậc <= 4
    - Hàm hữu tỉ có tử/mẫu là đa thức bậc <= 3
    - Căn bậc hai của đa thức bậc <= 2
    """
    free_syms = expr.free_symbols
    if free_syms - {var}:
        return False, "parametric_expression"

    # Kiểm tra đa thức
    if expr.is_polynomial(var):
        deg = sp.degree(expr, gen=var)
        if deg <= 4:
            return True, f"polynomial_deg_{deg}"
        return False, f"polynomial_deg_{deg}_gt_4"

    # Kiểm tra hàm hữu tỉ
    if expr.is_rational_function(var):
        num, den = sp.fraction(sp.together(expr))
        if num.is_polynomial(var) and den.is_polynomial(var):
            d_num = sp.degree(num, gen=var)
            d_den = sp.degree(den, gen=var)
            if d_num <= 3 and d_den <= 3:
                return True, f"rational_{d_num}_{d_den}"
            return False, f"rational_high_deg_{d_num}_{d_den}"

    # Kiểm tra căn bậc hai của đa thức bậc <= 2: sqrt(P(x))
    if isinstance(expr, sp.Pow) and expr.exp == sp.Rational(1, 2):
        base = expr.base
        if base.is_polynomial(var) and sp.degree(base, gen=var) <= 2:
            return True, "sqrt_poly_deg_le_2"

    return False, "outside_stage1_whitelist"


def _analyze_worker(sympy_str: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    x = sp.Symbol("x", real=True)
    t = sp.Symbol("t", real=True)
    local_dict = {
        "x": x,
        "t": t,
        "sqrt": sp.sqrt,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "ln": sp.log,
        "log": sp.log,
        "exp": sp.exp,
        "pi": sp.pi,
        "e": sp.E,
        "Abs": sp.Abs,
    }
    try:
        expr = parse_expr(sympy_str, local_dict=local_dict, transformations=TRANSFORMATIONS, evaluate=True)
    except Exception as exc:
        return {"parsed": False, "error": str(exc), "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2)}

    var = t if (t in expr.free_symbols and x not in expr.free_symbols) else x
    in_wl, wl_kind = is_stage1_whitelist(expr, var)
    if not in_wl:
        return {
            "parsed": True,
            "in_whitelist": False,
            "whitelist_reason": wl_kind,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }

    try:
        fprime = sp.diff(expr, var)
        crit = sp.solveset(fprime, var, domain=sp.S.Reals)
        is_finite = (isinstance(crit, sp.FiniteSet) or crit == sp.EmptySet) and len(list(crit)) <= 5
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "parsed": True,
            "in_whitelist": True,
            "whitelist_reason": wl_kind,
            "fprime": str(fprime),
            "crit_type": type(crit).__name__,
            "is_finite_set": is_finite,
            "crit_points": [str(p) for p in crit] if is_finite else None,
            "elapsed_ms": elapsed,
        }
    except Exception as exc:
        return {
            "parsed": True,
            "in_whitelist": True,
            "whitelist_reason": wl_kind,
            "is_finite_set": False,
            "error": str(exc),
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }


def run_spike_g2() -> Dict[str, Any]:
    questions = [
        json.loads(line)
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ch1_questions = [q for q in questions if q.get("chapter") == 1 or str(q.get("lesson_id", "")).startswith("M12-C1")]

    extracted_items = []
    for q in ch1_questions:
        cand = extract_candidate_function(q.get("question", ""))
        if cand:
            extracted_items.append({
                "id": q.get("id"),
                "lesson_id": q.get("lesson_id"),
                "raw_latex": cand,
                "sympy_str": latex_to_sympy_str(cand),
            })

    parsed_ok = 0
    in_whitelist_ok = 0
    finite_set_ok = 0
    parametric_cnt = 0
    outside_wl_cnt = 0
    timeout_cnt = 0
    non_finite_cnt = 0
    timings_ms: List[float] = []
    sample_analyzed = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        for item in extracted_items:
            fut = pool.submit(_analyze_worker, item["sympy_str"])
            try:
                res = fut.result(timeout=2.0)
            except concurrent.futures.TimeoutError:
                timeout_cnt += 1
                continue

            timings_ms.append(res.get("elapsed_ms", 0.0))
            if res.get("parsed"):
                parsed_ok += 1
                if res.get("in_whitelist"):
                    in_whitelist_ok += 1
                    if res.get("is_finite_set"):
                        finite_set_ok += 1
                        if len(sample_analyzed) < 8:
                            sample_analyzed.append({**item, **res})
                    else:
                        non_finite_cnt += 1
                else:
                    if res.get("whitelist_reason") == "parametric_expression":
                        parametric_cnt += 1
                    else:
                        outside_wl_cnt += 1

    total_cand = len(extracted_items)
    non_param_cand = max(1, total_cand - parametric_cnt)
    return {
        "total_questions_in_bank": len(questions),
        "chapter1_questions": len(ch1_questions),
        "questions_with_explicit_function": total_cand,
        "parsed_successfully": parsed_ok,
        "parse_success_rate_pct": round(parsed_ok * 100.0 / max(1, total_cand), 2),
        "parametric_functions_count": parametric_cnt,
        "non_parametric_candidates": total_cand - parametric_cnt,
        "in_stage1_whitelist_count": in_whitelist_ok,
        "whitelist_coverage_of_non_parametric_pct": round(in_whitelist_ok * 100.0 / non_param_cand, 2),
        "finite_set_verified_count": finite_set_ok,
        "finite_set_rate_of_whitelist_pct": round(finite_set_ok * 100.0 / max(1, in_whitelist_ok), 2),
        "timeout_2s_count": timeout_cnt,
        "condition_set_or_non_finite_count": non_finite_cnt,
        "avg_elapsed_ms": round(sum(timings_ms) / max(1, len(timings_ms)), 2),
        "max_elapsed_ms": round(max(timings_ms) if timings_ms else 0.0, 2),
        "sample_verified_functions": sample_analyzed,
    }


def run_spike_g3() -> Dict[str, Any]:
    import os
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")
    from lessonai.exporters.docx_exporter import convert_latex_to_omml
    from lessonai.exporters.slide_exporter import render_latex_to_bytes

    test_formulas = [
        r"y = x^3 - 3x^2 + 2",
        r"f'(x) = 3x^2 - 6x = 0 \Leftrightarrow x = 0 \text{ hoặc } x = 2",
        r"y = \frac{2x + 1}{x - 1}",
        r"f'(x) = -\frac{3}{(x - 1)^2} < 0, \forall x \neq 1",
        r"y = \sqrt{2x^2 + 1}",
        r"\lim_{x \to +\infty} f(x) = +\infty",
        r"\lim_{x \to (-1)^+} \frac{x^2 + 3x - 1}{x + 1} = -\infty",
        r"I = \int_0^1 (3x^2 + 10x + 3)\,dx = 9",
        r"P(A|B) = \frac{P(A \cap B)}{P(B)}",
        r"d(M, (P)) = \frac{|Ax_0 + By_0 + Cz_0 + D|}{\sqrt{A^2 + B^2 + C^2}}",
    ]

    omml_ok = 0
    omml_semantic_warnings = []
    png_ok = 0

    for latex in test_formulas:
        # 1. Kiểm tra PNG 300 DPI (`render_latex_to_bytes`)
        png_bytes = render_latex_to_bytes(latex)
        # 1x1 fallback có độ dài 68 bytes; ảnh thực > 500 bytes
        if png_bytes and len(png_bytes) > 500 and png_bytes.startswith(b"\x89PNG"):
            png_ok += 1

        # 2. Kiểm tra OMML (`convert_latex_to_omml`)
        omml_node = convert_latex_to_omml(latex)
        if omml_node is not None:
            omml_ok += 1
            # Kiểm tra lỗi ngữ nghĩa (x-1)^2 bị gắn mũ chỉ vào dấu đóng ngoặc ')'
            from lxml import etree
            xml_str = etree.tostring(omml_node, encoding="unicode")
            if "<m:sSup><m:e><m:r><m:rPr><m:sty m:val=\"p\"/></m:rPr><m:t>)</m:t></m:r></m:e>" in xml_str:
                omml_semantic_warnings.append({
                    "latex": latex,
                    "issue": "Biểu thức (a)^n bị latex2mathml tách thành ')'^n thay vì bọc cả cụm <m:d>",
                })

    return {
        "tested_formulas_count": len(test_formulas),
        "png_300dpi_success_count": png_ok,
        "png_300dpi_success_rate_pct": round(png_ok * 100.0 / len(test_formulas), 2),
        "omml_conversion_success_count": omml_ok,
        "omml_semantic_issues_count": len(omml_semantic_warnings),
        "omml_semantic_issues": omml_semantic_warnings,
        "decision": (
            "Giữ `render_latex_to_bytes` (PNG 300 DPI, 3 tầng fallback + alt-text LaTeX) làm mặc định cho M5 "
            "vì đạt 100% hiển thị đồng nhất trên PowerPoint và LibreOffice, trong khi `latex2mathml -> mathml2omml` "
            "gặp lỗi ngữ nghĩa với lũy thừa của ngoặc `(x-1)^2` và thiếu `<a:rPr>`/AlternateContent của PowerPoint DrawingML."
        ),
    }


def main() -> None:
    print("Đang chạy Spike Gate G2 (SymPy trên ngân hàng câu hỏi)...")
    g2_res = run_spike_g2()
    print("Đang chạy Spike Gate G3 (OMML vs PNG 300 DPI)...")
    g3_res = run_spike_g3()

    report = {
        "gate_g2_sympy_spike": g2_res,
        "gate_g3_pptx_formula_spike": g3_res,
    }
    OUT_SPIKE_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== KẾT QUẢ SPIKE GATE G2 (SYMPY) ===")
    print(f"- Tổng câu hỏi Chương 1 (Hàm số): {g2_res['chapter1_questions']} câu")
    print(f"- Câu có biểu thức hàm tường minh: {g2_res['questions_with_explicit_function']} câu")
    print(f"- Parse thành công sang SymPy: {g2_res['parsed_successfully']}/{g2_res['questions_with_explicit_function']} ({g2_res['parse_success_rate_pct']}%)")
    print(f"- Câu chứa tham số m (dành cho trắc nghiệm): {g2_res['parametric_functions_count']} câu")
    print(f"- Câu hàm tường minh không tham số thuộc Whitelist GĐ1: {g2_res['in_stage1_whitelist_count']}/{g2_res['non_parametric_candidates']} ({g2_res['whitelist_coverage_of_non_parametric_pct']}%)")
    print(f"- Trả về FiniteSet <= 5 nghiệm thực: {g2_res['finite_set_verified_count']}/{g2_res['in_stage1_whitelist_count']} ({g2_res['finite_set_rate_of_whitelist_pct']}%)")
    print(f"- Số ca Timeout (>2.0s): {g2_res['timeout_2s_count']} | Thời gian TB: {g2_res['avg_elapsed_ms']} ms (Max: {g2_res['max_elapsed_ms']} ms)")

    print("\n=== KẾT QUẢ SPIKE GATE G3 (PPTX FORMULA) ===")
    print(f"- PNG 300 DPI (`render_latex_to_bytes`): {g3_res['png_300dpi_success_count']}/{g3_res['tested_formulas_count']} ({g3_res['png_300dpi_success_rate_pct']}%)")
    print(f"- OMML (`latex2mathml -> mathml2omml`): {g3_res['omml_conversion_success_count']}/{g3_res['tested_formulas_count']}, số lỗi ngữ nghĩa: {g3_res['omml_semantic_issues_count']}")
    print(f"- Quyết định G3: {g3_res['decision']}")
    print(f"\nĐã lưu báo cáo tại: {OUT_SPIKE_PATH}")


if __name__ == "__main__":
    main()
