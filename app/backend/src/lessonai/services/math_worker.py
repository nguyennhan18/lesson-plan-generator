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


def execute(operation, payload):
    if operation == "math.plot":
        return _plot(payload)
    if operation == "math.verify":
        return _verify(payload)
    raise ExpressionError("expression_unsupported", "Tác vụ toán chưa hỗ trợ")


def verify_equality(lhs, rhs, *, symbols=("x", "a", "b"), syntax="expression"):
    from lessonai.core.jobs import get_runner, JobError
    try:
        return get_runner().run("math.verify", {"lhs": lhs, "rhs": rhs,
                                "symbols": symbols, "syntax": syntax})
    except (JobError, ValueError) as error:
        return {"status": "unverified", "reason": str(error)}
