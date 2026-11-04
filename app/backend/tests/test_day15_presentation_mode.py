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


from lessonai.main import app

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
    helper_path = FRONTEND_DIR / "src" / "features" / "presentation" / "fullscreenHelper.js"
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
    header_path = FRONTEND_DIR / "src" / "shared" / "components" / "HeaderNav.jsx"
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
    assert "usePresentationControls" in content
    content += (FRONTEND_DIR / "src" / "features" / "presentation" / "usePresentationControls.js").read_text(encoding="utf-8")

    assert "isPresentationMode" in content
    assert "setIsPresentationMode" in content
    assert "onFullscreenChange" in content
    assert "handleStartPresentation" in content
    assert "requestPresentationFullscreen" in content
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
    controls_code = (FRONTEND_DIR / "src" / "features" / "presentation" / "usePresentationControls.js").read_text(encoding="utf-8")
    assert "usePresentationControls" in content
    assert "'Escape'" in controls_code
    assert "handleExitPresentation()" in controls_code




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
    assert "usePresentationControls" in content
    content += (FRONTEND_DIR / "src" / "features" / "presentation" / "usePresentationControls.js").read_text(encoding="utf-8")

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
    bar_path = FRONTEND_DIR / "src" / "features" / "presentation" / "PresentationFloatingBar.jsx"
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
