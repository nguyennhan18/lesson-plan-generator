import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Thêm đường dẫn src vào sys.path
TESTS_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTS_DIR.parent / "src"

from lessonai.parsers.common import clean_text, ParsedDocumentResponse
from lessonai.parsers.docx_parser import parse_docx
from lessonai.parsers.pptx_parser import parse_pptx
from lessonai.main import app

client = TestClient(app)

DOCX_SAMPLE = TESTS_DIR / "fixtures" / "GA_test_5512.docx"
PPTX_SAMPLE = TESTS_DIR / "fixtures" / "sample_slide.pptx"


def test_clean_text():
    """
    Test Case 1: Kiểm tra hàm làm sạch văn bản clean_text() trong common.py.
    """
    raw = "  Bài 1:\xa0Phương trình\u200b   bậc hai \x0b Dòng phụ \r\n\r\n   Dòng 2   "
    cleaned = clean_text(raw)
    assert cleaned == "Bài 1: Phương trình bậc hai\nDòng phụ\nDòng 2"
    assert clean_text(None) == ""
    assert clean_text("   \n\t  ") == ""


def test_parse_docx_real_file():
    """
    Test Case 2: Kiểm tra parse_docx() với file Giáo án 5512 thực tế (GA_test_5512.docx).
    """
    assert DOCX_SAMPLE.exists(), f"Không tìm thấy file mẫu: {DOCX_SAMPLE}"
    result = parse_docx(DOCX_SAMPLE)

    assert result["file_type"] == "docx"
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert result["total_paragraphs"] > 0 or result["total_tables"] > 0
    assert isinstance(result["raw_text"], str) and len(result["raw_text"]) > 100
    assert isinstance(result["blocks"], list) and len(result["blocks"]) > 0

    print(f"\n[DOCX] Tiêu đề: {result['title']}")
    print(f"[DOCX] Số đoạn văn: {result['total_paragraphs']} | Số bảng: {result['total_tables']}")


def test_parse_pptx_real_file():
    """
    Test Case 3: Kiểm tra parse_pptx() với file PowerPoint bài giảng thực tế (test_15.pptx).
    """
    assert PPTX_SAMPLE.exists(), f"Không tìm thấy file mẫu: {PPTX_SAMPLE}"
    result = parse_pptx(PPTX_SAMPLE)

    assert result["file_type"] == "pptx"
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert result["total_slides"] > 0
    assert len(result["slides"]) == result["total_slides"]
    assert isinstance(result["raw_text"], str) and len(result["raw_text"]) > 50

    print(f"\n[PPTX] Tiêu đề: {result['title']}")
    print(f"[PPTX] Tổng số slide: {result['total_slides']}")


def test_ingest_api_upload_docx_and_pptx():
    """
    Test Case 4: Kiểm tra API POST /api/v1/ingest/parse-document với cả 2 định dạng .docx và .pptx.
    """
    # 1. Upload file DOCX
    with open(DOCX_SAMPLE, "rb") as f:
        res_docx = client.post(
            "/api/v1/ingest/parse-document",
            files={"file": (DOCX_SAMPLE.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    assert res_docx.status_code == 200
    data_docx = res_docx.json()
    assert data_docx["filename"] == DOCX_SAMPLE.name
    assert data_docx["file_type"] == "docx"
    assert len(data_docx["raw_text"]) > 100
    # Kiểm định khớp chuẩn ParsedDocumentResponse
    validated_docx = ParsedDocumentResponse(**data_docx)
    assert validated_docx.file_type == "docx"

    # 2. Upload file PPTX
    with open(PPTX_SAMPLE, "rb") as f:
        res_pptx = client.post(
            "/api/v1/ingest/parse-document",
            files={"file": (PPTX_SAMPLE.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        )
    assert res_pptx.status_code == 200
    data_pptx = res_pptx.json()
    assert data_pptx["filename"] == PPTX_SAMPLE.name
    assert data_pptx["file_type"] == "pptx"
    assert data_pptx["total_slides"] > 0
    validated_pptx = ParsedDocumentResponse(**data_pptx)
    assert validated_pptx.file_type == "pptx"


def test_ingest_api_invalid_extension_and_empty_file():
    """
    Test Case 5: Kiểm tra chốt chặn lỗi 400 khi tải lên định dạng không hỗ trợ (.txt) hoặc file rỗng (0 bytes).
    """
    # 1. File sai định dạng (.txt)
    res_invalid = client.post(
        "/api/v1/ingest/parse-document",
        files={"file": ("bai_giang.txt", b"Noi dung text", "text/plain")}
    )
    assert res_invalid.status_code == 415

    # 2. File đúng đuôi .docx nhưng rỗng (0 bytes)
    res_empty = client.post(
        "/api/v1/ingest/parse-document",
        files={"file": ("giao_an_rong.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res_empty.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

@pytest.fixture(autouse=True)
def generated_office_fixtures(tmp_path,monkeypatch):
    """Portable real Office files built for tests; no local untracked resources required."""
    from docx import Document
    from pptx import Presentation
    from pptx.util import Inches
    doc=Document();doc.add_heading('Bài kiểm tra nhập tài liệu',0)
    doc.add_paragraph('Nội dung được chuẩn bị để kiểm tra bảo toàn đoạn văn và công thức trong tài liệu của giáo viên. Đây là dữ liệu kiểm thử, không được đưa vào sản phẩm.')
    table=doc.add_table(rows=2,cols=2);table.cell(0,0).text='Điều kiện';table.cell(1,0).text='x > 0'
    doc_path=tmp_path/'source.docx';doc.save(doc_path)
    prs=Presentation();page=prs.slides.add_slide(prs.slide_layouts[5]);page.shapes.title.text='Tài liệu kiểm thử'
    page.shapes.add_textbox(Inches(1),Inches(2),Inches(8),Inches(2)).text='Nội dung dùng kiểm tra bộ nhập slide: giữ đúng thứ tự văn bản được cung cấp.'
    pptx_path=tmp_path/'source.pptx';prs.save(pptx_path)
    monkeypatch.setattr(__import__(__name__), 'DOCX_SAMPLE',doc_path)
    monkeypatch.setattr(__import__(__name__), 'PPTX_SAMPLE',pptx_path)
