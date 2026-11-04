"""Conservative native Office math conversion. Unsupported nodes stay explicit."""
from lxml import etree

M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def omml_to_latex(node):
    def convert(element):
        tag = etree.QName(element).localname
        if etree.QName(element).namespace != M:
            raise ValueError('Namespace công thức chưa hỗ trợ')
        if tag in {'oMath', 'e', 'num', 'den', 'sup', 'sub', 'deg'}:
            return ''.join(convert(child) for child in element)
        if tag == 'r':
            if any(etree.QName(child).localname not in {'t', 'rPr'} for child in element):
                raise ValueError('Run công thức chưa hỗ trợ')
            return ''.join(convert(child) for child in element if etree.QName(child).localname == 't')
        if tag == 't':
            text = element.text or ''
            if any(char in text for char in '\\{}$&#_%'):
                raise ValueError('Ký hiệu cần đối chiếu thủ công')
            return text.replace('−', '-').replace('×', r'\times ').replace('÷', r'\div ').replace('≤', r'\le ').replace('≥', r'\ge ').replace('∞', r'\infty ')
        def part(name):
            child = element.find(f'{{{M}}}{name}')
            if child is None:
                raise ValueError('Công thức thiếu thành phần')
            return convert(child)
        allowed = {'f': {'num', 'den'}, 'sSup': {'e', 'sup'}, 'sSub': {'e', 'sub'}, 'sSubSup': {'e', 'sub', 'sup'}}
        if tag in allowed:
            if any(etree.QName(child).localname not in allowed[tag] for child in element):
                raise ValueError('Thuộc tính công thức chưa hỗ trợ')
            if tag == 'f':
                return r'\frac{' + part('num') + '}{' + part('den') + '}'
            result = '{' + part('e') + '}'
            if 'sub' in allowed[tag]:
                result += '_{' + part('sub') + '}'
            if 'sup' in allowed[tag]:
                result += '^{' + part('sup') + '}'
            return result
        raise ValueError(f'Cấu trúc OMML chưa hỗ trợ: {tag}')
    value = convert(node)
    if not value.strip():
        raise ValueError('Công thức rỗng')
    return value
