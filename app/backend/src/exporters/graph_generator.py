import io
import re
import matplotlib
matplotlib.use('Agg')  # Render headless không mở cửa sổ GUI
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

_X = sp.symbols('x')
_ALLOWED_FUNCS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "log": sp.log,
                  "exp": sp.exp, "sqrt": sp.sqrt, "Abs": sp.Abs, "pi": sp.pi}

def safe_eval_expression(expr_str: str):
    """Parse biểu thức bằng Sympy — chỉ cho phép biến x + các hàm đã liệt kê,
    KHÔNG dùng eval() nên không có rủi ro thực thi code tuỳ ý."""
    expr = sp.sympify(expr_str, locals=_ALLOWED_FUNCS)
    if expr.free_symbols - {_X}:
        raise ValueError(f"Biểu thức chứa biến không hợp lệ: {expr.free_symbols}")
    return sp.lambdify(_X, expr, modules=["numpy"])


plt.rcParams['font.sans-serif'] = ['Times New Roman', 'Arial', 'DejaVu Sans']
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.unicode_minus'] = False

# Các giá trị `kind` / `plot_type` được phép vẽ đồ thị hàm số và hệ bất phương trình
_FUNCTION_KINDS = {"function", "function_plot", "arithmetic_sequence"}
_INEQUALITY_KINDS = {"inequality_system", "linear_programming"}
_PLIFTABLE_KINDS = _FUNCTION_KINDS | _INEQUALITY_KINDS


def _plain_value(v):
    """Enum (kể cả str-Enum) -> giá trị thuần; so sánh chuỗi sẽ không còn phụ thuộc vào kiểu Enum."""
    return getattr(v, "value", v)


def is_plottable(config) -> bool:
    """Kiểm tra NHANH (không vẽ) xem chart_spec có thể vẽ thành đồ thị hàm số / hệ BPT không.
    Exporter dùng hàm này để quyết định bố cục có/không có cột đồ thị trước khi đặt chữ."""
    if not isinstance(config, dict):
        return False
    plot_type = _plain_value(config.get("plot_type") or config.get("kind") or "")
    if plot_type not in _PLIFTABLE_KINDS:
        return False
    if plot_type in _INEQUALITY_KINDS:
        return bool(config.get("boundary_lines") or config.get("vertices") or config.get("expression") or config.get("formula"))
    expr_str = config.get("expression") or config.get("formula")
    if not isinstance(expr_str, str) or not expr_str.strip():
        return False
    try:
        expr = sp.sympify(expr_str)
        if expr.free_symbols - {_X}:
            return False
        f = sp.lambdify(_X, expr, modules=["numpy"])
        with np.errstate(all="ignore"):
            y = np.asarray(f(np.linspace(-1.0, 1.0, 5)), dtype=float)
        return bool(np.isfinite(y).any()) or y.ndim == 0
    except Exception:
        return False


def generate_math_plot(config: dict, figsize: tuple = (6, 4)) -> bytes:
    """
    Tạo đồ thị toán học động bằng SymPy & Matplotlib.
    - Đọc linh hoạt config từ Pydantic ChartSpec (expression, x_min, x_max, chart_title).
    - Ném ValueError rõ ràng nếu không vẽ được (kind = none, thiếu/sai biểu thức) —
      KHÔNG vẽ đồ thị giả (khung trống hoặc y = x) để slide không chèn ảnh vô nghĩa.
    - figsize: kích thước (inch) của ảnh; nên truyền đúng tỉ lệ vùng đặt trên slide để ảnh không bị méo.
    """
    if not isinstance(config, dict):
        raise ValueError("chart_spec không hợp lệ (không phải dict)")

    plot_type = _plain_value(config.get("plot_type") or config.get("kind") or "function")

    if plot_type in _INEQUALITY_KINDS:
        from matplotlib.patches import Polygon
        boundary_lines = config.get("boundary_lines") or []
        if not boundary_lines and config.get("expression"):
            raw_expr = str(config.get("expression"))
            exprs = [e.strip() for e in raw_expr.split(";") if e.strip()]
            boundary_lines = [{"expr": e, "label": f"y = {e}"} for e in exprs]
        
        vertices = config.get("vertices") or []
        x_min = float(config.get("x_min", -1.0))
        x_max = float(config.get("x_max", 6.0))
        y_min = float(config.get("y_min", -1.0))
        y_max = float(config.get("y_max", 6.0))
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.axhline(0, color='black', linewidth=1.0)
        ax.axvline(0, color='black', linewidth=1.0)
        ax.text(x_max - 0.3, -0.45, '$x$', fontsize=11, fontweight='bold', fontfamily='Times New Roman')
        ax.text(-0.45, y_max - 0.3, '$y$', fontsize=11, fontweight='bold', fontfamily='Times New Roman')
        ax.text(-0.35, -0.35, '$O$', fontsize=10, fontfamily='Times New Roman')
        
        # 1. Vẽ các đường thẳng biên ranh giới của hệ BPT
        line_colors = ["#2563eb", "#7c3aed", "#d97706", "#0284c7"]
        for idx, line_info in enumerate(boundary_lines):
            expr_val = line_info.get("expr") or line_info.get("expression")
            lbl = line_info.get("label", f"d_{idx+1}")
            color = line_info.get("color") or line_colors[idx % len(line_colors)]
            try:
                sym_line = sp.sympify(expr_val)
                f_line = sp.lambdify(_X, sym_line, modules=["numpy"])
                x_pts = np.linspace(x_min, x_max, 400)
                y_pts = f_line(x_pts)
                ax.plot(x_pts, y_pts, label=lbl, color=color, linewidth=1.8, linestyle='-')
            except Exception:
                pass
                
        # 2. Tô màu miền nghiệm đa giác lồi
        if vertices and len(vertices) >= 3:
            poly = Polygon(vertices, closed=True, facecolor='#10b981', alpha=0.35, edgecolor='#059669', linewidth=1.5, label='Miền nghiệm (đa giác OABC)')
            ax.add_patch(poly)
            default_labels = ["O(0,0)", "A(4,0)", "B(8/3, 8/3)", "C(0,4)"]
            for idx, pt in enumerate(vertices):
                vx, vy = float(pt[0]), float(pt[1])
                ax.scatter([vx], [vy], color='#dc2626', s=45, zorder=5)
                lbl = default_labels[idx] if idx < len(default_labels) else f"P{idx+1}({vx:.1f}, {vy:.1f})"
                ax.annotate(lbl, (vx, vy), textcoords="offset points", xytext=(6, 6),
                            fontsize=10, fontfamily='Times New Roman', fontweight='bold', color='#1e293b')
                            
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right', prop={'family': 'Times New Roman', 'size': 9})

    elif plot_type in _FUNCTION_KINDS:
        expr_str = config.get("expression") or config.get("formula")
        if not isinstance(expr_str, str) or not expr_str.strip():
            raise ValueError("chart_spec thiếu 'expression' nên không thể vẽ đồ thị hàm số")

        x_min = config.get("x_min")
        x_max = config.get("x_max")
        if x_min is None or x_max is None:
            x_min, x_max = config.get("x_range", (-4.0, 4.0))

        expr = sp.sympify(expr_str)
        if expr.free_symbols - {_X}:
            raise ValueError(f"Biểu thức chứa biến không hợp lệ: {expr.free_symbols}")
        f = sp.lambdify(_X, expr, modules=["numpy"])

        x_vals = np.linspace(float(x_min), float(x_max), 600)
        with np.errstate(all="ignore"):
            y_vals = np.asarray(f(x_vals), dtype=float)
        if y_vals.ndim == 0:
            y_vals = np.full_like(x_vals, float(y_vals))
        y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)
        if not np.isfinite(y_vals).any():
            raise ValueError(f"Biểu thức '{expr_str}' không có giá trị hữu hạn trên [{x_min}, {x_max}]")

        fig, ax = plt.subplots(figsize=figsize)
        legend_label = f"y = {sp.latex(expr)}"
        ax.plot(x_vals, y_vals, label=f"${legend_label}$", color="#1f77b4", linewidth=2)

        # Hàm có tiệm cận (tan, 1/x...) làm trục y quá lớn -> giới hạn theo phân vị để thấy rõ dạng đồ thị
        finite = y_vals[np.isfinite(y_vals)]
        lo, hi = np.percentile(finite, [1, 99])
        if (finite.max() - finite.min()) > 20 * max(hi - lo, 1e-9):
            pad = 0.15 * max(hi - lo, 1.0)
            ax.set_ylim(lo - pad, hi + pad)

        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(prop={'family': 'Times New Roman', 'size': 11})

    elif plot_type == "chart":
        labels = config.get("labels", [])
        values = config.get("values", [])
        if not labels or not values:
            raise ValueError("chart_spec dạng 'chart' thiếu labels/values")
        fig, ax = plt.subplots(figsize=figsize)
        chart_kind = config.get("chart_kind", "bar")
        if chart_kind == "bar":
            ax.bar(labels, values, color="#1f77b4")
        elif chart_kind == "pie":
            ax.pie(values, labels=labels, autopct='%1.1f%%')

    else:
        raise ValueError(f"Loại đồ thị '{plot_type}' không cần / không hỗ trợ vẽ")

    # Đặt tiêu đề từ chart_title hoặc title
    title = config.get("chart_title") or config.get("title") or ""
    if title and isinstance(title, str):
        ax.set_title(title, fontdict={'fontname': 'Times New Roman', 'fontsize': 14, 'fontweight': 'bold'})

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)

    return buf.getvalue()


if __name__ == "__main__":
    buf = generate_math_plot({"expression": "x**3 - 3*x", "chart_title": "Đồ thị y = x^3 - 3x"})
    print(f"Đã tạo thành công ảnh đồ thị Matplotlib! Kích thước: {len(buf)} bytes")
