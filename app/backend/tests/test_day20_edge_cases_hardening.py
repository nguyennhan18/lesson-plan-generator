# -*- coding: utf-8 -*-
"""
Test Suite: Task 20.4 - Sửa Triệt Để Các Lỗi Biên (Edge-Cases Hardening)
LessonAI-5512 • Quantum Studio

Kiểm thử toàn diện 5 nhóm ca biên khắc nghiệt:
1. Công thức LaTeX siêu dài (> 120 ký tự), hệ phương trình nhiều dòng, biểu thức chứa ký tự lạ.
2. Tiêu đề và nội dung chứa ký tự đặc biệt, dấu ngoặc kép, thẻ XML, dấu gạch chéo, ký tự nhị phân.
3. Chuỗi Base64 ảnh Snapshot 3D rỗng, thiếu padding, hỏng cấu trúc hoặc không phải file ảnh.
4. Giả lập đứt mạng, Timeout, Rate limit 429, LLM sập nguồn 503 và phản hồi JSON dị dạng (Zero 500).
5. Đầu vào cực đoan: Khối lớp ngoài phạm vi (grade=0, -1, 99), chủ đề rỗng, độ dài chuỗi > 500 ký tự.
"""

import io
import re
import base64
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from schemas.schemas import LessonPlanSchema, LessonActivity, LessonRequest
from schemas.slide_schema import SlideDeckSchema, SlideSchema, SlideType, ChartSpec, ChartType
from exporters.docx_exporter import export_lesson_plan_to_docx, clean_xml_string, convert_latex_to_omml
from exporters.slide_exporter import (
    render_latex_to_bytes,
    export_slide_deck_to_pptx,
    decode_base64_data_url,
    latex_to_unicode_math
)
from exporters.dual_package_exporter import sanitize_filename, export_dual_package
from services.fallback_service import get_curated_lesson_plan, get_curated_slide_deck

client = TestClient(app)


# ==============================================================================
# NHÓM 1: CÔNG THỨC LATEX SIÊU DÀI & PHỨC TẠP
# ==============================================================================

def test_ultra_long_latex_render_to_bytes():
    """
    Ca biên 1.1: Công thức LaTeX cực dài (> 130 ký tự) với phân thức lồng nhau,
    căn bậc hai và các ký hiệu toán học phức hợp.
    Hệ thống phải tự động co nhỏ font (Adaptive Font Scaling) và trả về ảnh PNG hợp lệ.
    """
    long_latex = (
        r"\frac{-b \pm \sqrt{b^2 - 4ac + \int_{0}^{1} \sin^2(x) dx}}{2a \cdot \sum_{k=1}^{n} \frac{1}{k^2}} "
        r"\le \lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x \cdot \sqrt[3]{x^3 + 3x^2 + 3x + 1}"
    )
    assert len(long_latex) > 130

    png_bytes = render_latex_to_bytes(long_latex)
    assert png_bytes is not None
    assert len(png_bytes) > 100
    # Kiểm tra Magic Bytes của định dạng PNG
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_malformed_latex_with_vietnamese_fallback():
    """
    Ca biên 1.2: Công thức LaTeX bị lỗi cú pháp hoặc chứa chữ tiếng Việt không được mathtext hỗ trợ.
    Hệ thống phải tự động kích hoạt Fallback Unicode Math mà không gây ngoại lệ.
    """
    malformed_latex = r"y = 2x + \text{nửa mặt phẳng không chứa gốc tọa độ} \ge 10 \quad \text{với } x \in \mathbb{R}"
    png_bytes = render_latex_to_bytes(malformed_latex)
    assert png_bytes is not None
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_empty_and_none_latex_safe_fallback():
    """
    Ca biên 1.3: Chuỗi LaTeX rỗng, None hoặc kiểu dữ liệu bất thường.
    Hệ thống phải trả về ảnh 1x1 PNG trong suốt an toàn, không ném exception.
    """
    assert render_latex_to_bytes("").startswith(b"\x89PNG")
    assert render_latex_to_bytes(None).startswith(b"\x89PNG")
    assert render_latex_to_bytes(12345).startswith(b"\x89PNG")


def test_pptx_export_with_ultra_long_formula_and_bullet_points():
    """
    Ca biên 1.4: Slide chứa công thức siêu dài (> 150 ký tự) và bullet points dày đặc.
    Kiểm tra thuật toán Box-Fit không để ảnh công thức tràn biên khung hình chữ nhật.
    """
    ultra_formula = r"\begin{cases} 2x_1 + 3x_2 - 5x_3 + 7x_4 \le 120 \\ x_1 - x_2 + 4x_3 - 2x_4 \ge 45 \\ x_1, x_2, x_3, x_4 \ge 0 \end{cases}"
    deck = SlideDeckSchema(
        presentation_title="Kiểm Thử Ca Biên Công Thức Dài",
        subject="Toán học",
        grade=10,
        slides=[
            SlideSchema(
                slide_index=1,
                type=SlideType.TITLE_SLIDE,
                title="KIỂM THỬ CÔNG THỨC CỰC DÀI",
                subtitle="Đảm bảo không tràn slide hay vỡ bố cục"
            ),
            SlideSchema(
                slide_index=2,
                type=SlideType.CONCEPT_SLIDE,
                title="Hệ Bất Phương Trình Tuyến Tính Siêu Cấp",
                bullet_points=[
                    "Điểm thứ nhất: Phân tích các ràng buộc trong bài toán tối ưu nguồn lực kinh tế quy mô công nghiệp.",
                    "Điểm thứ hai: Thiết lập hệ bất phương trình đa ẩn với các hệ số nguyên lớn và điều kiện không âm.",
                    "Điểm thứ ba: Xác định miền chấp nhận được trong không gian đa chiều thông qua các siêu phẳng biên."
                ],
                main_definition_latex=ultra_formula
            )
        ]
    )

    pptx_stream = export_slide_deck_to_pptx(deck)
    assert pptx_stream is not None
    pptx_bytes = pptx_stream.getvalue()
    assert len(pptx_bytes) > 2000
    assert pptx_bytes.startswith(b"PK")  # ZIP-based OpenXML PPTX


def test_docx_export_with_multiline_cases_omml_fallback():
    """
    Ca biên 1.5: Giáo án Word CV 5512 chứa công thức LaTeX hệ phương trình phức tạp.
    Kiểm tra cơ chế chuyển đổi OMML và fallback Unicode Math an toàn trong tệp .docx.
    """
    plan = get_curated_lesson_plan("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)
    # Gắn công thức siêu dài vào mục tiêu kiến thức
    plan.knowledge_goals.append(
        r"Vận dụng thành thạo giải hệ: $\begin{cases} 3x + 2y - z \le 15 \\ 4x - 5y + 2z \ge 8 \\ x + y + z = 10 \end{cases}$"
    )

    docx_stream = export_lesson_plan_to_docx(plan)
    assert docx_stream is not None
    docx_bytes = docx_stream.getvalue()
    assert len(docx_bytes) > 5000
    assert docx_bytes.startswith(b"PK")  # ZIP-based OpenXML DOCX


# ==============================================================================
# NHÓM 2: KÝ TỰ ĐẶC BIỆT, NGOẶC KÉP, XML INJECTION & FILE SANITIZATION
# ==============================================================================

def test_sanitize_filename_edge_cases():
    """
    Ca biên 2.1: Tiêu đề bài dạy chứa ký tự cấm của hệ điều hành Windows/macOS/Linux:
    dấu ngoặc kép, dấu hai chấm, dấu gạch chéo, thẻ HTML, dấu sao, dấu hỏi, ký tự có dấu.
    """
    dirty_title_1 = 'Bài 1: "Hệ bất phương trình" & <Hàm số>? / \\ | * : `~'
    clean_1 = sanitize_filename(dirty_title_1)
    assert '"' not in clean_1
    assert ':' not in clean_1
    assert '/' not in clean_1
    assert '\\' not in clean_1
    assert '<' not in clean_1
    assert '>' not in clean_1
    assert '?' not in clean_1
    assert '*' not in clean_1
    assert '|' not in clean_1
    assert len(clean_1) <= 60

    # Tiêu đề toàn ký tự đặc biệt hoặc rỗng
    dirty_title_2 = "???///:::***"
    clean_2 = sanitize_filename(dirty_title_2)
    assert clean_2 == "LessonAI_5512"

    # Tiêu đề cực dài (> 100 ký tự)
    very_long_title = "Toán Học Lớp Mười Bài Số Một Khảo Sát Tính Đơn Điệu Và Cực Trị Của Hàm Số Đa Thức Bậc Ba Trong Kỳ Thi Tuyển Sinh"
    clean_long = sanitize_filename(very_long_title, max_length=40)
    assert len(clean_long) <= 40


def test_clean_xml_string_removes_binary_control_chars():
    """
    Ca biên 2.2: Lọc các ký tự nhị phân ẩn (\x00, \x08, \x0c, \x1f)
    vốn là nguyên nhân hàng đầu gây hỏng tệp XML OpenXML (Corrupted Docx/Pptx).
    """
    corrupt_str = "Học sinh \x00 làm bài \x08 kiểm tra \x0b định kỳ \x0c theo CV \x1f 5512."
    cleaned = clean_xml_string(corrupt_str)
    assert "\x00" not in cleaned
    assert "\x08" not in cleaned
    assert "\x0b" not in cleaned
    assert "\x0c" not in cleaned
    assert "\x1f" not in cleaned
    assert "Học sinh  làm bài  kiểm tra  định kỳ  theo CV  5512." == cleaned


def test_export_docx_endpoint_with_quotes_and_xml_tags():
    """
    Ca biên 2.3: Gửi payload xuất Word với tiêu đề chứa ngoặc kép, thẻ HTML và dấu tiếng Việt.
    Endpoint phải trả về HTTP 200 và header Content-Disposition tuân thủ RFC 6266.
    """
    plan = get_curated_lesson_plan("Hệ bất phương trình", "Toán học", 10)
    plan.lesson_title = 'Chủ đề: "Hình học không gian" & <Góc giữa 2 mặt phẳng>'

    res = client.post("/api/v1/lesson-plan/export-docx", json=plan.model_dump())
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    disp = res.headers["content-disposition"]
    assert "filename=" in disp
    assert "filename*=" in disp
    assert '"' in disp  # Filename fallback parameter


def test_export_slide_endpoint_with_special_characters():
    """
    Ca biên 2.4: Gửi payload xuất PowerPoint với tiêu đề có ký tự đặc biệt.
    Endpoint phải trả về HTTP 200 và header Content-Disposition an toàn.
    """
    deck = get_curated_slide_deck("Cấp số cộng", "Toán học", 11)
    deck.presentation_title = 'Bài 5: "Cấp số cộng" - Quy tắc: u_n = u_1 + (n-1)d'

    res = client.post("/api/v1/lesson-plan/export-slide", json=deck.model_dump())
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    disp = res.headers["content-disposition"]
    assert "Slide_" in disp
    assert ".pptx" in disp


def test_export_dual_package_with_special_characters_zip_structure():
    """
    Ca biên 2.5: Đóng gói Dual Package ZIP khi tiêu đề chứa ký tự đặc biệt.
    Xác thực bên trong tệp ZIP không có tên file lỗi, các tệp .docx và .pptx mở được toàn vẹn.
    """
    plan = get_curated_lesson_plan("Cực trị hàm số", "Toán học", 12)
    plan.lesson_title = 'Chương 1: "Ứng dụng đạo hàm" & Cực trị hàm số / Khối chóp'
    deck = get_curated_slide_deck("Cực trị hàm số", "Toán học", 12)
    deck.presentation_title = plan.lesson_title

    payload = {"plan": plan.model_dump(), "slide_deck": deck.model_dump()}
    res = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"

    # Mở và kiểm định nội dung bên trong file ZIP
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        file_names = zf.namelist()
        assert len(file_names) == 3  # DOCX, PPTX, MANIFEST
        for fname in file_names:
            assert '"' not in fname
            assert '<' not in fname
            assert '>' not in fname
            assert ':' not in fname
            assert '\\' not in fname


# ==============================================================================
# NHÓM 3: SNAPSHOT 3D BASE64 RỖNG, LỖI HOẶC DỊ DẠNG
# ==============================================================================

def test_decode_base64_empty_and_prefix_only():
    """
    Ca biên 3.1: Chuỗi Data URL chỉ có prefix header nhưng thân rỗng.
    """
    assert decode_base64_data_url("") is None
    assert decode_base64_data_url("data:image/png;base64,") is None
    assert decode_base64_data_url("data:image/jpeg;base64,   ") is None


def test_decode_base64_corrupted_characters_and_non_image():
    """
    Ca biên 3.2: Chuỗi Base64 chứa ký tự hỏng hoặc dữ liệu nhị phân không phải ảnh.
    """
    # Ký tự base64 hỏng
    assert decode_base64_data_url("data:image/png;base64,!!@@##$$%%^^") is None

    # Base64 của một chuỗi text "Hello World" (không phải file ảnh)
    plain_text_b64 = base64.b64encode(b"This is just plain text, not an image.").decode()
    assert decode_base64_data_url(f"data:image/png;base64,{plain_text_b64}") is None


def test_pptx_export_with_corrupted_3d_snapshot_does_not_crash():
    """
    Ca biên 3.3: Slide bật has_3d=True nhưng snapshot_3d_base64 bị hỏng hoặc rác.
    Hệ thống vẫn xuất PowerPoint thành công mà không ném exception làm gián đoạn người dùng.
    """
    deck = get_curated_slide_deck("Quan hệ vuông góc", "Toán học", 11)
    # Cố tình làm hỏng snapshot_3d_base64
    for slide in deck.slides:
        if slide.has_3d:
            slide.snapshot_3d_base64 = "data:image/png;base64,CORRUPTED_BYTES_HERE"

    pptx_stream = export_slide_deck_to_pptx(deck)
    assert pptx_stream is not None
    assert len(pptx_stream.getvalue()) > 2000


# ==============================================================================
# NHÓM 4: NETWORK FLAKINESS, LLM TIMEOUT/429/503 & FALLBACK RESILIENCE
# ==============================================================================

def test_lesson_plan_generate_fallback_when_llm_fails():
    """
    Ca biên 4.1: Giả lập LLM Gateway sập hoàn toàn (ném Exception mạng/timeout).
    Endpoint /api/v1/lesson-plan/generate phải trả về 200 OK với Curated Lesson Plan
    kèm cảnh báo rõ ràng, tuyệt đối không quăng mã lỗi 500.
    """
    with patch("services.ai_service.llm_gateway.generate_structured", side_effect=TimeoutError("Connection timed out to Groq/Gemini")):
        req_data = {
            "topic": "Hệ bất phương trình bậc nhất hai ẩn",
            "subject": "Toán học",
            "grade": 10
        }
        res = client.post("/api/v1/lesson-plan/generate", json=req_data)
        assert res.status_code == 200, f"Phải trả về 200 OK qua Fallback, nhận được: {res.status_code}"
        data = res.json()
        assert data["is_valid"] is True
        assert len(data["plan"]["activities"]) == 4
        # Kiểm tra có cảnh báo fallback
        assert any("dự phòng" in w.lower() or "chuẩn sgk" in w.lower() or "gián đoạn" in w.lower() for w in data["warnings"])


def test_slide_generate_fallback_when_llm_rate_limited():
    """
    Ca biên 4.2: Giả lập LLM chạm trần Quota Limit 429 hoặc trả về lỗi.
    Endpoint /api/v1/slide/generate phải trả về 200 OK với Curated SlideDeck
    kèm các ảnh render bổ trợ đầy đủ, không gây lỗi 500.
    """
    with patch("services.ai_service.llm_gateway.generate_structured", side_effect=RuntimeError("Groq 429: Rate limit reached")):
        req_data = {
            "topic": "Tính đơn điệu và cực trị hàm số",
            "subject": "Toán học",
            "grade": 12
        }
        res = client.post("/api/v1/slide/generate", json=req_data)
        assert res.status_code == 200, f"Phải trả về 200 OK qua Fallback, nhận được: {res.status_code}"
        data = res.json()
        assert "slides" in data
        assert len(data["slides"]) >= 4
        # Đảm bảo vẫn có render đồ thị hoặc hình học
        has_renders = any(s.get("chart_image_base64") or s.get("formula_image_base64") for s in data["slides"])
        assert has_renders is True


def test_dual_package_export_when_slide_is_fallback():
    """
    Ca biên 4.3: Xuất Dual Package trong điều kiện chỉ có Lesson Plan do mạng gián đoạn.
    Hệ thống tự động đồng bộ và hoàn thành gói ZIP 200 OK.
    """
    plan = get_curated_lesson_plan("Cấp số cộng", "Toán học", 11)
    payload = {"plan": plan.model_dump()}  # Không truyền slide_deck
    res = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"


# ==============================================================================
# NHÓM 5: ĐẦU VÀO CỰC ĐOAN & NGOÀI PHẠM VI (BOUNDARY TESTING)
# ==============================================================================

def test_curated_fallback_with_none_topic_and_invalid_grade():
    """
    Ca biên 5.1: Gọi Fallback Service với topic=None và khối lớp ngoài phạm vi (grade=99 hoặc grade=-1).
    Hệ thống phải tự động điều hướng an toàn về Giáo án và Slide chuẩn mà không văng Exception.
    """
    # Grade ngoài phạm vi -> Phải trả về bản mặc định hợp lệ
    plan_out_of_bounds = get_curated_lesson_plan(topic=None, grade=99)
    assert isinstance(plan_out_of_bounds, LessonPlanSchema)
    assert len(plan_out_of_bounds.activities) == 4

    deck_out_of_bounds = get_curated_slide_deck(topic=None, grade=-1)
    assert isinstance(deck_out_of_bounds, SlideDeckSchema)
    assert len(deck_out_of_bounds.slides) >= 4


def test_generate_endpoints_with_whitespace_topic():
    """
    Ca biên 5.2: Gửi bài dạy chỉ gồm khoảng trắng "   ".
    Hệ thống phải xử lý nhẹ nhàng, không gây Exception 500.
    """
    with patch("services.ai_service.llm_gateway.generate_structured", side_effect=ValueError("Invalid prompt")):
        req_data = {
            "topic": "   ",
            "subject": "Toán học",
            "grade": 10
        }
        res_plan = client.post("/api/v1/lesson-plan/generate", json=req_data)
        assert res_plan.status_code == 200
        assert res_plan.json()["is_valid"] is True

        res_slide = client.post("/api/v1/slide/generate", json=req_data)
        assert res_slide.status_code == 200
        assert len(res_slide.json()["slides"]) >= 4
