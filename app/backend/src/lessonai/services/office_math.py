"""Conservative native Office math conversion. Unsupported nodes stay explicit."""
from typing import Dict, Tuple, Set, Any
import unicodedata
from lxml import etree

M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

MATH_MAP: Dict[str, str] = {
    '−': '-',
    '×': r'\times ',
    '÷': r'\div ',
    '≤': r'\le ',
    '≥': r'\ge ',
    '≠': r'\neq ',
    '≈': r'\approx ',
    '∞': r'\infty ',
    '±': r'\pm ',
    '∓': r'\mp ',
    '∈': r'\in ',
    '∉': r'\notin ',
    '⊂': r'\subset ',
    '⊆': r'\subseteq ',
    '∪': r'\cup ',
    '∩': r'\cap ',
    '∅': r'\emptyset ',
    '∀': r'\forall ',
    '∃': r'\exists ',
    '⇒': r'\Rightarrow ',
    '⇔': r'\Leftrightarrow ',
    '→': r'\to ',
    '←': r'\leftarrow ',
    '⊥': r'\bot ',
    '∥': r'\parallel ',
    '…': r'\dots ',
    '′': "'",
    '″': "''",
    '°': r'^\circ ',
    'π': r'\pi ',
    'α': r'\alpha ',
    'β': r'\beta ',
    'γ': r'\gamma ',
    'θ': r'\theta ',
    'ω': r'\omega ',
    'λ': r'\lambda ',
    'σ': r'\sigma ',
    'φ': r'\varphi ',
    'Δ': r'\Delta ',
    'ε': r'\in ',
    '%': r'\%',
}

OPEN_DELIMS: Dict[str, str] = {
    '(': r'\left(',
    '[': r'\left[',
    '{': r'\left\{',
    '|': r'\left|',
    '': r'\left.',
}

CLOSE_DELIMS: Dict[str, str] = {
    ')': r'\right)',
    ']': r'\right]',
    '}': r'\right\}',
    '|': r'\right|',
    '': r'\right.',
}

IGNORE_PROPERTIES: Set[str] = {
    'ctrlPr', 'rPr', 'dPr', 'fPr', 'sSupPr', 'sSubPr', 'sSubSupPr',
    'radPr', 'accPr', 'funcPr', 'limLowPr', 'limUppPr', 'barPr',
    'eqArrPr', 'naryPr', 'groupChrPr', 'boxPr', 'borderBoxPr', 'argPr',
}

STANDARD_FUNCTIONS: Set[str] = {
    'sin', 'cos', 'tan', 'cot', 'ln', 'log', 'exp', 'lim', 'min', 'max',
    'arcsin', 'arccos', 'arctan', 'det', 'gcd', 'deg',
}


def omml_to_latex(node: etree._Element) -> str:
    """Chuyển đổi cây XML công thức toán Office (OMML) sang cú pháp LaTeX chuẩn.
    
    Hỗ trợ đầy đủ các cấu trúc toán học phổ biến trong SGK Toán 12:
    - Phân số (`m:f`)
    - Lũy thừa, chỉ số dưới (`m:sSup`, `m:sSub`, `m:sSubSup`)
    - Dấu ngoặc, hệ phương trình (`m:d`)
    - Căn thức (`m:rad`)
    - Dấu phụ, vectơ, mũ góc (`m:acc`)
    - Hàm số lượng giác, logarit (`m:func`)
    - Giới hạn (`m:limLow`, `m:limUpp`)
    - Gạch đầu, gạch chân (`m:bar`)
    - Tích phân, tổng xích-ma (`m:nary`)
    - Khung đóng hộp (`m:borderBox`, `m:box`)
    - Dãy / hệ phương trình (`m:eqArr`)
    - Ma trận (`m:m`)
    
    Các nút không hợp lệ hoặc cấu trúc không được hỗ trợ sẽ raise ValueError tường minh.
    """
    def convert(element: etree._Element) -> str:
        qname = etree.QName(element)
        tag = qname.localname
        if qname.namespace != M:
            raise ValueError(f'Namespace công thức chưa hỗ trợ: {qname.namespace}')

        if tag in {
            'oMath', 'oMathPara', 'e', 'num', 'den', 'sup', 'sub',
            'deg', 'lim', 'fName', 'box',
        }:
            return ''.join(
                convert(child)
                for child in element
                if etree.QName(child).localname not in IGNORE_PROPERTIES
            )

        if tag == 'borderBox':
            inner = ''.join(
                convert(child)
                for child in element
                if etree.QName(child).localname not in IGNORE_PROPERTIES
            )
            return r'\boxed{' + inner + '}'

        if tag == 'r':
            return ''.join(
                convert(child)
                for child in element
                if etree.QName(child).localname == 't'
            )

        if tag == 't':
            raw = element.text or ''
            raw = raw.replace('\u00A0', ' ')
            text = unicodedata.normalize('NFKD', raw)
            for k, v in MATH_MAP.items():
                text = text.replace(k, v)
            text = text.replace('{', r'\{').replace('}', r'\}')
            forbidden = {'$', '_', '#'}
            if any(char in text for char in forbidden):
                raise ValueError(f'Ký hiệu cần đối chiếu thủ công: {text}')
            return text

        if tag == 'f':
            num_el = element.find(f'{{{M}}}num')
            den_el = element.find(f'{{{M}}}den')
            if num_el is None or den_el is None:
                raise ValueError('Phân số thiếu num hoặc den')
            return r'\frac{' + convert(num_el) + '}{' + convert(den_el) + '}'

        if tag in {'sSup', 'sSub', 'sSubSup'}:
            e_el = element.find(f'{{{M}}}e')
            if e_el is None:
                raise ValueError('Lũy thừa/chỉ số thiếu e')
            res = '{' + convert(e_el) + '}'
            if tag in {'sSub', 'sSubSup'}:
                sub_el = element.find(f'{{{M}}}sub')
                if sub_el is not None:
                    res += '_{' + convert(sub_el) + '}'
            if tag in {'sSup', 'sSubSup'}:
                sup_el = element.find(f'{{{M}}}sup')
                if sup_el is not None:
                    res += '^{' + convert(sup_el) + '}'
            return res

        if tag == 'rad':
            e_el = element.find(f'{{{M}}}e')
            if e_el is None:
                raise ValueError('Căn thức thiếu e')
            deg_el = element.find(f'{{{M}}}deg')
            rad_pr = element.find(f'{{{M}}}radPr')
            deg_hide = False
            if rad_pr is not None:
                deg_hide_el = rad_pr.find(f'{{{M}}}degHide')
                if deg_hide_el is not None and deg_hide_el.get(f'{{{M}}}val') in {'on', '1', 'true'}:
                    deg_hide = True
            deg_text = convert(deg_el).strip() if (deg_el is not None and not deg_hide) else ''
            if deg_text:
                return r'\sqrt[' + deg_text + ']{' + convert(e_el) + '}'
            return r'\sqrt{' + convert(e_el) + '}'

        if tag == 'acc':
            e_el = element.find(f'{{{M}}}e')
            if e_el is None:
                raise ValueError('Cấu trúc OMML chưa hỗ trợ: acc')
            acc_pr = element.find(f'{{{M}}}accPr')
            chr_val = '̂'
            if acc_pr is not None:
                chr_el = acc_pr.find(f'{{{M}}}chr')
                if chr_el is not None:
                    chr_val = chr_el.get(f'{{{M}}}val', '̂')
            inner = convert(e_el)
            if chr_val in {'̂', '^', '\u0302'}:
                return r'\hat{' + inner + '}'
            elif chr_val in {'⃗', '→', '\u20D7', '\u2192'}:
                return r'\vec{' + inner + '}'
            elif chr_val in {'¯', '‾', '\u00AF', '\u203E'}:
                return r'\overline{' + inner + '}'
            elif chr_val == '.':
                return r'\dot{' + inner + '}'
            elif chr_val == '..':
                return r'\ddot{' + inner + '}'
            elif chr_val in {"'", '′', '\u2032'}:
                return '{' + inner + '}\''
            elif chr_val == '~':
                return r'\tilde{' + inner + '}'
            return r'\vec{' + inner + '}'

        if tag == 'd':
            d_pr = element.find(f'{{{M}}}dPr')
            beg = '('
            end = ')'
            sep = ','
            if d_pr is not None:
                beg_el = d_pr.find(f'{{{M}}}begChr')
                if beg_el is not None:
                    beg = beg_el.get(f'{{{M}}}val', '')
                end_el = d_pr.find(f'{{{M}}}endChr')
                if end_el is not None:
                    end = end_el.get(f'{{{M}}}val', '')
                sep_el = d_pr.find(f'{{{M}}}sepChr')
                if sep_el is not None:
                    sep = sep_el.get(f'{{{M}}}val', ',')

            left_delim = OPEN_DELIMS.get(beg, r'\left.' if beg == '' else beg)
            right_delim = CLOSE_DELIMS.get(end, r'\right.' if end == '' else end)

            e_elements = [child for child in element if etree.QName(child).localname == 'e']
            inner = (sep + ' ').join(convert(e) for e in e_elements)
            return left_delim + inner + right_delim

        if tag == 'func':
            fname_el = element.find(f'{{{M}}}fName')
            e_el = element.find(f'{{{M}}}e')
            if fname_el is None or e_el is None:
                raise ValueError('Hàm thiếu fName hoặc e')
            fname = convert(fname_el).strip()
            e_str = convert(e_el)
            if fname in STANDARD_FUNCTIONS:
                return '\\' + fname + ' ' + e_str
            return fname + ' ' + e_str

        if tag in {'limLow', 'limUpp'}:
            e_el = element.find(f'{{{M}}}e')
            lim_el = element.find(f'{{{M}}}lim')
            if e_el is None or lim_el is None:
                raise ValueError('Giới hạn thiếu e hoặc lim')
            e_str = convert(e_el).strip()
            lim_str = convert(lim_el).strip()
            if e_str in {'lim', 'min', 'max'}:
                return '\\' + e_str + '_{' + lim_str + '}'
            return '{' + e_str + '}_{' + lim_str + '}'

        if tag == 'bar':
            e_el = element.find(f'{{{M}}}e')
            if e_el is None:
                raise ValueError('Bar thiếu e')
            bar_pr = element.find(f'{{{M}}}barPr')
            pos = 'top'
            if bar_pr is not None:
                pos_el = bar_pr.find(f'{{{M}}}pos')
                if pos_el is not None:
                    pos = pos_el.get(f'{{{M}}}val', 'top')
            inner = convert(e_el)
            return (r'\overline{' + inner + '}') if pos == 'top' else (r'\underline{' + inner + '}')

        if tag == 'eqArr':
            e_elements = [child for child in element if etree.QName(child).localname == 'e']
            lines = [convert(e).strip() for e in e_elements]
            return r'\begin{aligned} ' + ' \\\\ '.join(lines) + r' \end{aligned}'

        if tag == 'nary':
            nary_pr = element.find(f'{{{M}}}naryPr')
            chr_val = '∫'
            if nary_pr is not None:
                chr_el = nary_pr.find(f'{{{M}}}chr')
                if chr_el is not None:
                    chr_val = chr_el.get(f'{{{M}}}val', '∫')
            op = r'\int' if chr_val in {'∫', '∭', '∬'} else (r'\sum' if chr_val == '∑' else (r'\prod' if chr_val == '∏' else chr_val))
            sub_el = element.find(f'{{{M}}}sub')
            sup_el = element.find(f'{{{M}}}sup')
            e_el = element.find(f'{{{M}}}e')
            res = op
            if sub_el is not None:
                res += '_{' + convert(sub_el) + '}'
            if sup_el is not None:
                res += '^{' + convert(sup_el) + '}'
            if e_el is not None:
                res += ' ' + convert(e_el)
            return res

        if tag == 'groupChr':
            e_el = element.find(f'{{{M}}}e')
            if e_el is None:
                raise ValueError('GroupChr thiếu e')
            g_pr = element.find(f'{{{M}}}groupChrPr')
            pos = 'bot'
            if g_pr is not None:
                pos_el = g_pr.find(f'{{{M}}}pos')
                if pos_el is not None:
                    pos = pos_el.get(f'{{{M}}}val', 'bot')
            inner = convert(e_el)
            return (r'\overbrace{' + inner + '}') if pos == 'top' else (r'\underbrace{' + inner + '}')

        if tag == 'm':
            rows = []
            for mr in element:
                if etree.QName(mr).localname == 'mr':
                    row_cells = [convert(e).strip() for e in mr if etree.QName(e).localname == 'e']
                    rows.append(' & '.join(row_cells))
            return r'\begin{matrix} ' + ' \\\\ '.join(rows) + r' \end{matrix}'

        raise ValueError(f'Cấu trúc OMML chưa hỗ trợ: {tag}')

    value = convert(node)
    if not value.strip():
        raise ValueError('Công thức rỗng')
    return value


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def extract_docx_paragraph_text(p_elem: Any) -> str:
    """Trích xuất văn bản có cấu trúc từ thẻ paragraph Word (<w:p>),
    tự động chuyển đổi các công thức toán OMML (<m:oMath>, <m:oMathPara>) sang LaTeX.
    
    Bảo toàn tính liên tục ngữ nghĩa của câu văn chứa công thức inline ($...$)
    hoặc khối công thức trưng bày ($$...$$).
    """
    if p_elem is None:
        return ''
    parts = []

    def _traverse(node):
        for child in node:
            qname = etree.QName(child)
            tag = qname.localname
            ns = qname.namespace

            if tag == 'r' and (ns == W_NS or 'wordprocessingml' in str(ns)):
                for t in child.findall(f'{{{W_NS}}}t'):
                    if t.text:
                        parts.append(t.text)
            elif tag == 'hyperlink':
                _traverse(child)
            elif tag == 'oMath' and ns == M:
                try:
                    latex = omml_to_latex(child)
                    parts.append(f' ${latex}$ ')
                except Exception:
                    raw = ''.join(child.itertext()).strip()
                    if raw:
                        parts.append(f' {raw} ')
            elif tag == 'oMathPara' and ns == M:
                math_children = child.findall(f'{{{M}}}oMath')
                if math_children:
                    para_latex = []
                    for mc in math_children:
                        try:
                            para_latex.append(omml_to_latex(mc))
                        except Exception:
                            raw = ''.join(mc.itertext()).strip()
                            if raw:
                                para_latex.append(raw)
                    if para_latex:
                        parts.append(f"\n$$\n{' '.join(para_latex)}\n$$\n")
                else:
                    try:
                        latex = omml_to_latex(child)
                        parts.append(f'\n$$\n{latex}\n$$\n')
                    except Exception:
                        raw = ''.join(child.itertext()).strip()
                        if raw:
                            parts.append(f' {raw} ')
            elif tag == 'br':
                parts.append('\n')
            elif tag == 'tab':
                parts.append('\t')

    _traverse(p_elem)
    return ''.join(parts)


def extract_pptx_paragraph_text(p_elem: Any) -> str:
    """Trích xuất văn bản có cấu trúc từ thẻ paragraph PowerPoint (<a:p>),
    tự động phát hiện và chuyển đổi các công thức toán OMML trong DrawingML (<a14:m>, <m:oMath>) sang LaTeX.
    """
    if p_elem is None:
        return ''
    parts = []

    for child in p_elem:
        qname = etree.QName(child)
        tag = qname.localname
        ns = qname.namespace

        if tag == 'r' and (ns == A_NS or 'drawingml' in str(ns)):
            t = child.find(f'{{{A_NS}}}t')
            if t is not None and t.text:
                parts.append(t.text)
        elif tag == 'br':
            parts.append('\n')
        elif tag in {'m', 'oMath'}:
            math_node = child if tag == 'oMath' else child.find(f'.//{{{M}}}oMath')
            if math_node is not None:
                try:
                    latex = omml_to_latex(math_node)
                    parts.append(f' ${latex}$ ')
                except Exception:
                    raw = ''.join(math_node.itertext()).strip()
                    if raw:
                        parts.append(f' {raw} ')
            else:
                math_para = child.find(f'.//{{{M}}}oMathPara')
                if math_para is not None:
                    try:
                        latex = omml_to_latex(math_para)
                        parts.append(f' $${latex}$$ ')
                    except Exception:
                        raw = ''.join(math_para.itertext()).strip()
                        if raw:
                            parts.append(f' {raw} ')

    return ''.join(parts)

