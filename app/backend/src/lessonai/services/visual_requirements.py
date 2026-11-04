"""Server-signed confirmation of explicit teacher data, never an LLM boolean."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from lessonai.services.math_expression import parse_expression

_KEY = secrets.token_bytes(32)


class VisualError(ValueError):
    code = "visual_needs_review"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


SOURCE_FIELDS = ("title", "subtitle", "bullet_points", "question", "main_definition_latex", "math_formulas", "worked_solution_steps", "blocks", "table_data", "source_refs")


def visual_source(slide):
    def prune(value):
        if isinstance(value,dict):return {key:prune(item) for key,item in value.items() if item not in (None,"",[],{})}
        if isinstance(value,list):return [prune(item) for item in value]
        return value
    return prune({key:slide[key] for key in SOURCE_FIELDS if slide.get(key) not in (None,"",[])})


def confirm_requirement(data):
    """Called only by the explicit confirmation UI, not by generation/enrichment."""
    scope = {name: str(data.get(name) or "") for name in ("deck_id", "slide_id")}
    if not all(scope.values()):
        raise VisualError("Cần định danh bài và slide trước khi xác nhận dữ kiện")
    if not isinstance(data.get("source",{}),dict):
        raise VisualError("Nguồn dữ kiện không đúng cấu trúc")
    kind = data.get("kind")
    if kind == "function_plot":
        expression = data.get("expression")
        parse_expression(expression)
        operation = data.get("operation", "function")
        if operation not in {"function", "derivative"}:
            raise VisualError("Chưa hỗ trợ yêu cầu này")
        spec = {"kind": kind, "expression": expression, "operation": operation,
                "x_min": float(data["x_min"]), "x_max": float(data["x_max"])}
        if not -1e6 <= spec["x_min"] < spec["x_max"] <= 1e6:
            raise VisualError("Cửa sổ vẽ không hợp lệ")
        if data.get("y_min") is not None or data.get("y_max") is not None:
            try:
                lo, hi = float(data["y_min"]), float(data["y_max"])
            except (KeyError, TypeError, ValueError):
                raise VisualError("Cần cả hai giới hạn trục y") from None
            if not -1e6 <= lo < hi <= 1e6:
                raise VisualError("Giới hạn trục y không hợp lệ")
            spec.update(y_min=lo, y_max=hi)
    elif kind in {"arithmetic_sequence","inequality_system"}:
        from lessonai.services.discrete_visuals import normalize
        spec=normalize(data)
    elif kind == "geometry":
        from lessonai.services.geometry_scene import normalize_spec
        spec = {"kind": kind, **normalize_spec(data)}
    else:
        raise VisualError("Loại hình chưa được hỗ trợ")
    spec["source_fingerprint"] = fingerprint(visual_source(data.get("source") or {}))
    record = {**scope, "spec": spec, "confirmed_at": int(time.time()),
              "expires_at": int(time.time()) + 86400, "method": "teacher_confirmation"}
    payload = base64.urlsafe_b64encode(canonical(record).encode()).decode()
    signature = hmac.new(_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return {"requirement_token": f"{payload}.{signature}", "requirement": record,
            "spec_fingerprint": fingerprint(spec)}


def checked_requirement(spec):
    try:
        token = spec.get("requirement_token", "")
        if len(token) > 16000:
            raise ValueError()
        payload, signature = token.split(".")
        expected = hmac.new(_KEY, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        record = json.loads(base64.urlsafe_b64decode(payload))
        if record["expires_at"] < time.time():
            raise ValueError()
        for name in ("deck_id", "slide_id"):
            if spec.get(name) != record[name]:
                raise ValueError()
        for name, value in record["spec"].items():
            actual = spec.get(name, "function" if name == "operation" else None)
            if actual != value:
                raise ValueError()
        return record
    except (ValueError, TypeError, KeyError):
        raise VisualError("Dữ kiện hình chưa được xác nhận, đã thay đổi hoặc đã hết hạn. Cần đối chiếu lại với đề bài.") from None


def checked_slide_requirement(deck,slide,spec):
    record=checked_requirement(spec)
    if spec.get("deck_id")!=deck.get("deck_id") or spec.get("slide_id")!=slide.get("slide_id"):
        raise VisualError("Hình không thuộc slide hiện hành")
    if spec.get("source_fingerprint")!=fingerprint(visual_source(slide)):
        raise VisualError("Đề/giả thiết đã thay đổi sau khi xác nhận hình")
    return record
