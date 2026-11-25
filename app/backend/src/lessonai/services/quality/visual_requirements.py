"""Server-signed confirmation of explicit teacher data, never an LLM boolean."""
import math
import time
from typing import NamedTuple
from lessonai.core import signing
from lessonai.core.hashing import canonical, fingerprint  # re-exported for existing callers
from lessonai.services.math.math_expression import parse_expression

_PURPOSE = "visual_confirmation"
_NOT_CONFIRMED = "Dữ kiện hình chưa được xác nhận hoặc đã thay đổi. Cần đối chiếu lại với đề bài."


class VisualError(ValueError):
    code = "visual_needs_review"


class ConfirmationKeyChanged(VisualError):
    code = signing.KeyChanged.code


KEY_CHANGED_MESSAGE = ("Xác nhận dữ kiện hình không còn hiệu lực vì được ký bằng khóa không có trên máy này (tệp khóa đã bị xóa "
                       "hoặc thay, hoặc xác nhận được tạo trên máy khác). Cần đối chiếu với đề bài và xác nhận lại.")


SOURCE_FIELDS = ("title", "subtitle", "bullet_points", "question", "main_definition_latex", "math_formulas", "worked_solution_steps", "blocks", "table_data", "source_refs")
# Problem text and formulas of an Outline Item: `points` in the Dàn ý spec, `bullet_points`/`math_focus` on today's outline items.
ITEM_SOURCE_FIELDS = ("title", "points", "bullet_points", "math_focus")


class Scope(NamedTuple):
    ids: tuple            # What a confirmation is bound to.
    source_fields: tuple  # What its source fingerprint covers.


SCOPES = {"slide": Scope(("deck_id", "slide_id"), SOURCE_FIELDS), "outline_item": Scope(("project_id", "item_id"), ITEM_SOURCE_FIELDS)}


def visual_source(source, fields=SOURCE_FIELDS):
    def prune(value):
        if isinstance(value,dict):return {key:prune(item) for key,item in value.items() if item not in (None,"",[],{})}
        if isinstance(value,list):return [prune(item) for item in value]
        return value
    return prune({key:source[key] for key in fields if source.get(key) not in (None,"",[])})


def requirement_scope(data):
    """A confirmation belongs to one slide, or to one Outline Item of a Bài giảng (project_id)."""
    if data.get("item_id") in (None, ""):
        scope_kind, missing = "slide", "Cần định danh bài và slide trước khi xác nhận dữ kiện"
    elif data.get("slide_id") in (None, ""):
        scope_kind, missing = "outline_item", "Cần định danh Bài giảng và Mục dàn ý trước khi xác nhận dữ kiện"
    else:
        raise VisualError("Mỗi xác nhận chỉ gắn với một slide hoặc một Mục dàn ý")
    scope = {name: str(data.get(name) or "") for name in SCOPES[scope_kind].ids}
    if not all(scope.values()):
        raise VisualError(missing)
    return scope_kind, scope


def _validate_graph_spec(kind, payload):
    expression = payload.get("expression")
    parse_expression(expression)
    operation = payload.get("operation", "function")
    if operation not in {"function", "derivative"}:
        raise VisualError("Chưa hỗ trợ yêu cầu này")
    try:
        xmin = float(payload["x_min"])
        xmax = float(payload["x_max"])
    except (KeyError, TypeError, ValueError):
        raise VisualError("Thiếu khoảng vẽ trục x") from None
    if not (math.isfinite(xmin) and math.isfinite(xmax) and -1e6 <= xmin < xmax <= 1e6):
        raise VisualError("Cửa sổ vẽ không hợp lệ")
    spec = {"kind": kind, "expression": expression, "operation": operation, "x_min": xmin, "x_max": xmax}
    if payload.get("y_min") is not None or payload.get("y_max") is not None:
        try:
            lo, hi = float(payload["y_min"]), float(payload["y_max"])
        except (KeyError, TypeError, ValueError):
            raise VisualError("Cần cả hai giới hạn trục y") from None
        if not (math.isfinite(lo) and math.isfinite(hi) and -1e6 <= lo < hi <= 1e6):
            raise VisualError("Giới hạn trục y không hợp lệ")
        spec.update(y_min=lo, y_max=hi)
    area = payload.get("area")
    if area is not None:
        if not isinstance(area, dict):
            raise VisualError("Cấu hình miền tô không hợp lệ")
        target = str(area.get("target") or "ox").strip()
        if target.lower() != "ox":
            parse_expression(target)
        else:
            target = "ox"
        try:
            a_val = float(area["a"])
            b_val = float(area["b"])
        except (KeyError, TypeError, ValueError):
            raise VisualError("Miền tô cần cận a và b hợp lệ") from None
        if not (math.isfinite(a_val) and math.isfinite(b_val) and xmin <= a_val < b_val <= xmax):
            raise VisualError("Cận miền tô [a; b] phải thỏa x_min <= a < b <= x_max")
        spec["area"] = {"target": target, "a": a_val, "b": b_val}
    return spec


def confirm_requirement(data):
    """Called only by the explicit confirmation UI, not by generation/enrichment."""
    import math as _math  # noqa: F401
    scope_kind, scope = requirement_scope(data)
    if not isinstance(data.get("source", {}), dict):
        raise VisualError("Nguồn dữ kiện không đúng cấu trúc")
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    merged = {**nested, **{k: v for k, v in data.items() if k != "data"}}
    kind = merged.get("kind")
    if kind in {"function_plot", "graph"}:
        spec = _validate_graph_spec(kind, merged)
    elif kind == "bbt":
        from lessonai.services.visuals.workbench_visuals import classify_bbt_family
        expression = merged.get("expression")
        parse_expression(expression)
        family_info = classify_bbt_family(expression)
        spec = {"kind": "bbt", "expression": expression, "family": family_info["family"], "family_label": family_info["family_label"]}
    elif kind in {"geometry", "solid"}:
        from lessonai.services.visuals.geometry_scene import normalize_spec
        spec = {"kind": kind, **normalize_spec(merged)}
    elif kind == "oxyz":
        from lessonai.services.visuals.geometry_scene import normalize_oxyz_spec
        spec = {"kind": "oxyz", **normalize_oxyz_spec(merged)}
    else:
        raise VisualError("Loại hình chưa được hỗ trợ")
    spec["source_fingerprint"] = fingerprint(visual_source(data.get("source") or {}, SCOPES[scope_kind].source_fields))
    record = {"scope": scope_kind, **scope, "spec": spec, "confirmed_at": int(time.time()), "method": "teacher_confirmation"}
    return {"requirement_token": signing.sign(_PURPOSE, record), "requirement": record,
            "spec_fingerprint": fingerprint(spec)}


def checked_requirement(spec):
    nested = spec.get("data") if isinstance(spec.get("data"), dict) else {}
    merged = {**nested, **{k: v for k, v in spec.items() if k != "data"}}
    try:
        record = signing.verify(_PURPOSE, merged.get("requirement_token"), max_length=16000)
    except signing.KeyChanged:
        raise ConfirmationKeyChanged(KEY_CHANGED_MESSAGE) from None
    except signing.InvalidToken:
        raise VisualError(_NOT_CONFIRMED) from None
    try:
        scope_kind, scope = requirement_scope(merged)
        if record["scope"] != scope_kind or any(merged.get(name) != record[name] for name in scope):
            raise ValueError()
        for name, value in record["spec"].items():
            if name in {"family", "family_label"} and name not in merged:
                continue
            if name == "source_fingerprint" and merged.get("source_fingerprint") is None:
                if isinstance(merged.get("source"), dict):
                    actual = fingerprint(visual_source(merged["source"], SCOPES[scope_kind].source_fields))
                    if actual != value:
                        raise ValueError()
                elif scope_kind == "outline_item":
                    continue
                else:
                    raise ValueError()
                continue
            actual = merged.get(name, "function" if name == "operation" else None)
            if actual != value:
                raise ValueError()
        return record
    except (ValueError, TypeError, KeyError):
        raise VisualError(_NOT_CONFIRMED) from None


def checked_slide_requirement(deck,slide,spec):
    record=checked_requirement(spec)
    if spec.get("deck_id")!=deck.get("deck_id") or spec.get("slide_id")!=slide.get("slide_id"):
        raise VisualError("Hình không thuộc slide hiện hành")
    if spec.get("source_fingerprint")!=fingerprint(visual_source(slide)):
        raise VisualError("Đề/giả thiết đã thay đổi sau khi xác nhận hình")
    return record
