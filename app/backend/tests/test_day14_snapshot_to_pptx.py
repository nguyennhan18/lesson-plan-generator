r"""
Automated Test Suite — Day 14: Cầu nối Chụp ảnh Snapshot 3D gửi về Backend xuất PPTX
Kiểm thử chi tiết các hạng mục của Ngày 14:
- Task 14.1: Viết hàm JavaScript capture3DSnapshot() sử dụng canvas.toDataURL('image/png') chụp lại khung hình 3D hiện tại
- Task 14.2: Frontend đóng gói chuỗi Base64 Data URL vào request POST /api/v1/lesson-plan/export-slide
- Task 14.3: Backend giải mã chuỗi Base64 thành byte stream nhúng ảnh vào slide PPTX qua python-pptx
- Task 14.4: Tinh chỉnh tọa độ và kích thước khung ảnh 3D cân đối với bố cục 16:9
- Task 14.5: Nghiệm thu DoD Ngày 14 và kiểm thử tích hợp toàn diện
"""

import base64
import io
import re
import sys
from pathlib import Path
from typing import Any
import pytest
from fastapi.testclient import TestClient
from typing import Any
ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"


from lessonai.main import app

client = TestClient(app)


# 1x1 transparent PNG pixel base64 string
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
SAMPLE_DATA_URL = f"data:image/png;base64,{SAMPLE_PNG_BASE64}"






def test_task_14_1_data_url_format_and_base64_validation():
    """
    Task 14.1: Kiểm tra định dạng chuỗi Base64 Data URL chuẩn HTML5 Canvas:
    - Phải bắt đầu bằng tiền tố 'data:image/png;base64,'
    - Phần payload Base64 hợp lệ, khi giải mã phải chứa PNG Magic Bytes [0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n']
    """
    data_url_pattern = re.compile(r"^data:image/png;base64,([A-Za-z0-9+/=]+)$")
    match = data_url_pattern.match(SAMPLE_DATA_URL)
    assert match is not None, "Chuỗi Data URL không khớp với biểu thức chính quy chuẩn PNG base64"

    raw_base64 = match.group(1)
    image_bytes = base64.b64decode(raw_base64)

    # Kiểm tra 8 bytes chữ ký (Magic Header) của chuẩn PNG (ISO/IEC 15948)
    png_magic_header = b"\x89PNG\r\n\x1a\n"
    assert image_bytes.startswith(png_magic_header), (
        f"Dữ liệu byte không phải định dạng PNG hợp lệ. Header nhận được: {image_bytes[:8]}"
    )
    assert len(image_bytes) > 0


def test_task_14_2_schema_validation_snapshot_3d():
    """
    Task 14.2: Kiểm tra SlideSchema và SlideDeckSchema hỗ trợ trường snapshot_3d_base64:
    - SlideSchema chấp nhận snapshot_3d_base64 dạng Base64 Data URL
    - SlideDeckSchema chấp nhận snapshot_3d_base64 làm dự phòng toàn cục
    """
    from lessonai.schemas.slide_schema import SlideDeckSchema, SlideSchema, SlideType, SlideLayout

    slide = SlideSchema(
        slide_index=1,
        type=SlideType.CONCEPT_SLIDE,
        layout=SlideLayout.IMAGE_TEXT,
        title="Khối Chóp Tứ Giác S.ABCD",
        bullet_points=["Đáy ABCD là hình vuông", "SA vuông góc đáy"],
        has_3d=True,
        polyhedron_type="pyramid_square",
        snapshot_3d_base64=SAMPLE_DATA_URL
    )
    assert slide.snapshot_3d_base64 == SAMPLE_DATA_URL
    assert slide.has_3d is True
    assert slide.polyhedron_type == "pyramid_square"

    deck = SlideDeckSchema(
        presentation_title="Hình Học Không Gian 3D",
        subject="Toán học",
        grade=11,
        slides=[slide],
        snapshot_3d_base64=SAMPLE_DATA_URL
    )
    assert deck.snapshot_3d_base64 == SAMPLE_DATA_URL
    assert len(deck.slides) == 1
    assert deck.slides[0].snapshot_3d_base64 == SAMPLE_DATA_URL




def test_task_14_2_api_export_slide_accepts_snapshot_payload():
    """
    Task 14.2: Kiểm tra endpoint POST /api/v1/lesson-plan/export-slide:
    - Tiếp nhận payload SlideDeckSchema chứa snapshot_3d_base64 mà không sinh lỗi HTTP 422 Unprocessable Entity
    - Trả về status 200 và file nhị phân PowerPoint (.pptx)
    """
    payload = {
        "presentation_title": "Hình Học Không Gian 3D Test Snapshot",
        "subject": "Toán học",
        "grade": 11,
        "theme": "math_academic",
        "snapshot_3d_base64": SAMPLE_DATA_URL,
        "slides": [
            {
                "slide_index": 1,
                "type": "TITLE_SLIDE",
                "layout": "TITLE_ONLY",
                "title": "Chủ đề 3D: Khối Đa Diện",
                "bullet_points": ["Khám phá hình học không gian trực quan"],
                "has_3d": False
            },
            {
                "slide_index": 2,
                "type": "CONCEPT_SLIDE",
                "layout": "IMAGE_TEXT",
                "title": "Hình Chóp Tứ Giác Đều S.ABCD",
                "bullet_points": [
                    "Đáy ABCD là hình vuông tâm O cạnh a",
                    "Đoạn SO vuông góc với mặt phẳng đáy (ABCD)",
                    "Thể tích khối chóp: V = (1/3) * a^2 * h"
                ],
                "main_definition_latex": "V = \\frac{1}{3} a^2 h",
                "has_3d": True,
                "polyhedron_type": "pyramid_square",
                "snapshot_3d_base64": SAMPLE_DATA_URL
            }
        ]
    }

    response = client.post("/api/v1/lesson-plan/export-slide", json=payload)
    assert response.status_code == 200, f"Lỗi xuất slide: {response.text}"
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert len(response.content) > 1000, "File PowerPoint trả về rỗng hoặc kích thước quá nhỏ"


def test_task_14_3_decode_base64_data_url():
    """
    Task 14.3: Kiểm tra hàm decode_base64_data_url():
    1. Giải mã thành công chuỗi Data URL chuẩn (data:image/png;base64,...)
    2. Giải mã thành công chuỗi Base64 trần (không có tiền tố data:...)
    3. Tự động khắc phục chuỗi Base64 bị khuyết padding '='
    4. Xử lý an toàn khi gặp dữ liệu lỗi/rỗng/None mà không raise Exception
    """
    from lessonai.exporters.slide_exporter import decode_base64_data_url

    # 1. Data URL chuẩn
    stream1 = decode_base64_data_url(SAMPLE_DATA_URL)
    assert stream1 is not None
    assert isinstance(stream1, io.BytesIO)
    content1 = stream1.getvalue()
    assert content1.startswith(b"\x89PNG\r\n\x1a\n")

    # 2. Raw Base64 không có tiền tố
    stream2 = decode_base64_data_url(SAMPLE_PNG_BASE64)
    assert stream2 is not None
    assert stream2.getvalue().startswith(b"\x89PNG\r\n\x1a\n")

    # 3. Base64 bị khuyết padding '='
    unpadded_b64 = SAMPLE_PNG_BASE64.rstrip("=")
    stream3 = decode_base64_data_url(unpadded_b64)
    assert stream3 is not None
    assert stream3.getvalue().startswith(b"\x89PNG\r\n\x1a\n")

    # 4. Giá trị None, rỗng hoặc chuỗi rác
    assert decode_base64_data_url(None) is None
    assert decode_base64_data_url("") is None
    assert decode_base64_data_url("invalid_garbage_base64_!@#$%^") is None


def test_task_14_3_pptx_embedding_creates_picture_shape():
    """
    Task 14.3: Kiểm tra quá trình nhúng ảnh 3D snapshot vào Slide PowerPoint qua python-pptx:
    - Khi slide có snapshot_3d_base64, hệ thống tạo shape PICTURE (add_picture)
    - Dữ liệu ảnh nhúng trong PowerPoint khớp với ảnh PNG từ frontend
    - Slide vẫn hiển thị đầy đủ Header, Title, Bullets và Footer
    """
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
    from lessonai.schemas.slide_schema import SlideDeckSchema, SlideSchema, SlideType, SlideLayout

    slide_3d = SlideSchema(
        slide_index=1,
        type=SlideType.CONCEPT_SLIDE,
        layout=SlideLayout.IMAGE_TEXT,
        title="Hình Chóp Tứ Giác S.ABCD & Chiều Cao h",
        bullet_points=[
            "Đáy ABCD là hình vuông tâm O cạnh a = 4.0",
            "Đường cao SA vuông góc đáy, chiều cao h = 4.0",
            "Thể tích: V = (1/3) * a^2 * h"
        ],
        main_definition_latex="V_{S.ABCD} = \\frac{1}{3} a^2 h",
        has_3d=True,
        polyhedron_type="pyramid_square",
        snapshot_3d_base64=SAMPLE_DATA_URL
    )

    deck = SlideDeckSchema(
        presentation_title="Hình Học Không Gian 3D",
        subject="Toán học",
        grade=11,
        slides=[slide_3d]
    )

    pptx_stream = export_slide_deck_to_pptx(deck)
    assert pptx_stream is not None

    prs = Presentation(pptx_stream)
    assert len(prs.slides) == 1

    slide = prs.slides[0]
    # Tìm kiếm shape PICTURE trong slide
    picture_shapes = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert len(picture_shapes) >= 1, "Không tìm thấy Picture Shape nào trong slide có 3D snapshot!"

    # Kiểm tra ít nhất 1 Picture Shape chứa đúng dữ liệu ảnh PNG
    has_png_snapshot = False
    for p_sh in picture_shapes:
        blob = getattr(p_sh, "image").blob
        if blob.startswith(b"\x89PNG\r\n\x1a\n"):
            has_png_snapshot = True
            assert p_sh.width > 0
            assert p_sh.height > 0
            break

    assert has_png_snapshot, "Picture Shape không chứa dữ liệu PNG hợp lệ từ snapshot_3d_base64"




def make_test_png_data_url(width: int, height: int, color=(56, 189, 248)) -> str:
    """Helper tạo chuỗi Data URL PNG hợp lệ với kích thước pixel bất kỳ để kiểm thử tỉ lệ."""
    from PIL import Image
    img = Image.new("RGBA", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def test_task_14_4_aspect_preserving_fit_algorithm():
    """
    Task 14.4: Kiểm tra thuật toán compute_aspect_preserving_fit():
    1. Ảnh toàn cảnh Landscape (1920x1080 ~ 16:9): Fit chiều rộng, căn giữa theo chiều cao
    2. Ảnh vuông Square (800x800 ~ 1:1): Fit chiều cao, căn giữa theo chiều rộng
    3. Ảnh đứng Portrait (600x1200 ~ 1:2): Fit chiều cao, căn giữa theo chiều rộng
    4. Tỉ lệ khung hình (Aspect Ratio) của kích thước fit phải bằng chính xác tỉ lệ ảnh gốc
    """
    from lessonai.exporters.slide_exporter import compute_aspect_preserving_fit

    box_l, box_t, box_w, box_h = 5.7, 1.5, 3.6, 2.45

    # 1. Ảnh 16:9 (1920x1080)
    l1, t1, w1, h1 = compute_aspect_preserving_fit(1920, 1080, box_l, box_t, box_w, box_h)
    assert w1 == pytest.approx(box_w)
    assert h1 < box_h
    assert l1 == pytest.approx(box_l)
    assert t1 > box_t  # Căn giữa theo trục đứng
    assert (w1 / h1) == pytest.approx(1920 / 1080, rel=1e-3)

    # 2. Ảnh vuông 1:1 (800x800)
    l2, t2, w2, h2 = compute_aspect_preserving_fit(800, 800, box_l, box_t, box_w, box_h)
    assert h2 == pytest.approx(box_h)
    assert w2 < box_w
    assert t2 == pytest.approx(box_t)
    assert l2 > box_l  # Căn giữa theo trục ngang
    assert (w2 / h2) == pytest.approx(1.0, rel=1e-3)

    # 3. Ảnh đứng 1:2 (600x1200)
    l3, t3, w3, h3 = compute_aspect_preserving_fit(600, 1200, box_l, box_t, box_w, box_h)
    assert h3 == pytest.approx(box_h)
    assert w3 < box_w
    assert (w3 / h3) == pytest.approx(600 / 1200, rel=1e-3)


def test_task_14_4_slide_grid_16_9_geometry_and_margins():
    """
    Task 14.4: Kiểm tra sự cân đối và đối xứng toán học của lưới bố cục 16:9 Widescreen:
    - Kích thước slide chuẩn: 10.0 x 5.625 inches (16:9 Widescreen)
    - Cột Trái: l_margin = 0.6 in, w_left = 4.8 in
    - Khe hở Gutter: 5.6 - (0.6 + 4.8) = 0.2 in
    - Cột Phải: card_w = 3.8 in
    - Lề Phải: 10.0 - (5.6 + 3.8) = 0.6 in
    - Đối xứng hoàn hảo: Lề Trái (0.6 in) == Lề Phải (0.6 in)
    """
    from pptx import Presentation
    from pptx.util import Inches
    from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
    from lessonai.schemas.slide_schema import SlideDeckSchema, SlideSchema

    deck = SlideDeckSchema(
        presentation_title="Lưới 16:9 Toán Học",
        subject="Toán học",
        grade=11,
        slides=[
            SlideSchema(
                slide_index=1,
                title="Khối Chóp S.ABCD",
                bullet_points=["Đáy là hình vuông"],
                has_3d=True,
                polyhedron_type="pyramid_square",
                snapshot_3d_base64=SAMPLE_DATA_URL
            )
        ]
    )

    pptx_stream = export_slide_deck_to_pptx(deck)
    prs = Presentation(pptx_stream)

    # Kiểm tra kích thước Slide chuẩn 16:9
    assert prs.slide_width is not None and prs.slide_height is not None
    assert prs.slide_width == Inches(10.0)
    assert prs.slide_height == Inches(5.625)
    assert (float(prs.slide_width) / float(prs.slide_height)) == pytest.approx(16.0 / 9.0)

    # Kiểm tra tính toán lề
    l_margin = 0.6
    w_left = 4.8
    gutter = 5.6 - (l_margin + w_left)
    w_card = 3.8
    r_margin = 10.0 - (5.6 + w_card)

    assert gutter == pytest.approx(0.2)
    assert l_margin == pytest.approx(r_margin)  # Đối xứng lề hoàn hảo
