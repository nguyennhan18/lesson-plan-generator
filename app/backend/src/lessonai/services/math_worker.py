"""Only this isolated worker constructs symbolic expressions from checked trees."""
import math
from lessonai.services.math_expression import parse_expression, ExpressionError


def _symbolic(node):
    import sympy as s
    args = [_symbolic(c) for c in node.children]
    if node.kind == "number":
        return s.Rational(node.value)
    if node.kind == "symbol":
        return s.Symbol(node.value, real=True)
    if node.kind == "constant":
        return {"pi": s.pi, "E": s.E}[node.value]
    if node.kind == "unary":
        return args[0] if node.value == "+" else s.Mul(-1, args[0], evaluate=False)
    if node.kind == "binary":
        a, b = args
        return {"+": lambda: s.Add(a, b, evaluate=False),
                "-": lambda: s.Add(a, s.Mul(-1, b, evaluate=False), evaluate=False),
                "*": lambda: s.Mul(a, b, evaluate=False),
                "/": lambda: s.Mul(a, s.Pow(b, -1, evaluate=False), evaluate=False),
                "^": lambda: s.Pow(a, b, evaluate=False)}[node.value]()
    functions = {"sin": s.sin, "cos": s.cos, "tan": s.tan, "log": s.log,
                 "exp": s.exp, "sqrt": s.sqrt, "Abs": s.Abs}
    return functions[node.value](*args, evaluate=False)


def _tree(source, symbols=("x",), syntax="expression"):
    return parse_expression(source, symbols=symbols, syntax=syntax).root


def _domain(node, variable, window):
    """Intersect original subexpressions before simplification can erase holes."""
    import sympy as s
    from sympy.calculus.util import continuous_domain
    domain = continuous_domain(_symbolic(node), variable, window)
    for child in node.children:
        domain = s.Intersection(domain, _domain(child, variable, window))
    if node.kind == "binary" and node.value == "/":
        excluded = s.solveset(_symbolic(node.children[1]), variable, domain=window)
        if excluded.has(s.ConditionSet):
            raise ValueError("Chưa xác định được miền của mẫu số")
        domain -= excluded
    return domain


def _plot(payload):
    import sympy as s
    import numpy as np
    expression = payload["expression"]
    root = _tree(expression)
    x = s.Symbol("x", real=True)
    original = _symbolic(root)
    operation = payload.get("operation", "function")
    if operation not in {"function", "derivative"}:
        raise ValueError("Chỉ hỗ trợ hàm gốc hoặc đạo hàm")
    target = s.diff(original, x) if operation == "derivative" else original
    xmin, xmax = float(payload["x_min"]), float(payload["x_max"])
    if not all(map(math.isfinite, [xmin, xmax])) or not -1e6 <= xmin < xmax <= 1e6:
        raise ValueError("Khoảng vẽ không hợp lệ")
    window = s.Interval(xmin, xmax)
    domain = _domain(root, x, window)
    domain = s.Intersection(domain, s.calculus.util.continuous_domain(target, x, window)).doit()
    intervals = list(domain.args) if isinstance(domain, s.Union) else [domain]
    if len(intervals) > 64:
        raise ValueError("Quá nhiều khoảng liên tục trong cửa sổ vẽ")
    # lambdify only receives constructors from the checked tree and fixed modules.
    evaluate = s.lambdify(x, target, modules=["numpy"], cse=False)
    segments = []
    total = 0
    for interval in intervals:
        if interval is s.EmptySet:
            continue
        if not isinstance(interval, s.Interval):
            raise ValueError("Miền xác định này chưa được hỗ trợ")
        lo, hi = float(interval.start), float(interval.end)
        delta = max((hi - lo) * 1e-5, 1e-9)
        lo += delta if interval.left_open else 0
        hi -= delta if interval.right_open else 0
        if hi <= lo:
            continue
        count = min(400, max(16, int(1600 * (hi - lo) / (xmax - xmin))))
        if total + count > 2000:
            raise ValueError("Vượt ngân sách lấy mẫu")
        total += count
        xs = np.linspace(lo, hi, count)
        with np.errstate(all="ignore"):
            ys = np.broadcast_to(evaluate(xs), xs.shape)
        segment = []
        for a, b in zip(xs, ys):
            if np.isreal(b) and math.isfinite(float(np.real(b))):
                segment.append([float(a), float(np.real(b))])
            elif segment:
                segments.append(segment)
                segment = []
        if segment:
            segments.append(segment)
    if not segments:
        raise ValueError("Không có điểm thực trong khoảng vẽ")
    return {"segments": segments, "expression": str(target), "domain": str(domain),
            "operation": operation, "status": "computed"}


def _verify(payload):
    import sympy as s
    symbols = tuple(payload.get("symbols", ("x", "a", "b")))
    if len(symbols) > 3:
        return {"status": "unverified", "reason": "Tối đa ba ký hiệu"}
    roots = [_tree(payload[key], symbols, payload.get("syntax", "expression"))
             for key in ("lhs", "rhs")]
    left, right = map(_symbolic, roots)
    variables = sorted(left.free_symbols | right.free_symbols, key=str)
    if not variables:
        difference = s.simplify(left - right)
        if difference.has(s.zoo, s.nan, s.oo, -s.oo) or not difference.is_real:
            return {"status": "unverified", "reason": "Biểu thức không xác định trên số thực"}
        return {"status": "verified" if difference == 0 else "failed", "reason": "Đẳng thức số học"}
    if all(expr.is_polynomial(*variables) for expr in (left, right)):
        if any(s.Poly(s.expand(expr.doit()), *variables).total_degree() > 8 for expr in (left, right)):
            return {"status": "unverified", "reason": "Bậc đa thức ngoài phạm vi"}
        return {"status": "verified" if s.expand(left - right) == 0 else "failed",
                "reason": "Đồng nhất thức đa thức trên các biến thực"}
    if len(variables) == 1 and all(expr.is_rational_function(*variables) for expr in (left, right)):
        domains = [_domain(root, variables[0], s.S.Reals) for root in roots]
        if domains[0] != domains[1]:
            return {"status": "unverified", "reason": "Hai biểu thức khác miền xác định"}
        return {"status": "verified" if s.cancel(left - right) == 0 else "failed",
                "reason": f"Đồng nhất thức trên miền {domains[0]}"}
    return {"status": "unverified", "reason": "Ngoài phạm vi kiểm chứng hiện tại"}


def _derivative(payload):
    """Prove a derivative label by exact polynomial or rational identity; sampling is never proof."""
    import sympy as s
    variable = payload["variable"]
    parameters = payload.get("parameters", [])
    symbols = tuple([variable, *parameters])
    if len(symbols) > 3:
        return {"status": "unverified", "reason": "Tối đa ba ký hiệu"}
    fn_root = _tree(payload["function"], symbols)
    lbl_root = _tree(payload["label"], symbols)
    function, label = _symbolic(fn_root), _symbolic(lbl_root)
    if any(expr.doit().has(s.zoo, s.nan, s.oo, -s.oo) for expr in (function, label)):
        return {"status": "unverified", "reason": "Biểu thức không xác định trên số thực"}
    variables = sorted(function.free_symbols | label.free_symbols, key=str)
    x_sym = s.Symbol(variable, real=True)
    if all(expr.is_polynomial(*variables) for expr in (function, label)):
        if any(variables and s.Poly(s.expand(expr.doit()), *variables).total_degree() > 8
               for expr in (function, label)):
            return {"status": "unverified", "reason": "Tổng bậc đa thức ngoài phạm vi (tối đa 8, tính cả tham số)"}
        derivative = s.diff(function.doit(), x_sym)
        if s.expand(derivative - label.doit()) == 0:
            return {"status": "verified", "reason": "Đạo hàm ký hiệu trùng nhãn trên mọi giá trị thực"}
        return {"status": "failed", "reason": f"Đạo hàm đúng là {s.expand(derivative)}"}
    if not parameters and not _has_unsafe_ast_nodes(fn_root, allow_division=True) and not _has_unsafe_ast_nodes(lbl_root, allow_division=True):
        fn_doit, lbl_doit = function.doit(), label.doit()
        if fn_doit.is_rational_function(x_sym) and lbl_doit.is_rational_function(x_sym):
            num, den = s.fraction(s.together(fn_doit))
            if den.is_polynomial(x_sym) and num.is_polynomial(x_sym) and s.expand(den) != 0:
                if s.Poly(num, x_sym).total_degree() <= 4 and s.Poly(den, x_sym).total_degree() <= 2:
                    derivative = s.diff(fn_doit, x_sym)
                    if s.cancel(derivative - lbl_doit) == 0:
                        return {"status": "verified", "reason": "Đạo hàm phân thức hữu tỉ trùng nhãn trên miền xác định"}
                    return {"status": "failed", "reason": f"Đạo hàm đúng là {s.together(derivative)}"}
    return {"status": "unverified", "reason": "Ngoài phạm vi: chỉ kiểm đạo hàm của đa thức hoặc phân thức hữu tỉ bậc thấp"}


_EMPTY_TOKENS = {"none", "empty", "[]", "∅", "khong co", "không có"}


def _has_unsafe_ast_nodes(node, *, allow_division=False):
    if node.kind == "function":
        return True
    if node.kind == "binary":
        if node.value == "/" and not allow_division:
            return True
        if node.value == "^":
            right = node.children[1]
            if right.kind != "number" or "." in right.value or int(right.value) < 0:
                return True
    return any(_has_unsafe_ast_nodes(child, allow_division=allow_division) for child in node.children)


def _collect_denominators(node):
    denoms = []
    if node.kind == "binary" and node.value == "/":
        denoms.append(node.children[1])
    for child in node.children:
        denoms.extend(_collect_denominators(child))
    return denoms


def _split_top_level(text, sep=","):
    parts = []
    depth = 0
    current = []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _parse_regime_and_body(label, parameters):
    import re
    raw = label.strip()
    if ":" in raw:
        head, body = raw.split(":", 1)
        head = head.strip()
        if not parameters:
            return ("none", None), body.strip()
        param = parameters[0]
        m = re.fullmatch(rf"{re.escape(param)}\s*(<|>|==|=)\s*0", head)
        if m:
            op = "=" if m.group(1) in {"=", "=="} else m.group(1)
            return (op, param), body.strip()
        return ("unsupported", head), body.strip()
    if parameters:
        return ("missing", parameters[0]), raw
    return ("none", None), raw


def _prepare_polynomial_on_regime(payload, regime_info, *, allow_rational=False):
    import sympy as s
    variable = payload["variable"]
    parameters = payload.get("parameters", [])
    if len(parameters) > 1:
        return None, {"status": "unverified", "reason": "Ngoài phạm vi: tối đa một tham số thực؛ cần giáo viên duyệt"}
    symbols = tuple([variable, *parameters])
    root = _tree(payload["function"], symbols)
    x = s.Symbol(variable, real=True)
    if _has_unsafe_ast_nodes(root):
        if allow_rational and not parameters and not _has_unsafe_ast_nodes(root, allow_division=True):
            expr = _symbolic(root).doit()
            if expr.has(s.zoo, s.nan, s.oo, -s.oo) or not expr.is_rational_function(x):
                return None, {"status": "unverified", "reason": "Biểu thức không xác định trên số thực"}
            num, den = s.fraction(s.together(expr))
            if not (num.is_polynomial(x) and den.is_polynomial(x) and s.expand(den) != 0):
                return None, {"status": "unverified", "reason": "Ngoài phạm vi: chỉ hỗ trợ đa thức hoặc phân thức hữu tỉ bậc thấp"}
            if s.Poly(num, x).total_degree() <= 4 and 1 <= s.Poly(den, x).total_degree() <= 2:
                return (expr, x, None, None, symbols), None
        return None, {"status": "unverified", "reason": "Ngoài phạm vi: chỉ hỗ trợ đa thức؛ cần giáo viên duyệt"}
    expr = _symbolic(root).doit()
    if expr.has(s.zoo, s.nan, s.oo, -s.oo):
        return None, {"status": "unverified", "reason": "Biểu thức không xác định trên số thực"}
    vars_all = [x, *(s.Symbol(p, real=True) for p in parameters)]
    if not expr.is_polynomial(*vars_all) or s.Poly(s.expand(expr), *vars_all).total_degree() > 8:
        return None, {"status": "unverified", "reason": "Ngoài phạm vi công bố: chỉ hỗ trợ đa thức tổng bậc tối đa 8"}
    op, param = regime_info
    if op == "missing":
        return None, {"status": "unverified", "reason": "Thiếu miền tham số; cần giáo viên duyệt"}
    if op == "unsupported":
        return None, {"status": "unverified", "reason": "Miền tham số chưa được hỗ trợ; cần giáo viên duyệt"}
    param_sym = None
    if param:
        base_p = s.Symbol(param, real=True)
        if op == "=":
            expr = s.expand(expr.subs(base_p, s.Integer(0)))
            param_sym = s.Integer(0)
        elif op == "<":
            param_sym = s.Symbol(param, real=True, negative=True)
            expr = s.expand(expr.subs(base_p, param_sym))
        elif op == ">":
            param_sym = s.Symbol(param, real=True, positive=True)
            expr = s.expand(expr.subs(base_p, param_sym))
    return (expr, x, param, param_sym, symbols), None


def _solve_factorized_poly_roots(poly_expr, x):
    """Prove exact real roots and multiplicities of a polynomial in x by low-degree factorization and discriminant sign."""
    import sympy as s
    expanded = s.expand(poly_expr)
    if expanded == 0:
        return None, "Đa thức đồng nhất bằng 0 có vô số nghiệm"
    poly = s.Poly(expanded, x)
    if poly.total_degree() == 0:
        return [], None
    _, factors = poly.factor_list()
    roots_with_mult = []
    for fac, mult in factors:
        deg = fac.degree(x)
        if deg == 1:
            c1 = fac.nth(1)
            c0 = fac.nth(0)
            root = s.simplify(-c0 / c1)
            if root.is_real is False:
                return None, "Nghiệm nhân tử bậc nhất không xác định trên số thực"
            roots_with_mult.append((root, int(mult)))
        elif deg == 2:
            a2 = fac.nth(2)
            a1 = fac.nth(1)
            a0 = fac.nth(0)
            delta = s.simplify(a1**2 - 4 * a2 * a0)
            if delta.is_negative is True:
                continue
            if delta.is_zero is True:
                root = s.simplify(-a1 / (2 * a2))
                roots_with_mult.append((root, 2 * int(mult)))
            elif delta.is_positive is True:
                r1 = s.simplify((-a1 - s.sqrt(delta)) / (2 * a2))
                r2 = s.simplify((-a1 + s.sqrt(delta)) / (2 * a2))
                roots_with_mult.append((r1, int(mult)))
                roots_with_mult.append((r2, int(mult)))
            else:
                return None, "Chưa chứng minh được dấu biệt thức bậc hai trên miền tham số; cần giáo viên duyệt"
        else:
            return None, "Ngoài phạm vi công bố: nhân tử bậc lớn hơn 2 chưa chứng minh được tính đầy đủ; cần giáo viên duyệt"
    merged = []
    for r, m in roots_with_mult:
        found = False
        for i, (er, em) in enumerate(merged):
            if s.simplify(r - er) == 0:
                merged[i] = (er, em + m)
                found = True
                break
        if not found:
            merged.append((r, m))

    def _order_key(item):
        r = item[0]
        free = list(r.free_symbols)
        sample = r.subs(free[0], s.Integer(1) if getattr(free[0], "is_positive", False) else s.Integer(-1)) if free else r
        return float(s.N(sample))

    try:
        merged.sort(key=_order_key)
    except Exception:
        return None, "Chưa sắp thứ tự được các nghiệm trên miền tham số"
    for i in range(len(merged) - 1):
        diff = s.simplify(merged[i + 1][0] - merged[i][0])
        if diff.is_positive is not True:
            return None, "Chưa chứng minh được thứ tự phân biệt giữa các điểm trên miền tham số"
    return merged, None


def _parse_claim_expr(source, symbols, param, param_sym):
    import sympy as s
    expr = _symbolic(_tree(source, symbols)).doit()
    if param and param_sym is not None:
        expr = expr.subs(s.Symbol(param, real=True), param_sym)
    return s.simplify(expr)


def _expand_pm_tokens(items):
    expanded = []
    for item in items:
        token = item.strip()
        if token.startswith("±") or token.startswith("+-") or token.startswith("-+"):
            core = token.lstrip("±+-").strip()
            expanded.append(f"-({core})")
            expanded.append(f"+({core})")
        else:
            expanded.append(token)
    return expanded


def _same_root_set(proven_roots, claimed_roots):
    import sympy as s
    if len(proven_roots) != len(claimed_roots):
        return False
    remaining = list(proven_roots)
    for c in claimed_roots:
        matched = None
        for idx, p in enumerate(remaining):
            if s.simplify(c - p) == 0:
                matched = idx
                break
        if matched is None:
            return False
        remaining.pop(matched)
    return not remaining


def _real_roots(payload):
    """Prove real roots and completeness on the declared parameter regime via factorization and sign conditions."""
    import sympy as s
    label = payload["label"].strip()
    if any(marker in label.lower() for marker in ("approx", "xấp xỉ", "~", "≈")):
        return {"status": "unverified", "reason": "Nghiệm xấp xỉ không được nâng lên verified; cần giáo viên duyệt"}
    parameters = payload.get("parameters", [])
    regime_info, body = _parse_regime_and_body(label, parameters)
    prepared, err = _prepare_polynomial_on_regime(payload, regime_info, allow_rational=True)
    if err:
        return err
    expr, x, param, param_sym, symbols = prepared
    num, den = s.fraction(s.together(expr))
    poles = []
    if not expr.is_polynomial(x):
        pole_pairs, pole_err = _solve_factorized_poly_roots(den, x)
        if pole_err:
            return {"status": "unverified", "reason": pole_err}
        poles = [r for r, _ in pole_pairs]
    proven_with_mult, solve_err = _solve_factorized_poly_roots(num, x)
    if solve_err:
        return {"status": "unverified", "reason": solve_err}
    proven_roots = [r for r, _ in proven_with_mult if not any(s.simplify(r - p) == 0 for p in poles)]
    if body.lower() in _EMPTY_TOKENS:
        claimed_roots = []
    else:
        raw_tokens = _expand_pm_tokens(_split_top_level(body, ","))
        if not raw_tokens:
            return {"status": "unverified", "reason": "Danh sách nghiệm rỗng hoặc không hợp lệ"}
        claimed_roots = []
        for tok in raw_tokens:
            lhs_rhs = tok.split("=", 1)[1].strip() if "=" in tok else tok
            c_expr = _parse_claim_expr(lhs_rhs, symbols, param, param_sym)
            if c_expr.has(s.zoo, s.nan, s.oo, -s.oo) or c_expr.is_real is False:
                return {"status": "failed", "reason": f"Giá trị {tok} không phải nghiệm thực trên miền đã chọn"}
            if not any(s.simplify(c_expr - r) == 0 for r in claimed_roots):
                claimed_roots.append(c_expr)
    for c in claimed_roots:
        if any(s.simplify(c - p) == 0 for p in poles) or s.simplify(num.subs(x, c)) != 0:
            return {"status": "failed", "reason": f"Giá trị {c} không phải nghiệm của phương trình"}
    if _same_root_set(proven_roots, claimed_roots):
        return {
            "status": "verified",
            "reason": f"Đã chứng minh đồng nhất thức phân tích nhân tử {s.factor(num)} và tính đầy đủ của {len(proven_roots)} nghiệm thực",
        }
    return {"status": "failed", "reason": "Tập nghiệm chưa đầy đủ hoặc không khớp trên miền đã chọn"}


def _derivative_analysis(expr, x):
    """Return derivative, ordered stationary points with multiplicities, interval signs, and classified extrema."""
    import sympy as s
    if not expr.is_polynomial(x):
        df = s.together(s.diff(expr, x))
        df_num, df_den = s.fraction(df)
        df_num = s.expand(df_num)
        df_den = s.expand(df_den)
        if df_num == 0:
            return None, "Đạo hàm đồng nhất bằng 0"
        _, den_orig = s.fraction(s.together(expr))
        poles_mult, p_err = _solve_factorized_poly_roots(den_orig, x)
        if p_err:
            return None, p_err
        poles = [r for r, _ in poles_mult]
        stat_raw, s_err = _solve_factorized_poly_roots(df_num, x)
        if s_err:
            return None, s_err
        stationary = [(r, m) for r, m in stat_raw if not any(s.simplify(r - p) == 0 for p in poles)]
        den_roots, d_err = _solve_factorized_poly_roots(df_den, x)
        if d_err:
            return None, d_err
        events = []
        for r, m in stationary:
            events.append((r, m, "stationary"))
        for r, m in den_roots:
            events.append((r, m, "pole"))
        events.sort(key=lambda item: float(s.N(item[0])))
        lc_num = s.Poly(df_num, x).LC() if s.Poly(df_num, x).total_degree() > 0 else df_num
        lc_den = s.Poly(df_den, x).LC() if s.Poly(df_den, x).total_degree() > 0 else df_den
        ratio_lc = s.simplify(lc_num / lc_den)
        if ratio_lc.is_positive is True:
            rightmost_sign = "+"
        elif ratio_lc.is_negative is True:
            rightmost_sign = "-"
        else:
            return None, "Chưa chứng minh được dấu hệ số cao nhất của đạo hàm phân thức"
        n = len(events)
        interval_signs = [None] * (n + 1)
        current = rightmost_sign
        interval_signs[n] = current
        for idx in range(n - 1, -1, -1):
            _, mult, _ = events[idx]
            if mult % 2 == 1:
                current = "-" if current == "+" else "+"
            interval_signs[idx] = current
        extrema = []
        for idx, (root, _, kind_ev) in enumerate(events):
            if kind_ev != "stationary":
                continue
            left_s, right_s = interval_signs[idx], interval_signs[idx + 1]
            if left_s == "+" and right_s == "-":
                extrema.append(("max", root, s.simplify(expr.subs(x, root))))
            elif left_s == "-" and right_s == "+":
                extrema.append(("min", root, s.simplify(expr.subs(x, root))))
        return {
            "df": df,
            "stationary": stationary,
            "poles": poles,
            "events": events,
            "interval_signs": interval_signs,
            "extrema": extrema,
        }, None

    df = s.expand(s.diff(expr, x))
    if df == 0:
        return None, "Đạo hàm đồng nhất bằng 0"
    poly = s.Poly(df, x)
    lc = poly.LC()
    if lc.is_positive is True:
        rightmost_sign = "+"
    elif lc.is_negative is True:
        rightmost_sign = "-"
    else:
        return None, "Chưa chứng minh được dấu hệ số cao nhất của đạo hàm trên miền tham số; cần giáo viên duyệt"
    stationary, err = _solve_factorized_poly_roots(df, x)
    if err:
        return None, err
    n = len(stationary)
    interval_signs = [None] * (n + 1)
    current = rightmost_sign
    interval_signs[n] = current
    for idx in range(n - 1, -1, -1):
        _, mult = stationary[idx]
        if mult % 2 == 1:
            current = "-" if current == "+" else "+"
        interval_signs[idx] = current
    extrema = []
    for idx, (root, _) in enumerate(stationary):
        left_s, right_s = interval_signs[idx], interval_signs[idx + 1]
        if left_s == "+" and right_s == "-":
            extrema.append(("max", root, s.simplify(expr.subs(x, root))))
        elif left_s == "-" and right_s == "+":
            extrema.append(("min", root, s.simplify(expr.subs(x, root))))
    return {"df": df, "stationary": stationary, "poles": [], "events": [(r, m, "stationary") for r, m in stationary], "interval_signs": interval_signs, "extrema": extrema}, None


def _stationary_points(payload):
    import sympy as s
    parameters = payload.get("parameters", [])
    regime_info, body = _parse_regime_and_body(payload["label"], parameters)
    prepared, err = _prepare_polynomial_on_regime(payload, regime_info, allow_rational=True)
    if err:
        return err
    expr, x, param, param_sym, symbols = prepared
    analysis, a_err = _derivative_analysis(expr, x)
    if a_err:
        return {"status": "unverified", "reason": a_err}
    proven = [r for r, _ in analysis["stationary"]]
    if body.lower() in _EMPTY_TOKENS:
        claimed = []
    else:
        tokens = _expand_pm_tokens(_split_top_level(body, ","))
        claimed = []
        for tok in tokens:
            rhs = tok.split("=", 1)[1].strip() if "=" in tok else tok
            c_expr = _parse_claim_expr(rhs, symbols, param, param_sym)
            if c_expr.has(s.zoo, s.nan, s.oo, -s.oo) or c_expr.is_real is False:
                return {"status": "failed", "reason": f"Điểm dừng {tok} không thuộc tập số thực trên miền đã chọn"}
            if not any(s.simplify(c_expr - r) == 0 for r in claimed):
                claimed.append(c_expr)
    if _same_root_set(proven, claimed):
        return {"status": "verified", "reason": f"Đã chứng minh đầy đủ {len(proven)} điểm dừng từ đạo hàm"}
    return {"status": "failed", "reason": "Danh sách điểm dừng không khớp hoặc thiếu điểm dừng"}


def _derivative_sign(payload):
    parameters = payload.get("parameters", [])
    regime_info, body = _parse_regime_and_body(payload["label"], parameters)
    prepared, err = _prepare_polynomial_on_regime(payload, regime_info, allow_rational=True)
    if err:
        return err
    expr, x, _, _, _ = prepared
    analysis, a_err = _derivative_analysis(expr, x)
    if a_err:
        return {"status": "unverified", "reason": a_err}
    interval_signs = analysis["interval_signs"]
    events = analysis.get("events", [])
    full_pattern = []
    for i, sgn in enumerate(interval_signs):
        if i > 0:
            ev_kind = events[i - 1][2] if i - 1 < len(events) else "stationary"
            full_pattern.append("||" if ev_kind == "pole" else "0")
        full_pattern.append(sgn)
    normalized_body = body.replace("−", "-").strip()
    tokens = [t.strip() for t in normalized_body.split(",") if t.strip()]
    if tokens == interval_signs or tokens == full_pattern:
        return {"status": "verified", "reason": f"Đã chứng minh dấu đạo hàm {', '.join(full_pattern)} trên toàn miền"}
    if not all(t in {"+", "-", "0", "||"} for t in tokens):
        return {"status": "unverified", "reason": "Định dạng mệnh đề dấu đạo hàm chưa hỗ trợ; cần giáo viên duyệt"}
    return {"status": "failed", "reason": f"Dấu đạo hàm đúng là {', '.join(interval_signs)}"}


def _extrema(payload):
    import re
    import sympy as s
    parameters = payload.get("parameters", [])
    regime_info, body = _parse_regime_and_body(payload["label"], parameters)
    prepared, err = _prepare_polynomial_on_regime(payload, regime_info, allow_rational=True)
    if err:
        return err
    expr, x, param, param_sym, symbols = prepared
    analysis, a_err = _derivative_analysis(expr, x)
    if a_err:
        return {"status": "unverified", "reason": a_err}
    proven = analysis["extrema"]
    if body.lower() in _EMPTY_TOKENS:
        if not proven:
            return {"status": "verified", "reason": "Đã chứng minh hàm số không có cực trị trên miền đã chọn"}
        return {"status": "failed", "reason": f"Hàm số có {len(proven)} cực trị trên miền đã chọn"}
    items = _split_top_level(body, ",")
    claimed = []
    for item in items:
        m = re.fullmatch(r"(max|min|cd|ct|cđ)\s*\((.+)\)", item.strip(), flags=re.IGNORECASE)
        if not m:
            return {"status": "unverified", "reason": "Định dạng mệnh đề cực trị cần viết dạng max(x0, y0), min(x0, y0) hoặc none"}
        raw_kind = m.group(1).lower()
        kind = "max" if raw_kind in {"max", "cd", "cđ"} else "min"
        coords = _split_top_level(m.group(2), ",")
        if len(coords) != 2:
            coords = _split_top_level(m.group(2), ";")
        if len(coords) != 2:
            return {"status": "unverified", "reason": "Mỗi điểm cực trị cần đúng hai tọa độ (x0, y0)"}
        cx = _parse_claim_expr(coords[0], symbols, param, param_sym)
        cy = _parse_claim_expr(coords[1], symbols, param, param_sym)
        if any(v.has(s.zoo, s.nan, s.oo, -s.oo) or v.is_real is False for v in (cx, cy)):
            return {"status": "failed", "reason": f"Tọa độ cực trị {item} không xác định trên số thực"}
        claimed.append((kind, cx, cy))
    if len(claimed) != len(proven):
        return {"status": "failed", "reason": f"Số điểm cực trị không đầy đủ (đúng: {len(proven)}, khai báo: {len(claimed)})"}
    remaining = list(proven)
    for ck, cx, cy in claimed:
        matched = None
        for idx, (pk, px, py) in enumerate(remaining):
            if ck == pk and s.simplify(cx - px) == 0 and s.simplify(cy - py) == 0:
                matched = idx
                break
        if matched is None:
            return {"status": "failed", "reason": f"Điểm cực trị ({ck}, {cx}, {cy}) sai loại hoặc sai tọa độ"}
        remaining.pop(matched)
    return {
        "status": "verified",
        "reason": f"Đã chứng minh đầy đủ {len(proven)} điểm cực trị kèm dấu đạo hàm và tọa độ chính xác",
    }


def _parameter_safety(payload):
    """Prove parameter interval safety by structural AST analysis and polynomial degree bounds."""
    import re
    import sympy as s
    variable = payload["variable"]
    parameters = payload.get("parameters", [])
    if len(parameters) != 1:
        return {"status": "unverified", "reason": "Phép kiểm khoảng tham số yêu cầu đúng một tham số thực"}
    param = parameters[0]
    symbols = (variable, param)
    root = _tree(payload["function"], symbols)
    if _has_unsafe_ast_nodes(root):
        return {"status": "unverified", "reason": "Biểu thức có phép chia, căn hoặc hàm siêu việt cần kiểm riêng điều kiện tham số"}
    expr = _symbolic(root).doit()
    x_sym, p_sym = s.Symbol(variable, real=True), s.Symbol(param, real=True)
    if not expr.is_polynomial(x_sym, p_sym) or s.Poly(s.expand(expr), x_sym, p_sym).total_degree() > 8:
        return {"status": "unverified", "reason": "Ngoài phạm vi công bố: chỉ chứng minh cho đa thức tổng bậc tối đa 8"}
    label = payload["label"].strip()
    m = re.fullmatch(rf"(?:{re.escape(param)}\s*(?:in|∈)\s*)?\[\s*([^,;]+)\s*[,;]\s*([^,;]+)\s*\]", label)
    if not m:
        return {"status": "unverified", "reason": "Khoảng tham số cần khai báo dạng [a_min, a_max]"}
    lo = _symbolic(_tree(m.group(1), ())).doit()
    hi = _symbolic(_tree(m.group(2), ())).doit()
    if any(v.has(s.zoo, s.nan, s.oo, -s.oo) or v.is_real is False for v in (lo, hi)):
        return {"status": "unverified", "reason": "Cận khoảng tham số không phải số thực hữu hạn"}
    if not bool(lo < hi):
        return {"status": "failed", "reason": "Khoảng tham số không hợp lệ (cận dưới phải nhỏ hơn cận trên)"}
    return {
        "status": "verified",
        "reason": f"Đã chứng minh cấu trúc đa thức an toàn trên toàn đoạn [{lo}, {hi}] của {param} và mọi {variable} thực",
    }


def _exclusions(payload):
    """Prove completeness of domain exclusion list (including empty exclusions) from the un-simplified AST."""
    import sympy as s
    variable = payload["variable"]
    parameters = payload.get("parameters", [])
    symbols = tuple([variable, *parameters])
    root = _tree(payload["function"], symbols)
    if _has_unsafe_ast_nodes(root, allow_division=True):
        return {"status": "unverified", "reason": "Biểu thức chứa căn, log hoặc hàm lượng giác chưa chứng minh được danh sách loại trừ đầy đủ"}
    denoms = _collect_denominators(root)
    x_sym = s.Symbol(variable, real=True)
    vars_all = [x_sym, *(s.Symbol(p, real=True) for p in parameters)]
    body = payload["label"].strip()
    if not denoms:
        expr = _symbolic(root).doit()
        if expr.has(s.zoo, s.nan, s.oo, -s.oo) or not expr.is_polynomial(*vars_all) or s.Poly(s.expand(expr), *vars_all).total_degree() > 8:
            return {"status": "unverified", "reason": "Ngoài phạm vi công bố của phép kiểm đa thức"}
        if body.lower() in _EMPTY_TOKENS:
            return {"status": "verified", "reason": "Chứng minh bằng cấu trúc biểu thức đa thức: danh sách điều kiện loại trừ rỗng trên mọi giá trị thực"}
        return {"status": "failed", "reason": "Đa thức không có điểm loại trừ thực nào"}
    if parameters:
        for d_node in denoms:
            d_expr = _symbolic(d_node).doit()
            if any(s.Symbol(p, real=True) in d_expr.free_symbols for p in parameters):
                return {"status": "unverified", "reason": "Mẫu số phụ thuộc tham số cần giáo viên duyệt"}
    proven_excluded = []
    for d_node in denoms:
        d_expr = _symbolic(d_node).doit()
        if d_expr.has(s.zoo, s.nan, s.oo, -s.oo) or not d_expr.is_polynomial(x_sym):
            return {"status": "unverified", "reason": "Mẫu số không phải đa thức theo biến"}
        if s.expand(d_expr) == 0:
            return {"status": "unverified", "reason": "Mẫu số bằng 0"}
        roots, err = _solve_factorized_poly_roots(d_expr, x_sym)
        if err:
            return {"status": "unverified", "reason": err}
        for r, _ in roots:
            if not any(s.simplify(r - er) == 0 for er in proven_excluded):
                proven_excluded.append(r)
    if body.lower() in _EMPTY_TOKENS:
        claimed_excluded = []
    else:
        tokens = _expand_pm_tokens(_split_top_level(body, ","))
        claimed_excluded = []
        for tok in tokens:
            cleaned = tok.replace("!=", "=").replace("≠", "=")
            rhs = cleaned.split("=", 1)[1].strip() if "=" in cleaned else cleaned
            c_expr = _symbolic(_tree(rhs, symbols)).doit()
            if c_expr.has(s.zoo, s.nan, s.oo, -s.oo) or c_expr.is_real is False:
                return {"status": "failed", "reason": f"Giá trị loại trừ {tok} không phải số thực"}
            if not any(s.simplify(c_expr - er) == 0 for er in claimed_excluded):
                claimed_excluded.append(c_expr)
    if _same_root_set(proven_excluded, claimed_excluded):
        return {"status": "verified", "reason": f"Đã chứng minh đầy đủ {len(proven_excluded)} điều kiện loại trừ từ cấu trúc mẫu số"}
    return {"status": "failed", "reason": "Danh sách điều kiện loại trừ không đầy đủ hoặc sai"}


def _solution_step(payload):
    """Verify a single structured solution step without propagating verified status to prose or other steps."""
    label = payload["label"].strip()
    if ":" not in label:
        return {"status": "unverified", "reason": "Bước giải văn xuôi không có cấu trúc mệnh đề; cần giáo viên duyệt"}
    step_kind, step_body = (part.strip() for part in label.split(":", 1))
    step_kind = step_kind.lower()
    sub_payload = {**payload, "label": step_body}
    if step_kind in {"identity", "algebra"}:
        if "=" not in step_body:
            return {"status": "unverified", "reason": "Bước biến đổi đại số cần có dạng lhs = rhs"}
        lhs, rhs = (part.strip() for part in step_body.split("=", 1))
        symbols = tuple([payload["variable"], *payload.get("parameters", [])])
        return _verify({"lhs": lhs, "rhs": rhs, "symbols": symbols, "syntax": "expression"})
    if step_kind == "derivative":
        return _derivative(sub_payload)
    if step_kind in {"roots", "real_roots"}:
        return _real_roots(sub_payload)
    if step_kind == "stationary_points":
        return _stationary_points(sub_payload)
    if step_kind in {"sign", "derivative_sign"}:
        return _derivative_sign(sub_payload)
    if step_kind == "extrema":
        return _extrema(sub_payload)
    if step_kind == "exclusions":
        return _exclusions(sub_payload)
    if step_kind == "asymptotes":
        return _asymptotes(sub_payload)
    return {"status": "unverified", "reason": "Bước diễn giải bằng lời hoặc ngoài phạm vi phép kiểm; cần giáo viên duyệt"}


def _asymptotes(payload):
    """Prove vertical and horizontal/slant asymptotes of polynomials (none) and low-degree rational functions."""
    import sympy as s
    variable = payload["variable"]
    parameters = payload.get("parameters", [])
    if parameters:
        return {"status": "unverified", "reason": "Phép kiểm tiệm cận có tham số cần giáo viên duyệt"}
    symbols = (variable,)
    root = _tree(payload["function"], symbols)
    if _has_unsafe_ast_nodes(root, allow_division=True):
        return {"status": "unverified", "reason": "Biểu thức chứa căn, log hoặc hàm lượng giác ngoài phạm vi phép kiểm tiệm cận"}
    x = s.Symbol(variable, real=True)
    expr = _symbolic(root).doit()
    if expr.has(s.zoo, s.nan, s.oo, -s.oo):
        return {"status": "unverified", "reason": "Biểu thức không xác định trên số thực"}
    body = payload["label"].strip()
    if expr.is_polynomial(x):
        if s.Poly(s.expand(expr), x).total_degree() > 8:
            return {"status": "unverified", "reason": "Bậc đa thức ngoài phạm vi"}
        if body.lower() in _EMPTY_TOKENS:
            return {"status": "verified", "reason": "Chứng minh bằng cấu trúc đa thức: đồ thị không có đường tiệm cận"}
        return {"status": "failed", "reason": "Hàm đa thức không có đường tiệm cận"}
    if not expr.is_rational_function(x):
        return {"status": "unverified", "reason": "Ngoài phạm vi công bố của phép kiểm tiệm cận"}
    num, den = s.fraction(s.together(expr))
    num, den = s.expand(num), s.expand(den)
    if not (num.is_polynomial(x) and den.is_polynomial(x) and den != 0):
        return {"status": "unverified", "reason": "Ngoài phạm vi công bố của phép kiểm tiệm cận"}
    deg_num = s.Poly(num, x).total_degree()
    deg_den = s.Poly(den, x).total_degree()
    if deg_den != 1 or deg_num > 2:
        return {"status": "unverified", "reason": "Chỉ chứng minh tiệm cận cho phân thức bậc tử tối đa 2 trên bậc mẫu bằng 1"}
    x0 = s.solve(den, x)[0]
    if s.simplify(num.subs(x, x0)) == 0:
        return {"status": "unverified", "reason": "Phân thức suy biến (tử số và mẫu số có nghiệm chung)"}
    quo, rem = s.div(num, den, domain="QQ")
    if s.simplify(rem) == 0:
        return {"status": "unverified", "reason": "Phân thức rút gọn thành đa thức"}
    proven_x = s.simplify(x0)
    proven_y = s.simplify(quo)
    if body.lower() in _EMPTY_TOKENS:
        return {"status": "failed", "reason": "Phân thức hữu tỉ này có hai đường tiệm cận"}
    parts = _split_top_level(body, ",")
    claimed_x, claimed_y = [], []
    for part in parts:
        if "=" not in part:
            return {"status": "unverified", "reason": "Mỗi đường tiệm cận cần viết dạng x = x0 hoặc y = ax + b"}
        lhs, rhs = (p.strip() for p in part.split("=", 1))
        if lhs == variable:
            claimed_x.append(s.simplify(_symbolic(_tree(rhs, symbols)).doit()))
        elif lhs == "y":
            claimed_y.append(s.simplify(_symbolic(_tree(rhs, symbols)).doit()))
        else:
            return {"status": "unverified", "reason": f"Phương trình tiệm cận không hợp lệ: {part}"}
    if len(claimed_x) == 1 and len(claimed_y) == 1 and s.simplify(claimed_x[0] - proven_x) == 0 and s.simplify(claimed_y[0] - proven_y) == 0:
        return {
            "status": "verified",
            "reason": f"Đã chứng minh tiệm cận đứng x = {proven_x} và tiệm cận {'ngang' if deg_num <= 1 else 'xiên'} y = {proven_y}",
        }
    return {"status": "failed", "reason": f"Tiệm cận đúng là x = {proven_x}, y = {proven_y}"}


def execute(operation, payload):
    if operation == "math.plot":
        return _plot(payload)
    if operation == "math.verify":
        return _verify(payload)
    if operation == "math.derivative":
        return _derivative(payload)
    if operation == "math.real_roots":
        return _real_roots(payload)
    if operation == "math.stationary_points":
        return _stationary_points(payload)
    if operation == "math.derivative_sign":
        return _derivative_sign(payload)
    if operation == "math.extrema":
        return _extrema(payload)
    if operation == "math.parameter_safety":
        return _parameter_safety(payload)
    if operation == "math.exclusions":
        return _exclusions(payload)
    if operation == "math.asymptotes":
        return _asymptotes(payload)
    if operation == "math.solution_step":
        return _solution_step(payload)
    raise ExpressionError("expression_unsupported", "Tác vụ toán chưa hỗ trợ")


def verify_equality(lhs, rhs, *, symbols=("x", "a", "b"), syntax="expression"):
    from lessonai.core.jobs import get_runner, JobError
    try:
        return get_runner().run("math.verify", {"lhs": lhs, "rhs": rhs,
                                "symbols": symbols, "syntax": syntax})
    except (JobError, ValueError) as error:
        return {"status": "unverified", "reason": str(error)}
