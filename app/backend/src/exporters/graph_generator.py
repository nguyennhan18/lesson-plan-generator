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

# Các giá trị `kind` / `plot_type` được phép vẽ đồ thị hàm số
_FUNCTION_KINDS = {"function", "function_plot", "arithmetic_sequence"}


def _plain_value(v):
    """Enum (kể cả str-Enum) -> giá trị thuần; so sánh chuỗi sẽ không còn phụ thuộc vào kiểu Enum."""
    return getattr(v, "value", v)


def is_plottable(config) -> bool:
    """Kiểm tra NHANH (không vẽ) xem chart_spec có thể vẽ thành đồ thị hàm số không.
    Exporter dùng hàm này để quyết định bố cục có/không có cột đồ thị trước khi đặt chữ."""
    if not isinstance(config, dict):
        return False
    plot_type = _plain_value(config.get("plot_type") or config.get("kind") or "")
    if plot_type not in _FUNCTION_KINDS:
        return False
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

    if plot_type in _FUNCTION_KINDS:
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
    print(f"✅ Đã tạo thành công ảnh đồ thị Matplotlib! Kích thước: {len(buf)} bytes")
