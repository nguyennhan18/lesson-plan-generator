r"""
Automated Test Suite — Day 12: Thêm Thanh Điều khiển Tham số Hình học (Slider Controls)
Kiểm thử chi tiết các hạng mục của Ngày 12:
- Task 12.1: Thanh trượt UI (Slider) Chiều cao h (1-10) và Cạnh đáy a (1-8)
- Task 12.2: Bắt sự kiện oninput, API cập nhật tọa độ đỉnh S(0, 0, h) theo thời gian thực
- Task 12.3: Bảng thông số động & Công thức thể tích KaTeX V = 1/3 S_đáy * h tự động nhảy số theo thanh trượt
"""

import math
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
from services.geometry_service import calculate_parametric_geometry, get_apex_coordinates

client = TestClient(app)


def test_task_12_1_and_12_2_geometry_service_apex_and_parameters():
    """
    Kiểm tra dịch vụ hình học tính toán tọa độ đỉnh S(0, 0, h) và các đỉnh đáy theo tham số a, h.
    """
    # 1. Chóp tứ giác S.ABCD với h = 6.0, a = 4.0
    res_obj = calculate_parametric_geometry("pyramid_square", height=6.0, base_edge=4.0)
    res = res_obj.model_dump()
    assert res["polyhedron_type"] == "pyramid_square"
    assert res["apex_coordinates"] == {"x": 0.0, "y": 0.0, "z": 6.0}
    assert res["vertices"]["S"] == {"x": 0.0, "y": 0.0, "z": 6.0}
    assert res["vertices"]["A"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert res["vertices"]["B"] == {"x": 4.0, "y": 0.0, "z": 0.0}
    assert res["vertices"]["C"] == {"x": 4.0, "y": 4.0, "z": 0.0}
    assert res["vertices"]["D"] == {"x": 0.0, "y": 4.0, "z": 0.0}

    # 2. Kiểm tra hàm get_apex_coordinates độc lập
    apex_res = get_apex_coordinates(height=8.5)
    assert apex_res["apex_name"] == "S"
    assert apex_res["coordinates"] == {"x": 0.0, "y": 0.0, "z": 8.5}
    assert apex_res["descartes_notation"] == "S(0.0, 0.0, 8.5)"


def test_task_12_3_dynamic_volume_and_measurements():
    """
    Task 12.3: Kiểm tra công thức thể tích động V = 1/3 * S_đáy * h và diện tích S_đáy tự động tính chuẩn xác.
    """
    # 1. Chóp tứ giác đều / SA vuông góc đáy: S_đáy = a^2 = 16.0, h = 6.0 => V = 1/3 * 16 * 6 = 32.0
    res_sq = calculate_parametric_geometry("pyramid_square", height=6.0, base_edge=4.0).model_dump()
    meas_sq = res_sq["measurements"]
    assert meas_sq["base_area"] == 16.0
    assert meas_sq["height"] == 6.0
    assert math.isclose(meas_sq["volume"], 32.0, rel_tol=1e-3)
    assert "1/3 * S_day * h" in meas_sq.get("volume_formula", "1/3 * S_day * h = 1/3 * a^2 * h")

    # 2. Chóp tam giác S.ABC: S_đáy = 1/2 * a^2 = 8.0, h = 9.0 => V = 1/3 * 8 * 9 = 24.0
    res_tri = calculate_parametric_geometry("pyramid_triangle", height=9.0, base_edge=4.0).model_dump()
    meas_tri = res_tri["measurements"]
    assert meas_tri["base_area"] == 8.0
    assert meas_tri["height"] == 9.0
    assert math.isclose(meas_tri["volume"], 24.0, rel_tol=1e-3)

    # 3. Lăng trụ tam giác: V = S_đáy * h = 8.0 * 5.0 = 40.0
    res_prism = calculate_parametric_geometry("prism_triangle", height=5.0, base_edge=4.0).model_dump()
    meas_prism = res_prism["measurements"]
    assert meas_prism["base_area"] == 8.0
    assert meas_prism["height"] == 5.0
    assert math.isclose(meas_prism["volume"], 40.0, rel_tol=1e-3)

    # 4. Hình lập phương: V = a^3 = 5^3 = 125.0
    res_cube = calculate_parametric_geometry("cube", height=5.0, base_edge=5.0).model_dump()
    meas_cube = res_cube["measurements"]
    assert meas_cube["base_area"] == 25.0
    assert math.isclose(meas_cube["volume"], 125.0, rel_tol=1e-3)


def test_task_12_api_endpoints():
    """
    Kiểm tra hai API endpoints RESTful cho phép đồng bộ hóa dữ liệu đỉnh và thông số hình học.
    """
    # Endpoint 1: POST /api/v1/geometry/parametric-coordinates
    payload = {
        "polyhedron_type": "pyramid_square",
        "height": 7.5,
        "base_edge": 3.0
    }
    response = client.post("/api/v1/geometry/parametric-coordinates", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["apex_coordinates"]["z"] == 7.5
    assert data["measurements"]["base_area"] == 9.0
    # V = 1/3 * 9.0 * 7.5 = 22.5
    assert math.isclose(data["measurements"]["volume"], 22.5, rel_tol=1e-3)

    # Endpoint 2: GET /api/v1/geometry/apex-coordinates
    response_apex = client.get("/api/v1/geometry/apex-coordinates?height=5.2")
    assert response_apex.status_code == 200
    apex_data = response_apex.json()
    assert apex_data["apex_coordinates"]["z"] == 5.2
    assert apex_data["vertices"]["S"]["z"] == 5.2


def test_task_12_frontend_code_integration():
    """
    Kiểm tra sự tích hợp của mã giao diện người dùng (UI Components) cho Ngày 12:
    - App.jsx: Quản lý state geoHeight và geoBaseEdge
    - PresentationStage.jsx: Có Slider Controls, MathText KaTeX động, Bảng thông số S_đáy, h, V
    - ThreeCanvas.jsx: Nhận props heightParam, baseParam và tỷ lệ co giãn tham số
    - RightToolsDock.jsx: Có Sliders và hiển thị thể tích động
    - geometryClient.js: Cung cấp computeParametricCoordinatesLocal và fetchParametricCoordinatesRemote
    """
    app_jsx = (FRONTEND_DIR / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "geoHeight" in app_jsx
    assert "geoBaseEdge" in app_jsx

    pres_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "handleHeightInput" in pres_jsx
    assert "handleBaseEdgeInput" in pres_jsx
    assert "volumeLatex" in pres_jsx
    assert "Bảng Thông Số Động & Thể Tích" in pres_jsx
    assert "generalFormula" in pres_jsx
    assert "substFormula" in pres_jsx

    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")
    assert "heightParam" in canvas_jsx
    assert "baseParam" in canvas_jsx

    dock_jsx = (FRONTEND_DIR / "src" / "components" / "RightToolsDock.jsx").read_text(encoding="utf-8")
    assert "computeParametricCoordinatesLocal" in dock_jsx
    assert "Thể tích V:" in dock_jsx

    client_js = (FRONTEND_DIR / "src" / "utils" / "geometryClient.js").read_text(encoding="utf-8")
    assert "computeParametricCoordinatesLocal" in client_js
    assert "fetchParametricCoordinatesRemote" in client_js


def test_task_12_4_render_performance_raf_and_texture_cache():
    """
    Task 12.4: Kiểm tra tối ưu hiệu năng render 60 FPS:
    - ThreeCanvas.jsx: Tái sử dụng Texture qua labelTextureCache (Map), tránh cấp phát canvas rác
    - ThreeCanvas.jsx: Điều phối việc tái dựng mô hình hình học qua requestAnimationFrame (rafRebuildRef)
    - PresentationStage.jsx: Bắt sự kiện oninput và throttle qua requestAnimationFrame (rafHeightRef, rafBaseRef)
    - RightToolsDock.jsx: Áp dụng requestAnimationFrame cho cụm thanh trượt
    - Có biểu tượng và trạng thái '60 FPS rAF' thông báo cho giáo viên
    """
    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")
    assert "labelTextureCache" in canvas_jsx
    assert "getOrCreateLabelTexture" in canvas_jsx
    assert "rafRebuildRef" in canvas_jsx
    assert "requestAnimationFrame(rebuildModel)" in canvas_jsx
    assert "cancelAnimationFrame" in canvas_jsx
    assert "60 FPS rAF" in canvas_jsx

    pres_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "rafHeightRef" in pres_jsx
    assert "rafBaseRef" in pres_jsx
    assert "requestAnimationFrame" in pres_jsx
    assert "cancelAnimationFrame" in pres_jsx
    assert "60 FPS rAF" in pres_jsx

    dock_jsx = (FRONTEND_DIR / "src" / "components" / "RightToolsDock.jsx").read_text(encoding="utf-8")
    assert "rafHeightRef" in dock_jsx
    assert "rafBaseRef" in dock_jsx
    assert "requestAnimationFrame" in dock_jsx
    assert "cancelAnimationFrame" in dock_jsx
    assert "60 FPS rAF" in dock_jsx


def test_task_12_5_dod_day12_drag_slider_height_3_to_8_end_to_end():
    """
    Task 12.5 (DoD Ngày 12): Nghiệm thu tiêu chí hoàn thành cốt lõi:
    - Kéo slider chiều cao h từ 3.0 lên 8.0:
      1. Tọa độ đỉnh chóp dịch chuyển: S(0.0, 0.0, 3.0) -> S(0.0, 0.0, 8.0)
      2. Diện tích đáy S_đáy không đổi: S_đáy = a^2 = 16.0 (với a = 4.0)
      3. Thể tích nhảy số chuẩn xác từ V(h=3) = 16.0 lên V(h=8) = 42.67:
         V = 1/3 * 16.0 * h
      4. Tỷ lệ tăng thể tích V(8) / V(3) = 8 / 3 (tuyến tính chuẩn xác)
      5. Hai API endpoint GET và POST trả về kết quả đồng nhất với tính toán cục bộ
    """
    base_a = 4.0

    # Bước 1: Trạng thái ban đầu h = 3.0
    res_start = calculate_parametric_geometry("pyramid_square", height=3.0, base_edge=base_a).model_dump()
    assert res_start["apex_coordinates"]["z"] == 3.0
    assert res_start["measurements"]["base_area"] == 16.0
    assert math.isclose(res_start["measurements"]["volume"], 16.0, rel_tol=1e-3)

    # Bước 2: Kéo slider tăng dần h từ 3.0 lên 8.0 theo từng bước (step = 0.5)
    prev_vol = 16.0
    steps = [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
    for h_val in steps:
        step_res = calculate_parametric_geometry("pyramid_square", height=h_val, base_edge=base_a).model_dump()
        curr_vol = step_res["measurements"]["volume"]
        # Thể tích phải tăng nghiêm ngặt theo chiều cao
        assert curr_vol > prev_vol
        assert step_res["apex_coordinates"]["z"] == h_val
        assert step_res["measurements"]["base_area"] == 16.0
        expected_vol = (1.0 / 3.0) * 16.0 * h_val
        assert math.isclose(curr_vol, expected_vol, rel_tol=1e-2)
        prev_vol = curr_vol

    # Bước 3: Trạng thái đích h = 8.0
    res_end = calculate_parametric_geometry("pyramid_square", height=8.0, base_edge=base_a).model_dump()
    assert res_end["apex_coordinates"]["z"] == 8.0
    assert res_end["measurements"]["base_area"] == 16.0
    # V(h=8) = (1/3) * 16 * 8 = 128 / 3 = 42.6667
    assert math.isclose(res_end["measurements"]["volume"], 42.6667, rel_tol=1e-3)

    # Kiểm tra tỷ lệ tuyến tính
    ratio = res_end["measurements"]["volume"] / res_start["measurements"]["volume"]
    assert math.isclose(ratio, 8.0 / 3.0, rel_tol=1e-3)

    # Bước 4: Kiểm tra sự đồng nhất giữa API Backend và Dịch vụ
    api_resp = client.post("/api/v1/geometry/parametric-coordinates", json={
        "polyhedron_type": "pyramid_square",
        "height": 8.0,
        "base_edge": 4.0
    })
    assert api_resp.status_code == 200
    api_data = api_resp.json()
    assert api_data["apex_coordinates"]["z"] == 8.0
    assert math.isclose(api_data["measurements"]["volume"], 42.6667, rel_tol=1e-3)


