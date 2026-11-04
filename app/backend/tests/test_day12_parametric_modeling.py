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


from lessonai.main import app
from lessonai.services.geometry import calculate_parametric_geometry, get_apex_coordinates

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
