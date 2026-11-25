"""Render công thức LaTeX thành PNG bằng mathtext của Matplotlib.

Tách khỏi `exporters/slide_exporter.py` để `services/visuals/rendering.py` dùng
được mà không phải import ngược lên tầng exporters.
"""
import io
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lessonai.core.render_runtime import serialized_render
from lessonai.utils.xml_text import clean_xml_string


@serialized_render
def render_latex_to_bytes(latex_str: str) -> bytes:
    """Render a formula, preserving raw LaTeX when mathtext cannot parse it.

    A rendering failure is explicit: never replace nonempty content with an
    invisible pixel and report the export as successful.
    """
    if not isinstance(latex_str, str) or not latex_str.strip():
        raise ValueError("Không có công thức để render")

    if len(latex_str)>4000:
        raise ValueError("Công thức quá dài để render; cần chia nhỏ")
    clean_str = latex_str.replace(r'\(', '').replace(r'\)', '').strip()

    clean_str = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', clean_str)
    clean_str = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', clean_str)
    clean_str = re.sub(r'\\implies(?![a-zA-Z])', r'\\Rightarrow', clean_str)
    clean_str = re.sub(r'\\iff(?![a-zA-Z])', r'\\Leftrightarrow', clean_str)
    clean_str = re.sub(r'\\to(?![a-zA-Z])', r'\\rightarrow', clean_str)
    clean_str = clean_str.replace(r'\quad', ' ').replace(r'\qquad', ' ')
    clean_str = clean_str.replace(r'\tg', r'\tan').replace(r'\ctg', r'\cot')

    # Adaptive Font Scaling: Tự động thu nhỏ cỡ font cho công thức cực dài (> 35 ký tự)
    # Giữ nguyên 20pt cho công thức ngắn; co dần xuống 10pt cho công thức dài >= 115 ký tự
    formula_len = len(clean_str)
    calc_fontsize = max(10, min(20, int(20 - (max(0, formula_len - 35) / 8.0))))
    calc_fallback_font = max(9, min(18, int(18 - (max(0, formula_len - 35) / 8.0))))

    fig, ax = plt.subplots(figsize=(0.1, 0.1))
    ax.axis('off')

    try:
        formatted_latex = f"${clean_str}$" if not clean_str.startswith("$") else clean_str
        ax.text(
            0.5, 0.5, formatted_latex,
            fontsize=calc_fontsize, ha='center', va='center', color='#1e3a8a'
        )
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, dpi=300, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        plt.close(fig)
        try:
            # Fallback 1: render bằng Unicode text
            fig, ax = plt.subplots(figsize=(0.1, 0.1))
            ax.axis('off')
            unicode_str = "LaTeX gốc: " + clean_xml_string(latex_str)
            ax.text(
                0.5, 0.5, unicode_str,
                fontsize=calc_fallback_font, ha='center', va='center', color='#1e3a8a', fontname='DejaVu Sans'
            )
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, dpi=300, transparent=True)
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()
        except Exception:
            try:
                plt.close(fig)
            except Exception:
                pass
            raise ValueError("Không thể render công thức; chưa tạo file xuất")
