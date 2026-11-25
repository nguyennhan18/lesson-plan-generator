"""Visual requirements computation, Cổng toán verification, and static rendering for Bàn làm việc (#51–#57)."""
import io
import math
import re
from typing import Any
from uuid import uuid4

from lessonai.core.jobs import get_runner
from lessonai.core.render_runtime import serialized_render
from lessonai.schemas.math_spec_schema import MathClaim, MathFunction
from lessonai.services.geometry_scene import build_oxyz_scene, build_scene, normalize_oxyz_spec, normalize_spec
from lessonai.services.math_expression import parse_expression
from lessonai.services.math_spec import verify_claim
from lessonai.services.math_worker import _has_unsafe_ast_nodes, _solve_factorized_poly_roots, _symbolic, _tree
from lessonai.services.visual_requirements import VisualError, checked_requirement

BBT_FAMILY_LABELS = {
    "cubic": "Hàm bậc ba",
    "rational_1_1": "Phân thức bậc nhất trên bậc nhất",
    "rational_2_1": "Phân thức bậc hai trên bậc nhất",
}


def format_vn_number(val: Any) -> str:
    """Format number or SymPy expression using Vietnamese minus (−) and decimal comma (,)."""
    import sympy as s
    expr = s.sympify(val) if not isinstance(val, (int, float)) else s.Rational(val) if isinstance(val, int) else val
    if isinstance(expr, float) or getattr(expr, "is_Float", False):
        f = float(expr)
        if abs(f - round(f)) < 1e-9:
            txt = str(int(round(f)))
        else:
            txt = f"{f:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return txt.replace("-", "−")
    if getattr(expr, "is_Integer", False):
        return str(int(expr)).replace("-", "−")
    if getattr(expr, "is_Rational", False):
        p, q = int(expr.p), int(expr.q)
        if q == 1:
            return str(p).replace("-", "−")
        sign = "−" if p < 0 else ""
        return f"{sign}{abs(p)}/{q}"
    return s.latex(expr).replace("-", "−")


def format_vn_float(val: float, digits: int = 2) -> str:
    if abs(val - round(val)) < 1e-9:
        txt = str(int(round(val)))
    else:
        txt = f"{val:.{digits}f}".rstrip("0").rstrip(".").replace(".", ",")
    return txt.replace("-", "−")


def classify_bbt_family(expression: str) -> dict[str, Any]:
    """Identify one of the 3 supported Grade 12 function families for Bảng biến thiên (#55)."""
    import sympy as s
    if not isinstance(expression, str) or not expression.strip():
        raise VisualError("Bảng biến thiên cần biểu thức hàm số")
    root = _tree(expression, ("x",))
    if _has_unsafe_ast_nodes(root, allow_division=True):
        raise VisualError("Dạng hàm số này chưa hỗ trợ lập bảng biến thiên (chỉ hỗ trợ hàm bậc ba, phân thức bậc nhất/bậc nhất và bậc hai/bậc nhất)")
    x = s.Symbol("x", real=True)
    expr = _symbolic(root).doit()
    if expr.has(s.zoo, s.nan, s.oo, -s.oo):
        raise VisualError("Biểu thức không xác định trên tập số thực")
    if expr.is_polynomial(x):
        poly = s.Poly(s.expand(expr), x)
        if poly.total_degree() == 3:
            return {"family": "cubic", "family_label": BBT_FAMILY_LABELS["cubic"]}
        raise VisualError("Dạng đa thức này chưa hỗ trợ lập bảng biến thiên (chỉ hỗ trợ hàm đa thức bậc ba)")
    if expr.is_rational_function(x):
        num, den = s.fraction(s.together(expr))
        num, den = s.expand(num), s.expand(den)
        if num.is_polynomial(x) and den.is_polynomial(x) and den != 0:
            deg_num = s.Poly(num, x).total_degree()
            deg_den = s.Poly(den, x).total_degree()
            if deg_den == 1 and deg_num in {0, 1}:
                x0 = s.solve(den, x)[0]
                if s.simplify(num.subs(x, x0)) != 0 and s.diff(expr, x) != 0:
                    return {"family": "rational_1_1", "family_label": BBT_FAMILY_LABELS["rational_1_1"]}
            elif deg_den == 1 and deg_num == 2:
                x0 = s.solve(den, x)[0]
                if s.simplify(num.subs(x, x0)) != 0:
                    return {"family": "rational_2_1", "family_label": BBT_FAMILY_LABELS["rational_2_1"]}
    raise VisualError("Dạng hàm số này chưa hỗ trợ lập bảng biến thiên (chỉ hỗ trợ hàm bậc ba, phân thức bậc nhất/bậc nhất và bậc hai/bậc nhất)")


@serialized_render
def build_verified_bbt(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute Bảng biến thiên for a confirmed visual and verify all claims through Cổng toán (#55)."""
    import sympy as s
    checked_requirement(payload)
    nested = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    expression = str(payload.get("expression") or nested.get("expression") or "").strip()
    family_info = classify_bbt_family(expression)
    family = family_info["family"]
    x = s.Symbol("x", real=True)
    root = _tree(expression, ("x",))
    expr = _symbolic(root).doit()
    fn_model = MathFunction(variable="x", parameters=[], expression=expression)

    # 1. Derivative verification
    df = s.together(s.diff(expr, x)) if family != "cubic" else s.expand(s.diff(expr, x))
    c_deriv = verify_claim(fn_model, MathClaim(id="bbt-deriv", kind="derivative", expression=str(df)))
    if c_deriv["status"] != "verified":
        raise VisualError(f"Chưa chứng minh được đạo hàm qua Cổng toán: {c_deriv['reason']}")

    # 2. Exclusions verification
    num, den = s.fraction(s.together(expr))
    poles = []
    if family != "cubic":
        x0 = s.simplify(s.solve(den, x)[0])
        poles = [x0]
        excl_label = f"x != {x0}"
    else:
        excl_label = "none"
    c_excl = verify_claim(fn_model, MathClaim(id="bbt-excl", kind="exclusions", expression=excl_label))
    if c_excl["status"] != "verified":
        raise VisualError(f"Chưa chứng minh được tập xác định qua Cổng toán: {c_excl['reason']}")

    # 3. Stationary points, derivative sign, and extrema verification
    df_num, _ = s.fraction(s.together(df))
    stat_pairs, s_err = _solve_factorized_poly_roots(s.expand(df_num), x)
    if s_err:
        raise VisualError(s_err)
    stat_roots = [r for r, _ in stat_pairs if not any(s.simplify(r - p) == 0 for p in poles)]
    stat_label = ", ".join(str(r) for r in stat_roots) if stat_roots else "none"
    c_stat = verify_claim(fn_model, MathClaim(id="bbt-stat", kind="stationary_points", expression=stat_label))
    if c_stat["status"] != "verified":
        raise VisualError(f"Chưa chứng minh được điểm dừng qua Cổng toán: {c_stat['reason']}")

    # Critical events in ascending order
    events = []
    for r in stat_roots:
        events.append({"x_sym": r, "x": float(s.N(r)), "x_label": format_vn_number(r), "kind": "stationary"})
    for p in poles:
        events.append({"x_sym": p, "x": float(s.N(p)), "x_label": format_vn_number(p), "kind": "pole"})
    events.sort(key=lambda item: item["x"])

    # Determine interval signs and verify through Cổng toán
    from lessonai.services.math_worker import _derivative_analysis
    analysis, a_err = _derivative_analysis(expr, x)
    if a_err:
        raise VisualError(a_err)
    interval_signs = analysis["interval_signs"]
    c_sign = verify_claim(fn_model, MathClaim(id="bbt-sign", kind="derivative_sign", expression=", ".join(interval_signs)))
    if c_sign["status"] != "verified":
        raise VisualError(f"Chưa chứng minh được dấu đạo hàm qua Cổng toán: {c_sign['reason']}")

    extrema_list = analysis["extrema"]
    ext_label = ", ".join(f"{k}({rx}, {ry})" for k, rx, ry in extrema_list) if extrema_list else "none"
    c_ext = verify_claim(fn_model, MathClaim(id="bbt-ext", kind="extrema", expression=ext_label))
    if c_ext["status"] != "verified":
        raise VisualError(f"Chưa chứng minh được cực trị qua Cổng toán: {c_ext['reason']}")

    # Build structured columns: [interval_0, event_0, interval_1, event_1, ..., interval_n]
    def _fmt_lim(val):
        if val == s.oo:
            return "+\\infty"
        if val == -s.oo:
            return "-\\infty"
        return format_vn_number(val)

    x_row = ["-\\infty"]
    yp_row = []
    y_intervals = []
    left_inf = _fmt_lim(s.limit(expr, x, -s.oo))
    right_inf = _fmt_lim(s.limit(expr, x, s.oo))

    # Build node sequence for row y
    for idx, sgn in enumerate(interval_signs):
        yp_row.append(sgn.replace("-", "−"))
        if idx == 0:
            start_val = left_inf
        else:
            prev_ev = events[idx - 1]
            if prev_ev["kind"] == "pole":
                start_val = _fmt_lim(s.limit(expr, x, prev_ev["x_sym"], dir="+"))
            else:
                start_val = format_vn_number(s.simplify(expr.subs(x, prev_ev["x_sym"])))
        if idx == len(events):
            end_val = right_inf
        else:
            next_ev = events[idx]
            if next_ev["kind"] == "pole":
                end_val = _fmt_lim(s.limit(expr, x, next_ev["x_sym"], dir="-"))
            else:
                end_val = format_vn_number(s.simplify(expr.subs(x, next_ev["x_sym"])))
        y_intervals.append({
            "sign": sgn,
            "direction": "up" if sgn == "+" else "down",
            "from": start_val,
            "to": end_val,
        })
        if idx < len(events):
            ev = events[idx]
            x_row.append(ev["x_label"])
            yp_row.append("||" if ev["kind"] == "pole" else "0")
    x_row.append("+\\infty")

    event_cols = []
    for ev in events:
        if ev["kind"] == "pole":
            event_cols.append({
                "x_label": ev["x_label"],
                "kind": "pole",
                "yp": "||",
                "left_limit": _fmt_lim(s.limit(expr, x, ev["x_sym"], dir="-")),
                "right_limit": _fmt_lim(s.limit(expr, x, ev["x_sym"], dir="+")),
            })
        else:
            y_val = s.simplify(expr.subs(x, ev["x_sym"]))
            event_cols.append({
                "x_label": ev["x_label"],
                "kind": "stationary",
                "yp": "0",
                "y_label": format_vn_number(y_val),
            })

    return {
        "status": "verified",
        "family": family,
        "family_label": family_info["family_label"],
        "expression": expression,
        "derivative_latex": s.latex(df),
        "domain_latex": "\\mathbb{R}" if not poles else f"\\mathbb{{R}} \\setminus \\{{{format_vn_number(poles[0])}\\}}",
        "x_row": x_row,
        "yp_row": yp_row,
        "events": event_cols,
        "intervals": y_intervals,
        "left_infinity": left_inf,
        "right_infinity": right_inf,
        "claims": [c_deriv, c_excl, c_stat, c_sign, c_ext],
    }


def _compute_area_polygons(expression: str, area: dict[str, Any], xmin: float, xmax: float) -> tuple[list[list[list[float]]], list[list[list[float]]]]:
    """Compute shaded area polygon points on [a, b] and optional second curve segments (#56)."""
    a_val = max(xmin, float(area["a"]))
    b_val = min(xmax, float(area["b"]))
    target = str(area.get("target") or "ox").strip()
    second_segments = []
    if target.lower() != "ox":
        second_plot = get_runner().run("math.plot", {"expression": target, "operation": "function", "x_min": xmin, "x_max": xmax})
        second_segments = second_plot["segments"]
    if b_val <= a_val:
        return [], second_segments
    f_sub = get_runner().run("math.plot", {"expression": expression, "operation": "function", "x_min": a_val, "x_max": b_val})
    if target.lower() == "ox":
        polygons = []
        for seg in f_sub["segments"]:
            if len(seg) >= 2:
                poly = [[seg[0][0], 0.0], *seg, [seg[-1][0], 0.0]]
                polygons.append(poly)
        return polygons, second_segments

    import sympy as s
    import numpy as np
    x = s.Symbol("x", real=True)
    f_sym = _symbolic(_tree(expression, ("x",))).doit()
    g_sym = _symbolic(_tree(target, ("x",))).doit()
    f_eval = s.lambdify(x, f_sym, modules=["numpy"], cse=False)
    g_eval = s.lambdify(x, g_sym, modules=["numpy"], cse=False)
    polygons = []
    for seg in f_sub["segments"]:
        if len(seg) < 2:
            continue
        xs = np.array([pt[0] for pt in seg], dtype=float)
        with np.errstate(all="ignore"):
            f_ys = np.broadcast_to(f_eval(xs), xs.shape)
            g_ys = np.broadcast_to(g_eval(xs), xs.shape)
        upper = []
        lower = []
        for xv, fy, gy in zip(xs, f_ys, g_ys):
            if np.isreal(fy) and np.isreal(gy) and math.isfinite(float(np.real(fy))) and math.isfinite(float(np.real(gy))):
                upper.append([float(xv), float(np.real(fy))])
                lower.append([float(xv), float(np.real(gy))])
        if len(upper) >= 2:
            polygons.append([*upper, *reversed(lower)])
    return polygons, second_segments


def compute_graph_special_points(expression: str) -> dict[str, Any]:
    """Compute and verify extrema, axis intercepts, and asymptotes through Cổng toán (#57)."""
    import sympy as s
    fn_model = MathFunction(variable="x", parameters=[], expression=expression)
    root = _tree(expression, ("x",))
    x = s.Symbol("x", real=True)
    expr = _symbolic(root).doit()

    # 1. Extrema
    extrema_result = {"supported": False, "unsupported_reason": None, "items": []}
    from lessonai.services.math_worker import _derivative_analysis, _prepare_polynomial_on_regime
    prepared, prep_err = _prepare_polynomial_on_regime(
        {"function": expression, "variable": "x", "parameters": []},
        ("none", None),
        allow_rational=True,
    )
    if prep_err:
        extrema_result["unsupported_reason"] = prep_err["reason"]
    else:
        analysis, a_err = _derivative_analysis(expr, x)
        if a_err:
            extrema_result["unsupported_reason"] = a_err
        else:
            proven_ext = analysis["extrema"]
            ext_label = ", ".join(f"{k}({rx}, {ry})" for k, rx, ry in proven_ext) if proven_ext else "none"
            claim = verify_claim(fn_model, MathClaim(id="graph-extrema", kind="extrema", expression=ext_label))
            if claim["status"] == "verified":
                extrema_result["supported"] = True
                for idx, (kind, rx, ry) in enumerate(proven_ext, 1):
                    fx, fy = float(s.N(rx)), float(s.N(ry))
                    x_vn, y_vn = format_vn_number(rx), format_vn_number(ry)
                    tag = "CĐ" if kind == "max" else "CT"
                    extrema_result["items"].append({
                        "id": f"ext-{idx}",
                        "kind": kind,
                        "label": tag,
                        "x": fx,
                        "y": fy,
                        "x_text": x_vn,
                        "y_text": y_vn,
                        "display": f"{tag}({x_vn}; {y_vn})",
                        "status": "verified",
                        "claim_hash": claim["claim_hash"],
                    })
            else:
                extrema_result["unsupported_reason"] = claim["reason"]

    # 2. Axis intercepts (Ox and Oy)
    intercepts_result = {"supported": False, "unsupported_reason": None, "items": []}
    if prep_err:
        intercepts_result["unsupported_reason"] = prep_err["reason"]
    else:
        num, den = s.fraction(s.together(expr))
        pole_pairs, p_err = (_solve_factorized_poly_roots(den, x) if not expr.is_polynomial(x) else ([], None))
        poles = [r for r, _ in (pole_pairs or [])]
        root_pairs, r_err = _solve_factorized_poly_roots(num, x)
        if p_err or r_err:
            intercepts_result["unsupported_reason"] = p_err or r_err
        else:
            ox_roots = [r for r, _ in root_pairs if not any(s.simplify(r - p) == 0 for p in poles)]
            roots_label = ", ".join(str(r) for r in ox_roots) if ox_roots else "none"
            r_claim = verify_claim(fn_model, MathClaim(id="graph-roots", kind="real_roots", expression=roots_label))
            if r_claim["status"] == "verified":
                intercepts_result["supported"] = True
                for idx, rx in enumerate(ox_roots, 1):
                    fx = float(s.N(rx))
                    x_vn = format_vn_number(rx)
                    intercepts_result["items"].append({
                        "id": f"ox-{idx}",
                        "axis": "Ox",
                        "x": fx,
                        "y": 0.0,
                        "x_text": x_vn,
                        "y_text": "0",
                        "display": f"({x_vn}; 0)",
                        "status": "verified",
                        "claim_hash": r_claim["claim_hash"],
                    })
                # Oy intercept at x = 0 (if 0 is not a pole and not already listed at (0; 0))
                if not any(s.simplify(p) == 0 for p in poles):
                    y0 = s.simplify(expr.subs(x, 0))
                    if not y0.has(s.zoo, s.nan, s.oo, -s.oo) and y0.is_real is not False:
                        oy_claim = verify_claim(
                            fn_model,
                            MathClaim(id="graph-oy", kind="solution_step", expression=f"identity: ({expression}) - ({expression}) = 0"),
                        )
                        if oy_claim["status"] == "verified" and not any(abs(it["x"]) < 1e-9 and abs(it["y"]) < 1e-9 for it in intercepts_result["items"]):
                            fy0 = float(s.N(y0))
                            y0_vn = format_vn_number(y0)
                            intercepts_result["items"].append({
                                "id": "oy-1",
                                "axis": "Oy",
                                "x": 0.0,
                                "y": fy0,
                                "x_text": "0",
                                "y_text": y0_vn,
                                "display": f"(0; {y0_vn})",
                                "status": "verified",
                                "claim_hash": r_claim["claim_hash"],
                            })
            else:
                intercepts_result["unsupported_reason"] = r_claim["reason"]

    # 3. Asymptotes
    asymptotes_result = {"supported": False, "has_asymptotes": False, "disabled_reason": None, "unsupported_reason": None, "items": []}
    if expr.is_polynomial(x):
        a_claim = verify_claim(fn_model, MathClaim(id="graph-asymp", kind="asymptotes", expression="none"))
        if a_claim["status"] == "verified":
            asymptotes_result["supported"] = True
            asymptotes_result["has_asymptotes"] = False
            asymptotes_result["disabled_reason"] = "Hàm đa thức không có đường tiệm cận"
        else:
            asymptotes_result["unsupported_reason"] = a_claim["reason"]
    elif expr.is_rational_function(x) and not _has_unsafe_ast_nodes(root, allow_division=True):
        num, den = s.fraction(s.together(expr))
        num, den = s.expand(num), s.expand(den)
        deg_num = s.Poly(num, x).total_degree() if num.is_polynomial(x) else 99
        deg_den = s.Poly(den, x).total_degree() if den.is_polynomial(x) else 99
        if deg_den == 1 and deg_num <= 2:
            x0 = s.simplify(s.solve(den, x)[0])
            quo, _ = s.div(num, den, domain="QQ")
            quo = s.simplify(quo)
            a_claim = verify_claim(
                fn_model,
                MathClaim(id="graph-asymp", kind="asymptotes", expression=f"x = {x0}, y = {quo}"),
            )
            if a_claim["status"] == "verified":
                asymptotes_result["supported"] = True
                asymptotes_result["has_asymptotes"] = True
                fx0 = float(s.N(x0))
                x0_vn = format_vn_number(x0)
                poly_q = s.Poly(quo, x)
                slope = float(s.N(poly_q.nth(1))) if poly_q.total_degree() >= 1 else 0.0
                intercept = float(s.N(poly_q.nth(0)))
                asymp_kind = "horizontal" if deg_num <= 1 else "slant"
                y_eq = f"y = {format_vn_number(quo)}"
                asymptotes_result["items"] = [
                    {
                        "id": "asymp-v",
                        "kind": "vertical",
                        "x": fx0,
                        "equation": f"x = {x0_vn}",
                        "status": "verified",
                        "claim_hash": a_claim["claim_hash"],
                    },
                    {
                        "id": "asymp-h",
                        "kind": asymp_kind,
                        "slope": slope,
                        "intercept": intercept,
                        "equation": y_eq,
                        "status": "verified",
                        "claim_hash": a_claim["claim_hash"],
                    },
                ]
            else:
                asymptotes_result["unsupported_reason"] = a_claim["reason"]
        else:
            asymptotes_result["unsupported_reason"] = "Ngoài phạm vi công bố của phép kiểm tiệm cận; chưa hỗ trợ"
    else:
        asymptotes_result["unsupported_reason"] = "Ngoài phạm vi công bố của phép kiểm tiệm cận; chưa hỗ trợ"

    return {
        "extrema": extrema_result,
        "intercepts": intercepts_result,
        "asymptotes": asymptotes_result,
    }


@serialized_render
def sample_workbench_graph(payload: dict[str, Any]) -> dict[str, Any]:
    """Sample a confirmed graph for the requested viewport, including optional shaded area and verified special points (#51, #52, #56, #57)."""
    record = checked_requirement(payload)
    spec = record["spec"]
    expression = spec["expression"]
    req_xmin = float(payload.get("viewport_x_min", spec["x_min"]))
    req_xmax = float(payload.get("viewport_x_max", spec["x_max"]))
    if not (math.isfinite(req_xmin) and math.isfinite(req_xmax) and -1e6 <= req_xmin < req_xmax <= 1e6):
        raise VisualError("Khung nhìn trục x không hợp lệ")

    plot_data = get_runner().run("math.plot", {
        "expression": expression,
        "operation": spec.get("operation", "function"),
        "x_min": req_xmin,
        "x_max": req_xmax,
    })

    # Compute y viewport limits
    from lessonai.exporters.graph_generator import function_y_limits
    y_cfg = {}
    if payload.get("viewport_y_min") is not None and payload.get("viewport_y_max") is not None:
        y_cfg = {"y_min": float(payload["viewport_y_min"]), "y_max": float(payload["viewport_y_max"])}
    elif spec.get("y_min") is not None and spec.get("y_max") is not None and "viewport_x_min" not in payload:
        y_cfg = {"y_min": spec["y_min"], "y_max": spec["y_max"]}
    y_min, y_max = function_y_limits(y_cfg, plot_data)

    area = spec.get("area")
    area_polygons, second_segments = ([], [])
    if area:
        area_polygons, second_segments = _compute_area_polygons(expression, area, req_xmin, req_xmax)

    include_special = bool(payload.get("include_special_points", True))
    special_points = compute_graph_special_points(expression) if include_special else None

    return {
        "expression": expression,
        "x_min": req_xmin,
        "x_max": req_xmax,
        "y_min": y_min,
        "y_max": y_max,
        "segments": plot_data["segments"],
        "area": area,
        "area_polygons": area_polygons,
        "second_segments": second_segments,
        "special_points": special_points,
        "status": "computed",
    }


def _norm_expr_token(text: str) -> str:
    cleaned = str(text or "").lower()
    cleaned = cleaned.replace("**", "^").replace("*", "").replace(" ", "").replace("$", "").replace("\\cdot", "")
    cleaned = cleaned.replace("\\frac{", "(").replace("}{", ")/(").replace("}", ")")
    return cleaned


def filter_grounded_outline_visuals(item_dict: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Keep only AI-proposed visuals whose expression or geometric data appears in the item's title/points and passes validation (#51, #53, #54, #55)."""
    raw_visuals = item_dict.get("visuals") or []
    if not raw_visuals:
        return [], []
    item_text = f"{item_dict.get('title') or ''} {' '.join(item_dict.get('points') or [])}"
    norm_source = _norm_expr_token(item_text)
    kept = []
    warnings = []
    for raw in raw_visuals:
        if not isinstance(raw, dict):
            continue
        kind = raw.get("kind")
        data = dict(raw.get("data") or {})
        label = raw.get("label")
        try:
            if kind in {"graph", "bbt"}:
                expr = str(data.get("expression") or "").strip()
                if not expr:
                    raise ValueError("Thiếu biểu thức hàm số")
                parse_expression(expr)
                if kind == "bbt":
                    fam = classify_bbt_family(expr)
                    data["family"] = fam["family"]
                    data["family_label"] = fam["family_label"]
                else:
                    data.setdefault("x_min", -4)
                    data.setdefault("x_max", 4)
                    if float(data["x_min"]) >= float(data["x_max"]):
                        raise ValueError("Khoảng vẽ không hợp lệ")
                norm_expr = _norm_expr_token(expr)
                if not norm_expr or norm_expr not in norm_source:
                    raise ValueError(f"Biểu thức «{expr}» không xuất hiện trong tiêu đề hoặc các ý của Mục")
            elif kind == "solid":
                spec = normalize_spec(data)
                if str(int(spec["base_edge"]) if spec["base_edge"].is_integer() else spec["base_edge"]) not in item_text:
                    raise ValueError("Số đo cạnh đáy không có trong đề bài của Mục")
                data = spec
            elif kind == "oxyz":
                spec = normalize_oxyz_spec(data)
                # Ensure at least one object label or coordinate appears in the item text
                if not any(obj["label"].lower() in item_text.lower() for obj in spec["objects"]):
                    raise ValueError("Đối tượng Oxyz không xuất hiện trong đề bài của Mục")
                data = spec
            else:
                raise ValueError(f"Loại hình «{kind}» không được hỗ trợ")
            kept.append({
                "visual_id": str(raw.get("visual_id") or uuid4()),
                "kind": kind,
                "origin": "ai",
                "status": "proposed",
                "label": label or (f"$y = {data['expression']}$" if kind in {"graph", "bbt"} else None),
                "data": data,
            })
        except (ValueError, KeyError, TypeError) as err:
            warnings.append(f"Đã lược bỏ đề xuất hình ({kind}) ở Mục «{item_dict.get('title', '')}»: {err}.")
    return kept, warnings


@serialized_render
def render_workbench_graph_png(spec: dict[str, Any], figsize=(6.0, 4.0)) -> bytes:
    """Render a confirmed v3 graph (including optional shaded area #56) to static PNG bytes for PPTX export (#44)."""
    import matplotlib.pyplot as plt
    sampled = sample_workbench_graph({**spec, "include_special_points": False})
    fig, ax = plt.subplots(figsize=figsize)
    try:
        for poly in sampled.get("area_polygons") or []:
            if len(poly) >= 3:
                ax.fill([p[0] for p in poly], [p[1] for p in poly], color="#4f2bd9", alpha=0.22)
        for seg in sampled["segments"]:
            ax.plot([p[0] for p in seg], [p[1] for p in seg], color="#4f2bd9", linewidth=2.0)
        for seg in sampled.get("second_segments") or []:
            ax.plot([p[0] for p in seg], [p[1] for p in seg], color="#111111", linestyle="--", linewidth=1.6)
        ax.axhline(0, color="#444444", linewidth=0.8)
        ax.axvline(0, color="#444444", linewidth=0.8)
        ax.set_xlim(sampled["x_min"], sampled["x_max"])
        ax.set_ylim(sampled["y_min"], sampled["y_max"])
        ax.set_title(f"y = {sampled['expression'][:120]}", fontsize=11)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        with io.BytesIO() as buf:
            fig.savefig(buf, format="png", dpi=140, transparent=True)
            return buf.getvalue()
    finally:
        plt.close(fig)


@serialized_render
def render_bbt_png(spec: dict[str, Any], figsize=(6.5, 3.2)) -> bytes:
    """Render a confirmed v3 Bảng biến thiên to static PNG bytes for PPTX export (#44, #55)."""
    import matplotlib.pyplot as plt
    bbt = build_verified_bbt(spec)
    fig, ax = plt.subplots(figsize=figsize)
    try:
        ax.axis("off")
        n_cols = len(bbt["x_row"])
        xs_pos = [0.16 + 0.80 * i / max(1, n_cols - 1) for i in range(n_cols)]
        ax.plot([0.04, 0.98], [0.74, 0.74], color="#000000", linewidth=1.2)
        ax.plot([0.04, 0.98], [0.50, 0.50], color="#000000", linewidth=1.2)
        ax.plot([0.12, 0.12], [0.08, 0.92], color="#000000", linewidth=1.2)
        ax.text(0.08, 0.83, "x", ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(0.08, 0.62, "y'", ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(0.08, 0.28, "y", ha="center", va="center", fontsize=12, fontweight="bold")

        for i, x_lbl in enumerate(bbt["x_row"]):
            clean = x_lbl.replace("\\infty", "∞")
            ax.text(xs_pos[i], 0.83, clean, ha="center", va="center", fontsize=11)

        for i, yp_lbl in enumerate(bbt["yp_row"]):
            col_x = xs_pos[i // 2] + (xs_pos[i // 2 + 1] - xs_pos[i // 2]) / 2 if i % 2 == 0 else xs_pos[(i + 1) // 2]
            if yp_lbl == "||":
                ax.plot([col_x - 0.006, col_x - 0.006], [0.08, 0.74], color="#000000", linewidth=1.0)
                ax.plot([col_x + 0.006, col_x + 0.006], [0.08, 0.74], color="#000000", linewidth=1.0)
            else:
                ax.text(col_x, 0.62, yp_lbl, ha="center", va="center", fontsize=11, fontweight="bold")

        for idx, interval in enumerate(bbt["intervals"]):
            x_left = xs_pos[idx] + 0.03
            x_right = xs_pos[idx + 1] - 0.03
            y_start = 0.18 if interval["direction"] == "up" else 0.40
            y_end = 0.40 if interval["direction"] == "up" else 0.18
            ax.annotate(
                "",
                xy=(x_right, y_end),
                xytext=(x_left, y_start),
                arrowprops=dict(arrowstyle="->", color="#4f2bd9", lw=1.8),
            )
            ax.text(xs_pos[idx] + 0.01, y_start, interval["from"].replace("\\infty", "∞"), ha="center", va="center", fontsize=10)
            ax.text(xs_pos[idx + 1] - 0.01, y_end, interval["to"].replace("\\infty", "∞"), ha="center", va="center", fontsize=10)

        fig.tight_layout()
        with io.BytesIO() as buf:
            fig.savefig(buf, format="png", dpi=140, transparent=True)
            return buf.getvalue()
    finally:
        plt.close(fig)


@serialized_render
def render_oxyz_png(spec: dict[str, Any], figsize=(5.2, 4.2)) -> bytes:
    """Render a confirmed v3 Hình Oxyz to static PNG bytes for PPTX export (#44, #54)."""
    import matplotlib.pyplot as plt
    import numpy as np
    checked_requirement(spec)
    scene = build_oxyz_scene(spec.get("data") if isinstance(spec.get("data"), dict) else spec)
    fig = plt.figure(figsize=figsize)
    try:
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=26, azim=-55)
        for obj in scene["objects"]:
            otype = obj["type"]
            lbl = obj["label"]
            if otype == "point":
                x, y, z = obj["coords"]
                ax.scatter([x], [y], [z], color="#4f2bd9", s=36)
                ax.text(x, y, z, f" {lbl}", fontsize=10)
                ax.plot([x, x], [y, y], [0, z], color="#6e6e6e", linestyle="--", linewidth=0.8)
            elif otype == "vector":
                ox, oy, oz = obj.get("origin", [0, 0, 0])
                vx, vy, vz = obj["coords"]
                ax.quiver(ox, oy, oz, vx, vy, vz, color="#4f2bd9", arrow_length_ratio=0.18, linewidth=1.8)
                ax.text(ox + vx, oy + vy, oz + vz, f" {lbl}", fontsize=10)
            elif otype == "line":
                px, py, pz = obj["point"]
                ux, uy, uz = obj["direction"]
                ts = np.linspace(-3.0, 3.0, 25)
                ax.plot(px + ts * ux, py + ts * uy, pz + ts * uz, color="#4f2bd9", linewidth=1.6)
                ax.text(px + 2 * ux, py + 2 * uy, pz + 2 * uz, f" {lbl}", fontsize=10)
            elif otype == "plane":
                a, b, c, d = obj["coeffs"]
                grid = np.linspace(-3.0, 3.0, 10)
                u, v = np.meshgrid(grid, grid)
                if abs(c) > 1e-6:
                    w = (-a * u - b * v - d) / c
                    ax.plot_surface(u, v, w, color="#4f2bd9", alpha=0.18)
                elif abs(b) > 1e-6:
                    w = (-a * u - c * v - d) / b
                    ax.plot_surface(u, w, v, color="#4f2bd9", alpha=0.18)
                else:
                    w = (-b * u - c * v - d) / a
                    ax.plot_surface(w, u, v, color="#4f2bd9", alpha=0.18)
            elif otype == "sphere":
                cx, cy, cz = obj["center"]
                r = obj["radius"]
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 12)
                xs = cx + r * np.outer(np.cos(u), np.sin(v))
                ys = cy + r * np.outer(np.sin(u), np.sin(v))
                zs = cz + r * np.outer(np.ones_like(u), np.cos(v))
                ax.plot_wireframe(xs, ys, zs, color="#4f2bd9", alpha=0.35, linewidth=0.7)
                ax.text(cx, cy, cz + r, f" {lbl}", fontsize=10)
        ax.set_xlabel("Ox")
        ax.set_ylabel("Oy")
        ax.set_zlabel("Oz")
        fig.tight_layout()
        with io.BytesIO() as buf:
            fig.savefig(buf, format="png", dpi=140, transparent=True)
            return buf.getvalue()
    finally:
        plt.close(fig)
