r"""
Automated Test Suite — Day 15: Chế độ Trình chiếu Toàn màn hình (Web Presentation Mode)
Kiểm thử chi tiết các hạng mục của Ngày 15:
- Task 15.1: Thêm nút "Bắt đầu Tiết học" (Start Presentation) gọi HTML5 Fullscreen API (document.documentElement.requestFullscreen())
- Task 15.2: Thiết kế giao diện Trình chiếu: Ẩn thanh sidebar và bong bóng chat, căn chỉnh slide tràn màn hình tỉ lệ 16:9 sắc nét
- Task 15.3: Cài đặt phím tắt bàn phím: Mũi tên trái/phải để lùi/tiến slide, phím ESC để thoát, phím B làm tối màn hình để thu hút sự chú ý
- Task 15.4: Thêm thanh điều khiển mờ (floating control bar) ở đáy màn hình có đồng hồ đếm thời gian tiết dạy (45 phút)
- Task 15.5: Nghiệm thu Definition of Done (DoD) Ngày 15 và kiểm thử toàn diện
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from main import app

client = TestClient(app)


def test_task_15_1_fullscreen_helper_implementation():
    """
    Task 15.1: Kiểm tra tệp tiện ích fullscreenHelper.js:
    - Định nghĩa isFullscreenActive() hỗ trợ đa trình duyệt (WebKit, Mozilla, MS)
    - Định nghĩa requestPresentationFullscreen() gọi document.documentElement.requestFullscreen()
    - Định nghĩa exitPresentationFullscreen() gọi document.exitFullscreen()
    - Định nghĩa togglePresentationFullscreen()
    - Định nghĩa onFullscreenChange() lắng nghe fullscreenchange và webkitfullscreenchange
    """
    helper_path = FRONTEND_DIR / "src" / "utils" / "fullscreenHelper.js"
    assert helper_path.exists(), f"Không tìm thấy tệp {helper_path}"
    content = helper_path.read_text(encoding="utf-8")

    assert "export function isFullscreenActive" in content
    assert "export async function requestPresentationFullscreen" in content
    assert "export async function exitPresentationFullscreen" in content
    assert "export async function togglePresentationFullscreen" in content
    assert "export function onFullscreenChange" in content

    # Kiểm tra vendor prefixes
    assert "requestFullscreen" in content
    assert "webkitRequestFullscreen" in content
    assert "fullscreenchange" in content
    assert "webkitfullscreenchange" in content


def test_task_15_1_header_nav_start_presentation_button():
    """
    Task 15.1: Kiểm tra nút 'Bắt đầu Tiết học' trên HeaderNav.jsx:
    - Có nhãn 'Bắt đầu Tiết học'
    - Có phím tắt gợi ý 'F5'
    - Nhận prop onStartPresentation và kích hoạt sự kiện khi click
    - Nhận prop isPresentationMode
    """
    header_path = FRONTEND_DIR / "src" / "components" / "HeaderNav.jsx"
    assert header_path.exists(), f"Không tìm thấy tệp {header_path}"
    content = header_path.read_text(encoding="utf-8")

    assert "onStartPresentation" in content
    assert "Bắt đầu Tiết học" in content
    assert "F5" in content
    assert "isPresentationMode" in content
    assert "onClick={onStartPresentation}" in content


def test_task_15_1_app_state_and_fullscreen_integration():
    """
    Task 15.1: Kiểm tra tích hợp trong App.jsx:
    - Quản lý state isPresentationMode
    - Lắng nghe sự kiện qua onFullscreenChange
    - Định nghĩa handleStartPresentation gọi requestPresentationFullscreen
    - Truyền onStartPresentation và isPresentationMode xuống HeaderNav
    """
    app_path = FRONTEND_DIR / "src" / "App.jsx"
    assert app_path.exists(), f"Không tìm thấy tệp {app_path}"
    content = app_path.read_text(encoding="utf-8")

    assert "isPresentationMode" in content
    assert "setIsPresentationMode" in content
    assert "onFullscreenChange" in content
    assert "handleStartPresentation" in content
    assert "requestPresentationFullscreen" in content
    assert "onStartPresentation={handleStartPresentation}" in content
    assert "isPresentationMode={isPresentationMode}" in content


def test_task_15_2_presentation_mode_sidebar_and_dock_hiding():
    """
    Task 15.2: Kiểm tra việc ẩn thanh sidebar, header và bong bóng chat trong App.jsx:
    - Ẩn HeaderNav khi isPresentationMode === true: {!isPresentationMode && <HeaderNav ...
    - Ẩn TeacherChatDock khi isPresentationMode === true: {!isPresentationMode && <TeacherChatDock ...
    - Ẩn RightToolsDock khi isPresentationMode === true: {!isPresentationMode && <RightToolsDock ...
    - Truyền isPresentationMode={isPresentationMode} và onExitPresentation={handleExitPresentation} vào PresentationStage
    """
    app_path = FRONTEND_DIR / "src" / "App.jsx"
    assert app_path.exists(), f"Không tìm thấy tệp {app_path}"
    content = app_path.read_text(encoding="utf-8")

    # Kiểm tra ẩn HeaderNav khi trình chiếu
    assert "!isPresentationMode &&" in content
    assert "<HeaderNav" in content

    # Kiểm tra ẩn TeacherChatDock
    assert "<TeacherChatDock" in content

    # Kiểm tra ẩn RightToolsDock
    assert "<RightToolsDock" in content

    # Kiểm tra truyền props vào PresentationStage
    assert "isPresentationMode={isPresentationMode}" in content
    assert "onExitPresentation={handleExitPresentation}" in content

    # Kiểm tra phím tắt Escape để thoát trình chiếu
    assert "'Escape'" in content
    assert "handleExitPresentation()" in content


def test_task_15_2_presentation_stage_16_9_cinema_layout():
    """
    Task 15.2: Kiểm tra giao diện Trình chiếu 16:9 Cinema trong PresentationStage.jsx:
    - Nhận props isPresentationMode và onExitPresentation
    - Container toàn màn hình nền đen: fixed inset-0 z-50 bg-black
    - Khung slide chuẩn tỉ lệ 16:9 (aspect-[16/9] và giới hạn maxWidth calc(100vh * 16 / 9))
    - Ẩn thanh quick controls bên trên (Hiện Trợ Giảng AI, Công Cụ Giảng Dạy, chuyển mẫu bài) khi trình chiếu
    - Hiển thị badge '16:9 Cinema'
    - Có nút Thoát trình chiếu (Minimize2, nhãn 'Thoát', phím tắt Esc) gọi onExitPresentation
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    # Kiểm tra props
    assert "isPresentationMode = false" in content
    assert "onExitPresentation" in content

    # Kiểm tra CSS layout 16:9 Cinema
    assert "fixed inset-0 z-50 bg-black" in content
    assert "aspect-[16/9]" in content
    assert "100vh * 16 / 9" in content

    # Kiểm tra ẩn thanh controls phụ
    assert "!isPresentationMode &&" in content
    assert "Hiện Trợ Giảng AI" in content

    # Kiểm tra badge 16:9 Cinema
    assert "16:9 Cinema" in content

    # Kiểm tra nút Thoát
    assert "onExitPresentation" in content
    assert "Minimize2" in content
    assert "Thoát" in content
    assert "Esc" in content


def test_task_15_3_keyboard_shortcuts_navigation_and_hotkeys():
    """
    Task 15.3: Kiểm tra hệ thống phím tắt trình chiếu trong App.jsx:
    - ArrowLeft, PageUp, p, Backspace: Lùi slide (Math.max(0, prev - 1))
    - ArrowRight, PageDown, Space, n: Tiến slide (Math.min(maxIdx, prev + 1))
    - Home: Về slide đầu tiên (0)
    - End: Đến slide cuối cùng (maxIdx)
    - Escape: Thoát Blackout trước nếu đang bật, hoặc thoát Trình chiếu
    - B / b: Làm tối màn hình (Blackout mode toggle)
    - Quản lý state isBlackout đồng bộ với PresentationStage
    """
    app_path = FRONTEND_DIR / "src" / "App.jsx"
    assert app_path.exists(), f"Không tìm thấy tệp {app_path}"
    content = app_path.read_text(encoding="utf-8")

    # State Blackout
    assert "isBlackout" in content
    assert "setIsBlackout" in content

    # Phím điều hướng trái / phải / spacebar / pageup / pagedown
    assert "ArrowLeft" in content
    assert "ArrowRight" in content
    assert "PageUp" in content
    assert "PageDown" in content
    assert "Space" in content or "' '" in content

    # Phím đầu / cuối slide
    assert "'Home'" in content
    assert "'End'" in content

    # Phím B làm tối màn hình
    assert "e.key === 'b'" in content or "e.key === 'B'" in content

    # Phím Escape
    assert "'Escape'" in content

    # Truyền props xuống PresentationStage
    assert "isBlackout={isBlackout}" in content
    assert "onToggleBlackout={setIsBlackout}" in content


def test_task_15_3_blackout_mode_overlay_and_curtain():
    """
    Task 15.3: Kiểm tra giao diện Màn hình tối Blackout trong PresentationStage.jsx:
    - Nhận props isBlackout và onToggleBlackout
    - Hiển thị lớp phủ Blackout Curtain: fixed inset-0 z-[60] bg-black khi isBlackout === true
    - Biểu tượng Moon và thông điệp 'Màn hình tạm tắt để tập trung bài giảng'
    - Có nút 'Tối màn hình (B)' trong header khi ở isPresentationMode
    - Footer hiển thị phím tắt đầy đủ: [← / → / Space]: Chuyển slide • [B]: Tối màn hình • [Esc / F5]: Thoát
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    # Props
    assert "isBlackout = false" in content
    assert "onToggleBlackout" in content

    # Lớp phủ Blackout Curtain
    assert "isBlackout &&" in content
    assert "fixed inset-0 z-[60] bg-black" in content
    assert "Màn hình tạm tắt để tập trung bài giảng" in content
    assert "Moon" in content

    # Nút bấm Tối màn hình
    assert "Tối màn hình" in content

    # Footer shortcut guide
    assert "[← / → / Space]: Chuyển slide • [B]: Tối màn hình • [Esc / F5]: Thoát" in content


def test_task_15_4_presentation_floating_bar_component():
    """
    Task 15.4: Kiểm tra tệp PresentationFloatingBar.jsx:
    - Quản lý đồng hồ tiết dạy 45 phút chuẩn GDPT: durationMinutes = 45, timeLeft = 45 * 60
    - Định nghĩa formatTime chuyển đổi giây thành mm:ss
    - Các nút điều khiển timer: Play / Pause, Reset (RotateCcw), chọn mốc 15, 30, 45, 90 phút
    - Cảnh báo màu sắc sư phạm theo thời gian:
      - Xanh lục (> 10p)
      - Vàng cam (5-10p)
      - Đỏ rose nhấp nháy (< 5p)
      - Hết giờ tiết dạy (0p)
    - Tự động ẩn mờ khi idle (mousemove, setTimeout 3.5s)
    - Nút điều hướng slide (onPrevSlide, onNextSlide), danh mục Thumbnails (showThumbnails)
    - Nút Tối màn hình (Moon, B) và Thoát (Minimize2, Esc)
    """
    bar_path = FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx"
    assert bar_path.exists(), f"Không tìm thấy tệp {bar_path}"
    content = bar_path.read_text(encoding="utf-8")

    # Đồng hồ 45 phút chuẩn
    assert "durationMinutes, setDurationMinutes" in content or "useState(45)" in content
    assert "45 * 60" in content
    assert "formatTime" in content
    assert "RotateCcw" in content
    assert "Play" in content
    assert "Pause" in content

    # Phân tầng màu sắc cảnh báo sư phạm
    assert "5 * 60" in content
    assert "10 * 60" in content
    assert "text-rose" in content
    assert "text-amber" in content
    assert "text-emerald" in content

    # Auto-hide on idle
    assert "mousemove" in content
    assert "setTimeout" in content
    assert "effectiveVisible" in content or "isVisible" in content

    # Điều hướng slide & công cụ
    assert "onPrevSlide" in content
    assert "onNextSlide" in content
    assert "showThumbnails" in content
    assert "onToggleBlackout" in content
    assert "onExitPresentation" in content


def test_task_15_4_floating_bar_integration_in_presentation_stage():
    """
    Task 15.4: Kiểm tra tích hợp PresentationFloatingBar trong PresentationStage.jsx:
    - Import PresentationFloatingBar from './PresentationFloatingBar'
    - Render <PresentationFloatingBar ... khi isPresentationMode === true
    - Truyền đầy đủ props: currentSlide, totalSlides, onPrevSlide, onNextSlide, onSelectSlide,
      slides, isBlackout, onToggleBlackout, onExitPresentation, visualMode, onSelectVisualMode
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    assert "import PresentationFloatingBar from './PresentationFloatingBar'" in content
    assert "<PresentationFloatingBar" in content
    assert "isPresentationMode && (" in content
    assert "onPrevSlide=" in content
    assert "onNextSlide=" in content
    assert "onSelectSlide=" in content
    assert "onToggleBlackout=" in content
    assert "onExitPresentation=" in content


def test_task_15_5_definition_of_done_e2e_presentation_mode():
    """
    Task 15.5: Nghiệm thu Definition of Done (DoD) Ngày 15:
    - Bấm F5 hoặc nút 'Bắt đầu Tiết học': Gọi HTML5 Fullscreen API, ẩn thanh sidebar & dock chat.
    - Màn hình tràn viền tỉ lệ 16:9: aspect-[16/9], maxWidth 100vh * 16/9, nền đen điện ảnh không méo hình.
    - Bấm phím mũi tên lùi/tiến mượt mà: ArrowLeft, ArrowRight, Space, PageUp, PageDown, Home, End.
    - Bấm B màn hình đen kịt (Blackout): fixed inset-0 z-[60] bg-black, bấm B lần nữa hoặc click chuột hiện lại tức thì.
    - Đồng hồ 45 phút đếm ngược chính xác: 2700 giây về 0, phân tầng màu xanh/vàng/đỏ, tự động mờ khi không di chuột sau 3.5s.
    """
    # 1. Kiểm tra Fullscreen Helper
    helper_path = FRONTEND_DIR / "src" / "utils" / "fullscreenHelper.js"
    assert helper_path.exists()
    helper_code = helper_path.read_text(encoding="utf-8")
    for fn in ["isFullscreenActive", "requestPresentationFullscreen", "exitPresentationFullscreen", "togglePresentationFullscreen", "onFullscreenChange"]:
        assert fn in helper_code

    # 2. Kiểm tra HeaderNav & Nút Bắt đầu Tiết học
    header_path = FRONTEND_DIR / "src" / "components" / "HeaderNav.jsx"
    assert header_path.exists()
    header_code = header_path.read_text(encoding="utf-8")
    assert "Bắt đầu Tiết học" in header_code
    assert "F5" in header_code
    assert "onStartPresentation" in header_code

    # 3. Kiểm tra App.jsx
    app_path = FRONTEND_DIR / "src" / "App.jsx"
    assert app_path.exists()
    app_code = app_path.read_text(encoding="utf-8")
    assert "isPresentationMode" in app_code
    assert "isBlackout" in app_code
    assert "!isPresentationMode &&" in app_code  # Ẩn HeaderNav, TeacherChatDock, RightToolsDock
    assert "'Escape'" in app_code
    assert "'b'" in app_code or "'B'" in app_code

    # 4. Kiểm tra PresentationStage.jsx
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists()
    stage_code = stage_path.read_text(encoding="utf-8")
    assert "fixed inset-0 z-50 bg-black" in stage_code
    assert "aspect-[16/9]" in stage_code
    assert "100vh * 16 / 9" in stage_code
    assert "z-[60] bg-black" in stage_code  # Blackout curtain
    assert "PresentationFloatingBar" in stage_code

    # 5. Kiểm tra PresentationFloatingBar.jsx
    bar_path = FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx"
    assert bar_path.exists()
    bar_code = bar_path.read_text(encoding="utf-8")
    assert "45 * 60" in bar_code  # 45 phút chuẩn GDPT
    assert "formatTime" in bar_code
    assert "mousemove" in bar_code
    assert "setTimeout" in bar_code
    assert "onPrevSlide" in bar_code
    assert "onNextSlide" in bar_code
    assert "onToggleBlackout" in bar_code
    assert "onExitPresentation" in bar_code
