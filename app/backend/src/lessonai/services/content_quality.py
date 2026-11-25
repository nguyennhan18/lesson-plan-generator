"""Content acceptance is distinct from JSON validity and render success."""
import re
import time
from functools import lru_cache
from lessonai.services.math_worker import verify_equality
from lessonai.services.math_expression import parse_expression
from lessonai.services.visual_requirements import fingerprint, checked_requirement, visual_source

MATH = re.compile(r"\$\$?(.*?)\$\$?|\\\((.*?)\\\)|\\\[(.*?)\\\]", re.S)


def math_fields(slide):
    for field in ("main_definition_latex", "math_formulas", "bullet_points", "worked_solution_steps", "teacher_note", "title", "subtitle", "key_message", "question", "target_outcome", "blocks", "table_data"):
        yield from _walk(slide.get(field), field, field in {"main_definition_latex", "math_formulas"})
    for index, option in enumerate(slide.get("quiz_options") or []):
        # False distractors are intentional; the explanation still needs review.
        if option.get("is_correct"):
            yield from _walk(option.get("text"), f"quiz_options[{index}].text")
        yield from _walk(option.get("distractor_rationale"), f"quiz_options[{index}].distractor_rationale")


def _walk(value, path, raw=False):
    if isinstance(value, list):
        for i, item in enumerate(value):
            yield from _walk(item, f"{path}[{i}]", raw)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in {"id", "source", "source_ref", "image", "image_base64", "url"}:
                yield from _walk(item, f"{path}.{key}", raw or key in {"latex", "expression"})
    elif isinstance(value, str) and value.strip():
        matches = list(MATH.finditer(value))
        if matches:
            for match in matches:
                yield path, next(group for group in match.groups() if group is not None)
        elif raw or re.fullmatch(r"[\s\d.+*/()^=\-]+", value):
            yield path, value


@lru_cache(maxsize=256)
def check_formula(formula):
    pieces = formula.strip().strip("$").split("=")
    if len(pieces) != 2 or not all(p.strip() for p in pieces):
        return {"status": "unverified", "reason": "Chưa xác minh mệnh đề/biểu thức này"}
    try:
        trees = [parse_expression(p, symbols=("x", "a", "b"), syntax="latex") for p in pieces]
        if any(tree.symbols for tree in trees):
            # An equation to solve is not an identity. Never label it false by guessing intent.
            return {"status": "unverified", "reason": "Cần xác định vai trò và điều kiện của đẳng thức có biến"}
    except ValueError as error:
        return {"status": "unverified", "reason": str(error)}
    return verify_equality(*pieces, syntax="latex")


def evaluate_deck(deck):
    issues, checks = [], []
    deadline = time.monotonic() + 10
    slides = deck.get("slides") or []
    if not str(deck.get("presentation_title") or "").strip():
        issues.append({"field":"presentation_title","severity":"error","message":"Thiếu tên bài giảng"})
    if not slides:
        issues.append({"field": "slides", "severity": "error", "message": "Bộ slide rỗng"})
    for index, slide in enumerate(slides):
        sid = slide.get("slide_id") or str(index)
        def issue(field, message, severity="error"):
            issues.append({"slide_id": sid, "slide_index": index + 1, "field": field,
                           "severity": severity, "message": message})
        if not str(slide.get("title") or "").strip():
            issue("title", "Thiếu tiêu đề")
        if slide.get("layout") == "TWO_COLUMN" and not slide.get("worked_solution_steps"):
            issue("worked_solution_steps", "Thiếu bước giải cho bố cục bài giải")
        from lessonai.services.content_blocks import block_errors
        for field, message in block_errors(slide):
            issue(field, message)
        options = slide.get("quiz_options") or []
        if slide.get("layout") == "QUIZ_OPTION" or options:
            if len(options) != 4 or len({o.get("label") for o in options}) != 4 or sum(bool(o.get("is_correct")) for o in options) != 1:
                issue("quiz_options", "Câu hỏi một đáp án cần 4 lựa chọn riêng biệt và đúng 1 đáp án")
            if any(not o.get("text") or (not o.get("is_correct") and not o.get("distractor_rationale")) for o in options):
                issue("quiz_options", "Thiếu nội dung lựa chọn hoặc giải thích phương án sai")
        for assertion in slide.get("math_assertions") or []:
            if len(checks)>=100 or time.monotonic()>deadline:
                issue("math_assertions","Vượt ngân sách kiểm định","warning");break
            if not isinstance(assertion,dict):
                issue("math_assertions","Mệnh đề không đúng cấu trúc");continue
            if assertion.get("role") != "identity":
                issue("math_assertions", "Vai trò mệnh đề chưa được hỗ trợ", "warning")
                continue
            result = verify_equality(assertion.get("lhs", ""), assertion.get("rhs", ""), symbols=tuple(assertion.get("symbols", ["x","a","b"])), syntax=assertion.get("syntax","expression"))
            checks.append({"slide_id":sid,"field":"math_assertions",**result})
            if result["status"]!="verified":
                issue("math_assertions",result["reason"],"error" if result["status"]=="failed" else "warning")
        for path, formula in math_fields(slide):
            if len(checks) >= 100 or time.monotonic() > deadline:
                issue(path, "Vượt ngân sách kiểm định; cần chia nhỏ bộ bài", "warning")
                break
            result = check_formula(formula)
            checks.append({"slide_id": sid, "field": path, "formula": formula, **result})
            if result["status"] != "verified":
                issue(path, result["reason"], "error" if result["status"] == "failed" else "warning")
        for field, required in (("chart_spec", bool(slide.get("chart_spec") and slide["chart_spec"].get("kind") not in (None, "none"))),
                                ("scene_spec", bool(slide.get("has_3d")))):
            if required:
                try:
                    spec = slide.get(field) or {}
                    if spec.get("deck_id") != deck.get("deck_id") or spec.get("slide_id") != sid:
                        raise ValueError("Hình chưa gắn với bài/slide hiện hành")
                    checked_requirement(spec)
                    if spec.get("source_fingerprint") != fingerprint(visual_source(slide)):
                        raise ValueError("Nội dung đề/giả thiết đã đổi sau lần xác nhận hình")
                except ValueError as error:
                    issue(field, str(error), "error")
        # Prose, pedagogical flow and source accuracy are not proven by arithmetic checks.
        issue("content", "Cần giáo viên duyệt đề, giả thiết, nguồn và tiến trình bài dạy", "warning")
    for index, entry in enumerate(issues):
        entry["issue_id"] = fingerprint({"issue": entry, "position": index})
    status = "blocked" if any(i["severity"] == "error" for i in issues) else "needs_review"
    return {"status": status, "issues": issues, "checks": checks,
            "content_fingerprint": fingerprint(content_snapshot(deck)),
            "scope": "Đẳng thức số học; hình có xác nhận dữ kiện. Văn xuôi và sư phạm cần giáo viên duyệt."}


def content_snapshot(deck):
    ignored = {"quality_report", "review_token", "chart_image_base64", "formula_image_base64",
               "snapshot_3d_base64", "snapshot_3d", "chart_render_status", "chart_render_error", "has_chart"}
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in ignored}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean(deck)
