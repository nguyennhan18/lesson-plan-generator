r"""
Automated Test Suite — Day 13: Xử lý Đường Nét Đứt (Hidden Lines) & Nhiều Góc Nhìn
Kiểm thử chi tiết các hạng mục của Ngày 13:
- Task 13.1: Cấu hình thuật toán hiển thị nét đứt cho các cạnh khuất nằm phía sau mặt phẳng trong mô hình 3D
- Task 13.2: Bộ chuyển đổi nhanh góc nhìn chuẩn SGK (Phối cảnh, Chiếu đứng, Chiếu bằng, Chiếu cạnh)
- Task 13.3: Chế độ Hình khai triển phẳng 2D song song với hình 3D
- Task 13.4: Bật/tắt nhãn đỉnh và tọa độ Descartes sư phạm
- Task 13.5: Nghiệm thu DoD Ngày 13 và kiểm thử toàn diện
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
from lessonai.services.geometry import get_polyhedron_edge_topology

client = TestClient(app)


def test_task_13_1_polyhedron_edge_topology_rules():
    """
    Task 13.1: Kiểm tra cấu trúc cạnh khuất (nét đứt) và cạnh thấy (nét liền) chuẩn SGK GDPT 2018:
    1. Chóp tứ giác S.ABCD: 3 cạnh khuất (AB, AD, SA), 5 cạnh thấy (BC, CD, SB, SC, SD), 2 đường chéo phụ nét đứt (AC, BD)
    2. Chóp tam giác S.ABC: 3 cạnh khuất (AB, AC, SA), 3 cạnh thấy (BC, SB, SC), 1 đường cao đáy nét đứt (AH)
    3. Lăng trụ đứng tam giác: 3 cạnh khuất (AB, AC, AA'), 6 cạnh thấy
    4. Hình lập phương: 3 cạnh khuất (AB, AD, AA'), 9 cạnh thấy
    """
    # 1. Chóp tứ giác S.ABCD
    topo_sq = get_polyhedron_edge_topology("pyramid_square")
    assert topo_sq["polyhedron_type"] == "pyramid_square"
    assert topo_sq["hidden_count"] == 3
    assert topo_sq["visible_count"] == 5
    assert ["A", "B"] in topo_sq["hidden_edges"]
    assert ["A", "D"] in topo_sq["hidden_edges"]
    assert ["S", "A"] in topo_sq["hidden_edges"]
    assert ["B", "C"] in topo_sq["visible_edges"]
    assert ["S", "C"] in topo_sq["visible_edges"]
    assert ["A", "C"] in topo_sq["auxiliary_dashed_edges"]

    # 2. Chóp tam giác S.ABC
    topo_tri = get_polyhedron_edge_topology("pyramid_triangle")
    assert topo_tri["polyhedron_type"] == "pyramid_triangle"
    assert topo_tri["hidden_count"] == 3
    assert ["A", "B"] in topo_tri["hidden_edges"]
    assert ["A", "C"] in topo_tri["hidden_edges"]
    assert ["S", "A"] in topo_tri["hidden_edges"]
    assert ["B", "C"] in topo_tri["visible_edges"]
    assert ["A", "H"] in topo_tri["auxiliary_dashed_edges"]

    # 3. Lăng trụ đứng tam giác
    topo_prism = get_polyhedron_edge_topology("prism_triangle")
    assert topo_prism["polyhedron_type"] == "prism_triangle"
    assert topo_prism["hidden_count"] == 3
    assert topo_prism["visible_count"] == 6
    assert ["A", "A'"] in topo_prism["hidden_edges"]
    assert ["A", "B"] in topo_prism["hidden_edges"]
    assert ["A", "C"] in topo_prism["hidden_edges"]

    # 4. Hình lập phương ABCD.A'B'C'D'
    topo_cube = get_polyhedron_edge_topology("cube")
    assert topo_cube["polyhedron_type"] == "cube"
    assert topo_cube["hidden_count"] == 3
    assert topo_cube["visible_count"] == 9
    assert ["A", "B"] in topo_cube["hidden_edges"]
    assert ["A", "D"] in topo_cube["hidden_edges"]
    assert ["A", "A'"] in topo_cube["hidden_edges"]
    assert ["B", "C"] in topo_cube["visible_edges"]
    assert ["A'", "B'"] in topo_cube["visible_edges"]








def test_task_13_3_unfolded_net_topology_calculation():
    """
    Task 13.3: Kiểm tra giải thuật tính toán tọa độ bản vẽ Khai Triển Phẳng 2D (Unfolded Net):
    1. Chóp tứ giác: 5 mảnh mặt (1 đáy vuông ABCD + 4 mặt bên tam giác SAB, SBC, SCD, SDA)
       - Nếp gấp: 4 cạnh tiếp giáp đáy
       - S_xq = ah + a*sqrt(a^2 + h^2)
    2. Lăng trụ đứng tam giác: 5 mảnh mặt (3 mặt bên chữ nhật liên tiếp + 2 đáy tam giác vuông cân)
       - S_xq = (2a + a*sqrt(2))*h
    3. Khối lập phương: 6 mảnh mặt vuông chữ thập (4 mặt xung quanh + 2 mặt đáy)
       - S_xq = 4*a^2, S_tp = 6*a^2
    """
    from lessonai.services.geometry import get_unfolded_net_topology

    # 1. Chóp tứ giác (a = 4.0, h = 4.0)
    net_sq = get_unfolded_net_topology("pyramid_square", height=4.0, base_edge=4.0)
    assert net_sq["polyhedron_type"] == "pyramid_square"
    assert len(net_sq["faces"]) == 5
    assert net_sq["measurements"]["base_area"] == 16.0
    # S_xq = 4*4 + 4*sqrt(32) = 16 + 22.627 = 38.627
    assert pytest.approx(net_sq["measurements"]["lateral_area"], 0.01) == 38.627
    assert pytest.approx(net_sq["measurements"]["total_area"], 0.01) == 54.627
    assert len(net_sq["fold_lines"]) == 4
    assert "S_{xq}" in net_sq["formulas"]["latex_sxq"]
    assert "bounding_box" in net_sq
    assert net_sq["bounding_box"]["width"] > 0

    # 2. Lăng trụ đứng tam giác (a = 4.0, h = 4.0)
    net_prism = get_unfolded_net_topology("prism_triangle", height=4.0, base_edge=4.0)
    assert net_prism["polyhedron_type"] == "prism_triangle"
    assert len(net_prism["faces"]) == 5
    assert net_prism["measurements"]["base_area"] == 8.0
    # S_xq = (2*4 + 4*sqrt(2))*4 = (8 + 5.657)*4 = 54.627
    assert pytest.approx(net_prism["measurements"]["lateral_area"], 0.01) == 54.627
    assert pytest.approx(net_prism["measurements"]["total_area"], 0.01) == 70.627
    assert len(net_prism["fold_lines"]) == 4

    # 3. Khối lập phương (a = 4.0, h = 4.0)
    net_cube = get_unfolded_net_topology("cube", height=4.0, base_edge=4.0)
    assert net_cube["polyhedron_type"] == "cube"
    assert len(net_cube["faces"]) == 6
    assert net_cube["measurements"]["base_area"] == 16.0
    assert net_cube["measurements"]["lateral_area"] == 64.0
    assert net_cube["measurements"]["total_area"] == 96.0






def test_task_13_4_vertex_labels_taxonomy():
    """
    Task 13.4: Kiểm tra danh mục tên các đỉnh (S, A, B, C, D...) và vai trò hình học SGK:
    1. Chóp tứ giác: S, A, B, C, D, O (6 đỉnh / điểm đặc biệt)
    2. Chóp tam giác: S, A, B, C, H (5 đỉnh / điểm đặc biệt)
    3. Lăng trụ tam giác: A, B, C, A', B', C' (6 đỉnh)
    4. Hình lập phương: A, B, C, D, A', B', C', D' (8 đỉnh)
    """
    from lessonai.services.geometry import get_polyhedron_vertex_labels

    # 1. Chóp tứ giác
    v_sq = get_polyhedron_vertex_labels("pyramid_square")
    assert v_sq["polyhedron_type"] == "pyramid_square"
    assert v_sq["vertex_count"] == 6
    assert v_sq["vertex_labels"] == ["S", "A", "B", "C", "D", "O"]
    assert any(x["label"] == "S" and x["role"] == "Apex" for x in v_sq["vertices_info"])
    assert any(x["label"] == "A" and "Origin" in x["role"] for x in v_sq["vertices_info"])

    # 2. Chóp tam giác
    v_tri = get_polyhedron_vertex_labels("pyramid_triangle")
    assert v_tri["vertex_count"] == 5
    assert v_tri["vertex_labels"] == ["S", "A", "B", "C", "H"]
    assert any(x["label"] == "H" for x in v_tri["vertices_info"])

    # 3. Lăng trụ tam giác
    v_prism = get_polyhedron_vertex_labels("prism_triangle")
    assert v_prism["vertex_count"] == 6
    assert v_prism["vertex_labels"] == ["A", "B", "C", "A'", "B'", "C'"]

    # 4. Hình lập phương
    v_cube = get_polyhedron_vertex_labels("cube")
    assert v_cube["vertex_count"] == 8
    assert len(v_cube["vertex_labels"]) == 8
    assert "D'" in v_cube["vertex_labels"]
