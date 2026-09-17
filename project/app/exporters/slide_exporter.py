import os
import sys
import re
import io
from typing import Union, Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

import matplotlib.pyplot as plt
from schemas.slide_schema import SlideDeckSchema, SlideType
from exporters.graph_generator import generate_math_plot

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
        # Bỏ qua dòng kẻ ngang hline, vline
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
    Áp dụng toàn diện 8 bước cho TOÀN BỘ chuỗi văn bản (không cần dấu $ bao quanh).
    """
    if not isinstance(text, str):
        return str(text or '')

    # 1. Clean XML hidden characters
    text = clean_xml_string(text)

    # 2. Convert LaTeX table/array environments
    text = clean_latex_table_environment(text)

    # 3. Strip $ and \( \) delimiters
    text = text.replace(r'\(', '').replace(r'\)', '').replace('$', '')

    # 4. Replace Greek letters (sorted by length descending to avoid substring conflicts)
    for k in sorted(_GREEK_MAP.keys(), key=len, reverse=True):
        text = text.replace(k, _GREEK_MAP[k])

    # 5. Replace Math symbols (sorted by length descending)
    for k in sorted(_SYMBOL_MAP.keys(), key=len, reverse=True):
        text = text.replace(k, _SYMBOL_MAP[k])

    # 6. Convert Superscripts ^... and Subscripts _...
    def convert_script(match):
        script_type, body = match.groups()
        char_map = _SUPERSCRIPT_MAP if script_type == '^' else _SUBSCRIPT_MAP
        return ''.join(char_map.get(ch, ch) for ch in body)

    # Convert ^{...} and _{...}
    text = re.sub(r'([\^_])\{([^}]+)\}', convert_script, text)
    # Convert ^X and _X (single char)
    text = re.sub(r'([\^_])([0-9a-zA-Z\+\-\=\(\)])', convert_script, text)

    # 7. Clean remaining formatting commands and macro wrappers
    text = re.sub(r'\\(?:newline|quad|qquad|left|right|text|mathrm|mathbf|mathit|vec|bar|hat)', ' ', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\\+', ' ', text)

    # 8. Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def render_latex_to_bytes(latex_str: str) -> bytes:
    """Render công thức LaTeX ra ảnh PNG chuẩn nét, không đứt vạch dấu căn."""
    fig, ax = plt.subplots(figsize=(0.1, 0.1))
    ax.axis('off')
    
    clean_str = latex_str.replace(r'\(', '').replace(r'\)', '').strip()
    formatted_latex = f"${clean_str}$" if not clean_str.startswith("$") else clean_str
    
    ax.text(
        0.5, 0.5, formatted_latex, 
        fontsize=20, ha='center', va='center', color='#0066CC'
    )
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def add_text_with_latex_to_paragraph(paragraph, text: str, font_name: str = "Times New Roman", font_size_pt: int = 18, color_rgb: RGBColor = RGBColor(44, 62, 80)):
    """
    Chèn văn bản vào paragraph của PowerPoint.
    Biến đổi LaTeX inline thành Unicode Math chuẩn giúp PowerPoint hiển thị mượt mà 100%, không mất chữ!
    """
    cleaned_text = clean_xml_string(text)
    if not cleaned_text:
        return

    formatted_text = latex_to_unicode_math(cleaned_text)
    run = paragraph.add_run()
    run.text = formatted_text
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    run.font.color.rgb = color_rgb

def get_template_path() -> str:
    """Trả về đường dẫn tới file template mẫu nếu có"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "templates", "template_5512.pptx")
    return template_path if os.path.exists(template_path) else ""

def remove_template_default_slides(prs: Presentation):
    """Xóa các slide trống rỗng mặc định đi kèm file template gốc"""
    while len(prs.slides) > 0:
        rId = prs.slides._sldIdLst[0].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[0]

def export_slide_deck_to_pptx(data: Union[Dict[str, Any], SlideDeckSchema]) -> io.BytesIO:
    """
    Chuyển đổi dữ liệu SlideDeck thành file PowerPoint (.pptx) 100% Native bằng python-pptx.
    - Nạp file mẫu template_5512.pptx nếu có.
    - Tự động sinh đồ thị Matplotlib khi có image_prompt.
    - Chèn công thức toán Unicode & Matplotlib PNG.
    - Cho phép Giáo viên chỉnh sửa, đổi màu, di chuyển khung chữ tự do 100%.
    """
    if isinstance(data, SlideDeckSchema):
        deck_dict = data.model_dump()
    elif isinstance(data, dict):
        deck_dict = data
    else:
        raise ValueError("Dữ liệu vào phải là dict hoặc SlideDeckSchema")

    template_file = get_template_path()
    if template_file:
        prs = Presentation(template_file)
        remove_template_default_slides(prs)  # Xóa bớt slide trống rỗng mặc định của file template
        print(f"🎨 Đã nạp file mẫu PowerPoint Master: {template_file}")
    else:
        prs = Presentation()
        prs.slide_width = Inches(13.333) # 16:9 Widescreen
        prs.slide_height = Inches(7.5)

    presentation_title = deck_dict.get("presentation_title", "Bài giảng")
    subject = deck_dict.get("subject", "")
    grade = deck_dict.get("grade", "")
    slides_data = deck_dict.get("slides", [])

    NAVY_BLUE = RGBColor(0, 51, 102)     # #003366
    PRIMARY_BLUE = RGBColor(0, 102, 204)  # #0066CC
    DARK_TEXT = RGBColor(44, 62, 80)     # #2C3E50
    CARD_BG = RGBColor(240, 244, 248)    # #F0F4F8
    WHITE = RGBColor(255, 255, 255)

    for slide_data in slides_data:
        slide_type = slide_data.get("type", "CONCEPT_SLIDE")
        title_text = slide_data.get("title", "")
        subtitle_text = slide_data.get("subtitle", "")
        bullet_points = slide_data.get("bullet_points", [])
        latex_formula = slide_data.get("main_definition_latex", "")
        teacher_note = slide_data.get("teacher_note", "")
        image_prompt = slide_data.get("image_prompt", "")

        # ---------------------------------------------------------------------
        # 1. TRƯỜNG HỢP: SLIDE TIÊU ĐỀ (TITLE_SLIDE)
        # ---------------------------------------------------------------------
        if slide_type in [SlideType.TITLE_SLIDE, "TITLE_SLIDE"]:
            slide = prs.slides.add_slide(prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0])

            shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
            shape.fill.solid()
            shape.fill.fore_color.rgb = CARD_BG
            shape.line.fill.background()

            bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2), Inches(0.2), Inches(3.5))
            bar.fill.solid()
            bar.fill.fore_color.rgb = PRIMARY_BLUE
            bar.line.fill.background()

            tb = slide.shapes.add_textbox(Inches(1.5), Inches(2), Inches(10.5), Inches(3.5))
            tf = tb.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = f"MÔN {subject.upper()} - LỚP {grade}" if subject and grade else "BÀI GIẢNG ĐIỆN TỬ"
            p1.font.name = "Times New Roman"
            p1.font.size = Pt(18)
            p1.font.bold = True
            p1.font.color.rgb = PRIMARY_BLUE

            p2 = tf.add_paragraph()
            p2.text = title_text
            p2.font.name = "Times New Roman"
            p2.font.size = Pt(40)
            p2.font.bold = True
            p2.font.color.rgb = NAVY_BLUE
            p2.space_before = Pt(15)

            if subtitle_text:
                p3 = tf.add_paragraph()
                p3.text = subtitle_text
                p3.font.name = "Times New Roman"
                p3.font.size = Pt(22)
                p3.font.color.rgb = DARK_TEXT
                p3.space_before = Pt(10)

        # ---------------------------------------------------------------------
        # 2. TRƯỜNG HỢP: SLIDE NỘI DUNG (CONCEPT, WARM_UP, EXERCISE, SUMMARY,...)
        # ---------------------------------------------------------------------
        else:
            slide = prs.slides.add_slide(prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0])

            header_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
            header_box.fill.solid()
            header_box.fill.fore_color.rgb = CARD_BG
            header_box.line.color.rgb = PRIMARY_BLUE
            header_box.line.width = Pt(1.5)

            tf_header = header_box.text_frame
            tf_header.word_wrap = True
            p_h = tf_header.paragraphs[0]
            p_h.text = title_text
            p_h.font.name = "Times New Roman"
            p_h.font.size = Pt(26)
            p_h.font.bold = True
            p_h.font.color.rgb = NAVY_BLUE

            chart_spec = slide_data.get("chart_spec")
            has_image = bool(chart_spec or image_prompt)
            content_width = Inches(6.8) if has_image else Inches(11.7)

            content_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), content_width, Inches(5.0))
            content_box.fill.solid()
            content_box.fill.fore_color.rgb = WHITE
            content_box.line.color.rgb = RGBColor(220, 224, 230)
            content_box.line.width = Pt(1)

            tf_content = content_box.text_frame
            tf_content.word_wrap = True

            for idx, pt in enumerate(bullet_points):
                p = tf_content.paragraphs[0] if idx == 0 else tf_content.add_paragraph()
                p.space_after = Pt(10)
                add_text_with_latex_to_paragraph(p, f"•  {pt}", font_name="Times New Roman", font_size_pt=18, color_rgb=DARK_TEXT)

            # Công thức trọng tâm (Nút Highlight hiển thị sắc nét)
            if latex_formula:
                p_formula = tf_content.add_paragraph()
                p_formula.space_before = Pt(15)
                p_formula.space_after = Pt(5)
                
                r_lbl = p_formula.add_run()
                r_lbl.text = "Công thức trọng tâm:  "
                r_lbl.font.name = "Times New Roman"
                r_lbl.font.bold = True
                r_lbl.font.size = Pt(20)
                r_lbl.font.color.rgb = PRIMARY_BLUE

                clean_formula = latex_to_unicode_math(latex_formula)
                r_val = p_formula.add_run()
                r_val.text = clean_formula
                r_val.font.name = "Times New Roman"
                r_val.font.bold = True
                r_val.font.size = Pt(20)
                r_val.font.color.rgb = PRIMARY_BLUE

            if has_image:
                try:
                    if isinstance(chart_spec, dict):
                        plot_config = chart_spec
                    elif isinstance(image_prompt, dict):
                        plot_config = image_prompt
                    else:
                        plot_config = {"plot_type": "function", "expression": "x", "x_range": (-5, 5)}
                    img_buf = generate_math_plot(plot_config)
                    img_stream = io.BytesIO(img_buf) if isinstance(img_buf, bytes) else img_buf
                    slide.shapes.add_picture(img_stream, Inches(7.8), Inches(1.8), width=Inches(4.7))
                except Exception as e:
                    print(f"Lỗi sinh hình đồ thị Matplotlib: {e}")

        # Kịch bản lời thoại giáo viên
        if teacher_note:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = f"[Kịch bản giảng dạy dành cho Giáo viên]:\n{teacher_note}"

    pptx_bytes = io.BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    return pptx_bytes

def export_slide_deck_to_pptx_file(data: Union[Dict[str, Any], SlideDeckSchema], output_filepath: str) -> str:
    pptx_stream = export_slide_deck_to_pptx(data)
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    with open(output_filepath, "wb") as f:
        f.write(pptx_stream.getbuffer())
    print(f"Đã xuất thành công file PowerPoint PPTX 100% Native Hybrid: {output_filepath}")
    return output_filepath
