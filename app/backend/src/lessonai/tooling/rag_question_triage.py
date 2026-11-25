"""Conservative, explainable triage for RAG question candidates.

This module does not approve, edit, or delete source data.  It only produces
evidence for a human reviewer.  ``auto_pass`` is deliberately unavailable
until an independent-solution checker is supplied by the caller.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional

import sympy as sp


TRIAGE_SCHEMA_VERSION = "1.0"
MACHINE_UNCHECKABLE = "machine_uncheckable"
NEEDS_TEACHER_REVIEW = "needs_teacher_review"
EXCLUDE_FROM_BATCH = "exclude_from_batch"


def _content_hash(question: Dict[str, Any]) -> str:
    material = "\n".join(str(question.get(k, "")) for k in ("id", "question", "answer", "solution", "choices"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _latex_to_sympy(expression: str) -> sp.Expr:
    """Parse the deliberately small rational-function subset used by v1."""
    text = expression.strip().strip("$")
    text = text.replace("\\left", "").replace("\\right", "")
    # Repeatedly lower simple \frac{numerator}{denominator} expressions.
    fraction = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
    while fraction.search(text):
        text = fraction.sub(r"(\1)/(\2)", text)
    text = text.replace("^", "**").replace("{", "(").replace("}", ")")
    text = re.sub(r"\\[,!; ]", "", text)
    if "\\" in text or not re.fullmatch(r"[0-9xX+*/().\-\s]+", text):
        raise ValueError("Biểu thức chứa cú pháp ngoài phạm vi hàm phân thức v1")
    return sp.cancel(sp.sympify(text, locals={"x": sp.Symbol("x", real=True)}))


def _extract_function(question_text: str) -> Optional[str]:
    for segment in re.findall(r"\$([^$]+)\$", question_text):
        if "=" in segment and ("\\frac" in segment or "/" in segment):
            return segment.split("=", 1)[1].strip()
    return None


def _choice_value(question: Dict[str, Any]) -> Optional[str]:
    selected = str(question.get("answer", "")).strip()
    for choice in question.get("choices") or []:
        if str(choice).lstrip().startswith(f"{selected}."):
            return str(choice).split(".", 1)[1].strip().rstrip(";.").strip().strip("$")
    return None


def _reason(check_type: str, status: str, expected: Any, derived: Any, discrepancy: Optional[str] = None) -> Dict[str, Any]:
    return {
        "check_type": check_type,
        "status": status,
        "expected": expected,
        "derived": derived,
        "discrepancy": discrepancy,
    }


def _is_nonnegative_rational(function: sp.Expr) -> bool:
    """Recognize only rational functions whose factored numerator/method are even powers.

    This is intentionally narrower than general inequality proving: a false
    negative produces a review item, while a false positive could incorrectly
    certify a source candidate.
    """
    numerator, denominator = sp.fraction(sp.cancel(function))
    numerator_coeff, numerator_factors = sp.factor_list(numerator)
    denominator_coeff, denominator_factors = sp.factor_list(denominator)
    coefficient = sp.Rational(numerator_coeff, denominator_coeff)
    return bool(
        coefficient >= 0
        and all(exponent % 2 == 0 for _, exponent in numerator_factors)
        and all(exponent % 2 == 0 for _, exponent in denominator_factors)
    )


def triage_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """Triage one multiple-choice rational-function question without mutation."""
    text = str(question.get("question", ""))
    result: Dict[str, Any] = {
        "schema_version": TRIAGE_SCHEMA_VERSION,
        "source": {"id": question.get("id"), "lesson_id": question.get("lesson_id")},
        "content_hash": _content_hash(question),
        "triage_status": NEEDS_TEACHER_REVIEW,
        "reason_category": "machine_parse",
        "checks": [],
    }
    expression = _extract_function(text)
    if not expression:
        result["checks"].append(_reason("rational_function", "not_checked", None, None, "Không trích được hàm phân thức có định dạng LaTeX hỗ trợ."))
        return result
    try:
        function = _latex_to_sympy(expression)
    except (sp.SympifyError, ValueError, TypeError) as exc:
        result["checks"].append(_reason("rational_function", "parse_error", expression, None, str(exc)))
        return result

    x = sp.Symbol("x", real=True)
    denominator = sp.denom(function)
    exclusions = sorted((str(v) for v in sp.solveset(denominator, x, domain=sp.S.Reals)), key=str)
    solution = str(question.get("solution", ""))
    domain_claim = re.search(r"D\s*=\s*([^$]+)", solution)
    claim = domain_claim.group(1).strip().rstrip(".") if domain_claim else ""
    plain_reals = claim in (r"\mathbb{R}", "ℝ")
    excluded_claim = re.fullmatch(r"(?:\\mathbb\{R\}|ℝ)\s*(?:\\setminus|∖)\s*\\?\{\s*([^{}]+?)\s*\\?\}", claim)
    claimed_points = sorted(p.strip() for p in excluded_claim.group(1).rstrip("\\").split(";")) if excluded_claim else None
    if exclusions and plain_reals:
        result["checks"].append(_reason(
            "domain", "mismatch", "Tập xác định trong lời giải không được gồm nghiệm mẫu số.",
            {"excluded_x": exclusions}, f"Lời giải ghi R nhưng phải loại x = {', '.join(exclusions)}.",
        ))
    elif claimed_points == exclusions or (plain_reals and not exclusions):
        result["checks"].append(_reason("domain", "checked", "Không gồm nghiệm mẫu số.", {"excluded_x": exclusions}))
    else:
        result["checks"].append(_reason("domain", "not_checked", claim, {"excluded_x": exclusions}, "Chưa đối chiếu được miền xác định đã khai báo."))

    asks_minimum = "giá trị nhỏ nhất" in text.lower() and "trên đoạn" not in text.lower() and "trên khoảng" not in text.lower()
    if asks_minimum:
        derivative = sp.diff(function, x)
        critical = [v for v in sp.solveset(derivative, x, domain=sp.S.Reals) if denominator.subs(x, v) != 0]
        values = [(v, sp.simplify(function.subs(x, v))) for v in critical]
        if _is_nonnegative_rational(function) and values:
            minimum = min(values, key=lambda item: float(item[1]))
            answer_value = _choice_value(question)
            expected = str(minimum[1])
            if answer_value != expected:
                result["checks"].append(_reason(
                    "global_minimum", "mismatch", answer_value,
                    {"minimum": expected, "at_x": str(minimum[0])},
                    "Đáp án được chọn không khớp giá trị nhỏ nhất SymPy suy ra.",
                ))
            else:
                result["checks"].append(_reason("global_minimum", "checked", answer_value, {"minimum": expected, "at_x": str(minimum[0])}))
        else:
            result["checks"].append(_reason("global_minimum", "not_checked", None, None, "Không chứng minh được GTNN toàn cục an toàn trong phạm vi v1."))

    mismatches = [check for check in result["checks"] if check["status"] == "mismatch"]
    if mismatches:
        result["triage_status"] = EXCLUDE_FROM_BATCH
        result["reason_category"] = "mathematical_verification"
    else:
        # A clean machine check is not an approval: independent solving and human sampling remain required.
        result["triage_status"] = NEEDS_TEACHER_REVIEW
        result["reason_category"] = "awaiting_independent_solution"
    return result


def summarize(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(results)
    by_status: Dict[str, int] = {}
    for row in rows:
        status = row["triage_status"]
        by_status[status] = by_status.get(status, 0) + 1
    return {"total": len(rows), "by_triage_status": by_status}
