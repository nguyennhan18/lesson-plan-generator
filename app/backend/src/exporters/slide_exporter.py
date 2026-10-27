import os
import sys
import re
import io
import json
import math
import base64
from enum import Enum
from typing import Union, Dict, Any, List, Optional
import matplotlib.pyplot as plt
import sympy as sp
import numpy as np

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.slide_schema import SlideDeckSchema, SlideType, ThemeType
from exporters.graph_generator import generate_math_plot, is_plottable


def decode_base64_data_url(data_url: Optional[str]) -> Optional[io.BytesIO]:
    """
    Task 14.3 & Task 18.2: Giải mã chuỗi Base64 Data URL (data:image/png;base64,...) thành byte stream io.BytesIO.
    Xử lý:
    - Bóc tách prefix nếu có (data:image/...;base64,)
    - Bổ sung padding '=' nếu chuỗi Base64 chưa chia hết cho 4
    - Kiểm tra magic bytes nhận diện đúng định dạng ảnh (PNG: \x89PNG, JPEG: \xff\xd8, WebP: RIFF...WEBP)
    - Fallback kiểm tra cấu trúc file hợp lệ qua Pillow Image.verify()
    - Trả về io.BytesIO stream đã seek(0) sẵn sàng cho python-pptx add_picture
    """
    if not data_url or not isinstance(data_url, str):
        return None

    try:
        clean_str = data_url.strip()
        if "," in clean_str:
            _, b64_data = clean_str.split(",", 1)
        else:
            b64_data = clean_str

        b64_data = b64_data.strip()
        # Bổ sung padding Base64 nếu thiếu
        missing_padding = len(b64_data) % 4
        if missing_padding:
            b64_data += "=" * (4 - missing_padding)

        image_bytes = base64.b64decode(b64_data)
        if not image_bytes or len(image_bytes) < 8:
            return None

        # Kiểm tra magic bytes nhận diện đúng định dạng ảnh (PNG, JPEG, WebP)
        is_png = image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpeg = image_bytes.startswith(b"\xff\xd8")
        is_webp = image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]
        if not (is_png or is_jpeg or is_webp):
            try:
                with Image.open(io.BytesIO(image_bytes)) as test_im:
                    test_im.verify()
            except Exception:
                return None

        stream = io.BytesIO(image_bytes)
        stream.seek(0)
        return stream
    except Exception as e:
        print(f"[slide_exporter] Lỗi giải mã Base64 Data URL: {e}")
        return None


def compute_aspect_preserving_fit(
    img_px_w: int,
    img_px_h: int,
    box_left: float,
    box_top: float,
    box_w: float,
    box_h: float
) -> tuple:
    """
    Task 14.4 & Task 18.2: Thuật toán Box-Fit bảo toàn tỉ lệ khung hình (Aspect Ratio Preservation)
    Tính toán tọa độ (left, top) và kích thước (width, height) tối ưu để nhúng ảnh
    vào khung chứa 16:9 Widescreen mà không bị méo mó, co giãn hay biến dạng hình học:
    - Nếu aspect ảnh >= aspect khung: Fit theo chiều rộng (fit_w = box_w), căn giữa theo chiều dọc.
    - Nếu aspect ảnh < aspect khung: Fit theo chiều cao (fit_h = box_h), căn giữa theo chiều ngang.
    - Duy trì độ chính xác tuyệt đối tỉ lệ w/h bằng đúng tỉ lệ pixel của ảnh gốc.
    """
    w_px = max(1.0, float(img_px_w))
    h_px = max(1.0, float(img_px_h))
    aspect = w_px / h_px
    box_aspect = float(box_w) / max(1e-6, float(box_h))

    if aspect >= box_aspect:
        fit_w = box_w
        fit_h = box_w / aspect
    else:
        fit_h = box_h
        fit_w = box_h * aspect

    fit_left = box_left + (box_w - fit_w) / 2.0
    fit_top = box_top + (box_h - fit_h) / 2.0

    return fit_left, fit_top, fit_w, fit_h


def clean_xml_string(s: str) -> str:
    """Lọc ký tự rác / ẩn để tránh lỗi khi chèn XML vào PowerPoint"""
    if not isinstance(s, str):
        s = str(s or "")
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]', '', s)


_GREEK_MAP = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\varepsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η',
    r'\theta': 'θ', r'\vartheta': 'ϑ', r'\iota': 'ι', r'\kappa': 'κ',
    r'\lambda': 'λ', r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ',
    r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ', r'\tau': 'τ',
    r'\upsilon': 'υ', r'\phi': 'φ', r'\varphi': 'φ', r'\chi': 'χ',
    r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Upsilon': 'Υ',
    r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
}

_SYMBOL_MAP = {
    r'\times': '×', r'\div': '÷', r'\cdot': '·', r'\pm': '±', r'\mp': '∓',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\approx': '≈', r'\equiv': '≡',
    r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇', r'\emptyset': '∅',
    r'\forall': '∀', r'\exists': '∃', r'\in': '∈', r'\notin': '∉',
    r'\subset': '⊂', r'\supset': '⊃', r'\subseteq': '⊆', r'\supseteq': '⊇',
    r'\cup': '∪', r'\cap': '∩', r'\Rightarrow': '⇒', r'\Leftarrow': '⇐',
    r'\Leftrightarrow': '⇔', r'\rightarrow': '→', r'\leftarrow': '←',
    r'\leftrightarrow': '↔', r'\to': '→', r'\mathbb{R}': 'ℝ', r'\mathbb{N}': 'ℕ',
    r'\mathbb{Z}': 'ℤ', r'\mathbb{Q}': 'ℚ', r'\mathbb{C}': 'ℂ',
    r'\sqrt': '√', r'\int': '∫', r'\sum': '∑', r'\prod': '∏',
    r'\cos': 'cos', r'\sin': 'sin', r'\tan': 'tan', r'\cot': 'cot', r'\lim': 'lim',
    r'\log': 'log', r'\ln': 'ln',
}

_SUPERSCRIPT_MAP = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'n': 'ⁿ', 'i': 'ⁱ', 'x': 'ˣ', 'y': 'ʸ', 'k': 'ᵏ', 'm': 'ᵐ'
}

_SUBSCRIPT_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
    'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
    'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
    'v': 'ᵥ', 'x': 'ₓ'
}


def clean_latex_table_environment(text: str) -> str:
    """Biến đổi môi trường array/matrix/table của LaTeX thành dạng bảng văn bản thuần dòng/cột."""
    def replace_array(match):
        content = match.group(1)
        content = re.sub(r'\\hline|\\vline', '', content)
        rows = content.split(r'\\')
        cleaned_rows = []
        for r in rows:
            r_str = r.strip()
            if not r_str:
                continue
            cols = [c.strip() for c in r_str.split('&')]
            cleaned_rows.append(' | '.join(cols))
        return '\n' + '\n'.join(cleaned_rows) + '\n'

    pattern = r'\\begin\{(?:array|matrix|pmatrix|bmatrix|vmatrix)\}(?:\{.*?\})?(.*?)\\end\{(?:array|matrix|pmatrix|bmatrix|vmatrix)\}'
    return re.sub(pattern, replace_array, text, flags=re.DOTALL)


def latex_to_unicode_math(text: str) -> str:
    """
    Chuyển đổi mã LaTeX thành ký tự Unicode toán học chuẩn cho PowerPoint DrawingML.
    Áp dụng toàn diện các bước cho TOÀN BỘ chuỗi văn bản (không cần dấu $ bao quanh).
    """
    if not isinstance(text, str):
        return str(text or '')

    text = clean_xml_string(text)
    text = clean_latex_table_environment(text)
    text = text.replace(r'\(', '').replace(r'\)', '').replace('$', '')

    # Chuẩn hóa các ký hiệu toán học so sánh phổ biến
    text = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', text)
    text = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', text)

    # Chuyển đổi phân số \frac{a}{b} -> a/b hoặc (a)/(b)
    def _convert_frac(match):
        num, den = match.group(1).strip(), match.group(2).strip()
        need_paren_num = any(op in num for op in ['+', '-', ' ']) and not (num.startswith('(') and num.endswith(')'))
        need_paren_den = any(op in den for op in ['+', '-', ' ']) and not (den.startswith('(') and den.endswith(')'))
        n_str = f"({num})" if need_paren_num else num
        d_str = f"({den})" if need_paren_den else den
        return f"{n_str}/{d_str}"

    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', _convert_frac, text)

    for k in sorted(_GREEK_MAP.keys(), key=len, reverse=True):
        text = text.replace(k, _GREEK_MAP[k])

    for k in sorted(_SYMBOL_MAP.keys(), key=len, reverse=True):
        text = text.replace(k, _SYMBOL_MAP[k])

    def convert_script(match):
        script_type, body = match.groups()
        char_map = _SUPERSCRIPT_MAP if script_type == '^' else _SUBSCRIPT_MAP
        return ''.join(char_map.get(ch, ch) for ch in body)

    text = re.sub(r'([\^_])\{([^}]+)\}', convert_script, text)
    text = re.sub(r'([\^_])([0-9a-zA-Z\+\-\=\(\)])', convert_script, text)

    text = re.sub(r'\\(?:newline|quad|qquad|left|right|text|mathrm|mathbf|mathit|vec|bar|hat)', ' ', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\\+', ' ', text)

    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def render_latex_to_bytes(latex_str: str) -> bytes:
    """
    Render công thức LaTeX ra ảnh PNG chuẩn nét (300 DPI).
    Tự động co giãn kích thước font theo độ dài công thức (Adaptive Font Scaling)
    và có 3 tầng Fallback an toàn tuyệt đối, chống crash 100%.
    """
    if not latex_str or not isinstance(latex_str, str):
        # Trả về 1x1 transparent PNG chuẩn
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'

    clean_str = latex_str.replace(r'\(', '').replace(r'\)', '').strip()

    clean_str = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', clean_str)
    clean_str = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', clean_str)
    clean_str = re.sub(r'\\implies(?![a-zA-Z])', r'\\Rightarrow', clean_str)
    clean_str = re.sub(r'\\iff(?![a-zA-Z])', r'\\Leftrightarrow', clean_str)
    clean_str = re.sub(r'\\to(?![a-zA-Z])', r'\\rightarrow', clean_str)
    clean_str = clean_str.replace(r'\uparrow', r'\nearrow').replace(r'\downarrow', r'\searrow')
    clean_str = clean_str.replace(r'\quad', ' ').replace(r'\qquad', ' ')
    clean_str = clean_str.replace(r'\tg', r'\tan').replace(r'\ctg', r'\cot')
    clean_str = re.sub(r'\\text\{([^}]+)\}', r'\1', clean_str)
    clean_str = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', clean_str)

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
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, dpi=300, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        plt.close(fig)
        try:
            # Fallback 1: render bằng Unicode text
            fig, ax = plt.subplots(figsize=(0.1, 0.1))
            ax.axis('off')
            unicode_str = latex_to_unicode_math(latex_str)
            ax.text(
                0.5, 0.5, unicode_str,
                fontsize=calc_fallback_font, ha='center', va='center', color='#1e3a8a', fontname='Arial'
            )
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, dpi=300, transparent=True)
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()
        except Exception:
            try:
                plt.close(fig)
            except Exception:
                pass
            # Fallback 2: 1x1 transparent PNG tuyệt đối an toàn
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'


def _plain(obj):
    """Đưa Enum / Pydantic model về kiểu Python thuần (str, dict, list)."""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "model_dump"):
        return _plain(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


# Bảng màu chuẩn Academic Sư phạm (Đồng bộ 100% với giao diện Studio Web)
COLOR_NAVY = RGBColor(15, 43, 92)          # #0f2b5c: Header & tiêu đề chính
COLOR_ROYAL_BLUE = RGBColor(37, 99, 235)   # #2563eb: Điểm nhấn, nút, bullets
COLOR_ACCENT_BLUE = RGBColor(59, 130, 246) # #3b82f6: Đường viền accent header
COLOR_TEXT_MAIN = RGBColor(30, 41, 59)     # #1e293b: Văn bản nội dung
COLOR_TEXT_MUTED = RGBColor(71, 85, 105)   # #475569: Phụ đề & chú thích
COLOR_FOOTER = RGBColor(148, 163, 184)     # #94a3b8: Footer trang
COLOR_BG_FORMULA = RGBColor(248, 250, 252) # #f8fafc: Khung công thức
COLOR_BORDER_FORMULA = RGBColor(191, 219, 254) # #bfdbfe: Viền khung công thức
COLOR_CARD_BORDER = RGBColor(226, 232, 240)    # #e2e8f0: Viền card đồ thị
COLOR_WHITE = RGBColor(255, 255, 255)

# Bảng màu chuyên biệt cho Slide Trắc nghiệm (Task 18.1)
COLOR_QUIZ_A = RGBColor(37, 99, 235)           # #2563eb - Royal Blue
COLOR_QUIZ_B = RGBColor(5, 150, 105)          # #059669 - Emerald Green
COLOR_QUIZ_C = RGBColor(217, 119, 6)          # #d97706 - Amber Orange
COLOR_QUIZ_D = RGBColor(124, 58, 237)         # #7c3aed - Violet Purple
COLOR_QUIZ_CORRECT_BG = RGBColor(240, 253, 244) # #f0fdf4 - Light Mint Green
COLOR_QUIZ_CORRECT_BORDER = RGBColor(34, 197, 94) # #22c55e - Emerald Green
COLOR_QUIZ_CARD_BG = RGBColor(248, 250, 252)  # #f8fafc - Soft Slate
COLOR_QUIZ_CARD_BORDER = RGBColor(226, 232, 240) # #e2e8f0 - Slate Border
COLOR_QUIZ_BADGE_BG = RGBColor(238, 242, 255) # #eef2ff - Indigo Tint

# Từ điển tên chuẩn SGK cho các khối đa diện 3D WebGL (Task 18.2)
POLYHEDRON_LABELS = {
    'cube': "Hình Lập Phương ABCD.A'B'C'D'",
    'pyramid_square': "Hình Chóp Tứ Giác S.ABCD",
    'pyramid_triangle': "Hình Chóp Tam Giác S.ABC",
    'prism_triangle': "Hình Lăng Trụ Đứng ABC.A'B'C'",
    'cone': "Hình Nón Tròn Xoay (SGK)",
    'cylinder': "Hình Trụ Tròn Xoay (SGK)",
    'sphere': "Mặt Cầu & Khối Cầu (SGK)",
    'tetrahedron': "Tứ Diện Đều S.ABC",
    'parallelepiped': "Hình Hộp Chữ Nhật ABCD.A'B'C'D'",
    'truncated_pyramid': "Hình Chóp Cụt Tứ Giác Đều",
}


def calculate_auto_fit_font(
    text: str,
    max_chars_thresholds: List[tuple],
    default_pt: float
) -> float:
    """
    Task 18.4: Giải thuật tính toán cỡ chữ tự động co giãn (Auto-fit Font Calculation).
    Duyệt qua danh sách các ngưỡng độ dài (ngưỡng_ký_tự, font_size_pt) đã sắp xếp giảm dần,
    trả về font size tối ưu chống tràn khung hình và tránh đè lên các thành phần khác.
    """
    clean_len = len(str(text or "").strip())
    for threshold, size_pt in sorted(max_chars_thresholds, key=lambda x: x[0], reverse=True):
        if clean_len > threshold:
            return size_pt
    return default_pt


def build_slide_header(slide, slide_idx: int, total_slides: int, slide_type: str):
    """Vẽ thanh Header Academic Navy ở đỉnh slide (Mô phỏng chuẩn Web Studio)"""
    # 1. Thanh nền Navy
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10.0), Inches(0.65))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = COLOR_NAVY
    top_bar.line.fill.background()

    # 2. Đường kẻ accent xanh dương
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.65), Inches(10.0), Inches(0.04))
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_ACCENT_BLUE
    accent.line.fill.background()

    # 3. Badge số thứ tự slide (bên trái)
    badge_l = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(0.13), Inches(1.3), Inches(0.38))
    badge_l.fill.solid()
    badge_l.fill.fore_color.rgb = RGBColor(30, 58, 138)
    badge_l.line.color.rgb = RGBColor(96, 165, 250)
    badge_l.line.width = Pt(1)
    tf_l = badge_l.text_frame
    tf_l.word_wrap = False
    tf_l.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_l = tf_l.paragraphs[0]
    p_l.alignment = PP_ALIGN.CENTER
    r_l = p_l.add_run()
    r_l.text = f'SLIDE {slide_idx}/{total_slides}'
    r_l.font.name = 'Arial'
    r_l.font.size = Pt(9.5)
    r_l.font.bold = True
    r_l.font.color.rgb = COLOR_WHITE

    # 4. Badge loại slide (bên phải)
    clean_type = str(slide_type or 'SLIDE').replace('_', ' ').upper()
    badge_r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.1), Inches(0.13), Inches(1.5), Inches(0.38))
    badge_r.fill.solid()
    badge_r.fill.fore_color.rgb = COLOR_ROYAL_BLUE
    badge_r.line.fill.background()
    tf_r = badge_r.text_frame
    tf_r.word_wrap = False
    tf_r.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_r = tf_r.paragraphs[0]
    p_r.alignment = PP_ALIGN.CENTER
    r_r = p_r.add_run()
    r_r.text = clean_type
    r_r.font.name = 'Arial'
    r_r.font.size = Pt(8.5)
    r_r.font.bold = True
    r_r.font.color.rgb = COLOR_WHITE


def build_title_slide(slide, slide_data: dict, subject: str, grade: Any):
    """Thiết kế Slide Bìa (TITLE_SLIDE) chuẩn Sư phạm trang nhã"""
    # Tag Pill Môn học & Lớp
    tag_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.2), Inches(1.15), Inches(3.6), Inches(0.42))
    tag_pill.fill.solid()
    tag_pill.fill.fore_color.rgb = RGBColor(239, 246, 255)
    tag_pill.line.color.rgb = COLOR_BORDER_FORMULA
    tag_pill.line.width = Pt(1)
    tf_pill = tag_pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_pill = tf_pill.paragraphs[0]
    p_pill.alignment = PP_ALIGN.CENTER
    r_pill = p_pill.add_run()
    r_pill.text = f'MÔN {str(subject).upper()} - LỚP {grade}'
    r_pill.font.name = 'Arial'
    r_pill.font.size = Pt(10.5)
    r_pill.font.bold = True
    r_pill.font.color.rgb = COLOR_ROYAL_BLUE

    # Tiêu đề bài học chính (Hero Title) với Auto-fit font size
    title_text = latex_to_unicode_math(slide_data.get('title') or '')
    font_pt = calculate_auto_fit_font(
        title_text,
        [(110, 20.0), (80, 22.0), (55, 25.0), (35, 28.0)],
        default_pt=32.0
    )
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(8.4), Inches(1.4))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_title = tf_title.paragraphs[0]
    p_title.alignment = PP_ALIGN.CENTER
    r_t = p_title.add_run()
    r_t.text = title_text
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(font_pt)
    r_t.font.bold = True
    r_t.font.color.rgb = COLOR_NAVY

    # Phụ đề bài học với Auto-fit font size
    subtitle_text = latex_to_unicode_math(slide_data.get('subtitle') or '')
    if subtitle_text:
        sub_font_pt = calculate_auto_fit_font(
            subtitle_text,
            [(100, 12.5), (65, 14.0)],
            default_pt=16.0
        )
        sub_box = slide.shapes.add_textbox(Inches(1.0), Inches(3.3), Inches(8.0), Inches(0.9))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.alignment = PP_ALIGN.CENTER
        r_sub = p_sub.add_run()
        r_sub.text = subtitle_text
        r_sub.font.name = 'Times New Roman'
        r_sub.font.size = Pt(sub_font_pt)
        r_sub.font.italic = True
        r_sub.font.color.rgb = COLOR_TEXT_MUTED

    # Tagline chuẩn Công văn 5512
    tag_box = slide.shapes.add_textbox(Inches(2.0), Inches(4.55), Inches(6.0), Inches(0.4))
    tf_tag = tag_box.text_frame
    p_tag = tf_tag.paragraphs[0]
    p_tag.alignment = PP_ALIGN.CENTER
    r_tag = p_tag.add_run()
    r_tag.text = 'KẾ HOẠCH BÀI DẠY THEO CÔNG VĂN 5512'
    r_tag.font.name = 'Arial'
    r_tag.font.size = Pt(10)
    r_tag.font.bold = True
    r_tag.font.color.rgb = RGBColor(100, 116, 139)


def build_content_slide(slide, slide_data: dict, slide_idx: int, total_slides: int, subject: str, grade: Any):
    """Thiết kế Slide Nội dung (CONCEPT, EXERCISE, SUMMARY, v.v.)"""
    # 1. Tiêu đề slide với Auto-fit (Task 18.4 Text Overflow Guard)
    title_text = latex_to_unicode_math(slide_data.get('title') or '')
    t_font_pt = calculate_auto_fit_font(
        title_text,
        [(120, 16.5), (75, 18.5), (45, 20.0)],
        default_pt=22.0
    )
    t_height = Inches(0.65) if t_font_pt <= 18.5 else Inches(0.55)
    t_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(8.8), t_height)
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    r_t = p_t.add_run()
    r_t.text = title_text
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(t_font_pt)
    r_t.font.bold = True
    r_t.font.color.rgb = COLOR_NAVY

    # 2. Phụ đề slide (vị trí động dựa trên chiều cao tiêu đề)
    subtitle_text = latex_to_unicode_math(slide_data.get('subtitle') or '')
    if subtitle_text:
        sub_top = Inches(0.8) + t_height + Inches(0.04)
        sub_font_pt = calculate_auto_fit_font(
            subtitle_text,
            [(90, 11.5), (50, 12.5)],
            default_pt=13.0
        )
        sub_box = slide.shapes.add_textbox(Inches(0.6), sub_top, Inches(8.8), Inches(0.35))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        r_sub = p_sub.add_run()
        r_sub.text = subtitle_text
        r_sub.font.name = 'Times New Roman'
        r_sub.font.size = Pt(sub_font_pt)
        r_sub.font.italic = True
        r_sub.font.color.rgb = COLOR_TEXT_MUTED
        content_top = sub_top + Inches(0.38)
    else:
        content_top = Inches(0.8) + t_height + Inches(0.10)

    chart_spec = slide_data.get('chart_spec')
    has_chart = is_plottable(chart_spec)

    # Task 14.3 & Task 18.2: Nhận diện ảnh chụp mô hình 3D WebGL từ frontend hoặc cấp slide/deck
    snapshot_3d_url = (
        slide_data.get('snapshot_3d_base64')
        or slide_data.get('snapshot_3d')
        or slide_data.get('image_base64')
    )
    snapshot_stream = decode_base64_data_url(snapshot_3d_url) if snapshot_3d_url else None
    has_3d_snapshot = bool(snapshot_stream)

    bullets = [b for b in (slide_data.get('bullet_points') or []) if b]
    formula_latex = slide_data.get('main_definition_latex') or ''

    # TRƯỜNG HỢP 1: CÓ ĐỒ THỊ HÀM SỐ (BỐ CỤC 2 CỘT CHUẨN WEB STUDIO)
    if has_chart and not has_3d_snapshot:
        w_left = Inches(4.8)

        # Cột Trái: Bullet Points với Auto-fit font & khoảng cách dòng (Task 18.4)
        n_bullets = len(bullets)
        total_chars = sum(len(b) for b in bullets)

        if formula_latex:
            text_h = Inches(1.9)
            if n_bullets > 4 or total_chars > 200:
                b_font_pt = 11.0
                b_space_after = Pt(2)
            elif n_bullets > 3 or total_chars > 130:
                b_font_pt = 11.5
                b_space_after = Pt(2.5)
            elif n_bullets > 2 or total_chars > 80:
                b_font_pt = 12.0
                b_space_after = Pt(3)
            else:
                b_font_pt = 13.0
                b_space_after = Pt(4)
        else:
            text_h = Inches(3.2)
            if n_bullets > 5 or total_chars > 320:
                b_font_pt = 11.5
                b_space_after = Pt(2.5)
            elif n_bullets > 3 or total_chars > 180:
                b_font_pt = 12.5
                b_space_after = Pt(3.5)
            else:
                b_font_pt = 13.0
                b_space_after = Pt(4)

        text_box = slide.shapes.add_textbox(Inches(0.6), content_top, w_left, text_h)
        tf_c = text_box.text_frame
        tf_c.word_wrap = True
        for b_idx, b in enumerate(bullets):
            p_b = tf_c.paragraphs[0] if b_idx == 0 else tf_c.add_paragraph()
            p_b.space_after = b_space_after
            r_bullet = p_b.add_run()
            r_bullet.text = '•  '
            r_bullet.font.name = 'Arial'
            r_bullet.font.bold = True
            r_bullet.font.size = Pt(b_font_pt)
            r_bullet.font.color.rgb = COLOR_ROYAL_BLUE
            r_txt = p_b.add_run()
            r_txt.text = latex_to_unicode_math(b)
            r_txt.font.name = 'Times New Roman'
            r_txt.font.size = Pt(b_font_pt)
            r_txt.font.color.rgb = COLOR_TEXT_MAIN

        # Cột Trái: Formula Card Box (nằm phía dưới bullets)
        if formula_latex:
            f_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(3.85), w_left, Inches(1.2))
            f_box.fill.solid()
            f_box.fill.fore_color.rgb = COLOR_BG_FORMULA
            f_box.line.color.rgb = COLOR_BORDER_FORMULA
            f_box.line.width = Pt(1)

            f_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(3.85), Inches(0.06), Inches(1.2))
            f_accent.fill.solid()
            f_accent.fill.fore_color.rgb = COLOR_ROYAL_BLUE
            f_accent.line.fill.background()

            try:
                png_bytes = render_latex_to_bytes(formula_latex)
                with Image.open(io.BytesIO(png_bytes)) as im:
                    px_w, px_h = im.size
                asp = px_w / max(px_h, 1)
                max_w = Inches(4.4)
                max_h = Inches(1.0)
                if asp >= (max_w / max_h):
                    img_w = max_w
                    img_h = max_w / asp
                else:
                    img_h = max_h
                    img_w = max_h * asp
                img_left = Inches(0.6) + (w_left - img_w) / 2
                img_top = Inches(3.85) + (Inches(1.2) - img_h) / 2
                slide.shapes.add_picture(io.BytesIO(png_bytes), img_left, img_top, width=img_w, height=img_h)
            except Exception as e:
                print(f"Lỗi chèn ảnh công thức: {e}")

        # Cột Phải: Matplotlib Plot Card
        card_h = min(Inches(3.30), Inches(5.10) - content_top)
        card_right = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.6), content_top, Inches(3.8), card_h)
        card_right.fill.solid()
        card_right.fill.fore_color.rgb = COLOR_WHITE
        card_right.line.color.rgb = COLOR_CARD_BORDER
        card_right.line.width = Pt(1)

        try:
            chart_png = generate_math_plot(chart_spec, figsize=(4.8, 3.4))
            slide.shapes.add_picture(io.BytesIO(chart_png), Inches(5.7), content_top + Inches(0.08), width=Inches(3.6), height=Inches(2.45))
        except Exception as e:
            print(f"Lỗi chèn ảnh đồ thị: {e}")

        # Badge Đồ thị Matplotlib Native
        p_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.45), content_top + Inches(2.62), Inches(2.1), Inches(0.26))
        p_badge.fill.solid()
        p_badge.fill.fore_color.rgb = RGBColor(224, 242, 254)
        p_badge.line.fill.background()
        tf_pb = p_badge.text_frame
        tf_pb.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_run = tf_pb.paragraphs[0].add_run()
        p_run.text = 'Đồ thị Matplotlib Native'
        p_run.font.name = 'Arial'
        p_run.font.size = Pt(8.5)
        p_run.font.bold = True
        p_run.font.color.rgb = RGBColor(3, 105, 161)

        if chart_spec.get('chart_title'):
            ct_box = slide.shapes.add_textbox(Inches(5.7), content_top + Inches(2.9), Inches(3.6), Inches(0.35))
            ct_p = ct_box.text_frame.paragraphs[0]
            ct_p.alignment = PP_ALIGN.CENTER
            ct_r = ct_p.add_run()
            ct_r.text = chart_spec.get('chart_title')
            ct_r.font.name = 'Arial'
            ct_r.font.size = Pt(8.5)
            ct_r.font.color.rgb = COLOR_TEXT_MUTED

    # TRƯỜNG HỢP 2: CÓ ẢNH SNAPSHOT MÔ HÌNH HÌNH HỌC 3D (TASK 14.3)
    elif has_3d_snapshot:
        w_left = Inches(4.8)

        # Cột Trái: Bullet Points với Auto-fit font & khoảng cách dòng (Task 18.4)
        n_bullets = len(bullets)
        total_chars = sum(len(b) for b in bullets)

        if formula_latex:
            text_h = Inches(1.9)
            if n_bullets > 4 or total_chars > 200:
                b_font_pt = 11.0
                b_space_after = Pt(2)
            elif n_bullets > 3 or total_chars > 130:
                b_font_pt = 11.5
                b_space_after = Pt(2.5)
            elif n_bullets > 2 or total_chars > 80:
                b_font_pt = 12.0
                b_space_after = Pt(3)
            else:
                b_font_pt = 13.0
                b_space_after = Pt(4)
        else:
            text_h = Inches(3.2)
            if n_bullets > 5 or total_chars > 320:
                b_font_pt = 11.5
                b_space_after = Pt(2.5)
            elif n_bullets > 3 or total_chars > 180:
                b_font_pt = 12.5
                b_space_after = Pt(3.5)
            else:
                b_font_pt = 13.0
                b_space_after = Pt(4)

        text_box = slide.shapes.add_textbox(Inches(0.6), content_top, w_left, text_h)
        tf_c = text_box.text_frame
        tf_c.word_wrap = True
        for b_idx, b in enumerate(bullets):
            p_b = tf_c.paragraphs[0] if b_idx == 0 else tf_c.add_paragraph()
            p_b.space_after = b_space_after
            r_bullet = p_b.add_run()
            r_bullet.text = '•  '
            r_bullet.font.name = 'Arial'
            r_bullet.font.bold = True
            r_bullet.font.size = Pt(b_font_pt)
            r_bullet.font.color.rgb = COLOR_ROYAL_BLUE
            r_txt = p_b.add_run()
            r_txt.text = latex_to_unicode_math(b)
            r_txt.font.name = 'Times New Roman'
            r_txt.font.size = Pt(b_font_pt)
            r_txt.font.color.rgb = COLOR_TEXT_MAIN

        # Cột Trái: Formula Card Box (nằm phía dưới bullets)
        if formula_latex:
            f_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(3.85), w_left, Inches(1.2))
            f_box.fill.solid()
            f_box.fill.fore_color.rgb = COLOR_BG_FORMULA
            f_box.line.color.rgb = COLOR_BORDER_FORMULA
            f_box.line.width = Pt(1)

            f_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(3.85), Inches(0.06), Inches(1.2))
            f_accent.fill.solid()
            f_accent.fill.fore_color.rgb = COLOR_ROYAL_BLUE
            f_accent.line.fill.background()

            try:
                png_bytes = render_latex_to_bytes(formula_latex)
                with Image.open(io.BytesIO(png_bytes)) as im:
                    px_w, px_h = im.size
                asp = px_w / max(px_h, 1)
                max_w = Inches(4.4)
                max_h = Inches(1.0)
                if asp >= (max_w / max_h):
                    img_w = max_w
                    img_h = max_w / asp
                else:
                    img_h = max_h
                    img_w = max_h * asp
                img_left = Inches(0.6) + (w_left - img_w) / 2
                img_top = Inches(3.85) + (Inches(1.2) - img_h) / 2
                slide.shapes.add_picture(io.BytesIO(png_bytes), img_left, img_top, width=img_w, height=img_h)
            except Exception as e:
                print(f"Lỗi chèn ảnh công thức: {e}")

        # Cột Phải: Card Khung Hình Học Không Gian 3D (Task 14.3, 14.4 & Task 18.2)
        card_h = min(Inches(3.30), Inches(5.10) - content_top)
        card_right = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.6), content_top, Inches(3.8), card_h)
        card_right.fill.solid()
        card_right.fill.fore_color.rgb = COLOR_WHITE
        card_right.line.color.rgb = COLOR_CARD_BORDER
        card_right.line.width = Pt(1)

        try:
            # Task 14.4 & Task 18.2: Thuật toán Box-Fit bảo toàn tỉ lệ khung hình (Aspect Ratio) và căn giữa
            with Image.open(snapshot_stream) as im:
                px_w, px_h = im.size
            snapshot_stream.seek(0)

            box_l = Inches(5.7)
            box_t = content_top + Inches(0.08)
            box_w = Inches(3.6)
            box_h = Inches(2.45)

            fit_left, fit_top, fit_w, fit_h = compute_aspect_preserving_fit(
                px_w, px_h, box_l, box_t, box_w, box_h
            )

            # Nhúng byte stream ảnh snapshot 3D WebGL vào slide PowerPoint theo đúng tỉ lệ (bảo toàn int EMU)
            slide.shapes.add_picture(snapshot_stream, int(fit_left), int(fit_top), width=int(fit_w), height=int(fit_h))
        except Exception as e:
            print(f"Lỗi chèn ảnh snapshot 3D: {e}")

        # Badge Mô hình Không gian 3D WebGL
        p_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.3), content_top + Inches(2.62), Inches(2.4), Inches(0.26))
        p_badge.fill.solid()
        p_badge.fill.fore_color.rgb = RGBColor(224, 242, 254)
        p_badge.line.fill.background()
        tf_pb = p_badge.text_frame
        tf_pb.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_run = tf_pb.paragraphs[0].add_run()
        p_run.text = 'Mô hình 3D WebGL (SGK)'
        p_run.font.name = 'Arial'
        p_run.font.size = Pt(8.5)
        p_run.font.bold = True
        p_run.font.color.rgb = RGBColor(3, 105, 161)

        # Tiêu đề chú thích loại khối đa diện chuẩn SGK (Task 18.2)
        poly_type = str(slide_data.get('polyhedron_type') or '').lower().strip()
        poly_labels = POLYHEDRON_LABELS
        poly_title = (
            slide_data.get('polyhedron_label')
            or poly_labels.get(poly_type)
            or slide_data.get('image_prompt')
            or 'Hình học không gian trực quan'
        )
        pt_box = slide.shapes.add_textbox(Inches(5.7), content_top + Inches(2.9), Inches(3.6), Inches(0.35))
        pt_p = pt_box.text_frame.paragraphs[0]
        pt_p.alignment = PP_ALIGN.CENTER
        pt_r = pt_p.add_run()
        pt_r.text = poly_title
        pt_r.font.name = 'Arial'
        pt_r.font.size = Pt(8.5)
        pt_r.font.color.rgb = COLOR_TEXT_MUTED

    # TRƯỜNG HỢP 3: KHÔNG CÓ ĐỒ THỊ HOẶC ẢNH 3D (BỐ CỤC TOÀN CHIỀU RỘNG TRANG NHÃ)
    else:
        w_full = Inches(8.8)
        n_bullets = len(bullets)
        total_chars = sum(len(b) for b in bullets)

        if formula_latex:
            text_h = Inches(2.0)
            if n_bullets > 4 or total_chars > 300:
                b_font_pt = 12.5
                b_space_after = Pt(3)
            elif n_bullets > 3 or total_chars > 180:
                b_font_pt = 13.5
                b_space_after = Pt(4)
            else:
                b_font_pt = 15.0
                b_space_after = Pt(5)
        else:
            text_h = Inches(3.3)
            if n_bullets > 6 or total_chars > 500:
                b_font_pt = 12.5
                b_space_after = Pt(3)
            elif n_bullets > 4 or total_chars > 320:
                b_font_pt = 13.5
                b_space_after = Pt(4)
            elif n_bullets > 2:
                b_font_pt = 15.0
                b_space_after = Pt(5)
            else:
                b_font_pt = 16.0
                b_space_after = Pt(6)

        text_box = slide.shapes.add_textbox(Inches(0.6), content_top, w_full, text_h)
        tf_c = text_box.text_frame
        tf_c.word_wrap = True
        for b_idx, b in enumerate(bullets):
            p_b = tf_c.paragraphs[0] if b_idx == 0 else tf_c.add_paragraph()
            p_b.space_after = b_space_after
            r_bullet = p_b.add_run()
            r_bullet.text = '•  '
            r_bullet.font.name = 'Arial'
            r_bullet.font.bold = True
            r_bullet.font.size = Pt(b_font_pt)
            r_bullet.font.color.rgb = COLOR_ROYAL_BLUE
            r_txt = p_b.add_run()
            r_txt.text = latex_to_unicode_math(b)
            r_txt.font.name = 'Times New Roman'
            r_txt.font.size = Pt(b_font_pt)
            r_txt.font.color.rgb = COLOR_TEXT_MAIN

        if formula_latex:
            f_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(3.85), Inches(7.0), Inches(1.2))
            f_box.fill.solid()
            f_box.fill.fore_color.rgb = COLOR_BG_FORMULA
            f_box.line.color.rgb = COLOR_BORDER_FORMULA
            f_box.line.width = Pt(1)

            f_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(3.85), Inches(0.06), Inches(1.2))
            f_accent.fill.solid()
            f_accent.fill.fore_color.rgb = COLOR_ROYAL_BLUE
            f_accent.line.fill.background()

            try:
                png_bytes = render_latex_to_bytes(formula_latex)
                with Image.open(io.BytesIO(png_bytes)) as im:
                    px_w, px_h = im.size
                asp = px_w / max(px_h, 1)
                max_w = Inches(6.6)
                max_h = Inches(1.0)
                if asp >= (max_w / max_h):
                    img_w = max_w
                    img_h = max_w / asp
                else:
                    img_h = max_h
                    img_w = max_h * asp
                img_left = Inches(1.5) + (Inches(7.0) - img_w) / 2
                img_top = Inches(3.85) + (Inches(1.2) - img_h) / 2
                slide.shapes.add_picture(io.BytesIO(png_bytes), img_left, img_top, width=img_w, height=img_h)
            except Exception as e:
                print(f"Lỗi chèn ảnh công thức: {e}")

    # 3. Footer tinh tế ở chân slide
    ft_l = slide.shapes.add_textbox(Inches(0.6), Inches(5.26), Inches(5.0), Inches(0.25))
    p_ftl = ft_l.text_frame.paragraphs[0]
    r_ftl = p_ftl.add_run()
    r_ftl.text = f'Kế hoạch bài dạy môn {subject} - Lớp {grade}'
    r_ftl.font.name = 'Arial'
    r_ftl.font.size = Pt(8.5)
    r_ftl.font.color.rgb = COLOR_FOOTER

    ft_r = slide.shapes.add_textbox(Inches(8.0), Inches(5.26), Inches(1.4), Inches(0.25))
    p_ftr = ft_r.text_frame.paragraphs[0]
    p_ftr.alignment = PP_ALIGN.RIGHT
    r_ftr = p_ftr.add_run()
    r_ftr.text = f'Trang {slide_idx}/{total_slides}'
    r_ftr.font.name = 'Arial'
    r_ftr.font.size = Pt(8.5)
    r_ftr.font.color.rgb = COLOR_FOOTER


def build_quiz_slide(slide, slide_data: dict, slide_idx: int, total_slides: int, subject: str, grade: Any):
    """
    Task 18.1: Thiết kế Layout Native DrawingML Cho Slide Trắc Nghiệm (QUIZ_SLIDE).
    - Header Tag Pill: 'CÂU HỎI TRẮC NGHIỆM' hoặc activity_type (Rounded Rectangle Indigo).
    - Khung đề bài / Question Prompt Box: Textbox font Times New Roman, bold, Pt(13-15.5) tự động co giãn.
    - Lưới 2x2 Ô Phương án A, B, C, D (4 Card):
      + Shape bo góc: MSO_SHAPE.ROUNDED_RECTANGLE (#f8fafc hoặc #f0fdf4 nếu highlight đáp án đúng).
      + Huy hiệu tròn A/B/C/D: MSO_SHAPE.OVAL với bảng màu nhận diện sư phạm chuẩn mực:
        * A: Xanh Royal Blue (#2563eb)
        * B: Xanh Ngọc Lục Bảo (#059669)
        * C: Vàng Hổ Phách (#d97706)
        * D: Tím Hoa Cà (#7c3aed)
      + Nội dung văn bản phương án: Textbox chứa công thức Toán học được chuyển đổi sang Unicode Math rõ nét.
    - Footer tinh tế đồng bộ chân slide.
    """
    # 1. Header Tag Pill (Phân loại hoạt động sư phạm)
    tag_label = slide_data.get("activity_type") or "CÂU HỎI TRẮC NGHIỆM"
    tag_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.6), Inches(0.75), Inches(2.4), Inches(0.32)
    )
    tag_shape.fill.solid()
    tag_shape.fill.fore_color.rgb = COLOR_QUIZ_BADGE_BG
    tag_shape.line.color.rgb = COLOR_ROYAL_BLUE
    tag_shape.line.width = Pt(1)
    tf_tag = tag_shape.text_frame
    tf_tag.word_wrap = False
    tf_tag.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_tag = tf_tag.paragraphs[0]
    p_tag.alignment = PP_ALIGN.CENTER
    r_tag = p_tag.add_run()
    r_tag.text = tag_label.upper()
    r_tag.font.name = "Arial"
    r_tag.font.size = Pt(9.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_ROYAL_BLUE

    # 2. Khung Đề bài (Question Prompt Box)
    question_raw = (
        slide_data.get("question")
        or slide_data.get("prompt")
        or (slide_data.get("bullet_points") and slide_data["bullet_points"][0])
        or slide_data.get("title")
        or "Chọn khẳng định đúng trong các phương án sau:"
    )
    question_text = latex_to_unicode_math(question_raw)

    # Tự động điều chỉnh kích cỡ font câu hỏi theo độ dài (Task 18.4 Auto-fit & Text Overflow Guard)
    q_font_pt = calculate_auto_fit_font(
        question_text,
        [(180, 12.5), (120, 13.5), (80, 14.5)],
        default_pt=15.5
    )

    q_box = slide.shapes.add_textbox(Inches(0.6), Inches(1.12), Inches(8.8), Inches(1.10))
    tf_q = q_box.text_frame
    tf_q.word_wrap = True
    tf_q.vertical_anchor = MSO_ANCHOR.TOP
    p_q = tf_q.paragraphs[0]
    r_q = p_q.add_run()
    r_q.text = question_text
    r_q.font.name = "Times New Roman"
    r_q.font.size = Pt(q_font_pt)
    r_q.font.bold = True
    r_q.font.color.rgb = COLOR_NAVY

    # 3. Lưới 2x2 Ô Phương án A, B, C, D (4 Cards)
    raw_options = slide_data.get("quiz_options") or []
    if not raw_options:
        raw_options = [
            {"label": "A", "text": "Phương án A", "is_correct": True},
            {"label": "B", "text": "Phương án B", "is_correct": False},
            {"label": "C", "text": "Phương án C", "is_correct": False},
            {"label": "D", "text": "Phương án D", "is_correct": False},
        ]

    BADGE_COLOR_MAP = {
        "A": COLOR_QUIZ_A,
        "B": COLOR_QUIZ_B,
        "C": COLOR_QUIZ_C,
        "D": COLOR_QUIZ_D,
    }
    DEFAULT_BADGE_COLORS = [COLOR_QUIZ_A, COLOR_QUIZ_B, COLOR_QUIZ_C, COLOR_QUIZ_D]

    CARD_W = Inches(4.25)
    CARD_H = Inches(1.30)
    COL_POSITIONS = [Inches(0.60), Inches(5.15)]
    ROW_POSITIONS = [Inches(2.35), Inches(3.80)]

    highlight_correct = bool(slide_data.get("highlight_correct") or slide_data.get("show_correct"))

    for i in range(min(4, len(raw_options))):
        opt = raw_options[i]
        if isinstance(opt, dict):
            label = str(opt.get("label") or chr(65 + i)).strip()
            opt_text = str(opt.get("text") or "")
            is_correct = bool(opt.get("is_correct", False))
        else:
            label = chr(65 + i)
            opt_text = str(opt)
            is_correct = False

        col = i % 2
        row = i // 2
        card_left = COL_POSITIONS[col]
        card_top = ROW_POSITIONS[row]

        # Background Card Shape (MSO_SHAPE.ROUNDED_RECTANGLE)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, CARD_W, CARD_H)
        card.fill.solid()
        if is_correct and highlight_correct:
            card.fill.fore_color.rgb = COLOR_QUIZ_CORRECT_BG
            card.line.color.rgb = COLOR_QUIZ_CORRECT_BORDER
            card.line.width = Pt(1.5)
        else:
            card.fill.fore_color.rgb = COLOR_QUIZ_CARD_BG
            card.line.color.rgb = COLOR_QUIZ_CARD_BORDER
            card.line.width = Pt(1)

        # Circular Badge Indicator (MSO_SHAPE.OVAL)
        badge_size = Inches(0.36)
        badge_left = card_left + Inches(0.16)
        badge_top = card_top + (CARD_H - badge_size) / 2
        badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, badge_left, badge_top, badge_size, badge_size)
        badge.fill.solid()
        badge_color = BADGE_COLOR_MAP.get(label.upper(), DEFAULT_BADGE_COLORS[i % 4])
        badge.fill.fore_color.rgb = badge_color
        badge.line.fill.background()

        tf_b = badge.text_frame
        tf_b.word_wrap = False
        tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_b = tf_b.paragraphs[0]
        p_b.alignment = PP_ALIGN.CENTER
        r_b = p_b.add_run()
        r_b.text = label.upper()
        r_b.font.name = "Arial"
        r_b.font.size = Pt(12)
        r_b.font.bold = True
        r_b.font.color.rgb = COLOR_WHITE

        # Option Text Box
        txt_left = card_left + Inches(0.60)
        txt_top = card_top + Inches(0.08)
        txt_w = CARD_W - Inches(0.72)
        txt_h = CARD_H - Inches(0.16)
        txt_box = slide.shapes.add_textbox(txt_left, txt_top, txt_w, txt_h)
        tf_t = txt_box.text_frame
        tf_t.word_wrap = True
        tf_t.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_t = tf_t.paragraphs[0]

        clean_opt_text = latex_to_unicode_math(opt_text)
        r_t = p_t.add_run()
        r_t.text = clean_opt_text
        r_t.font.name = "Times New Roman"

        opt_font_pt = calculate_auto_fit_font(
            clean_opt_text,
            [(110, 10.5), (70, 11.5), (40, 12.5)],
            default_pt=13.0
        )
        r_t.font.size = Pt(opt_font_pt)
        r_t.font.color.rgb = COLOR_TEXT_MAIN

        # Tối ưu lề trong textbox tránh tràn cạnh card
        tf_t.margin_left = Inches(0.04)
        tf_t.margin_right = Inches(0.04)
        tf_t.margin_top = Inches(0.04)
        tf_t.margin_bottom = Inches(0.04)

    # 4. Footer tinh tế ở chân slide
    ft_l = slide.shapes.add_textbox(Inches(0.6), Inches(5.26), Inches(5.0), Inches(0.25))
    p_ftl = ft_l.text_frame.paragraphs[0]
    r_ftl = p_ftl.add_run()
    r_ftl.text = f'Kế hoạch bài dạy môn {subject} - Lớp {grade}'
    r_ftl.font.name = 'Arial'
    r_ftl.font.size = Pt(8.5)
    r_ftl.font.color.rgb = COLOR_FOOTER

    ft_r = slide.shapes.add_textbox(Inches(8.0), Inches(5.26), Inches(1.4), Inches(0.25))
    p_ftr = ft_r.text_frame.paragraphs[0]
    p_ftr.alignment = PP_ALIGN.RIGHT
    r_ftr = p_ftr.add_run()
    r_ftr.text = f'Trang {slide_idx}/{total_slides}'
    r_ftr.font.name = 'Arial'
    r_ftr.font.size = Pt(8.5)
    r_ftr.font.color.rgb = COLOR_FOOTER


def build_speaker_notes(
    slide,
    slide_data: dict,
    is_quiz: bool = False,
    subject: str = "Toán học",
    grade: Any = 12
) -> Optional[str]:
    """
    Task 18.3: Nhúng Kịch bản Lời thoại & Bóc tách Bẫy Sai lầm vào Speaker Notes (PresentationML notesSlide).
    Cung cấp toàn diện tài liệu giảng dạy cho Giáo viên trong Chế độ Trình chiếu Presenter View:
    1. Lời thoại & Kịch bản tổ chức bài dạy (Chuẩn Công văn 5512/BGDĐT).
    2. Mục tiêu sư phạm và phân hóa năng lực học sinh (basic, standard, advanced).
    3. Đáp án chính xác và Phân tích bẫy sai lầm toán học (Distractor Rationales) cho câu hỏi trắc nghiệm.
    4. Các bước giải tự luận chuẩn mực SGK (worked_solution_steps) để hướng dẫn học sinh ghi chép vào vở.
    5. Công thức toán trọng tâm và định nghĩa cốt lõi cần khắc sâu.
    """
    notes_slide = getattr(slide, "notes_slide", None)
    if notes_slide is None:
        return None

    text_frame = getattr(notes_slide, "notes_text_frame", None)
    if text_frame is None:
        return None

    sections = []

    # 1. Kịch bản lời giảng & Hướng dẫn tổ chức hoạt động của Giáo viên (Công văn 5512)
    teacher_note = str(slide_data.get("teacher_note") or "").strip()
    if teacher_note:
        clean_note = clean_xml_string(teacher_note)
        sections.append(f"[Kịch bản giảng dạy dành cho Giáo viên] (Chuẩn Công văn 5512/BGDĐT):\n{clean_note}")

    # 2. Mục tiêu năng lực & Phân hóa học sinh
    target_outcome = str(slide_data.get("target_outcome") or "").strip()
    class_proficiency = str(slide_data.get("class_proficiency") or "").strip().lower()
    prof_labels = {
        "basic": "Lớp cơ bản (Nhắc lại kiến thức nền & củng cố công thức cơ bản)",
        "standard": "Lớp chuẩn (Đạt chuẩn kiến thức & kỹ năng SGK)",
        "advanced": "Lớp nâng cao (Tư duy vận dụng & bài toán phân hóa cao)"
    }
    prof_text = prof_labels.get(class_proficiency, "")

    outcome_lines = []
    if target_outcome:
        outcome_lines.append(f"- Chuẩn đầu ra: {clean_xml_string(target_outcome)}")
    if prof_text:
        outcome_lines.append(f"- Trình độ phân hóa: {prof_text}")
    if outcome_lines:
        sections.append("🎯 [Mục tiêu sư phạm & Phân hóa năng lực]:\n" + "\n".join(outcome_lines))

    # 3. Phân tích Trắc nghiệm: Đáp án đúng & Bẫy sai lầm của học sinh (Distractor Rationales)
    quiz_options = slide_data.get("quiz_options") or []
    if is_quiz or quiz_options:
        correct_opt = next((o for o in quiz_options if isinstance(o, dict) and o.get("is_correct")), None)
        quiz_sections = []
        if correct_opt:
            c_label = correct_opt.get("label", "A")
            c_text = latex_to_unicode_math(correct_opt.get("text", ""))
            quiz_sections.append(f"[Đáp án đúng chuẩn SGK]: Phương án {c_label}. {c_text}")

        distractors = [
            o for o in quiz_options
            if isinstance(o, dict) and not o.get("is_correct")
        ]
        if distractors:
            quiz_sections.append("[Phân tích bẫy sai lầm của học sinh (Distractor Rationales)]:")
            for d in distractors:
                d_label = str(d.get("label", "")).strip()
                d_rationale = str(d.get("distractor_rationale") or "").strip()
                if not d_rationale:
                    d_rationale = "Học sinh dễ nhầm lẫn trong quá trình tính toán hoặc áp dụng sai điều kiện định lý."
                quiz_sections.append(f"- Phương án {d_label}: {clean_xml_string(d_rationale)}")

        if quiz_sections:
            sections.append("💡 [Đáp án & Phân tích bẫy sai lầm trắc nghiệm]:\n" + "\n".join(quiz_sections))

    # 4. Các bước giải tự luận mẫu chuẩn mực SGK
    solution_steps = slide_data.get("worked_solution_steps") or []
    if solution_steps:
        sol_lines = [
            f"  • Bước {s_idx + 1}: {latex_to_unicode_math(step)}"
            for s_idx, step in enumerate(solution_steps)
            if step
        ]
        if sol_lines:
            sections.append("📝 [Các bước giải mẫu tự luận chi tiết chuẩn SGK]:\n" + "\n".join(sol_lines))

    # 5. Công thức toán trọng tâm & Định nghĩa
    formula_latex = str(slide_data.get("main_definition_latex") or "").strip()
    if formula_latex:
        formula_unicode = latex_to_unicode_math(formula_latex)
        sections.append(f"📐 [Công thức toán trọng tâm bài học]:\n  {formula_unicode}")

    final_notes_text = "\n\n".join(sections).strip()
    if final_notes_text:
        text_frame.text = final_notes_text
    return final_notes_text


def export_slide_deck_to_pptx(data: Union[Dict[str, Any], SlideDeckSchema]) -> io.BytesIO:
    """
    Chuyển đổi dữ liệu SlideDeck thành file PowerPoint (.pptx) chuẩn 16:9 Widescreen.
    Đồng bộ 100% về bố cục, màu sắc, font chữ và đồ thị Matplotlib với giao diện Web Studio.
    Cho phép Giáo viên chỉnh sửa, thay đổi nội dung, đổi màu tự do 100% trong PowerPoint.
    """
    if isinstance(data, (SlideDeckSchema, dict)):
        deck_dict = _plain(data)
    else:
        raise ValueError("Dữ liệu vào phải là dict hoặc SlideDeckSchema")

    slides_data = deck_dict.get("slides", [])
    total_slides = len(slides_data)
    subject = deck_dict.get("subject", "Toán học")
    grade = deck_dict.get("grade", 12)

    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)

    deck_snapshot = deck_dict.get("snapshot_3d_base64") or deck_dict.get("snapshot_3d")

    for idx, slide_data in enumerate(slides_data):
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Xóa các placeholder thừa nếu có
        for sh in list(slide.placeholders):
            slide.shapes._spTree.remove(sh._element)

        slide_type = str(slide_data.get("type") or "CONCEPT_SLIDE")
        is_title = (slide_type == "TITLE_SLIDE")
        is_quiz = (
            slide_type == "QUIZ_SLIDE"
            or slide_data.get("layout") == "QUIZ_OPTION"
            or bool(slide_data.get("quiz_options"))
        )

        # 1. Header Banner
        header_type = "QUIZ_SLIDE" if is_quiz else slide_type
        build_slide_header(slide, idx + 1, total_slides, header_type)

        # 2. Nội dung slide
        if is_title:
            build_title_slide(slide, slide_data, subject, grade)
        elif is_quiz:
            build_quiz_slide(slide, slide_data, idx + 1, total_slides, subject, grade)
        else:
            # Task 14.3 & Task 18.2: Tự động kế thừa snapshot 3D từ deck_snapshot nếu slide có has_3d/polyhedron_type/layout
            if not slide_data.get("snapshot_3d_base64"):
                if slide_data.get("snapshot_3d"):
                    slide_data["snapshot_3d_base64"] = slide_data["snapshot_3d"]
                elif deck_snapshot and (
                    slide_data.get("has_3d")
                    or slide_data.get("polyhedron_type")
                    or slide_data.get("layout") == "IMAGE_TEXT"
                ):
                    slide_data["snapshot_3d_base64"] = deck_snapshot
            build_content_slide(slide, slide_data, idx + 1, total_slides, subject, grade)

        # 3. Kịch bản lời thoại giáo viên & Bóc tách bẫy sai lầm (Task 18.3 Speaker Notes Pane)
        build_speaker_notes(slide, slide_data, is_quiz=is_quiz, subject=subject, grade=grade)

    pptx_bytes = io.BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    return pptx_bytes


def export_slide_deck_to_pptx_file(data: Union[Dict[str, Any], SlideDeckSchema], output_filepath: str) -> str:
    """Xuất bài giảng ra file .pptx trên đĩa cứng"""
    pptx_stream = export_slide_deck_to_pptx(data)
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    with open(output_filepath, "wb") as f:
        f.write(pptx_stream.getbuffer())
    print(f"Đã xuất thành công file PowerPoint PPTX đồng bộ chuẩn Web Studio: {output_filepath}")
    return output_filepath


# Alias tương thích ngược
export_slide_to_pptx = export_slide_deck_to_pptx_file


def render_math_plot(chart_spec: dict) -> io.BytesIO:
    """Vẽ đồ thị toán học từ cấu hình chart_spec và trả về buffer ảnh (BytesIO)."""
    return io.BytesIO(generate_math_plot(chart_spec))


def load_manifest_config() -> dict:
    """Đọc file manifest.json trong thư mục templates/ (giữ cho tương thích ngược)"""
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(app_dir, "templates", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def select_template_presentation(theme_id: str = "math_academic") -> tuple[Any, dict]:
    """Tạo Presentation 16:9 widescreen đồng bộ với giao diện web"""
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)
    return prs, {}
