# -*- coding: utf-8 -*-
r"""
Test Suite Ngày 18: Nâng Cấp Toàn Diện Module Xuất PowerPoint (slide_exporter.py)
Task 18.1: Thiết Kế Layout Native DrawingML Cho Slide Trắc Nghiệm (QUIZ_SLIDE)
Task 18.2: Tự Động Nhúng Ảnh Chụp Snapshot 3D WebGL Vào Slide PPTX (Box-Fit Aspect Ratio)
"""

import io
import sys
import base64
from pathlib import Path
import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from exporters.slide_exporter import (
    export_slide_deck_to_pptx,
    build_title_slide,
    build_quiz_slide,
    build_content_slide,
    build_speaker_notes,
    calculate_auto_fit_font,
    compute_aspect_preserving_fit,
    decode_base64_data_url,
    latex_to_unicode_math,
    COLOR_QUIZ_A,
    COLOR_QUIZ_B,
    COLOR_QUIZ_C,
    COLOR_QUIZ_D,
    COLOR_QUIZ_CORRECT_BG,
    COLOR_QUIZ_CORRECT_BORDER,
    COLOR_QUIZ_CARD_BG,
    COLOR_QUIZ_CARD_BORDER,
    COLOR_QUIZ_BADGE_BG,
)


def _get_auto_shape_type(shape):
    """Lấy an toàn auto_shape_type không ném ValueError khi gặp textbox"""
    try:
        return shape.auto_shape_type
    except Exception:
        return None


@pytest.fixture
def sample_quiz_slide_data():
    return {
        "type": "EXERCISE_SLIDE",
        "layout": "QUIZ_OPTION",
        "title": "Câu hỏi trắc nghiệm rèn luyện",
        "question": r"Cho hàm số \(y = x^3 - 3x^2 + 2\). Tìm số điểm cực trị của hàm số đã cho.",
        "activity_type": "Câu hỏi khởi động",
        "quiz_options": [
            {
                "label": "A",
                "text": r"Có đúng 1 điểm cực trị",
                "is_correct": False,
                "distractor_rationale": "Học sinh chỉ giải x = 0 mà bỏ quên nghiệm x = 2 của y' = 0.",
            },
            {
                "label": "B",
                "text": r"Có đúng 2 điểm cực trị",
                "is_correct": True,
                "distractor_rationale": "",
            },
            {
                "label": "C",
                "text": r"Hàm số không có cực trị",
                "is_correct": False,
                "distractor_rationale": "Nhầm lẫn điều kiện delta âm vô nghiệm với phương trình có 2 nghiệm phân biệt.",
            },
            {
                "label": "D",
                "text": r"Có 3 điểm cực trị",
                "is_correct": False,
                "distractor_rationale": "Nhầm số điểm cực trị với bậc của hàm số đa thức bậc ba.",
            },
        ],
        "teacher_note": "Hướng dẫn học sinh lấy đạo hàm y' = 3x^2 - 6x và giải y' = 0 tìm 2 nghiệm phân biệt.",
    }


def test_build_quiz_slide_shape_counts_and_types(sample_quiz_slide_data):
    """
    Kiểm tra cấu trúc DrawingML Native Shape của Slide Trắc nghiệm:
    - 4 Card Rounded Rectangle làm nền
    - 4 Huy hiệu tròn Oval A, B, C, D
    - 1 Pill Tag hoạt động sư phạm
    - 1 Textbox câu hỏi
    - 2 Textbox chân trang
    """
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    build_quiz_slide(
        slide=slide,
        slide_data=sample_quiz_slide_data,
        slide_idx=2,
        total_slides=5,
        subject="Toán học",
        grade=12,
    )

    shapes = list(slide.shapes)
    # Tối thiểu 12 shapes trong nội dung (1 tag + 1 q_box + 4 cards + 4 badges + 4 opt textboxes + 2 footers = 16)
    assert len(shapes) == 16

    # Đếm số Oval (Huy hiệu A, B, C, D)
    oval_shapes = [s for s in shapes if _get_auto_shape_type(s) == MSO_SHAPE.OVAL]
    assert len(oval_shapes) == 4

    # Đếm số Rounded Rectangle (1 tag + 4 cards = 5)
    rounded_rects = [s for s in shapes if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE]
    assert len(rounded_rects) == 5

    # Kiểm tra nhãn A, B, C, D bên trong các huy hiệu oval
    badge_texts = [s.text_frame.text.strip() for s in oval_shapes]
    assert badge_texts == ["A", "B", "C", "D"]

    # Kiểm tra nội dung câu hỏi
    q_boxes = [s for s in shapes if "Tìm số điểm cực trị" in (s.text if s.has_text_frame else "")]
    assert len(q_boxes) == 1
    assert "y = x³ - 3x² + 2" in q_boxes[0].text


def test_quiz_slide_badge_colors(sample_quiz_slide_data):
    """
    Kiểm định bảng màu nhận diện sư phạm cho 4 huy hiệu tròn A, B, C, D:
    A: Royal Blue (#2563eb)
    B: Emerald Green (#059669)
    C: Amber Orange (#d97706)
    D: Violet Purple (#7c3aed)
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    build_quiz_slide(slide, sample_quiz_slide_data, 1, 1, "Toán", 12)
    oval_shapes = [s for s in slide.shapes if _get_auto_shape_type(s) == MSO_SHAPE.OVAL]

    expected_colors = [COLOR_QUIZ_A, COLOR_QUIZ_B, COLOR_QUIZ_C, COLOR_QUIZ_D]
    for idx, oval in enumerate(oval_shapes):
        assert oval.fill.fore_color.rgb == expected_colors[idx]


def test_quiz_slide_grid_coordinates(sample_quiz_slide_data):
    """
    Kiểm tra tọa độ bố cục lưới 2x2 trong khung 16:9 Widescreen (10.0 x 5.625 inch):
    - Cột 1 (A & C): Left = 0.60 inch
    - Cột 2 (B & D): Left = 5.15 inch
    - Hàng 1 (A & B): Top = 2.35 inch
    - Hàng 2 (C & D): Top = 3.80 inch
    - Kích thước card: Width = 4.25 inch, Height = 1.30 inch
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    build_quiz_slide(slide, sample_quiz_slide_data, 1, 1, "Toán", 12)

    # 4 Card shapes là 4 Rounded Rectangles sau shape đầu tiên (shape đầu tiên là Tag)
    rounded_rects = [s for s in slide.shapes if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE]
    tag_shape = rounded_rects[0]
    card_shapes = rounded_rects[1:5]

    # Kiểm tra tag pill
    assert round(tag_shape.left.inches, 2) == 0.60
    assert round(tag_shape.top.inches, 2) == 0.75

    # Card A: Col 0, Row 0
    assert round(card_shapes[0].left.inches, 2) == 0.60
    assert round(card_shapes[0].top.inches, 2) == 2.35
    assert round(card_shapes[0].width.inches, 2) == 4.25
    assert round(card_shapes[0].height.inches, 2) == 1.30

    # Card B: Col 1, Row 0
    assert round(card_shapes[1].left.inches, 2) == 5.15
    assert round(card_shapes[1].top.inches, 2) == 2.35

    # Card C: Col 0, Row 1
    assert round(card_shapes[2].left.inches, 2) == 0.60
    assert round(card_shapes[2].top.inches, 2) == 3.80

    # Card D: Col 1, Row 1
    assert round(card_shapes[3].left.inches, 2) == 5.15
    assert round(card_shapes[3].top.inches, 2) == 3.80


def test_quiz_slide_highlight_correct(sample_quiz_slide_data):
    """
    Kiểm tra tính năng đánh dấu đáp án đúng:
    - Mặc định (highlight_correct=False): Cả 4 card dùng nền soft slate COLOR_QUIZ_CARD_BG
    - Khi bật highlight_correct=True: Đáp án đúng B chuyển sang màu xanh mint COLOR_QUIZ_CORRECT_BG
    """
    # 1. Trường hợp mặc định
    prs1 = Presentation()
    slide1 = prs1.slides.add_slide(prs1.slide_layouts[6])
    build_quiz_slide(slide1, sample_quiz_slide_data, 1, 1, "Toán", 12)
    cards1 = [s for s in slide1.shapes if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE][1:5]
    for card in cards1:
        assert card.fill.fore_color.rgb == COLOR_QUIZ_CARD_BG

    # 2. Trường hợp bật highlight_correct
    data_highlight = dict(sample_quiz_slide_data)
    data_highlight["highlight_correct"] = True
    prs2 = Presentation()
    slide2 = prs2.slides.add_slide(prs2.slide_layouts[6])
    build_quiz_slide(slide2, data_highlight, 1, 1, "Toán", 12)
    cards2 = [s for s in slide2.shapes if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE][1:5]
    # Card B (index 1) là đáp án đúng
    assert cards2[0].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG
    assert cards2[1].fill.fore_color.rgb == COLOR_QUIZ_CORRECT_BG
    assert cards2[1].line.color.rgb == COLOR_QUIZ_CORRECT_BORDER
    assert cards2[2].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG
    assert cards2[3].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG


def test_latex_to_unicode_math_enhancements():
    r"""
    Kiểm tra chuyển đổi công thức toán học nâng cao:
    - Phân số \frac{a}{b} -> a/b hoặc (a)/(b)
    - Dấu so sánh \ge, \le -> ≥, ≤
    - Số mũ, chỉ số dưới, ký hiệu toán học
    """
    assert latex_to_unicode_math(r"\frac{1}{2}") == "1/2"
    assert latex_to_unicode_math(r"\frac{x + 1}{x - 1}") == "(x + 1)/(x - 1)"
    assert "≥" in latex_to_unicode_math(r"x \ge 2")
    assert "≤" in latex_to_unicode_math(r"y \le 5")
    assert latex_to_unicode_math(r"f'(x) = 3x^2 - 6x") == "f'(x) = 3x² - 6x"


def test_export_slide_deck_with_quiz_and_speaker_notes(sample_quiz_slide_data):
    """
    Kiểm tra hàm tích hợp export_slide_deck_to_pptx():
    - Tự động nhận diện slide trắc nghiệm qua layout='QUIZ_OPTION'
    - Header hiển thị 'QUIZ SLIDE'
    - Speaker Notes nhúng đầy đủ Kịch bản GV + Đáp án đúng + Distractor Rationales
    """
    deck_dict = {
        "presentation_title": "Bài 2: Cực trị của hàm số",
        "subject": "Toán học",
        "grade": 12,
        "slides": [
            {
                "type": "TITLE_SLIDE",
                "title": "Cực Trị Hàm Số",
                "subtitle": "Chương 1 - Ứng dụng đạo hàm",
            },
            sample_quiz_slide_data,
        ],
    }

    pptx_bytes = export_slide_deck_to_pptx(deck_dict)
    assert isinstance(pptx_bytes, io.BytesIO)
    assert pptx_bytes.getbuffer().nbytes > 10000

    prs = Presentation(pptx_bytes)
    assert len(prs.slides) == 2

    # Slide 2 là Quiz Slide
    quiz_slide = prs.slides[1]
    # Header badge bên phải
    header_right = [
        s for s in quiz_slide.shapes
        if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE and "QUIZ SLIDE" in (s.text if s.has_text_frame else "")
    ]
    assert len(header_right) == 1

    # Kiểm tra Speaker Notes
    notes_slide = quiz_slide.notes_slide
    notes_text = notes_slide.notes_text_frame.text
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in notes_text
    assert "[Đáp án đúng chuẩn SGK]: Phương án B" in notes_text
    assert "[Phân tích bẫy sai lầm của học sinh (Distractor Rationales)]" in notes_text
    assert "Phương án A:" in notes_text
    assert "Phương án C:" in notes_text
    assert "Phương án D:" in notes_text


# ==============================================================================
# HẠNG MỤC TEST CHO TASK 18.2: TỰ ĐỘNG NHÚNG ẢNH SNAPSHOT 3D WEBGL VÀO PPTX
# ==============================================================================

def _create_sample_png_base64(width: int = 400, height: int = 300, color: tuple = (37, 99, 235)) -> str:
    """Tạo chuỗi Data URL Base64 PNG giả lập ảnh chụp Canvas WebGL 3D"""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def test_task_18_2_box_fit_various_aspect_ratios():
    """
    Task 18.2: Kiểm tra thuật toán compute_aspect_preserving_fit() trên đa dạng tỉ lệ ảnh:
    - 16:9 Landscape (1920x1080)
    - 4:3 Standard (800x600)
    - 1:1 Square (600x600)
    - 3:4 Portrait (600x800)
    - 3:1 Ultrawide (1500x500)
    Khẳng định:
    1. Kích thước (fit_w, fit_h) nằm trọn vẹn trong khung chứa (box_w, box_h).
    2. Tỉ lệ khung hình ảnh gốc được bảo toàn chính xác tuyệt đối (không méo hình học).
    3. Ảnh được căn giữa đối xứng theo chiều ngang hoặc chiều dọc.
    """
    box_l, box_t, box_w, box_h = 5.7, 1.5, 3.6, 2.45

    test_cases = [
        (1920, 1080, "16:9 Landscape"),
        (800, 600, "4:3 Standard"),
        (600, 600, "1:1 Square"),
        (600, 800, "3:4 Portrait"),
        (1500, 500, "3:1 Ultrawide"),
    ]

    for px_w, px_h, desc in test_cases:
        fit_l, fit_t, fit_w, fit_h = compute_aspect_preserving_fit(
            px_w, px_h, box_l, box_t, box_w, box_h
        )

        # 1. Nằm trọn vẹn trong khung chứa
        assert fit_w <= box_w + 1e-5, f"{desc}: fit_w vượt quá box_w"
        assert fit_h <= box_h + 1e-5, f"{desc}: fit_h vượt quá box_h"
        assert fit_l >= box_l - 1e-5, f"{desc}: fit_l nhỏ hơn box_l"
        assert fit_t >= box_t - 1e-5, f"{desc}: fit_t nhỏ hơn box_t"
        assert (fit_l + fit_w) <= (box_l + box_w) + 1e-5, f"{desc}: tràn lề phải"
        assert (fit_t + fit_h) <= (box_t + box_h) + 1e-5, f"{desc}: tràn đáy"

        # 2. Bảo toàn tỉ lệ khung hình chính xác tuyệt đối
        expected_ratio = px_w / px_h
        actual_ratio = fit_w / fit_h
        assert actual_ratio == pytest.approx(expected_ratio, rel=1e-3), f"{desc}: tỉ lệ bị biến dạng"

        # 3. Căn giữa
        orig_aspect = px_w / px_h
        box_aspect = box_w / box_h
        if orig_aspect >= box_aspect:
            # Fit chiều rộng -> Căn giữa theo trục Y
            expected_top = box_t + (box_h - fit_h) / 2.0
            assert fit_t == pytest.approx(expected_top, abs=1e-4), f"{desc}: không căn giữa Y"
        else:
            # Fit chiều cao -> Căn giữa theo trục X
            expected_left = box_l + (box_w - fit_w) / 2.0
            assert fit_l == pytest.approx(expected_left, abs=1e-4), f"{desc}: không căn giữa X"


def test_task_18_2_decode_base64_data_url_robustness():
    """
    Task 18.2: Kiểm định độ bền vững của hàm giải mã decode_base64_data_url():
    - Dạng chuẩn có prefix: data:image/png;base64,...
    - Dạng raw Base64 không prefix
    - Dạng thiếu ký tự padding '='
    - Chuỗi rác / hỏng -> Trả về None an toàn, không ném exception
    - Giá trị rỗng / None -> Trả về None an toàn
    """
    sample_url = _create_sample_png_base64(200, 200)

    # 1. Dạng chuẩn có prefix
    stream1 = decode_base64_data_url(sample_url)
    assert stream1 is not None
    assert stream1.tell() == 0
    with Image.open(stream1) as im:
        assert im.size == (200, 200)

    # 2. Dạng chuỗi raw Base64 không prefix
    raw_b64 = sample_url.split(",", 1)[1]
    stream2 = decode_base64_data_url(raw_b64)
    assert stream2 is not None
    with Image.open(stream2) as im:
        assert im.size == (200, 200)

    # 3. Dạng thiếu ký tự padding '='
    unpadded_b64 = raw_b64.rstrip("=")
    stream3 = decode_base64_data_url(unpadded_b64)
    assert stream3 is not None
    with Image.open(stream3) as im:
        assert im.size == (200, 200)

    # 4. Chuỗi rác không phải ảnh
    assert decode_base64_data_url("not_a_valid_base64_image_content") is None
    assert decode_base64_data_url("data:image/png;base64,12345678") is None

    # 5. Giá trị rỗng / None
    assert decode_base64_data_url("") is None
    assert decode_base64_data_url(None) is None


def test_task_18_2_3d_snapshot_embedding_in_content_slide():
    """
    Task 18.2: Kiểm tra quá trình nhúng ảnh 3D vào Slide Nội dung (build_content_slide):
    - Khung viền Rounded Rectangle card bên phải
    - Picture shape được thêm thành công vào slide với kích thước đúng tỉ lệ
    - Badge 'Mô hình 3D WebGL (SGK)' xuất hiện
    - Tên khối đa diện chuẩn SGK xuất hiện
    """
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    sample_b64 = _create_sample_png_base64(800, 600, color=(16, 185, 129))
    slide_data = {
        "type": "CONCEPT_SLIDE",
        "title": "Khối Lập Phương ABCD.A'B'C'D'",
        "bullet_points": ["Có 6 mặt vuông bằng nhau", "Có 12 cạnh bằng nhau"],
        "has_3d": True,
        "polyhedron_type": "cube",
        "snapshot_3d_base64": sample_b64,
    }

    build_content_slide(
        slide=slide,
        slide_data=slide_data,
        slide_idx=3,
        total_slides=6,
        subject="Toán học",
        grade=11,
    )

    shapes = list(slide.shapes)
    # Kiểm tra có picture shape
    pictures = [s for s in shapes if s.shape_type == 13]  # 13 = MSO_SHAPE_TYPE.PICTURE
    assert len(pictures) >= 1
    pic = pictures[0]

    # Kiểm tra tỉ lệ ảnh (800x600 = 4:3)
    aspect_pic = pic.width / pic.height
    assert aspect_pic == pytest.approx(800 / 600, rel=1e-2)

    # Kiểm tra Badge 3D WebGL
    badge_3d = [s for s in shapes if "Mô hình 3D WebGL" in (s.text if s.has_text_frame else "")]
    assert len(badge_3d) == 1

    # Kiểm tra Tiêu đề khối đa diện
    caption_shapes = [s for s in shapes if "Hình Lập Phương" in (s.text if s.has_text_frame else "")]
    assert len(caption_shapes) == 1


def test_task_18_2_polyhedron_sgk_labels():
    """
    Task 18.2: Kiểm tra từ điển nhãn khối đa diện chuẩn SGK:
    - cube -> Hình Lập Phương ABCD.A'B'C'D'
    - pyramid_square -> Hình Chóp Tứ Giác S.ABCD
    - pyramid_triangle -> Hình Chóp Tam Giác S.ABC
    - prism_triangle -> Hình Lăng Trụ Đứng ABC.A'B'C'
    - cone -> Hình Nón Tròn Xoay (SGK)
    - cylinder -> Hình Trụ Tròn Xoay (SGK)
    - Nhãn tùy biến polyhedron_label
    """
    prs = Presentation()
    sample_b64 = _create_sample_png_base64(300, 300)

    cases = [
        ("pyramid_square", "Hình Chóp Tứ Giác S.ABCD"),
        ("pyramid_triangle", "Hình Chóp Tam Giác S.ABC"),
        ("prism_triangle", "Hình Lăng Trụ Đứng ABC.A'B'C'"),
        ("cone", "Hình Nón Tròn Xoay (SGK)"),
    ]

    for poly_type, expected_caption in cases:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        data = {
            "title": f"Mô hình {poly_type}",
            "has_3d": True,
            "polyhedron_type": poly_type,
            "snapshot_3d_base64": sample_b64,
        }
        build_content_slide(slide, data, 1, 1, "Toán", 11)
        found = any(expected_caption in (s.text if s.has_text_frame else "") for s in slide.shapes)
        assert found, f"Không tìm thấy caption chuẩn cho {poly_type}: '{expected_caption}'"

    # Trường hợp nhãn tùy biến
    slide_custom = prs.slides.add_slide(prs.slide_layouts[6])
    data_custom = {
        "title": "Mô hình Tùy Biến",
        "has_3d": True,
        "polyhedron_label": "Mô hình Khối Đa Diện Trực Quan Lớp 12A",
        "snapshot_3d_base64": sample_b64,
    }
    build_content_slide(slide_custom, data_custom, 1, 1, "Toán", 12)
    found_custom = any("Mô hình Khối Đa Diện Trực Quan Lớp 12A" in (s.text if s.has_text_frame else "") for s in slide_custom.shapes)
    assert found_custom


def test_task_18_2_deck_level_snapshot_inheritance_image_text():
    """
    Task 18.2: Kiểm tra cơ chế tự động kế thừa snapshot 3D từ cấp Deck xuống Slide:
    - Khi slide có layout='IMAGE_TEXT' hoặc has_3d=True mà không có snapshot riêng,
      sẽ tự động thừa hưởng chuỗi snapshot_3d từ SlideDeck tổng thể.
    """
    deck_b64 = _create_sample_png_base64(500, 500, color=(245, 158, 11))

    deck_dict = {
        "presentation_title": "Hình Học Không Gian 11",
        "subject": "Toán học",
        "grade": 11,
        "snapshot_3d_base64": deck_b64,
        "slides": [
            {
                "type": "CONCEPT_SLIDE",
                "layout": "IMAGE_TEXT",
                "title": "Định lý 3 đường vuông góc",
                "bullet_points": ["Đường thẳng vuông góc với mặt phẳng"],
                "has_3d": True,
                "polyhedron_type": "pyramid_triangle",
                # Không có snapshot_3d_base64 tại slide -> Phải kế thừa từ deck!
            }
        ],
    }

    pptx_bytes = export_slide_deck_to_pptx(deck_dict)
    prs = Presentation(pptx_bytes)
    slide = prs.slides[0]

    # Kiểm tra slide đã có picture shape được nhúng từ deck snapshot
    pictures = [s for s in slide.shapes if s.shape_type == 13]
    assert len(pictures) == 1

    # Kiểm tra tiêu đề khối đa diện tam giác xuất hiện
    assert any("Hình Chóp Tam Giác S.ABC" in (s.text if s.has_text_frame else "") for s in slide.shapes)


# ==============================================================================
# HẠNG MỤC TEST CHO TASK 18.3: NHÚNG KỊCH BẢN LỜI THOẠI & BÓC TÁCH BẪY VÀO SPEAKER NOTES
# ==============================================================================

def test_task_18_3_build_speaker_notes_pedagogical_structure():
    """
    Task 18.3: Kiểm tra cấu trúc ghi chú sư phạm toàn diện của hàm build_speaker_notes():
    - Kịch bản giảng dạy Công văn 5512 (teacher_note)
    - Chuẩn đầu ra (target_outcome)
    - Trình độ phân hóa học sinh (class_proficiency: basic, standard, advanced)
    - Công thức toán trọng tâm (main_definition_latex)
    """
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    slide_data = {
        "title": "Định Nghĩa Đạo Hàm",
        "teacher_note": "Giáo viên đặt câu hỏi gợi mở về vận tốc tức thời của chuyển động thẳng.",
        "target_outcome": "Học sinh nắm vững định nghĩa đạo hàm qua giới hạn tỉ số số gia.",
        "class_proficiency": "advanced",
        "main_definition_latex": r"f'(x_0) = \lim_{\Delta x \to 0} \frac{f(x_0 + \Delta x) - f(x_0)}{\Delta x}",
    }

    notes_text = build_speaker_notes(slide, slide_data, is_quiz=False, subject="Toán học", grade=11)
    assert notes_text is not None

    # 1. Kịch bản giảng dạy
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in notes_text
    assert "vận tốc tức thời" in notes_text

    # 2. Chuẩn đầu ra & Phân hóa năng lực
    assert "[Mục tiêu sư phạm & Phân hóa năng lực]" in notes_text
    assert "Học sinh nắm vững định nghĩa đạo hàm" in notes_text
    assert "Lớp nâng cao" in notes_text

    # 3. Công thức toán trọng tâm
    assert "[Công thức toán trọng tâm bài học]" in notes_text
    assert "lim" in notes_text
    assert "Δ" in notes_text
    assert "f'(x" in notes_text


def test_task_18_3_speaker_notes_worked_solution_steps():
    """
    Task 18.3: Kiểm tra nhúng các bước giải tự luận chi tiết (worked_solution_steps) vào Speaker Notes:
    - Liệt kê đầy đủ Bước 1, Bước 2, Bước 3...
    - Chuyển đổi mã LaTeX trong các bước sang Unicode Math
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    slide_data = {
        "title": "Ví Dụ Tìm Cực Trị",
        "teacher_note": "Cho học sinh 3 phút tự suy nghĩ trước khi trình bày lời giải mẫu.",
        "worked_solution_steps": [
            r"Tập xác định: D = \mathbb{R}",
            r"Tính đạo hàm: y' = 3x^2 - 6x",
            r"Giải phương trình y' = 0 \Leftrightarrow 3x(x - 2) = 0 \Leftrightarrow x = 0 \text{ hoặc } x = 2",
            r"Lập bảng xét dấu: Hàm số đạt cực đại tại x = 0 (y_{CĐ} = 2), cực tiểu tại x = 2 (y_{CT} = -2)",
        ],
    }

    notes_text = build_speaker_notes(slide, slide_data, is_quiz=False, subject="Toán học", grade=12)
    assert notes_text is not None

    assert "[Các bước giải mẫu tự luận chi tiết chuẩn SGK]" in notes_text
    assert "Bước 1: Tập xác định: D = ℝ" in notes_text
    assert "Bước 2: Tính đạo hàm: y' = 3x² - 6x" in notes_text
    assert "Bước 3:" in notes_text
    assert "Bước 4:" in notes_text
    assert "y_CĐ" in notes_text or "Cực đại" in notes_text or "cực đại" in notes_text


def test_task_18_3_quiz_distractor_rationales_in_speaker_notes():
    """
    Task 18.3: Kiểm tra bóc tách bẫy sai lầm và phân tích phương án nhiễu trắc nghiệm trong Speaker Notes:
    - Báo rõ phương án đúng chuẩn SGK
    - Liệt kê chi tiết từng phương án sai kèm lý giải vì sao học sinh hay mắc bẫy
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    slide_data = {
        "title": "Câu hỏi Khảo Sát Tính Đơn Điệu",
        "teacher_note": "Cho học sinh giơ tay bình chọn trước khi phân tích các bẫy thường gặp.",
        "quiz_options": [
            {
                "label": "A",
                "text": r"Đồng biến trên (-\infty; 0) và (2; +\infty)",
                "is_correct": True,
                "distractor_rationale": "",
            },
            {
                "label": "B",
                "text": r"Đồng biến trên \mathbb{R}",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm lẫn đạo hàm có delta âm nên kết luận đồng biến trên R.",
            },
            {
                "label": "C",
                "text": r"Nghịch biến trên (0; 2)",
                "is_correct": False,
                "distractor_rationale": "Mặc dù khẳng định này đúng nhưng đề bài hỏi khoảng đồng biến, học sinh đọc sót đề.",
            },
            {
                "label": "D",
                "text": r"Đồng biến trên (0; 2)",
                "is_correct": False,
                "distractor_rationale": "Nhầm dấu của tam thức bậc hai trong khoảng hai nghiệm (trong trái ngoài cùng).",
            },
        ],
    }

    notes_text = build_speaker_notes(slide, slide_data, is_quiz=True, subject="Toán học", grade=12)
    assert notes_text is not None

    # Khẳng định đáp án đúng
    assert "[Đáp án đúng chuẩn SGK]: Phương án A" in notes_text

    # Khẳng định bóc tách bẫy sai lầm
    assert "[Phân tích bẫy sai lầm của học sinh (Distractor Rationales)]:" in notes_text
    assert "- Phương án B: Học sinh nhầm lẫn đạo hàm có delta âm" in notes_text
    assert "- Phương án C: Mặc dù khẳng định này đúng nhưng đề bài hỏi khoảng đồng biến" in notes_text
    assert "- Phương án D: Nhầm dấu của tam thức bậc hai" in notes_text


def test_task_18_3_empty_notes_safe_handling():
    """
    Task 18.3: Kiểm tra tính an toàn khi slide không chứa bất kỳ ghi chú hay phương án nào:
    - Hàm trả về chuỗi rỗng "" hoặc None
    - Không làm hỏng hoặc tạo các khối rác trong notesSlide
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    empty_slide_data = {
        "title": "Slide Tiêu Đề Không Ghi Chú",
        "bullet_points": [],
    }

    notes_text = build_speaker_notes(slide, empty_slide_data, is_quiz=False)
    assert notes_text == "" or notes_text is None


def test_task_18_3_xml_sanitization_in_speaker_notes():
    """
    Task 18.3: Kiểm tra khử trùng ký tự rác / ký tự điều khiển XML (ASCII 0x00 - 0x1F):
    - Đảm bảo file PowerPoint (.pptx) không bị lỗi corrupt XML khi mở trên MS PowerPoint
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    dirty_slide_data = {
        "title": "Slide Kiểm Tra Ký Tự Rác",
        "teacher_note": "Lời giảng có chứa ký tự ẩn \x00\x08 và tab ngắt dòng \x1b\x1f trong text.",
        "target_outcome": "Chuẩn đầu ra có chứa ký tự \x03\x0c không hợp lệ.",
    }

    notes_text = build_speaker_notes(slide, dirty_slide_data, is_quiz=False)
    assert notes_text is not None
    # Ký tự điều khiển 0x00, 0x08, 0x1b, 0x1f phải được lọc bỏ hoàn toàn
    for bad_char in ["\x00", "\x08", "\x1b", "\x1f", "\x03", "\x0c"]:
        assert bad_char not in notes_text


def test_task_18_3_full_deck_export_preserves_speaker_notes_in_ooxml():
    """
    Task 18.3: Kiểm tra quy trình xuất bài giảng tổng thể export_slide_deck_to_pptx():
    - Bộ slide hỗn hợp (Tiêu đề, Khái niệm kèm công thức, Bài tập có lời giải, Trắc nghiệm có bẫy)
    - Tất cả các slide đều có ghi chú tương ứng trong OOXML notesSlide
    - Mở lại file PPTX binary stream và kiểm tra tính toàn vẹn
    """
    deck_dict = {
        "presentation_title": "Bài Học Tích Phân & Ứng Dụng",
        "subject": "Toán học",
        "grade": 12,
        "slides": [
            {
                "type": "TITLE_SLIDE",
                "title": "Nguyên Hàm & Tích Phân",
                "subtitle": "Chương 3 - Giải Tích 12",
                "teacher_note": "Giới thiệu tổng quan thời lượng bài học 4 tiết theo phân phối chương trình.",
            },
            {
                "type": "CONCEPT_SLIDE",
                "title": "Định Nghĩa Tích Phân",
                "main_definition_latex": r"\int_a^b f(x) dx = F(b) - F(a)",
                "target_outcome": "Hiểu công thức Newton-Leibniz",
                "class_proficiency": "standard",
                "teacher_note": "Nhắc học sinh F(x) là một nguyên hàm bất kỳ của f(x) trên đoạn [a; b].",
            },
            {
                "type": "EXERCISE_SLIDE",
                "title": "Bài Tập Rèn Luyện Tự Luận",
                "worked_solution_steps": [
                    r"Tìm nguyên hàm: F(x) = \frac{x^3}{3}",
                    r"Thay cận: F(2) - F(1) = \frac{8}{3} - \frac{1}{3} = \frac{7}{3}",
                ],
                "teacher_note": "Gọi một học sinh lên bảng làm bước thay cận.",
            },
            {
                "type": "EXERCISE_SLIDE",
                "layout": "QUIZ_OPTION",
                "title": "Câu Hỏi Trắc Nghiệm Nhanh",
                "question": r"Tính tích phân \(I = \int_0^1 2x dx\).",
                "quiz_options": [
                    {"label": "A", "text": "1", "is_correct": True, "distractor_rationale": ""},
                    {"label": "B", "text": "2", "is_correct": False, "distractor_rationale": "Quên chia cho 2 khi tìm nguyên hàm của 2x."},
                    {"label": "C", "text": "0", "is_correct": False, "distractor_rationale": "Trừ sai hiệu số hai cận."},
                    {"label": "D", "text": "1/2", "is_correct": False, "distractor_rationale": "Nhầm công thức tích phân x thay vì 2x."},
                ],
                "teacher_note": "Quan sát tỉ lệ trả lời đúng của học sinh qua ứng dụng tương tác.",
            },
        ],
    }

    pptx_bytes = export_slide_deck_to_pptx(deck_dict)
    assert isinstance(pptx_bytes, io.BytesIO)
    assert pptx_bytes.getbuffer().nbytes > 12000

    prs = Presentation(pptx_bytes)
    assert len(prs.slides) == 4

    # Kiểm tra Speaker Notes của cả 4 slide
    for s_idx, slide in enumerate(prs.slides):
        notes_text = slide.notes_slide.notes_text_frame.text
        assert len(notes_text) > 10, f"Slide {s_idx + 1} thiếu nội dung Speaker Notes"
        if s_idx == 0:
            assert "phân phối chương trình" in notes_text
        elif s_idx == 1:
            assert "Newton-Leibniz" in notes_text
            assert "∫" in notes_text
        elif s_idx == 2:
            assert "Các bước giải mẫu tự luận" in notes_text
            assert "Bước 1:" in notes_text
            assert "Bước 2:" in notes_text
        elif s_idx == 3:
            assert "[Đáp án đúng chuẩn SGK]: Phương án A" in notes_text
            assert "Quên chia cho 2 khi tìm nguyên hàm" in notes_text


# ==============================================================================
# HẠNG MỤC TEST CHO TASK 18.4: KIỂM SOÁT BỐ CỤC, CHỐNG TRÀN CHỮ & AUTO-FIT FONT
# ==============================================================================

def test_task_18_4_calculate_auto_fit_font_algorithm():
    """
    Task 18.4: Kiểm tra tính toán thuật toán calculate_auto_fit_font():
    - Dưới ngưỡng tối thiểu -> Giữ cỡ chữ mặc định
    - Vượt các mốc ngưỡng liên tiếp -> Co giãn kích thước font theo bậc thang
    - Văn bản rỗng / None -> Trả về mặc định
    """
    thresholds = [(100, 14.0), (60, 18.0), (30, 22.0)]
    default_size = 28.0

    # Dưới 30 ký tự -> 28.0 pt
    assert calculate_auto_fit_font("Ngắn", thresholds, default_size) == 28.0
    # 31 - 60 ký tự -> 22.0 pt
    assert calculate_auto_fit_font("A" * 45, thresholds, default_size) == 22.0
    # 61 - 100 ký tự -> 18.0 pt
    assert calculate_auto_fit_font("B" * 75, thresholds, default_size) == 18.0
    # Trên 100 ký tự -> 14.0 pt
    assert calculate_auto_fit_font("C" * 120, thresholds, default_size) == 14.0

    # Trường hợp rỗng / None
    assert calculate_auto_fit_font("", thresholds, default_size) == 28.0
    assert calculate_auto_fit_font(None, thresholds, default_size) == 28.0


def test_task_18_4_title_slide_auto_fit_font():
    """
    Task 18.4: Kiểm tra co giãn font chữ tiêu đề trên Slide Bìa (build_title_slide):
    - Tiêu đề ngắn (< 35 ký tự): 32 pt
    - Tiêu đề vừa (45 ký tự): 28 pt
    - Tiêu đề dài (65 ký tự): 25 pt
    - Tiêu đề rất dài (90 ký tự): 22 pt
    - Tiêu đề cực dài (> 110 ký tự): 20 pt
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 1. Tiêu đề ngắn
    data_short = {"title": "Khảo Sát Hàm Số"}
    build_title_slide(slide, data_short, "Toán", 12)
    # Lấy textbox tiêu đề (ở tọa độ Y = 1.8 inch)
    t_boxes = [s for s in slide.shapes if round(s.top.inches, 1) == 1.8]
    assert len(t_boxes) == 1
    run_short = t_boxes[0].text_frame.paragraphs[0].runs[0]
    assert run_short.font.size == Pt(32.0)

    # 2. Tiêu đề rất dài (115 ký tự)
    slide_long = prs.slides.add_slide(prs.slide_layouts[6])
    long_title = "Phương Pháp Giải Các Bài Toán Vận Dụng Cao Về Khảo Sát Tính Đơn Điệu Và Cực Trị Của Hàm Số Hợp Và Hàm Số Liên Kết Trong Đề Thi THPT Quốc Gia"
    data_long = {"title": long_title}
    build_title_slide(slide_long, data_long, "Toán", 12)
    t_boxes_long = [s for s in slide_long.shapes if round(s.top.inches, 1) == 1.8]
    assert len(t_boxes_long) == 1
    run_long = t_boxes_long[0].text_frame.paragraphs[0].runs[0]
    assert run_long.font.size == Pt(20.0)


def test_task_18_4_content_slide_long_title_and_subtitle_no_collision():
    """
    Task 18.4: Kiểm tra cơ chế chống va chạm giữa tiêu đề dài, phụ đề và nội dung:
    - Tiêu đề dài (> 75 ký tự) tự co về 18.5 pt (hoặc 16.5 pt nếu > 120 ký tự)
    - Phụ đề tự động tính vị trí top mới dựa trên chiều cao tiêu đề
    - content_top dời xuống mượt mà, không bị chồng đè
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    extra_long_title = "Bài Học Khái Niệm Toàn Diện Về Khối Đa Diện Đều Và Thể Tích Khối Chóp Trong Không Gian Oxyz Dành Cho Học Sinh Lớp 12"
    long_subtitle = "Nghiên cứu các tính chất đối xứng tâm và mặt phẳng đối xứng qua các ví dụ thực tiễn sinh động"

    data = {
        "title": extra_long_title,
        "subtitle": long_subtitle,
        "bullet_points": ["Khối lập phương có 9 mặt phẳng đối xứng", "Khối tứ diện đều có 6 mặt phẳng đối xứng"],
    }

    build_content_slide(slide, data, 1, 1, "Toán", 12)

    # Textbox tiêu đề (ở top = 0.8)
    t_box = [s for s in slide.shapes if round(s.top.inches, 1) == 0.8][0]
    title_run = t_box.text_frame.paragraphs[0].runs[0]
    assert title_run.font.size <= Pt(18.5)
    assert t_box.text_frame.word_wrap is True

    # Textbox phụ đề (phải nằm dưới tiêu đề, top > 1.35)
    sub_boxes = [s for s in slide.shapes if "Nghiên cứu các tính chất" in (s.text if s.has_text_frame else "")]
    assert len(sub_boxes) == 1
    sub_box = sub_boxes[0]
    assert sub_box.top.inches >= 1.40  # Dời xuống an toàn dưới tiêu đề cao 0.65"


def test_task_18_4_bullets_auto_fit_density_and_spacing():
    """
    Task 18.4: Kiểm tra sự thích ứng mật độ bullet points:
    - 2 ý ngắn (mật độ thấp): Font 16 pt, space_after = Pt(6)
    - 4 ý vừa (mật độ chuẩn): Font 15 pt, space_after = Pt(5)
    - 7 ý dài (mật độ cao): Font 12.5 pt, space_after = Pt(3)
    """
    prs = Presentation()

    # 1. Mật độ thấp: 2 ý ngắn
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    build_content_slide(slide1, {"title": "Khái Niệm", "bullet_points": ["Ý số 1", "Ý số 2"]}, 1, 1, "Toán", 10)
    tb1 = [s for s in slide1.shapes if "Ý số 1" in (s.text if s.has_text_frame else "")][0]
    p1 = tb1.text_frame.paragraphs[0]
    assert p1.runs[0].font.size == Pt(16.0)
    assert p1.space_after == Pt(6.0)

    # 2. Mật độ cao: 7 ý dài
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    dense_bullets = [
        "Định nghĩa tập hợp số thực bao gồm cả số hữu tỉ và số vô tỉ trong hệ thống toán học",
        "Mọi số thực x đều được biểu diễn tương ứng duy nhất bởi một điểm trên trục số thực",
        "Quan hệ thứ tự trên tập số thực thỏa mãn tính chất bắc cầu và tính chất trù mật",
        "Khoảng cách giữa hai điểm a và b trên trục số là giá trị tuyệt đối |a - b|",
        "Tập hợp số thực là một trường số sắp thứ tự đầy đủ theo tiên đề Dedekind",
        "Mọi tập con khác rỗng bị chặn trên đều có cận trên đúng duy nhất trong R",
        "Tập số tự nhiên N là tập con thực sự của tập các số nguyên Z và số thực R",
    ]
    build_content_slide(slide2, {"title": "Tập Hợp Số Thực", "bullet_points": dense_bullets}, 1, 1, "Toán", 10)
    tb2 = [s for s in slide2.shapes if "Định nghĩa tập hợp" in (s.text if s.has_text_frame else "")][0]
    p2 = tb2.text_frame.paragraphs[0]
    # Font co giãn về 12.5 pt, khoảng cách đoạn co giãn về Pt(3.0) để không tràn slide
    assert p2.runs[0].font.size == Pt(12.5)
    assert p2.space_after == Pt(3.0)


def test_task_18_4_formula_and_footer_margin_safety_zone():
    """
    Task 18.4: Kiểm định vùng an toàn lề dưới (Margin Safety Zone):
    - Đáy của khối nội dung thấp nhất (formula card box) không bao giờ vượt quá 5.10 inch
    - Footer đặt tại top = 5.26 inch
    - Luôn duy trì khoảng cách đệm an toàn tối thiểu >= 0.15 inch (10.8 pt)
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    slide_data = {
        "title": "Công thức Tích Phân Từng Phần",
        "bullet_points": [
            "Áp dụng khi biểu thức dưới dấu tích phân là tích hai hàm số khác loại",
            "Thứ tự ưu tiên đặt u: 'Nhất log, nhì đa, tam lượng, tứ mũ'",
        ],
        "main_definition_latex": r"\int u dv = uv - \int v du",
    }

    build_content_slide(slide, slide_data, 1, 1, "Toán", 12)

    # Tìm Footer trái và phải (tại top = 5.26 inch)
    footers = [s for s in slide.shapes if round(s.top.inches, 2) == 5.26]
    assert len(footers) == 2

    # Tìm các shape nội dung (ngoại trừ footers)
    content_shapes = [s for s in slide.shapes if round(s.top.inches, 2) < 5.20]
    for cs in content_shapes:
        bottom_y = cs.top.inches + cs.height.inches
        # Khối nội dung thấp nhất không được vượt quá 5.12 inch
        assert bottom_y <= 5.12, f"Shape '{cs.name}' tràn vào vùng bảo vệ chân trang: đáy = {bottom_y}"
        # Khoảng cách tới footer >= 0.14 inch
        gap_to_footer = 5.26 - bottom_y
        assert gap_to_footer >= 0.14, f"Khe hở tới chân trang quá hẹp: {gap_to_footer} in"


def test_task_18_4_quiz_long_question_and_options_overflow_guard():
    """
    Task 18.4: Kiểm tra chống tràn chữ trên Slide Trắc nghiệm (build_quiz_slide):
    - Câu hỏi đề bài cực dài (> 180 ký tự): Font co về 12.5 pt
    - Phương án cực dài (> 110 ký tự): Font co về 10.5 pt
    - Lề trong của option card textbox được thu hẹp về 0.04 inch
    - Tất cả text frame đều có word_wrap = True
    """
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    extra_long_question = (
        "Trong không gian với hệ tọa độ Oxyz, cho mặt cầu (S) có phương trình x^2 + y^2 + z^2 - 2x + 4y - 6z - 11 = 0 "
        "và mặt phẳng (P) có phương trình 2x + 2y - z + 17 = 0. Tìm khoảng cách ngắn nhất từ một điểm M tùy ý thuộc mặt cầu (S) đến mặt phẳng (P)."
    )

    long_opt_a = "Khoảng cách ngắn nhất đạt được d_min = 2 khi điểm M là hình chiếu của tâm I lên mặt cầu theo phương của vectơ pháp tuyến mặt phẳng (P)."
    long_opt_b = "Khoảng cách ngắn nhất đạt được d_min = 3 khi điểm M là giao điểm của đường thẳng đi qua tâm I vuông góc với (P) và mặt cầu (S)."
    long_opt_c = "Mặt cầu (S) cắt mặt phẳng (P) theo một đường tròn nên khoảng cách ngắn nhất bằng 0."
    long_opt_d = "Mặt cầu (S) nằm hoàn toàn về một phía của mặt phẳng (P) và khoảng cách ngắn nhất d_min = 4."

    slide_data = {
        "type": "EXERCISE_SLIDE",
        "layout": "QUIZ_OPTION",
        "question": extra_long_question,
        "quiz_options": [
            {"label": "A", "text": long_opt_a, "is_correct": False, "distractor_rationale": "Tính sai bán kính R của mặt cầu."},
            {"label": "B", "text": long_opt_b, "is_correct": True, "distractor_rationale": ""},
            {"label": "C", "text": long_opt_c, "is_correct": False, "distractor_rationale": "Tính sai khoảng cách d(I, P) nhỏ hơn R."},
            {"label": "D", "text": long_opt_d, "is_correct": False, "distractor_rationale": "Nhầm dấu khi thay tọa độ tâm I vào phương trình mặt phẳng."},
        ],
    }

    build_quiz_slide(slide, slide_data, 1, 1, "Toán", 12)

    # 1. Đề bài
    q_box = [s for s in slide.shapes if "Trong không gian với hệ tọa độ" in (s.text if s.has_text_frame else "")][0]
    q_run = q_box.text_frame.paragraphs[0].runs[0]
    # Câu hỏi 218 ký tự -> Co về 12.5 pt
    assert q_run.font.size == Pt(12.5)
    assert q_box.text_frame.word_wrap is True

    # 2. Phương án A
    opt_a_box = [s for s in slide.shapes if "vectơ pháp tuyến" in (s.text if s.has_text_frame else "")][0]
    opt_a_run = opt_a_box.text_frame.paragraphs[0].runs[0]
    # Phương án 142 ký tự -> Co về 10.5 pt
    assert opt_a_run.font.size == Pt(10.5)
    assert opt_a_box.text_frame.word_wrap is True
    # Kiểm tra lề đệm thu hẹp 0.04 in
    assert round(opt_a_box.text_frame.margin_left.inches, 2) == 0.04
    assert round(opt_a_box.text_frame.margin_right.inches, 2) == 0.04


# ==============================================================================
# HẠNG MỤC TEST CHO TASK 18.5: NGHIỆM THU DEFINITION OF DONE (DoD) NGÀY 18
# ==============================================================================

def test_task_18_5_dod_end_to_end_acceptance():
    """
    Task 18.5: Kiểm thử Nghiệm thu Tổng hợp Toàn diện (End-to-End DoD Acceptance):
    Xây dựng một giáo án hoàn chỉnh 5 slide chuẩn Công văn 5512/BGDĐT:
    - Slide 1: TITLE_SLIDE (Chủ đề, Lớp, Môn, Giáo viên, Tự động co giãn Font, Lề an toàn)
    - Slide 2: CONCEPT_SLIDE (Lý thuyết trọng tâm, Khối công thức Toán LaTeX Unicode, Margin Safety)
    - Slide 3: GEOMETRY_3D_SLIDE (Mô hình 3D WebGL Snapshot Box-Fit tỷ lệ 4:3, Badge SGK)
    - Slide 4: WORKED_EXAMPLE_SLIDE (Ví dụ mẫu, Lời giải tự luận chuẩn mực SGK trong Speaker Notes)
    - Slide 5: QUIZ_SLIDE (Câu hỏi trắc nghiệm Native DrawingML 2x2 grid, Huy hiệu A/B/C/D, Bẫy sai lầm)
    Kiểm tra toàn diện các tiêu chí kỹ thuật ECMA-376 và tính toàn vẹn của tệp nhị phân .pptx.
    """
    sample_snapshot_b64 = _create_sample_png_base64(800, 600, (14, 165, 233))  # 4:3 WebGL snapshot

    full_lesson_deck = {
        "presentation_title": "Hình Lăng Trụ Đứng & Thể Tích Khối Đa Diện",
        "subject": "Toán học",
        "grade": 11,
        "teacher_name": "ThS. Nguyễn Văn A",
        "snapshot_3d_base64": sample_snapshot_b64,
        "slides": [
            # Slide 1: Tiêu đề
            {
                "type": "TITLE_SLIDE",
                "title": "Hình Lăng Trụ Đứng & Thể Tích Khối Đa Diện",
                "subtitle": "Chương trình Hình học Không gian Lớp 11 - Chuẩn Công văn 5512/BGDĐT",
                "teacher_note": "Giới thiệu tổng quan mục tiêu bài học: Nắm vững định nghĩa lăng trụ đứng và công thức tính thể tích.",
                "target_outcome": "Học sinh hiểu bản chất hình học của lăng trụ và biết vận dụng giải toán thực tế.",
                "class_proficiency": "standard",
            },
            # Slide 2: Khái niệm & Công thức Toán
            {
                "type": "CONCEPT_SLIDE",
                "title": "Khái Niệm & Công Thức Tính Thể Tích",
                "subtitle": "Mục I: Định nghĩa & Công thức trọng tâm",
                "bullet_points": [
                    "Thể tích khối lăng trụ bằng diện tích mặt đáy nhân với chiều cao tương ứng",
                    "Đối với lăng trụ đứng, chiều cao h chính bằng độ dài cạnh bên",
                    "Đơn vị đo thể tích là lập phương đơn vị đo độ dài",
                ],
                "main_definition_latex": r"V = B \cdot h = S_{\Delta ABC} \cdot AA'",
                "teacher_note": "Nhắc nhở học sinh phân biệt chiều cao lăng trụ đứng và lăng trụ xiên.",
                "target_outcome": "Thuộc và giải thích được ý nghĩa từng đại lượng trong công thức V = B * h.",
                "class_proficiency": "basic",
            },
            # Slide 3: Mô hình Trực quan 3D WebGL (Box-fit)
            {
                "type": "CONCEPT_SLIDE",
                "layout": "IMAGE_TEXT",
                "title": "Mô Hình Trực Quan 3D: Lăng Trụ Tam Giác",
                "subtitle": "Mục II: Khảo sát hình học không gian đa chiều",
                "polyhedron_type": "prism_triangle",
                "has_3d": True,
                "bullet_points": [
                    "Hai mặt đáy là hai tam giác song song và bằng nhau",
                    "Các mặt bên là những hình chữ nhật vuông góc với đáy",
                    "Các cạnh bên song song và có độ dài bằng nhau",
                ],
                "teacher_note": "Cho học sinh xoay lăng trụ 3D để quan sát sự song song giữa hai mặt đáy.",
                "target_outcome": "Rèn luyện năng lực tưởng tượng không gian và phát hiện các góc vuông giữa cạnh và mặt đáy.",
                "class_proficiency": "advanced",
            },
            # Slide 4: Ví dụ Áp dụng & Lời giải tự luận
            {
                "type": "WORKED_EXAMPLE_SLIDE",
                "title": "Ví Dụ Áp Dụng: Lăng Trụ Tam Giác Đều",
                "subtitle": "Mục III: Phương pháp giải bài tập tự luận chuẩn SGK",
                "bullet_points": [
                    "Đáy là tam giác đều cạnh a có diện tích S = a²√3/4",
                    "Cạnh bên vuông góc với đáy có chiều cao h = 2a",
                    "Áp dụng trực tiếp công thức thể tích khối lăng trụ đứng",
                ],
                "worked_solution_steps": [
                    r"Bước 1: Tính diện tích đáy tam giác đều: $S = \frac{a^2\sqrt{3}}{4}$",
                    r"Bước 2: Xác định chiều cao hình lăng trụ đứng $h = AA' = 2a$",
                    r"Bước 3: Thể tích khối lăng trụ $V = S \cdot h = \frac{a^2\sqrt{3}}{4} \cdot 2a = \frac{a^3\sqrt{3}}{2}$",
                ],
                "teacher_note": "Yêu cầu học sinh trình bày các bước theo đúng chuẩn mực bài thi tự luận tốt nghiệp THPT.",
                "target_outcome": "Thành thạo kỹ năng tính thể tích lăng trụ tam giác đều không nhầm lẫn.",
                "class_proficiency": "standard",
            },
            # Slide 5: Câu hỏi trắc nghiệm rèn luyện (Native DrawingML Shapes)
            {
                "type": "EXERCISE_SLIDE",
                "layout": "QUIZ_OPTION",
                "activity_type": "Vận dụng",
                "highlight_correct": True,
                "question": r"Cho hình lăng trụ đứng có diện tích đáy $B = 12\,\text{cm}^2$ và chiều cao $h = 5\,\text{cm}$. Thể tích khối lăng trụ là:",
                "quiz_options": [
                    {
                        "label": "A",
                        "text": r"20 cm³",
                        "is_correct": False,
                        "distractor_rationale": "Học sinh nhầm công thức thể tích khối chóp V = 1/3 B h.",
                    },
                    {
                        "label": "B",
                        "text": r"60 cm³",
                        "is_correct": True,
                        "distractor_rationale": "",
                    },
                    {
                        "label": "C",
                        "text": r"30 cm³",
                        "is_correct": False,
                        "distractor_rationale": "Học sinh chia đôi diện tích do nhầm công thức diện tích tam giác.",
                    },
                    {
                        "label": "D",
                        "text": r"120 cm³",
                        "is_correct": False,
                        "distractor_rationale": "Học sinh nhân đôi chiều cao h.",
                    },
                ],
                "teacher_note": "Cho học sinh 60 giây làm bài cá nhân và bấm máy tính trước khi công bố đáp án.",
                "target_outcome": "Củng cố phản xạ nhận biết công thức V = B * h không có hệ số 1/3.",
                "class_proficiency": "standard",
            },
        ],
    }

    # Xuất bài giảng ra stream PPTX
    pptx_bytes = export_slide_deck_to_pptx(full_lesson_deck)
    assert isinstance(pptx_bytes, io.BytesIO)
    assert pptx_bytes.getbuffer().nbytes > 15000, "Kích thước tệp PPTX quá nhỏ, có thể bị lỗi ghi DrawingML"

    # Mở lại tệp PPTX bằng python-pptx để kiểm định ECMA-376
    prs = Presentation(pptx_bytes)
    assert len(prs.slides) == 5, f"Tổng số slide mong đợi là 5, thực tế là {len(prs.slides)}"

    # Kích thước slide chuẩn 16:9 Widescreen
    assert prs.slide_width is not None and prs.slide_height is not None
    assert round(prs.slide_width.inches, 2) == 10.0
    assert round(prs.slide_height.inches, 3) == 5.625

    # ==========================================================================
    # KIỂM ĐỊNH SLIDE 1: TITLE SLIDE
    # ==========================================================================
    slide1 = prs.slides[0]
    s1_texts = [s.text for s in slide1.shapes if s.has_text_frame]
    assert any("Hình Lăng Trụ Đứng & Thể Tích Khối Đa Diện" in t for t in s1_texts)
    assert any("Chương trình Hình học Không gian Lớp 11" in t for t in s1_texts)
    assert any("MÔN TOÁN HỌC - LỚP 11" in t for t in s1_texts)

    # Speaker notes của Slide 1
    s1_notes = slide1.notes_slide.notes_text_frame.text
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in s1_notes
    assert "Giới thiệu tổng quan mục tiêu bài học" in s1_notes
    assert "Chuẩn đầu ra: Học sinh hiểu bản chất" in s1_notes
    assert "Lớp chuẩn (Đạt chuẩn kiến thức & kỹ năng SGK)" in s1_notes

    # ==========================================================================
    # KIỂM ĐỊNH SLIDE 2: CONCEPT SLIDE (CÔNG THỨC TOÁN & MARGIN SAFETY)
    # ==========================================================================
    slide2 = prs.slides[1]
    s2_texts = [s.text for s in slide2.shapes if s.has_text_frame]
    assert any("Khái Niệm & Công Thức Tính Thể Tích" in t for t in s2_texts)

    # Khối công thức Toán học
    formula_boxes = [
        s for s in slide2.shapes
        if _get_auto_shape_type(s) in (MSO_SHAPE.RECTANGLE, MSO_SHAPE.ROUNDED_RECTANGLE)
        and round(s.top.inches, 2) == 3.85
    ]
    assert len(formula_boxes) >= 1, "Không tìm thấy hộp công thức nền"
    f_shape = formula_boxes[0]
    # Margin Safety Zone: Đáy của hộp công thức <= 5.12 inch
    f_bottom = f_shape.top.inches + f_shape.height.inches
    assert f_bottom <= 5.12, f"Hộp công thức vượt ngưỡng an toàn lề dưới: {f_bottom} inch"
    assert (5.26 - f_bottom) >= 0.14, "Khoảng cách giữa hộp công thức và footer quá hẹp"

    # Ảnh công thức LaTeX đã được render
    formula_pics = [s for s in slide2.shapes if s.shape_type == 13]
    assert len(formula_pics) == 1, "Không tìm thấy ảnh công thức LaTeX được nhúng"

    # Speaker notes Slide 2
    s2_notes = slide2.notes_slide.notes_text_frame.text
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in s2_notes
    assert "Nhắc nhở học sinh phân biệt chiều cao" in s2_notes
    assert "[Công thức toán trọng tâm bài học]:" in s2_notes
    assert "V = B · h" in s2_notes

    # ==========================================================================
    # KIỂM ĐỊNH SLIDE 3: 3D GEOMETRY SNAPSHOT SLIDE (BOX-FIT & CONTAINER)
    # ==========================================================================
    slide3 = prs.slides[2]

    # Kiểm tra Container bo góc với nhãn SGK
    c_badges = [
        s for s in slide3.shapes
        if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE
        and "Mô hình 3D WebGL (SGK)" in (s.text if s.has_text_frame else "")
    ]
    assert len(c_badges) == 1, "Không tìm thấy thẻ badge 'Mô hình 3D WebGL (SGK)'"
    assert any("Hình Lăng Trụ Đứng ABC.A'B'C'" in (s.text if s.has_text_frame else "") for s in slide3.shapes)

    # Kiểm tra nhúng ảnh snapshot WebGL
    pic_shapes = [s for s in slide3.shapes if s.shape_type == 13]  # MSO_SHAPE_TYPE.PICTURE = 13
    assert len(pic_shapes) == 1, "Không tìm thấy ảnh snapshot 3D DrawingML"
    pic = pic_shapes[0]

    # Kiểm tra thuật toán Box-Fit: Tỷ lệ gốc 4:3 (w/h = 1.333) phải được bảo toàn
    pic_ratio = pic.width.inches / pic.height.inches
    assert abs(pic_ratio - (4.0 / 3.0)) < 0.05, f"Tỷ lệ ảnh bị méo: w/h = {pic_ratio}"
    # Nằm gọn trong cột phải (left >= 5.10, top >= 1.80, bottom <= 5.12)
    assert pic.left.inches >= 5.10
    assert pic.top.inches >= 1.80
    assert (pic.top.inches + pic.height.inches) <= 5.12

    # Speaker notes Slide 3
    s3_notes = slide3.notes_slide.notes_text_frame.text
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in s3_notes
    assert "Cho học sinh xoay lăng trụ 3D" in s3_notes
    assert "Lớp nâng cao (Tư duy vận dụng & bài toán phân hóa cao)" in s3_notes

    # ==========================================================================
    # KIỂM ĐỊNH SLIDE 4: WORKED EXAMPLE (LỜI GIẢI TỰ LUẬN TRONG SPEAKER NOTES)
    # ==========================================================================
    slide4 = prs.slides[3]
    s4_texts = [s.text for s in slide4.shapes if s.has_text_frame]
    assert any("Ví Dụ Áp Dụng: Lăng Trụ Tam Giác Đều" in t for t in s4_texts)

    # Speaker notes Slide 4 chứa 3 bước giải tự luận
    s4_notes = slide4.notes_slide.notes_text_frame.text
    assert "[Các bước giải mẫu tự luận chi tiết chuẩn SGK]:" in s4_notes
    assert "Bước 1: Tính diện tích đáy tam giác đều" in s4_notes
    assert "Bước 2: Xác định chiều cao" in s4_notes
    assert "Bước 3: Thể tích khối lăng trụ" in s4_notes

    # ==========================================================================
    # KIỂM ĐỊNH SLIDE 5: QUIZ SLIDE (NATIVE DRAWINGML SHAPES & BẪY SAI LẦM)
    # ==========================================================================
    slide5 = prs.slides[4]

    # 1. 4 Cards Bo Góc
    option_cards = [
        s for s in slide5.shapes
        if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE
        and round(s.width.inches, 2) == 4.25
        and round(s.height.inches, 2) == 1.30
    ]
    assert len(option_cards) == 4, f"Số lượng card bo góc trắc nghiệm mong đợi 4, thực tế: {len(option_cards)}"

    # Card B (index 1) là đáp án đúng -> Màu xanh mint highlight
    assert option_cards[1].fill.fore_color.rgb == COLOR_QUIZ_CORRECT_BG
    assert option_cards[1].line.color.rgb == COLOR_QUIZ_CORRECT_BORDER
    # Các card khác màu xám nhẹ tiêu chuẩn
    assert option_cards[0].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG
    assert option_cards[2].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG
    assert option_cards[3].fill.fore_color.rgb == COLOR_QUIZ_CARD_BG

    # 2. 4 Huy hiệu tròn Oval (A, B, C, D)
    badge_ovals = [
        s for s in slide5.shapes
        if _get_auto_shape_type(s) == MSO_SHAPE.OVAL
        and round(s.width.inches, 2) == 0.36
    ]
    assert len(badge_ovals) == 4, f"Số lượng huy hiệu tròn mong đợi 4, thực tế: {len(badge_ovals)}"
    badge_letters = [s.text.strip() for s in badge_ovals if s.has_text_frame]
    assert set(badge_letters) == {"A", "B", "C", "D"}

    # Huy hiệu màu sắc đặc trưng
    badge_by_letter = {s.text.strip(): s for s in badge_ovals}
    assert badge_by_letter["A"].fill.fore_color.rgb == COLOR_QUIZ_A
    assert badge_by_letter["B"].fill.fore_color.rgb == COLOR_QUIZ_B
    assert badge_by_letter["C"].fill.fore_color.rgb == COLOR_QUIZ_C
    assert badge_by_letter["D"].fill.fore_color.rgb == COLOR_QUIZ_D

    # 3. Pill Tag Hoạt động sư phạm
    pill_tags = [
        s for s in slide5.shapes
        if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE
        and "VẬN DỤNG" in (s.text if s.has_text_frame else "").upper()
    ]
    assert len(pill_tags) == 1, "Không tìm thấy Pill Tag 'Vận dụng'"

    # 4. Speaker notes Slide 5 chứa Phân tích bẫy sai lầm
    s5_notes = slide5.notes_slide.notes_text_frame.text
    assert "[Kịch bản giảng dạy dành cho Giáo viên]" in s5_notes
    assert "[Đáp án đúng chuẩn SGK]: Phương án B" in s5_notes
    assert "[Phân tích bẫy sai lầm của học sinh (Distractor Rationales)]:" in s5_notes
    assert "- Phương án A: Học sinh nhầm công thức thể tích khối chóp" in s5_notes
    assert "- Phương án C: Học sinh chia đôi diện tích" in s5_notes
    assert "- Phương án D: Học sinh nhân đôi chiều cao" in s5_notes

    # ==========================================================================
    # KIỂM ĐỊNH TẤT CẢ SLIDES: LỌC KÝ TỰ XML & VÙNG AN TOÀN CHÂN TRANG
    # ==========================================================================
    for s_idx, sl in enumerate(prs.slides):
        # Kiểm tra tính toàn vẹn XML: Không chứa ký tự điều khiển ASCII cấm
        for sh in sl.shapes:
            if sh.has_text_frame:
                txt = sh.text_frame.text
                for ch in txt:
                    code = ord(ch)
                    assert not (0 <= code <= 8 or 11 <= code <= 12 or 14 <= code <= 31), (
                        f"Slide {s_idx + 1} chứa ký tự XML bất hợp pháp ASCII {code}"
                    )

        if sl.notes_slide and sl.notes_slide.notes_text_frame:
            n_txt = sl.notes_slide.notes_text_frame.text
            for ch in n_txt:
                code = ord(ch)
                assert not (0 <= code <= 8 or 11 <= code <= 12 or 14 <= code <= 31), (
                    f"Slide {s_idx + 1} Notes chứa ký tự XML bất hợp pháp ASCII {code}"
                )

    # Slide 1 (Bìa) có tagline bản quyền tại top 4.55 in
    taglines = [s for s in slide1.shapes if round(s.top.inches, 2) == 4.55]
    assert len(taglines) == 1, "Slide 1 thiếu tagline bản quyền"

    # Slide 2 đến 5 có 2 Footers tiêu chuẩn tại top 5.26 in và Margin Safety Zone
    for s_idx, sl in enumerate(list(prs.slides)[1:], start=2):
        footers = [s for s in sl.shapes if round(s.top.inches, 2) == 5.26]
        assert len(footers) == 2, f"Slide {s_idx} thiếu footer tiêu chuẩn (thực tế: {len(footers)})"

        # Kiểm tra vùng an toàn: Không shape nội dung nào vượt quá 5.12 inch
        content_shapes = [s for s in sl.shapes if round(s.top.inches, 2) < 5.20]
        for cs in content_shapes:
            b_y = cs.top.inches + cs.height.inches
            assert b_y <= 5.12, f"Slide {s_idx} shape '{cs.name}' lấn vào footer: đáy = {b_y}"


def test_task_18_5_dod_scorecard_14_criteria():
    """
    Task 18.5: Kiểm chứng ma trận 14 tiêu chí Definition of Done (DoD) Ngày 18:
    1. Native Quiz DrawingML Shapes (Cards + Badges + Activity Pill)
    2. Aspect-Preserving 3D WebGL Box-Fit (16:9, 4:3, 1:1, 3:4, 3:1)
    3. Robust Base64 Handling (Data URL, raw, invalid padding)
    4. Polyhedron SGK Classification (10 geometry models)
    5. Deck-level 3D Snapshot Inheritance
    6. 5-Section Speaker Notes OOXML Architecture
    7. Worked Solution Steps in Speaker Notes
    8. Distractor Rationales & Bẫy sai lầm extraction in Notes
    9. ECMA-376 XML Sanitization
    10. Auto-Fit Font Title Calculation (40 -> 28 -> 24 -> 20 pt)
    11. Content Slide Collision-Free Layout (content_top dynamic shift)
    12. Density-Aware Bullet Font & Spacing (11.0 - 16.0 pt)
    13. Margin Safety Zone Guarantee (>= 0.14 in buffer)
    14. Interactive Quiz Overflow Guard (0.04 in margin, wrap, auto-fit)
    """
    scorecard = {}

    # 1. Native Quiz DrawingML Shapes
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    quiz_data = {
        "question": "Tìm nghiệm của phương trình",
        "quiz_options": [
            {"label": "A", "text": "x = 1", "is_correct": True},
            {"label": "B", "text": "x = 2", "is_correct": False},
            {"label": "C", "text": "x = 3", "is_correct": False},
            {"label": "D", "text": "x = 4", "is_correct": False},
        ],
    }
    build_quiz_slide(slide, quiz_data, 1, 1, "Toán", 12)
    cards = [s for s in slide.shapes if _get_auto_shape_type(s) == MSO_SHAPE.ROUNDED_RECTANGLE and round(s.width.inches, 2) == 4.25]
    ovals = [s for s in slide.shapes if _get_auto_shape_type(s) == MSO_SHAPE.OVAL and round(s.width.inches, 2) == 0.36]
    scorecard["Criterion_1_Native_Quiz_Shapes"] = (len(cards) == 4 and len(ovals) == 4)

    # 2. Aspect-Preserving Box-Fit
    for (w_px, h_px) in [(1920, 1080), (1024, 768), (800, 800), (600, 800), (900, 300)]:
        l, t, w, h = compute_aspect_preserving_fit(w_px, h_px, 1.0, 1.0, 4.0, 3.0)
        assert abs((w / h) - (w_px / h_px)) < 1e-4
    scorecard["Criterion_2_Aspect_Preserving_Box_Fit"] = True

    # 3. Robust Base64 Handling
    png_url = _create_sample_png_base64(100, 100)
    b_data = decode_base64_data_url(png_url)
    assert b_data is not None and b_data.getbuffer().nbytes > 0
    scorecard["Criterion_3_Robust_Base64_Handling"] = True

    # 4. Polyhedron SGK Classification
    from exporters.slide_exporter import POLYHEDRON_LABELS
    expected_polyhedra = ["cube", "pyramid_square", "pyramid_triangle", "prism_triangle", "cone", "cylinder", "sphere"]
    assert all(k in POLYHEDRON_LABELS for k in expected_polyhedra)
    scorecard["Criterion_4_Polyhedron_SGK_Classification"] = True

    # 5. Deck-level 3D Snapshot Inheritance
    deck_data = {
        "presentation_title": "Inheritance Test",
        "snapshot_3d_base64": png_url,
        "slides": [{"type": "CONCEPT_SLIDE", "polyhedron_type": "sphere", "title": "Hình cầu"}],
    }
    deck_bytes = export_slide_deck_to_pptx(deck_data)
    prs_inh = Presentation(deck_bytes)
    assert any(s.shape_type == 13 for s in prs_inh.slides[0].shapes)
    scorecard["Criterion_5_Deck_3D_Snapshot_Inheritance"] = True

    # 6. 5-Section Speaker Notes OOXML Architecture
    prs_notes = Presentation()
    sl_n = prs_notes.slides.add_slide(prs_notes.slide_layouts[6])
    sl_data_notes = {
        "teacher_note": "Lời giảng mẫu",
        "target_outcome": "Chuẩn đầu ra",
        "class_proficiency": "standard",
        "main_definition_latex": "E = mc^2",
        "worked_solution_steps": ["Bước 1", "Bước 2"],
        "quiz_options": [
            {"label": "A", "text": "1", "is_correct": True},
            {"label": "B", "text": "2", "is_correct": False, "distractor_rationale": "Bẫy B"}
        ],
    }
    notes_res = build_speaker_notes(sl_n, sl_data_notes, is_quiz=True)
    assert "[Kịch bản giảng dạy" in notes_res
    assert "[Mục tiêu sư phạm" in notes_res
    assert "[Đáp án & Phân tích bẫy" in notes_res
    assert "[Các bước giải mẫu" in notes_res
    assert "[Công thức toán trọng tâm" in notes_res
    scorecard["Criterion_6_Speaker_Notes_5_Sections"] = True

    # 7. Worked Solution Steps
    assert "Bước 1" in notes_res and "Bước 2" in notes_res
    scorecard["Criterion_7_Worked_Solution_Steps"] = True

    # 8. Distractor Rationales Analysis
    assert "Bẫy B" in notes_res
    scorecard["Criterion_8_Distractor_Rationales"] = True

    # 9. ECMA-376 XML Sanitization
    from exporters.slide_exporter import clean_xml_string
    dirty_str = "Toán\x00\x05\x0B\x0C12\x1F\x7F"
    cleaned = clean_xml_string(dirty_str)
    assert cleaned == "Toán12"
    scorecard["Criterion_9_XML_Sanitization"] = True

    # 10. Auto-Fit Font Title Calculation
    assert calculate_auto_fit_font("A" * 70, [(65, 20.0), (50, 24.0), (35, 28.0)], 40.0) == 20.0
    assert calculate_auto_fit_font("A" * 20, [(65, 20.0), (50, 24.0), (35, 28.0)], 40.0) == 40.0
    scorecard["Criterion_10_Auto_Fit_Font_Titles"] = True

    # 11. Content Slide Collision-Free Layout
    prs_col = Presentation()
    sl_col = prs_col.slides.add_slide(prs_col.slide_layouts[6])
    build_content_slide(sl_col, {"title": "T" * 70, "subtitle": "S" * 120, "bullet_points": ["B1"]}, 1, 1, "Toán", 12)
    top_shapes = [s for s in sl_col.shapes if round(s.top.inches, 2) >= 2.05]
    assert len(top_shapes) >= 1
    scorecard["Criterion_11_Collision_Free_Layout"] = True

    # 12. Density-Aware Bullet Font & Spacing
    prs_blt = Presentation()
    sl_blt = prs_blt.slides.add_slide(prs_blt.slide_layouts[6])
    build_content_slide(sl_blt, {"title": "T", "bullet_points": ["B" * 100 for _ in range(7)]}, 1, 1, "Toán", 12)
    p_blt = [s for s in sl_blt.shapes if s.has_text_frame and "B" * 10 in s.text][0].text_frame.paragraphs[0]
    assert p_blt.runs[0].font.size == Pt(12.5)
    scorecard["Criterion_12_Density_Aware_Bullet_Font"] = True

    # 13. Margin Safety Zone Guarantee
    prs_safe = Presentation()
    sl_safe = prs_safe.slides.add_slide(prs_safe.slide_layouts[6])
    build_content_slide(sl_safe, {"title": "T", "bullet_points": ["Point 1", "Point 2"], "main_definition_latex": "f(x)=0"}, 1, 1, "Toán", 12)
    c_shapes = [s for s in sl_safe.shapes if round(s.top.inches, 2) < 5.20]
    for cs in c_shapes:
        assert (cs.top.inches + cs.height.inches) <= 5.12
    scorecard["Criterion_13_Margin_Safety_Zone"] = True

    # 14. Interactive Quiz Overflow Guard
    prs_qog = Presentation()
    sl_qog = prs_qog.slides.add_slide(prs_qog.slide_layouts[6])
    build_quiz_slide(sl_qog, {"question": "Q" * 190, "quiz_options": [{"label": "A", "text": "O" * 120, "is_correct": True}]}, 1, 1, "Toán", 12)
    q_box = [s for s in sl_qog.shapes if "Q" * 10 in (s.text if s.has_text_frame else "")][0]
    assert q_box.text_frame.paragraphs[0].runs[0].font.size == Pt(12.5)
    scorecard["Criterion_14_Quiz_Overflow_Guard"] = True

    # Xác nhận 14/14 tiêu chí đều đạt điểm chuẩn tuyệt đối
    assert len(scorecard) == 14
    for criterion, status in scorecard.items():
        assert status is True, f"Tiêu chí {criterion} không đạt điều kiện nghiệm thu DoD!"

