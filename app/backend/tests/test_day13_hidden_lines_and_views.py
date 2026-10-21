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

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from main import app
from services.geometry_service import get_polyhedron_edge_topology

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


def test_task_13_1_api_edge_topology_endpoint():
    """
    Task 13.1: Kiểm tra API GET /api/v1/geometry/edge-topology trả về cấu trúc cạnh chính xác.
    """
    # Query chóp tứ giác
    resp_sq = client.get("/api/v1/geometry/edge-topology?polyhedron_type=pyramid_square")
    assert resp_sq.status_code == 200
    data_sq = resp_sq.json()
    assert data_sq["hidden_count"] == 3
    assert ["S", "A"] in data_sq["hidden_edges"]

    # Query hình lập phương
    resp_cube = client.get("/api/v1/geometry/edge-topology?polyhedron_type=cube")
    assert resp_cube.status_code == 200
    data_cube = resp_cube.json()
    assert data_cube["hidden_count"] == 3
    assert ["A", "A'"] in data_cube["hidden_edges"]
    assert ["C'", "D'"] in data_cube["visible_edges"]


def test_task_13_1_frontend_code_integration():
    """
    Task 13.1: Kiểm tra mã nguồn Frontend đã tích hợp đầy đủ quy chuẩn nét đứt SGK:
    - ThreeCanvas.jsx: LineDashedMaterial có dashSize, gapSize và renderOrder
    - ThreeCanvas.jsx: Khối lập phương có 3 cạnh khuất nét đứt AB, AD, AA'
    - PresentationStage.jsx: Nút toggle 'Nét Đứt' ngay trên thanh công cụ
    - App.jsx: Truyền prop setShowHiddenLines xuống PresentationStage
    """
    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")
    assert "LineDashedMaterial" in canvas_jsx
    assert "dashSize" in canvas_jsx
    assert "gapSize" in canvas_jsx
    assert "computeLineDistances" in canvas_jsx
    # Kiểm tra Cube có cạnh nét đứt AB, AD, AA'
    assert 'addEdge(v.A, v.B, 0x38bdf8, true' in canvas_jsx
    assert 'addEdge(v.A, v.D, 0x38bdf8, true' in canvas_jsx
    assert 'addEdge(v.A, v["A\'"], 0x34d399, true' in canvas_jsx

    stage_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "setShowHiddenLines" in stage_jsx
    assert "Nét Đứt" in stage_jsx

    app_jsx = (FRONTEND_DIR / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "setShowHiddenLines={setShowHiddenLines}" in app_jsx


def test_task_13_2_camera_presets_multi_views():
    """
    Task 13.2: Kiểm tra 4 góc nhìn chuẩn SGK (TCVN 7284):
    1. Phối cảnh (Iso): Góc nhìn không gian chuẩn SGK (Pitch -22°, Yaw +35°)
    2. Chiếu đứng (Front): Chiếu trực diện từ trước ra sau (Pitch 0°, Yaw 0°)
    3. Chiếu bằng (Top): Chiếu thẳng từ trên xuống đáy Oxy (Pitch -90°, Yaw 0°)
    4. Chiếu cạnh (Side): Chiếu vuông góc từ bên hông (Pitch 0°, Yaw +90°)
    - PresentationStage.jsx: Có 4 nút chuyển góc nhìn trực quan
    - RightToolsDock.jsx: Có grid 4 nút góc nhìn chuẩn SGK
    - ThreeCanvas.jsx: Có bộ xử lý 4 presets với nội suy vi phân Lerp mượt mà
    """
    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")
    assert "cameraPreset === 'iso'" in canvas_jsx
    assert "cameraPreset === 'top'" in canvas_jsx
    assert "cameraPreset === 'front'" in canvas_jsx
    assert "cameraPreset === 'side'" in canvas_jsx
    # Kiểm tra góc quay Top View đúng -90 độ
    assert "-90 * (Math.PI / 180)" in canvas_jsx
    # Kiểm tra góc quay Side View đúng +90 độ
    assert "90 * (Math.PI / 180)" in canvas_jsx

    stage_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "Góc nhìn SGK:" in stage_jsx
    assert "Phối Cảnh" in stage_jsx
    assert "Chiếu Đứng" in stage_jsx
    assert "Chiếu Bằng" in stage_jsx
    assert "Chiếu Cạnh" in stage_jsx
    assert "onCameraPreset?.('top')" in stage_jsx
    assert "onCameraPreset?.('front')" in stage_jsx
    assert "onCameraPreset?.('side')" in stage_jsx

    dock_jsx = (FRONTEND_DIR / "src" / "components" / "RightToolsDock.jsx").read_text(encoding="utf-8")
    assert "Góc nhìn chuẩn SGK" in dock_jsx
    assert "onCameraPreset?.('iso')" in dock_jsx
    assert "onCameraPreset?.('front')" in dock_jsx
    assert "onCameraPreset?.('top')" in dock_jsx
    assert "onCameraPreset?.('side')" in dock_jsx

    app_jsx = (FRONTEND_DIR / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "onCameraPreset={setCameraPreset}" in app_jsx
    assert "cameraPreset={cameraPreset}" in app_jsx


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
    from services.geometry_service import get_unfolded_net_topology

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


def test_task_13_3_unfolded_net_api_endpoint():
    """
    Task 13.3: Kiểm tra API endpoint GET /api/v1/geometry/unfolded-net.
    """
    resp = client.get("/api/v1/geometry/unfolded-net?polyhedron_type=pyramid_square&height=4.0&base_edge=4.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["polyhedron_type"] == "pyramid_square"
    assert len(data["faces"]) == 5
    assert "measurements" in data
    assert "formulas" in data
    assert data["measurements"]["base_area"] == 16.0


def test_task_13_3_frontend_unfolded_net_integration():
    """
    Task 13.3: Kiểm tra mã nguồn Frontend tích hợp chế độ xem Khai triển phẳng 2D:
    - UnfoldedNetViewer.jsx: Vẽ SVG tương tác, polygon các mảnh, đường nếp gấp, chú giải S_xq
    - PresentationStage.jsx: Nút toggle 'Khai Triển 2D' và khung hiển thị song song Side-by-Side 3D + 2D
    - RightToolsDock.jsx: Bảng hiển thị thông số Sxq, Stp và nút bật tắt chế độ song song
    - App.jsx: Quản lý state showUnfoldedNet đồng bộ hai chiều
    - geometryClient.js: Hàm tính toán cục bộ computeUnfoldedNetLocal và fetchUnfoldedNetRemote
    """
    viewer_file = FRONTEND_DIR / "src" / "components" / "UnfoldedNetViewer.jsx"
    assert viewer_file.exists()
    viewer_jsx = viewer_file.read_text(encoding="utf-8")
    assert "<svg" in viewer_jsx
    assert "polygon" in viewer_jsx
    assert "strokeDasharray" in viewer_jsx
    assert "Sxq (Xung quanh)" in viewer_jsx
    assert "S toàn phần" in viewer_jsx

    stage_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "UnfoldedNetViewer" in stage_jsx
    assert "Khai Triển 2D" in stage_jsx
    assert "activeShowUnfoldedNet" in stage_jsx

    dock_jsx = (FRONTEND_DIR / "src" / "components" / "RightToolsDock.jsx").read_text(encoding="utf-8")
    assert "Khai triển 2D (Net):" in dock_jsx
    assert "netMetrics" in dock_jsx

    app_jsx = (FRONTEND_DIR / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "showUnfoldedNet={showUnfoldedNet}" in app_jsx

    geom_client = (FRONTEND_DIR / "src" / "utils" / "geometryClient.js").read_text(encoding="utf-8")
    assert "computeUnfoldedNetLocal" in geom_client
    assert "fetchUnfoldedNetRemote" in geom_client


def test_task_13_4_vertex_labels_taxonomy():
    """
    Task 13.4: Kiểm tra danh mục tên các đỉnh (S, A, B, C, D...) và vai trò hình học SGK:
    1. Chóp tứ giác: S, A, B, C, D, O (6 đỉnh / điểm đặc biệt)
    2. Chóp tam giác: S, A, B, C, H (5 đỉnh / điểm đặc biệt)
    3. Lăng trụ tam giác: A, B, C, A', B', C' (6 đỉnh)
    4. Hình lập phương: A, B, C, D, A', B', C', D' (8 đỉnh)
    """
    from services.geometry_service import get_polyhedron_vertex_labels

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


def test_task_13_4_vertex_labels_api_endpoint():
    """
    Task 13.4: Kiểm tra API endpoint GET /api/v1/geometry/vertex-labels.
    """
    resp = client.get("/api/v1/geometry/vertex-labels?polyhedron_type=pyramid_square")
    assert resp.status_code == 200
    data = resp.json()
    assert data["polyhedron_type"] == "pyramid_square"
    assert data["vertex_count"] == 6
    assert "S" in data["vertex_labels"]
    assert len(data["vertices_info"]) == 6


def test_task_13_4_frontend_vertex_labels_toggle_integration():
    """
    Task 13.4: Kiểm tra mã nguồn Frontend tích hợp nút bật/tắt tên các đỉnh:
    - PresentationStage.jsx: Nút toggle 'Tên Đỉnh' với icon Tag và active highlight
    - PresentationStage.jsx: Truyền showVertexLabels xuống cả ThreeCanvas và UnfoldedNetViewer
    - RightToolsDock.jsx: Checkbox bật/tắt tên đỉnh và danh sách chip nhãn đỉnh (vertexChipList)
    - ThreeCanvas.jsx: getOrCreateLabelTexture tạo font Times New Roman serif độ phân giải 128x128 Retina
    - ThreeCanvas.jsx: Tách biệt nhãn trục Oxyz (addAxisLabelSprite) và nhãn đỉnh (addVertexSprite)
    - UnfoldedNetViewer.jsx: Ẩn/hiện tên các đỉnh theo prop showVertexLabels
    """
    stage_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "Tên Đỉnh" in stage_jsx
    assert "setShowVertexLabels" in stage_jsx
    assert "showVertexLabels={showVertexLabels}" in stage_jsx

    dock_jsx = (FRONTEND_DIR / "src" / "components" / "RightToolsDock.jsx").read_text(encoding="utf-8")
    assert "vertexChipList" in dock_jsx
    assert "Hiện tên các đỉnh" in dock_jsx

    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")
    assert "if (!showVertexLabels) return;" in canvas_jsx
    assert "Times New Roman" in canvas_jsx
    assert "addAxisLabelSprite" in canvas_jsx

    viewer_jsx = (FRONTEND_DIR / "src" / "components" / "UnfoldedNetViewer.jsx").read_text(encoding="utf-8")
    assert "showVertexLabels" in viewer_jsx
    assert "{showVertexLabels && faces.map" in viewer_jsx


def test_task_13_5_raycasting_hidden_surface_removal_algorithm():
    """
    Task 13.5: Kiểm thử thuật toán Möller–Trumbore Raycasting & Khử mặt khuất (Hidden Surface Removal):
    1. Bắn tia từ Camera (6, 7, 9) tới midpoint các cạnh hình chóp S.ABCD:
       - 3 cạnh khuất: AB, AD, SA -> is_occluded == True, render_style == 'dashed'
       - 5 cạnh thấy: BC, CD, SB, SC, SD -> is_occluded == False, render_style == 'solid'
    2. API GET /api/v1/geometry/raycast-occlusion trả về kết quả 200 OK
    """
    from services.geometry_service import compute_hidden_surface_raycasting

    # 1. Chóp tứ giác
    res_sq = compute_hidden_surface_raycasting("pyramid_square", camera_position=(6.0, 7.0, 9.0))
    assert res_sq["total_edges"] == 8
    assert res_sq["occluded_count"] == 3
    assert res_sq["visible_count"] == 5

    status_map = {tuple(e["edge"]): e["render_style"] for e in res_sq["edges_status"]}
    assert status_map[("A", "B")] == "dashed"
    assert status_map[("D", "A")] == "dashed"
    assert status_map[("S", "A")] == "dashed"
    assert status_map[("B", "C")] == "solid"
    assert status_map[("S", "C")] == "solid"

    # 2. Khối lập phương
    res_cube = compute_hidden_surface_raycasting("cube", camera_position=(6.0, 7.0, 9.0))
    assert res_cube["total_edges"] == 12
    assert res_cube["occluded_count"] == 3
    cube_map = {tuple(e["edge"]): e["render_style"] for e in res_cube["edges_status"]}
    assert cube_map[("A", "B")] == "dashed"
    assert cube_map[("D", "A")] == "dashed"
    assert cube_map[("A", "A'")] == "dashed"

    # 3. API endpoint
    resp = client.get("/api/v1/geometry/raycast-occlusion?polyhedron_type=pyramid_square&cam_x=6.0&cam_y=7.0&cam_z=9.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["occluded_count"] == 3
    assert data["visible_count"] == 5


def test_task_13_5_definition_of_done_top_view_and_hidden_lines():
    """
    Task 13.5: Nghiệm thu Definition of Done (DoD) Ngày 13:
    'Bấm nút Hình chiếu bằng -> Khối chóp tự xoay về góc nhìn thẳng từ trên xuống đáy;
    các cạnh khuất hiển thị nét đứt rõ ràng.'

    Kiểm tra các tiêu chí kỹ thuật:
    1. Preset 'top' có góc Pitch -90° (tương đương -Math.PI / 2) và Yaw 0°
    2. Render loop sử dụng Lerp Damping (hệ số 0.20) mượt mà 60 FPS
    3. Cạnh khuất sử dụng LineDashedMaterial với dashSize 0.16, gapSize 0.10, renderOrder 2
    4. PresentationStage.jsx có nút 'Chiếu Bằng' kích hoạt onCameraPreset('top')
    5. Nút 'Nét Đứt' điều khiển hiển thị cạnh khuất
    6. Bản vẽ Khai Triển Phẳng 2D hiển thị song song khi bật 'Khai Triển 2D'
    """
    canvas_jsx = (FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx").read_text(encoding="utf-8")

    # 1. Preset Top View xoay thẳng góc nhìn từ trên xuống đáy (-90 độ)
    assert "cameraPreset === 'top'" in canvas_jsx
    assert "-90 * (Math.PI / 180)" in canvas_jsx

    # 2. Lerp damping mượt mà
    assert "cur.rotX += (target.rotX - cur.rotX) * factor" in canvas_jsx
    assert "const factor = 0.20" in canvas_jsx

    # 3. LineDashedMaterial và computeLineDistances
    assert "LineDashedMaterial" in canvas_jsx
    assert "dashSize: 0.16" in canvas_jsx
    assert "gapSize: 0.10" in canvas_jsx
    assert "line.computeLineDistances()" in canvas_jsx
    assert "line.renderOrder = 2" in canvas_jsx

    # 4. PresentationStage.jsx có nút Chiếu Bằng
    stage_jsx = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "Chiếu Bằng" in stage_jsx
    assert "onCameraPreset?.('top')" in stage_jsx

    # 5. Nút Nét Đứt
    assert "Nét Đứt" in stage_jsx
    assert "setShowHiddenLines" in stage_jsx

    # 6. Bản vẽ Khai Triển Phẳng 2D
    assert "Khai Triển 2D" in stage_jsx
    assert "UnfoldedNetViewer" in stage_jsx




