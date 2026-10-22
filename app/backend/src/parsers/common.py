import re
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union, List, Any, Optional, Dict, TypeAlias
from pydantic import BaseModel, Field
Source: TypeAlias = Union[str, Path, bytes, BinaryIO, BytesIO]

def read_source(source: Source) -> BytesIO:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")
        return BytesIO(path.read_bytes())

    if isinstance(source, bytes):
        return BytesIO(source)

    if isinstance(source, BytesIO):
        source.seek(0)
        return source

    if hasattr(source, "read"):
        if hasattr(source, "seek"):
            source.seek(0)
        data = source.read()
        return BytesIO(data if isinstance(data, bytes) else data.encode("utf-8"))

    raise TypeError(f"Định dạng input không được hỗ trợ {type(source)}")


def clean_text(text: str | None) -> str:
    """
    Làm sạch văn bản thô bóc tách từ file Word (.docx) và PowerPoint (.pptx):
    - Xử lý giá trị None hoặc chuỗi rỗng.
    - Xóa ký tự ẩn (null byte \\x00, zero-width space \\u200b, vertical tab \\x0b).
    - Chuẩn hóa khoảng trắng không ngắt (\\xa0) về dấu cách thường.
    - Gộp nhiều dấu cách/tab liên tiếp trên cùng một dòng và lọc bỏ các dòng trống thừa.
    """
    if not text:
        return ""

    # 1. Loại bỏ các ký tự điều khiển ẩn thường gặp trong XML của Office
    cleaned = (
        text.replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\x00", "")
        .replace("\x0b", "\n")  # Vertical tab (Shift+Enter trong Word/PPTX) -> xuống dòng
    )
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Chuẩn hóa từng dòng: gộp khoảng trắng thừa và bỏ dòng trống
    lines = []
    for line in cleaned.split("\n"):
        normalized_line = re.sub(r"[ \t]+", " ", line).strip()
        if normalized_line:
            lines.append(normalized_line)

    return "\n".join(lines)

class ParsedDocumentResponse(BaseModel):
    """Schema chuẩn hóa dữ liệu JSON đầu ra cho cả PPTX và DOCX Parser"""
    filename: str = Field(default="", description="Tên file gốc tải lên")
    file_type: str = Field(description="Loại tài liệu: 'pptx' hoặc 'docx'")
    title: str = Field(description="Tiêu đề bài giảng / giáo án nhận diện được")
    raw_text: str = Field(description="Toàn bộ nội dung văn bản đã làm sạch để đưa vào AI")

    # Trường chi tiết dành cho file PowerPoint (.pptx)
    total_slides: Optional[int] = Field(default=None, description="Tổng số trang slide (nếu là pptx)")
    slides: Optional[List[Dict[str, Any]]] = Field(default=None, description="Chi tiết từng trang slide")

    # Trường chi tiết dành cho file Word (.docx)
    total_paragraphs: Optional[int] = Field(default=None, description="Tổng số đoạn văn (nếu là docx)")
    total_tables: Optional[int] = Field(default=None, description="Tổng số bảng biểu (nếu là docx)")
    paragraphs: Optional[List[str]] = Field(default=None, description="Danh sách các đoạn văn")
    tables: Optional[List[List[List[str]]]] = Field(default=None, description="Danh sách các bảng biểu")
    blocks: Optional[List[Dict[str, Any]]] = Field(default=None, description="Các khối nội dung theo thứ tự từ trên xuống")
