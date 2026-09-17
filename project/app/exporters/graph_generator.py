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

def generate_math_plot(config: dict) -> bytes:
    """
    Tạo đồ thị toán học động bằng SymPy & Matplotlib.
    - Không chèn prompt vào title.
    - Sửa font chuẩn Times New Roman.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_type = config.get("plot_type", "function")
    
    if plot_type == "function":
        expr_str = config.get("expression", "x")
        x_min, x_max = config.get("x_range", (-10, 10))
        
        # Parse biểu thức toán bằng SymPy
        x = sp.Symbol('x')
        expr = sp.sympify(expr_str)
        f = sp.lambdify(x, expr, modules=['numpy'])
        
        x_vals = np.linspace(x_min, x_max, 400)
        y_vals = f(x_vals)
        
        legend_label = f"y = {sp.latex(expr)}"
        ax.plot(x_vals, y_vals, label=f"${legend_label}$", color="#1f77b4", linewidth=2)
        
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(prop={'family': 'Times New Roman', 'size': 11})
        
    elif plot_type == "chart":
        labels = config.get("labels", [])
        values = config.get("values", [])
        chart_kind = config.get("chart_kind", "bar")
        
        if chart_kind == "bar":
            ax.bar(labels, values, color="#1f77b4")
        elif chart_kind == "pie":
            ax.pie(values, labels=labels, autopct='%1.1f%%')
            
    # CHỈ đặt title nếu trong config có truyền title cụ thể (Không lấy prompt làm title)
    title = config.get("title", "")
    if title and isinstance(title, str):
        ax.set_title(title, fontdict={'fontname': 'Times New Roman', 'fontsize': 14, 'fontweight': 'bold'})
        
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)
    
    return buf.getvalue()
if __name__ == "__main__":
    buf = generate_math_plot("Minh họa Cấp số cộng")
    print(f"✅ Đã tạo thành công ảnh đồ thị Matplotlib! Kích thước: {len(buf.getvalue())} bytes")
