"""Lọc ký tự điều khiển khỏi văn bản trước khi ghi vào XML của Word/PowerPoint."""
import re

_CONTROL = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]')


def clean_xml_string(s: str) -> str:
    """Lọc ký tự rác / ẩn để tránh lỗi khi chèn văn bản vào XML Office."""
    if not isinstance(s, str):
        s = str(s or "")
    return _CONTROL.sub('', s)
