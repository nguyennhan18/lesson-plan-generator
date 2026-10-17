r"""
Automated Acceptance Test Suite — Day 8 (Nhúng Trình gõ Toán Trực quan MathLive)
Kiểm tra toàn diện 5 hạng mục của Ngày 8 theo Ke_Hoach_Phat_Trien.pdf:
- Task 8.1: Tích hợp thư viện mathlive CDN (mathlive-static.css & mathlive.min.js) vào index.html
- Task 8.2: Xây dựng Modal Popup chỉnh sửa công thức (MathLiveModal.jsx) & sự kiện onDoubleClick trên Slide
- Task 8.3: Cấu hình bàn phím ảo toán học tiếng Việt (phân số, tích phân, căn bậc 2, vectơ, giới hạn...)
- Task 8.4: Lắng nghe sự kiện input trên <math-field> để hiển thị bản xem trước (Preview) bằng KaTeX theo thời gian thực
- Task 8.5 (DoD): Nghiệm thu tích hợp <math-field>, chuẩn hóa placeholder \square cho nút Căn bậc 2 (\sqrt{#@}) không lỗi KaTeX
"""

import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
MATHLIVE_MODAL = FRONTEND_DIR / "src" / "components" / "MathLiveModal.jsx"
PRESENTATION_STAGE = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
SLIDE_EDITOR = FRONTEND_DIR / "src" / "components" / "SlideEditorScreen.jsx"
APP_JSX = FRONTEND_DIR / "src" / "App.jsx"


def test_task_8_1_mathlive_cdn_in_index_html():
    """Task 8.1: Kiểm tra index.html đã nhúng đủ CSS và JS của MathLive CDN."""
    assert INDEX_HTML.exists(), "Không tìm thấy file app/frontend/index.html"
    content = INDEX_HTML.read_text(encoding="utf-8")

    assert "mathlive-static.css" in content, "Thiếu stylesheet mathlive-static.css trong index.html"
    assert "mathlive.min.js" in content, "Thiếu script mathlive.min.js trong index.html"
    assert ("cdn.jsdelivr.net/npm/mathlive" in content or "unpkg.com/mathlive" in content), (
        "Thiếu đường dẫn CDN mathlive trong index.html"
    )


def test_task_8_2_double_click_modal_popup():
    """Task 8.2: Kiểm tra MathLiveModal.jsx và sự kiện onDoubleClick trên PresentationStage & SlideEditorScreen."""
    assert MATHLIVE_MODAL.exists(), "Không tìm thấy component MathLiveModal.jsx"
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")

    # Kiểm tra Web Component <math-field>
    assert "<math-field" in modal_code, "MathLiveModal.jsx phải sử dụng Web Component <math-field>"
    assert "unwrapLatexDelimiters" in modal_code
    assert "wrapLatexDelimiters" in modal_code

    # Kiểm tra onDoubleClick trên Sân khấu trình chiếu (PresentationStage.jsx)
    stage_code = PRESENTATION_STAGE.read_text(encoding="utf-8")
    assert "import MathLiveModal" in stage_code
    assert "onDoubleClick" in stage_code, "PresentationStage.jsx phải bắt sự kiện onDoubleClick trên công thức"
    assert "<MathLiveModal" in stage_code

    # Kiểm tra onDoubleClick trên Xưởng biên tập Slide (SlideEditorScreen.jsx)
    editor_code = SLIDE_EDITOR.read_text(encoding="utf-8")
    assert "import MathLiveModal" in editor_code
    assert "onDoubleClick" in editor_code
    assert "<MathLiveModal" in editor_code

    # Kiểm tra App.jsx đã chặn xung đột phím tắt toàn cục khi gõ trong MATH-FIELD
    app_code = APP_JSX.read_text(encoding="utf-8")
    assert "'MATH-FIELD'" in app_code, "App.jsx cần loại trừ MATH-FIELD khỏi phím tắt chuyển slide toàn cục"


def test_task_8_3_vietnamese_math_virtual_keyboard():
    """Task 8.3: Kiểm tra cấu hình bàn phím ảo toán học tiếng Việt (phân số, tích phân, căn, vectơ, giới hạn...)."""
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")

    assert "VIETNAMESE_MATH_KEYBOARD_TABS" in modal_code
    assert "configureVietnameseNativeVirtualKeyboard" in modal_code
    assert "window.mathVirtualKeyboard.layouts" in modal_code

    # Kiểm tra đầy đủ các nút toán học bắt buộc trong lộ trình Ngày 8 (chuỗi JS escape \\)
    required_buttons = [
        ("Phân số", r"\\frac{#@}{#?}"),
        ("Căn bậc 2", r"\\sqrt{#@}"),
        ("Căn bậc n", r"\\sqrt[#?]{#@}"),
        ("Giới hạn", r"\\lim_{x \\to #@}"),
        ("Tích phân", r"\\int_{#@}^{#?}"),
        ("Vectơ đơn", r"\\vec{#@}"),
        ("Vectơ 2 điểm", r"\\overrightarrow{#@}"),
        ("Hệ 2 PT", r"\\begin{cases}"),
    ]
    for name, latex_pattern in required_buttons:
        assert latex_pattern in modal_code, f"Thiếu cấu hình nút '{name}' ({latex_pattern}) trên bàn phím ảo Tiếng Việt"


def test_task_8_4_realtime_katex_preview_on_input_event():
    """Task 8.4: Kiểm tra lắng nghe sự kiện input trên <math-field> và render Preview bằng KaTeX thời gian thực."""
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")

    # Kiểm tra lắng nghe sự kiện DOM 'input' và lấy giá trị 'latex-expanded'
    assert "addEventListener('input'" in modal_code, "Phải lắng nghe sự kiện DOM 'input' trên <math-field>"
    assert "getValue('latex-expanded')" in modal_code, "Phải trích xuất chuỗi LaTeX bằng getValue('latex-expanded')"

    # Kiểm tra hiển thị bản xem trước bằng KaTeX (MathText & katex.renderToString)
    assert "katex.renderToString" in modal_code, "Phải kiểm tra cú pháp tức thì bằng katex.renderToString"
    assert "<MathText" in modal_code, "Phải hiển thị khung KaTeX Real-time Preview bằng <MathText />"


def test_task_8_5_dod_sqrt_button_and_placeholder_sanitization():
    """
    Task 8.5 (DoD Ngày 8):
    Click đúp vào công thức trên slide -> Hiện popup có bàn phím toán học ->
    Bấm nút căn bậc 2 ra hình cái căn luôn không lỗi.
    """
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")

    # Khi bấm nút căn bậc 2 (\sqrt{#@}), MathLive chèn lệnh executeCommand(['insert', ...])
    assert "executeCommand(['insert'" in modal_code
    # Đồng thời chuẩn hóa \placeholder{} của MathLive sang \square để KaTeX render hình cái căn mượt mà không lỗi
    assert r"replace(/\\placeholder\{[^}]*\}/g, '\\square')" in modal_code


class TestDay8MathLive(unittest.TestCase):
    def test_8_1_cdn(self):
        test_task_8_1_mathlive_cdn_in_index_html()

    def test_8_2_modal_popup(self):
        test_task_8_2_double_click_modal_popup()

    def test_8_3_vietnamese_keyboard(self):
        test_task_8_3_vietnamese_math_virtual_keyboard()

    def test_8_4_realtime_katex_preview(self):
        test_task_8_4_realtime_katex_preview_on_input_event()

    def test_8_5_dod_sqrt_rendering(self):
        test_task_8_5_dod_sqrt_button_and_placeholder_sanitization()


if __name__ == "__main__":
    unittest.main()
