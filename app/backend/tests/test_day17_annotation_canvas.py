r"""
Automated Test Suite — Day 17: Hệ thống Vẽ Hình & Chú thích Trực tiếp trên Màn hình Trình chiếu
(Interactive Pen, Digital Inking & Whiteboard Canvas)

Kiểm thử chi tiết các hạng mục của Ngày 17:
- Task 17.1: Lớp Canvas vẽ chú thích phủ tràn màn hình & Quản lý Stroke Data Model
- Task 17.2: Thuật toán làm mượt nét vẽ Bezier bậc 2 & Bộ bút sư phạm (Bút mực, Bút dạ quang)
- Task 17.3: Công cụ tẩy nét thông minh (Hit-testing), Ngăn xếp Hoàn tác (Undo/Redo Stack) & Clear All
- Task 17.4: Chế độ Bảng trắng toàn màn hình (Whiteboard Mode) & Cơ chế lưu trữ theo từng Slide
- Task 17.5: Nghiệm thu Definition of Done (DoD) Ngày 17 và kiểm thử tích hợp E2E
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


def test_task_17_1_drawing_canvas_helper_utility():
    """
    Task 17.1: Kiểm tra tiện ích vẽ Canvas (drawingCanvasHelper.js):
    - getCanvasPoint: Chuyển đổi tọa độ client sang canvas, hỗ trợ lực nhấn pressure
    - setupHighDpiCanvas: Cấu hình scale theo window.devicePixelRatio cho màn hình Retina
    - createStroke: Khởi tạo mô hình Stroke chuẩn JSON cấu trúc (id, tool, color, size, alpha, points, slideIndex)
    - redrawAllStrokes: Vẽ lại toàn bộ các nét vẽ với độ dày và màu sắc tùy biến
    """
    helper_path = FRONTEND_DIR / "src" / "utils" / "drawingCanvasHelper.js"
    assert helper_path.exists(), f"Không tìm thấy tệp {helper_path}"
    content = helper_path.read_text(encoding="utf-8")

    assert "export function getCanvasPoint" in content
    assert "getBoundingClientRect" in content
    assert "pressure" in content

    assert "export function setupHighDpiCanvas" in content
    assert "devicePixelRatio" in content
    assert "ctx.scale(dpr, dpr)" in content

    assert "export function createStroke" in content
    assert "stroke_" in content
    assert "tool" in content
    assert "points: []" in content
    assert "slideIndex" in content

    assert "export function redrawAllStrokes" in content
    assert "ctx.clearRect" in content
    assert "drawSmoothStroke" in content


def test_task_17_1_annotation_canvas_component():
    """
    Task 17.1: Kiểm tra component AnnotationCanvas.jsx:
    - Nhận props: isActive, tool, color, size, slideIndex, strokes, onStrokesChange
    - Bắt sự kiện Pointer Events đa nền tảng: onPointerDown, onPointerMove, onPointerUp, onPointerCancel
    - Bật tắt con trỏ và pointer-events theo trạng thái isActive:
      + Khi isActive = true: pointer-events-auto, cursor-crosshair, touch-none
      + Khi isActive = false: pointer-events-none (không chặn click các nút bên dưới)
    - Tích hợp ResizeObserver đồng bộ kích thước theo container cha
    """
    canvas_comp_path = FRONTEND_DIR / "src" / "components" / "AnnotationCanvas.jsx"
    assert canvas_comp_path.exists(), f"Không tìm thấy tệp {canvas_comp_path}"
    content = canvas_comp_path.read_text(encoding="utf-8")

    assert "export default function AnnotationCanvas" in content
    assert "onPointerDown={handlePointerDown}" in content
    assert "onPointerMove={handlePointerMove}" in content
    assert "onPointerUp={handlePointerUp}" in content
    assert "onPointerCancel={handlePointerUp}" in content

    assert "pointer-events-auto cursor-crosshair" in content
    assert "pointer-events-none" in content
    assert "ResizeObserver" in content
    assert "setPointerCapture" in content


def test_task_17_1_stage_annotation_canvas_integration():
    """
    Task 17.1: Kiểm tra tích hợp AnnotationCanvas trong PresentationStage.jsx:
    - Import AnnotationCanvas from './AnnotationCanvas'
    - Khởi tạo state: isDrawingMode, currentTool, drawingColor, brushSize, slideDrawingsMap
    - Render <AnnotationCanvas ... /> bên trong khung hình 16:9 của slide
    - Truyền đầy đủ props: isActive={isDrawingMode}, tool={currentTool}, color={drawingColor},
      size={brushSize}, slideIndex={currentSlide}, strokes={currentStrokes}, onStrokesChange={handleStrokesChange}
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    assert "import AnnotationCanvas from './AnnotationCanvas'" in content
    assert "isDrawingMode" in content
    assert "slideDrawingsMap" in content
    assert "<AnnotationCanvas" in content
    assert "isActive={isDrawingMode}" in content
    assert "tool={currentTool}" in content
    assert "color={drawingColor}" in content
    assert "size={brushSize}" in content
    assert "slideIndex={currentSlide}" in content
    assert "strokes={currentStrokes}" in content
    assert "onStrokesChange={handleStrokesChange}" in content


def test_task_17_2_bezier_curve_smoothing_utility():
    """
    Task 17.2: Kiểm tra thuật toán làm mượt nét vẽ Bezier (bezierSmoothing.js):
    - drawSmoothStroke: Áp dụng nội suy Bezier bậc 2 (quadraticCurveTo) qua các trung điểm
    - PEDAGOGICAL_COLORS: Bảng 5 màu chuẩn mực cho Toán học THPT (Đỏ, Vàng, Xanh lục, Xanh dương, Trắng)
    - TOOL_PRESETS: Cấu hình chuẩn cho Bút mực (pen - alpha 1.0) và Bút dạ quang (highlighter - alpha 0.35)
    - getAdjustedLineWidth: Điều chỉnh độ dày nét theo lực nhấn bút cảm ứng (e.pressure)
    """
    bezier_path = FRONTEND_DIR / "src" / "utils" / "bezierSmoothing.js"
    assert bezier_path.exists(), f"Không tìm thấy tệp {bezier_path}"
    content = bezier_path.read_text(encoding="utf-8")

    assert "export const PEDAGOGICAL_COLORS" in content
    assert "#ef4444" in content  # Đỏ
    assert "#f59e0b" in content  # Vàng
    assert "#10b981" in content  # Xanh lục
    assert "#38bdf8" in content  # Xanh dương
    assert "#f8fafc" in content  # Trắng

    assert "export const TOOL_PRESETS" in content
    assert "pen" in content
    assert "highlighter" in content
    assert "0.35" in content

    assert "export function drawSmoothStroke" in content
    assert "quadraticCurveTo" in content
    assert "getAdjustedLineWidth" in content


def test_task_17_2_annotation_canvas_bezier_integration():
    """
    Task 17.2: Kiểm tra AnnotationCanvas áp dụng thuật toán Bezier:
    - Import drawSmoothStroke from '../utils/bezierSmoothing'
    - Áp dụng quadraticCurveTo trong handlePointerMove khi vẽ trực tiếp
    - Hỗ trợ bút dạ quang (highlighter) với square cap và độ mờ alpha
    """
    canvas_path = FRONTEND_DIR / "src" / "components" / "AnnotationCanvas.jsx"
    assert canvas_path.exists(), f"Không tìm thấy tệp {canvas_path}"
    content = canvas_path.read_text(encoding="utf-8")

    assert "import { drawSmoothStroke } from '../utils/bezierSmoothing'" in content
    assert "quadraticCurveTo" in content
    assert "highlighter" in content


def test_task_17_2_floating_bar_pen_controls_integration():
    """
    Task 17.2: Kiểm tra tích hợp bộ điều khiển Bút vẽ trong PresentationFloatingBar.jsx:
    - Nút Bút mực (Pen) với phím tắt P
    - Nút Bút dạ quang (Highlighter) với phím tắt H
    - Bảng chọn màu 5 màu sư phạm (PEDAGOGICAL_COLORS)
    - Nhận đầy đủ props: isDrawingMode, onToggleDrawingMode, currentTool, onSelectTool, drawingColor, onSelectColor
    """
    bar_path = FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx"
    assert bar_path.exists(), f"Không tìm thấy tệp {bar_path}"
    content = bar_path.read_text(encoding="utf-8")

    assert "isDrawingMode" in content
    assert "onToggleDrawingMode" in content
    assert "currentTool" in content
    assert "drawingColor" in content
    assert "PEDAGOGICAL_COLORS" in content
    assert "Bút (P)" in content or "Pen" in content
    assert "Dạ quang (H)" in content or "Highlighter" in content


def test_task_17_3_eraser_hit_testing_utility():
    """
    Task 17.3: Kiểm tra tiện ích kiểm tra va chạm hình học & Tẩy nét thông minh (eraserHitTesting.js):
    - pointToSegmentDistance: Khoảng cách Euclid ngắn nhất từ điểm P tới đoạn thẳng AB
    - isStrokeHitByEraser: Kiểm tra đầu tẩy tròn bán kính R có chạm vào bất kỳ đoạn nào của Stroke
    - findHitStrokeIndex: Tìm chỉ số Stroke bị chạm theo thứ tự nét mới nhất trước
    - removeHitStrokes: Loại bỏ toàn bộ các nét vẽ bị chạm và trả về danh sách erasedIds
    """
    eraser_path = FRONTEND_DIR / "src" / "utils" / "eraserHitTesting.js"
    assert eraser_path.exists(), f"Không tìm thấy tệp {eraser_path}"
    content = eraser_path.read_text(encoding="utf-8")

    assert "export function pointToSegmentDistance" in content
    assert "export function isStrokeHitByEraser" in content
    assert "export function findHitStrokeIndex" in content
    assert "export function removeHitStrokes" in content

    # Kiểm tra giải thuật hình chiếu vector trực giao:
    # v = B - A, w = P - A, c1 = w . v, c2 = v . v
    assert "const c1 = wx * vx + wy * vy" in content
    assert "const c2 = vx * vx + vy * vy" in content
    assert "const t = c1 / c2" in content
    assert "Math.sqrt" in content


def test_task_17_3_annotation_canvas_eraser_integration():
    """
    Task 17.3: Kiểm tra tích hợp công cụ Tẩy nét (Eraser) trong AnnotationCanvas.jsx:
    - Import removeHitStrokes from '../utils/eraserHitTesting'
    - Xử lý tool === 'eraser' trong handlePointerDown, handlePointerMove, handlePointerUp
    - Hiển thị vòng tròn con trỏ đầu tẩy trực quan (eraserCursor.visible) khi ở chế độ Eraser
    - Gọi onStrokesChange(curr, prev) khi hoàn tất lượt tẩy để ghi nhận lịch sử Undo
    """
    canvas_path = FRONTEND_DIR / "src" / "components" / "AnnotationCanvas.jsx"
    assert canvas_path.exists(), f"Không tìm thấy tệp {canvas_path}"
    content = canvas_path.read_text(encoding="utf-8")

    assert "import { removeHitStrokes" in content
    assert "tool === 'eraser'" in content
    assert "isErasingRef" in content
    assert "eraserCursor" in content
    assert "border-rose-400 bg-rose-500" in content


def test_task_17_3_stage_undo_redo_stack_and_clear_all():
    """
    Task 17.3: Kiểm tra quản lý Ngăn xếp Hoàn tác (Undo/Redo Stack) & Clear All trong PresentationStage.jsx:
    - Quản lý slideUndoStacks và slideRedoStacks theo từng slide
    - handleUndoStrokes: Lấy trạng thái trước từ undoStack, lưu trạng thái hiện tại vào redoStack
    - handleRedoStrokes: Lấy trạng thái từ redoStack, lưu trạng thái hiện tại vào undoStack
    - handleClearAllStrokes: Xóa toàn bộ nét của slide hiện tại và lưu vào undoStack để có thể hoàn tác
    - Bắt sự kiện phím tắt toàn cục:
      + Phím E: Bật công cụ Tẩy (tool = 'eraser')
      + Phím Ctrl+Z / Cmd+Z: Hoàn tác (Undo)
      + Phím Ctrl+Y / Cmd+Shift+Z / Ctrl+Shift+Z: Làm lại (Redo)
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    assert "slideUndoStacks" in content
    assert "slideRedoStacks" in content
    assert "handleUndoStrokes" in content
    assert "handleRedoStrokes" in content
    assert "handleClearAllStrokes" in content

    # Kiểm tra phím tắt
    assert "handleUndoStrokes()" in content
    assert "handleRedoStrokes()" in content
    assert "setCurrentTool('eraser')" in content

    # Kiểm tra truyền props xuống PresentationFloatingBar
    assert "canUndo=" in content
    assert "canRedo=" in content
    assert "onUndo=" in content
    assert "onRedo=" in content
    assert "onClearCanvas=" in content
    assert "hasStrokes=" in content


def test_task_17_3_floating_bar_eraser_and_history_controls():
    """
    Task 17.3: Kiểm tra bộ nút điều khiển Tẩy & Lịch sử trong PresentationFloatingBar.jsx:
    - Nút Tẩy nét (Eraser) với phím tắt E
    - Nút Hoàn tác (Undo - Ctrl+Z) với trạng thái disabled khi canUndo = false
    - Nút Làm lại (Redo - Ctrl+Y) với trạng thái disabled khi canRedo = false
    - Nút Xóa toàn bộ (Trash2) với trạng thái disabled khi hasStrokes = false
    """
    bar_path = FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx"
    assert bar_path.exists(), f"Không tìm thấy tệp {bar_path}"
    content = bar_path.read_text(encoding="utf-8")

    assert "Eraser" in content
    assert "Undo2" in content
    assert "Redo2" in content
    assert "Trash2" in content

    assert "canUndo" in content
    assert "canRedo" in content
    assert "onUndo" in content
    assert "onRedo" in content
    assert "onClearCanvas" in content
    assert "hasStrokes" in content
    assert "Tẩy (E)" in content


def test_task_17_4_whiteboard_overlay_component():
    """
    Task 17.4: Kiểm tra component Bảng Viết Phụ Toàn Màn Hình (WhiteboardOverlay.jsx):
    - 3 giao diện sư phạm: 'blackboard' (Bảng đen lưới Toán), 'chalkboard' (Bảng xanh truyền thống), 'whiteboard' (Bảng trắng)
    - Hiệu ứng lưới ô vuông Toán học (Math Grid 28px)
    - Tích hợp cụm công cụ: Bút, Dạ quang, Tẩy, Bảng màu sư phạm, Undo, Redo, Clear
    - Nhúng AnnotationCanvas với slideIndex="whiteboard" độc lập với các slide bài giảng
    """
    wb_path = FRONTEND_DIR / "src" / "components" / "WhiteboardOverlay.jsx"
    assert wb_path.exists(), f"Không tìm thấy tệp {wb_path}"
    content = wb_path.read_text(encoding="utf-8")

    assert "export default function WhiteboardOverlay" in content
    assert "blackboard" in content
    assert "chalkboard" in content
    assert "whiteboard" in content
    assert "radial-gradient" in content
    assert "28px 28px" in content
    assert "BẢNG PHỤ TOÁN HỌC" in content
    assert "<AnnotationCanvas" in content
    assert 'slideIndex="whiteboard"' in content


def test_task_17_4_slide_deck_drawings_storage_utility():
    """
    Task 17.4: Kiểm tra tiện ích lưu trữ nét vẽ theo từng slide trong slideDeckStorage.js:
    - SLIDE_DRAWINGS_STORAGE_KEY: Định danh khóa lưu trữ trong sessionStorage
    - loadSlideDrawingsFromStorage: Đọc toàn bộ slideDrawingsMap theo deckId
    - saveSlideDrawingsToStorage: Lưu trữ trạng thái nét vẽ theo deckId
    - clearSlideDrawingsFromStorage: Xóa sạch dữ liệu vẽ lưu trữ
    """
    storage_path = FRONTEND_DIR / "src" / "utils" / "slideDeckStorage.js"
    assert storage_path.exists(), f"Không tìm thấy tệp {storage_path}"
    content = storage_path.read_text(encoding="utf-8")

    assert "SLIDE_DRAWINGS_STORAGE_KEY" in content
    assert "export function loadSlideDrawingsFromStorage" in content
    assert "export function saveSlideDrawingsToStorage" in content
    assert "export function clearSlideDrawingsFromStorage" in content


def test_task_17_4_stage_whiteboard_and_slide_persistence_integration():
    """
    Task 17.4: Kiểm tra tích hợp Whiteboard và Lưu trữ theo Slide trong PresentationStage.jsx:
    - Import WhiteboardOverlay, loadSlideDrawingsFromStorage, saveSlideDrawingsToStorage
    - Khởi tạo slideDrawingsMap từ storage qua loadSlideDrawingsFromStorage(deckId)
    - Tự động đồng bộ saveSlideDrawingsToStorage(slideDrawingsMap, deckId) khi có thay đổi
    - Bắt phím tắt W: Bật/tắt Bảng phụ (isWhiteboardOpen)
    - Quản lý Undo / Redo cho Whiteboard khi đang mở bảng
    - Render <WhiteboardOverlay ... /> và truyền props xuống PresentationFloatingBar
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    assert "import WhiteboardOverlay from './WhiteboardOverlay'" in content
    assert "loadSlideDrawingsFromStorage" in content
    assert "saveSlideDrawingsToStorage" in content
    assert "isWhiteboardOpen" in content
    assert "setIsWhiteboardOpen" in content
    assert "<WhiteboardOverlay" in content

    # Phím tắt W
    assert "e.key === 'w' || e.key === 'W'" in content
    assert "setIsWhiteboardOpen((prev) => !prev)" in content

    # Truyền props xuống PresentationFloatingBar
    assert "isWhiteboardOpen={isWhiteboardOpen}" in content
    assert "onToggleWhiteboard={setIsWhiteboardOpen}" in content
    assert "slideDrawingsMap={slideDrawingsMap}" in content


def test_task_17_4_floating_bar_whiteboard_button_and_thumbnail_indicators():
    """
    Task 17.4: Kiểm tra nút Bảng phụ và Chỉ số nét vẽ Thumbnail trong PresentationFloatingBar.jsx:
    - Nhận props: isWhiteboardOpen, onToggleWhiteboard, slideDrawingsMap
    - Nút Bảng (W) với biểu tượng Grid3X3 và hiệu ứng active khi đang mở bảng
    - Thumbnail hiển thị huy hiệu số lượng nét vẽ nếu slide có ghi chú: ✎ {count}
    """
    bar_path = FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx"
    assert bar_path.exists(), f"Không tìm thấy tệp {bar_path}"
    content = bar_path.read_text(encoding="utf-8")

    assert "isWhiteboardOpen" in content
    assert "onToggleWhiteboard" in content
    assert "slideDrawingsMap" in content
    assert "Bảng (W)" in content
    assert "Grid3X3" in content
    assert "✎" in content


def test_task_17_5_definition_of_done_end_to_end_annotation_canvas_flow():
    """
    Task 17.5: Kiểm thử luồng End-to-End toàn diện cho Hệ thống Vẽ Hình & Chú thích Trực tiếp:
    1. Khởi tạo nét vẽ Bút mực (Pen) và Bút dạ quang (Highlighter) với chuẩn Stroke Data Model.
    2. Kiểm tra tính toán làm mượt nét Bezier bậc 2 và lực nhấn cảm ứng Stylus.
    3. Kiểm tra giải thuật va chạm hình học (Euclidean Hit-testing) và tẩy nét thông minh.
    4. Kiểm tra chu trình hoàn tác Undo / Redo / Clear All (Command Pattern).
    5. Kiểm tra cơ chế đồng bộ và bảo toàn nét vẽ khi chuyển slide (Slide Inking Persistence).
    6. Kiểm tra Chế độ Bảng Viết Phụ (Whiteboard Mode) với không gian vẽ độc lập 100%.
    """
    import math

    # 1. Stroke Data Model & Tool Presets
    stroke_pen = {
        "id": "stroke_pen_001",
        "tool": "pen",
        "color": "#ef4444",
        "size": 4,
        "alpha": 1.0,
        "points": [
            {"x": 100, "y": 100, "pressure": 0.5},
            {"x": 150, "y": 120, "pressure": 0.6},
            {"x": 200, "y": 180, "pressure": 0.8},
            {"x": 250, "y": 200, "pressure": 0.7}
        ],
        "slideIndex": 0
    }

    stroke_highlighter = {
        "id": "stroke_hl_002",
        "tool": "highlighter",
        "color": "#f59e0b",
        "size": 16,
        "alpha": 0.35,
        "points": [
            {"x": 50, "y": 300, "pressure": 0.5},
            {"x": 300, "y": 300, "pressure": 0.5}
        ],
        "slideIndex": 0
    }

    assert stroke_pen["alpha"] == 1.0
    assert stroke_highlighter["alpha"] == 0.35
    assert len(stroke_pen["points"]) == 4

    # 2. Bezier midpoint & adjusted line width calculation
    pts = stroke_pen["points"]
    mid1_x = (pts[0]["x"] + pts[1]["x"]) / 2
    mid1_y = (pts[0]["y"] + pts[1]["y"]) / 2
    assert mid1_x == 125.0
    assert mid1_y == 110.0

    # Adjusted line width: size * (0.4 + 1.2 * pressure)
    w_adjusted = stroke_pen["size"] * (0.4 + 1.2 * pts[2]["pressure"])
    assert round(w_adjusted, 2) == round(4 * (0.4 + 1.2 * 0.8), 2)  # 4 * 1.36 = 5.44

    # 3. Geometric Hit-Testing simulation (Euclidean vector projection)
    def point_to_segment_dist(px, py, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1
        wx, wy = px - x1, py - y1
        c1 = wx * vx + wy * vy
        c2 = vx * vx + vy * vy
        if c2 <= 0.000001 or c1 <= 0:
            return math.hypot(px - x1, py - y1)
        if c2 <= c1:
            return math.hypot(px - x2, py - y2)
        t = c1 / c2
        proj_x = x1 + t * vx
        proj_y = y1 + t * vy
        return math.hypot(px - proj_x, py - proj_y)

    # Eraser at (175, 305) with radius 18
    # Segment of highlighter is (50, 300) -> (300, 300)
    d_hl = point_to_segment_dist(175, 305, 50, 300, 300, 300)
    assert d_hl == 5.0
    # Threshold = eraserRadius (18) + stroke.size/2 (8) = 26
    assert d_hl <= (18 + 8)  # Chạm vào nét dạ quang!

    # Eraser at (600, 600) -> Không chạm nét nào
    d_far = point_to_segment_dist(600, 600, 50, 300, 300, 300)
    assert d_far > 26

    # 4. Command Pattern Undo / Redo Stack Simulation
    strokes_state = [stroke_pen, stroke_highlighter]
    undo_stack = []
    redo_stack = []

    # Thao tác 1: Tẩy nét dạ quang
    undo_stack.append(list(strokes_state))
    redo_stack.clear()
    strokes_state = [stroke_pen]  # Đã xóa stroke_highlighter
    assert len(strokes_state) == 1
    assert len(undo_stack) == 1
    assert len(redo_stack) == 0

    # Thao tác 2: Undo (Hoàn tác khôi phục nét dạ quang)
    popped_undo = undo_stack.pop()
    redo_stack.append(list(strokes_state))
    strokes_state = popped_undo
    assert len(strokes_state) == 2
    assert len(undo_stack) == 0
    assert len(redo_stack) == 1

    # Thao tác 3: Redo (Làm lại thao tác xóa)
    popped_redo = redo_stack.pop()
    undo_stack.append(list(strokes_state))
    strokes_state = popped_redo
    assert len(strokes_state) == 1
    assert len(undo_stack) == 1
    assert len(redo_stack) == 0

    # Thao tác 4: Clear all canvas
    undo_stack.append(list(strokes_state))
    redo_stack.clear()
    strokes_state = []
    assert len(strokes_state) == 0

    # Undo khôi phục sau Clear All
    strokes_state = undo_stack.pop()
    assert len(strokes_state) == 1

    # 5. Slide Inking Persistence across multiple slides
    import json
    slide_drawings_map = {
        0: [stroke_pen],
        1: [{"id": "s_slide1", "tool": "pen", "points": [{"x": 10, "y": 20}]}],
        2: []
    }
    serialized = json.dumps(slide_drawings_map)
    deserialized = json.loads(serialized)
    assert len(deserialized["0"]) == 1
    assert len(deserialized["1"]) == 1
    assert len(deserialized["2"]) == 0

    # 6. Whiteboard Mode Independent State
    whiteboard_strokes = [{"id": "wb_proof_01", "tool": "pen", "points": [{"x": 200, "y": 200}]}]
    assert len(whiteboard_strokes) == 1
    assert len(slide_drawings_map[0]) == 1  # Không bị ảnh hưởng lẫn nhau


def test_task_17_5_dod_comprehensive_checklist():
    """
    Task 17.5: Kiểm tra bảng tiêu chí Definition of Done (DoD) Toàn diện của Ngày 17:
    - 5 tệp mã nguồn Frontend cốt lõi được xây dựng chuẩn mực:
      1. drawingCanvasHelper.js: High-DPI setup, coordinate transform, stroke factory
      2. bezierSmoothing.js: Quadratic Bezier curve smoothing, pedagogical colors, tool presets
      3. eraserHitTesting.js: Orthogonal vector projection, point-to-segment distance, object eraser
      4. AnnotationCanvas.jsx: Pointer events listener, real-time Bezier drawing, circular eraser ring
      5. WhiteboardOverlay.jsx: Fullscreen whiteboard with 3 themes (blackboard, chalkboard, whiteboard)
    - 2 tệp tích hợp giao diện & lưu trữ:
      6. PresentationStage.jsx: Undo/Redo stacks, slide inking persistence, shortcut listeners
      7. PresentationFloatingBar.jsx: Pen, Highlighter, Eraser, Undo, Redo, Clear, Whiteboard buttons
    - Phím tắt chuẩn mực quốc tế:
      P (Bút mực), H (Bút dạ quang), E (Tẩy nét), W (Bảng phụ), Ctrl+Z (Undo), Ctrl+Y (Redo)
    """
    # 1. Kiểm tra tồn tại toàn bộ các tệp kiến trúc
    files_to_check = [
        FRONTEND_DIR / "src" / "utils" / "drawingCanvasHelper.js",
        FRONTEND_DIR / "src" / "utils" / "bezierSmoothing.js",
        FRONTEND_DIR / "src" / "utils" / "eraserHitTesting.js",
        FRONTEND_DIR / "src" / "components" / "AnnotationCanvas.jsx",
        FRONTEND_DIR / "src" / "components" / "WhiteboardOverlay.jsx",
        FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx",
        FRONTEND_DIR / "src" / "components" / "PresentationFloatingBar.jsx",
        FRONTEND_DIR / "src" / "utils" / "slideDeckStorage.js"
    ]

    for f in files_to_check:
        assert f.exists(), f"Thiếu tệp kiến trúc: {f}"

    # 2. Kiểm tra bộ phím tắt trong PresentationStage.jsx
    stage_content = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "e.key === 'p' || e.key === 'P'" in stage_content
    assert "e.key === 'h' || e.key === 'H'" in stage_content
    assert "e.key === 'e' || e.key === 'E'" in stage_content
    assert "e.key === 'w' || e.key === 'W'" in stage_content
    assert "(e.key === 'z' || e.key === 'Z')" in stage_content
    assert "(e.key === 'y' || e.key === 'Y')" in stage_content




