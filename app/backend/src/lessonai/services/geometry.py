r"""
Geometry Service — Module Tính Toán Hình Học Không Gian Động & Tham Số Hóa 3D (Task 12.2)
Tài liệu tham chiếu: docs/Ke_Hoach_Phat_Trien.pdf (Trang 6 - Ngày 12).
Cung cấp các giải thuật toán học tọa độ giải tích trong không gian Descartes Oxyz:
- Cập nhật tọa độ đỉnh chóp S(0, 0, h) và các đỉnh đáy theo thời gian thực khi kéo thanh trượt
- Tính toán chính xác diện tích đáy S_đáy, chiều cao h, thể tích V = (1/3) * S_đáy * h
- Đảm bảo tính nhất quán toán học theo chuẩn SGK GDPT 2018
"""

import math
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Vertex3D(BaseModel):
    """Tọa độ một điểm trong không gian 3 chiều Descartes Oxyz"""
    x: float = Field(description="Hoành độ x (trục Ox)")
    y: float = Field(description="Tung độ y (trục Oy)")
    z: float = Field(description="Cao độ z (trục Oz)")

    def to_tuple(self):
        return (self.x, self.y, self.z)


class ParametricGeometryRequest(BaseModel):
    """Dữ liệu yêu cầu cập nhật tham số hình học từ thanh trượt UI"""
    polyhedron_type: str = Field(
        default="pyramid_square",
        description="Loại khối: pyramid_square, pyramid_triangle, prism_triangle, cube"
    )
    height: float = Field(
        default=4.0,
        ge=0.5,
        le=20.0,
        description="Chiều cao h của khối đa diện (thanh trượt 1 đến 10)"
    )
    base_edge: float = Field(
        default=4.0,
        ge=0.5,
        le=20.0,
        description="Cạnh đáy a của khối đa diện (thanh trượt 1 đến 8)"
    )


class ParametricGeometryResponse(BaseModel):
    """Kết quả tính toán tọa độ và các đại lượng hình học theo thời gian thực"""
    polyhedron_type: str
    height: float
    base_edge: float
    apex_coordinates: Vertex3D = Field(
        description="Tọa độ đỉnh chóp S(0, 0, h) trong hệ trục chuẩn hóa SGK"
    )
    vertices: Dict[str, Vertex3D] = Field(
        description="Danh sách tọa độ các đỉnh trong không gian Descartes Oxyz"
    )
    measurements: Dict[str, float] = Field(
        description="Các đại lượng hình học: diện tích đáy, chiều cao, thể tích, độ dài cạnh bên"
    )


def calculate_parametric_geometry(
    polyhedron_type: str = "pyramid_square",
    height: float = 4.0,
    base_edge: float = 4.0
) -> ParametricGeometryResponse:
    """
    Thuật toán tính toán tọa độ các đỉnh và thể tích khối đa diện theo tham số (a, h).
    Chuẩn hóa theo phương pháp tọa độ hóa SGK Toán 12:
    - Gốc tọa độ O(0, 0, 0)
    - Trục Oz thẳng đứng, đỉnh chóp S có tọa độ (0, 0, h)
    """
    h = max(0.5, min(20.0, float(height)))
    a = max(0.5, min(20.0, float(base_edge)))
    norm_type = str(polyhedron_type or "pyramid_square").lower().strip()

    vertices: Dict[str, Vertex3D] = {}
    measurements: Dict[str, float] = {}

    # 1. HÌNH CHÓP TỨ GIÁC S.ABCD (SA ⊥ Đáy ABCD, đáy hình vuông cạnh a)
    if norm_type in ("pyramid_square", "rectangular_pyramid", "pyramid4"):
        # Trong hệ trục tọa độ SGK với A là gốc tọa độ (0, 0, 0):
        # A(0, 0, 0), B(a, 0, 0) trên Ox, D(0, a, 0) trên Oy, C(a, a, 0)
        # SA ⊥ (ABCD) => Đỉnh S nằm trên trục Oz tại (0, 0, h)
        vertices["A"] = Vertex3D(x=0.0, y=0.0, z=0.0)
        vertices["B"] = Vertex3D(x=round(a, 4), y=0.0, z=0.0)
        vertices["C"] = Vertex3D(x=round(a, 4), y=round(a, 4), z=0.0)
        vertices["D"] = Vertex3D(x=0.0, y=round(a, 4), z=0.0)
        vertices["S"] = Vertex3D(x=0.0, y=0.0, z=round(h, 4))
        vertices["O"] = Vertex3D(x=round(a / 2, 4), y=round(a / 2, 4), z=0.0)

        apex = Vertex3D(x=0.0, y=0.0, z=round(h, 4))
        base_area = a * a
        volume = (1.0 / 3.0) * base_area * h
        diag = a * math.sqrt(2.0)
        sc = math.sqrt(h * h + 2.0 * a * a)

        measurements = {
            "base_area": round(base_area, 4),
            "height": round(h, 4),
            "volume": round(volume, 4),
            "lateral_edge_sa": round(h, 4),
            "lateral_edge_sc": round(sc, 4),
            "base_diagonal": round(diag, 4)
        }

    # 2. HÌNH CHÓP TAM GIÁC S.ABC (SA ⊥ Đáy ABC)
    elif norm_type in ("pyramid_triangle", "triangular_pyramid", "pyramid3", "tetrahedron"):
        # Đáy tam giác vuông cân tại A với cạnh góc vuông a:
        # A(0, 0, 0), B(a, 0, 0) trên Ox, C(0, a, 0) trên Oy
        # SA ⊥ (ABC) => S(0, 0, h)
        vertices["A"] = Vertex3D(x=0.0, y=0.0, z=0.0)
        vertices["B"] = Vertex3D(x=round(a, 4), y=0.0, z=0.0)
        vertices["C"] = Vertex3D(x=0.0, y=round(a, 4), z=0.0)
        vertices["S"] = Vertex3D(x=0.0, y=0.0, z=round(h, 4))

        # Điểm chân đường cao H trên BC (AH ⊥ BC)
        # Vector BC = (-a, a, 0), H là trung điểm BC => H(a/2, a/2, 0)
        vertices["H"] = Vertex3D(x=round(a / 2, 4), y=round(a / 2, 4), z=0.0)

        apex = Vertex3D(x=0.0, y=0.0, z=round(h, 4))
        base_area = 0.5 * a * a
        volume = (1.0 / 3.0) * base_area * h
        ah_len = (a * math.sqrt(2.0)) / 2.0
        sh_len = math.sqrt(h * h + ah_len * ah_len)

        measurements = {
            "base_area": round(base_area, 4),
            "height": round(h, 4),
            "volume": round(volume, 4),
            "lateral_edge_sa": round(h, 4),
            "altitude_ah": round(ah_len, 4),
            "slant_height_sh": round(sh_len, 4)
        }

    # 3. LĂNG TRỤ ĐỨNG TAM GIÁC ABC.A'B'C'
    elif norm_type in ("prism_triangle", "triangular_prism", "prism"):
        vertices["A"] = Vertex3D(x=0.0, y=0.0, z=0.0)
        vertices["B"] = Vertex3D(x=round(a, 4), y=0.0, z=0.0)
        vertices["C"] = Vertex3D(x=0.0, y=round(a, 4), z=0.0)
        vertices["A'"] = Vertex3D(x=0.0, y=0.0, z=round(h, 4))
        vertices["B'"] = Vertex3D(x=round(a, 4), y=0.0, z=round(h, 4))
        vertices["C'"] = Vertex3D(x=0.0, y=round(a, 4), z=round(h, 4))

        apex = Vertex3D(x=0.0, y=0.0, z=round(h, 4))
        base_area = 0.5 * a * a
        volume = base_area * h

        measurements = {
            "base_area": round(base_area, 4),
            "height": round(h, 4),
            "volume": round(volume, 4),
            "lateral_edge": round(h, 4)
        }

    # 4. HÌNH LẬP PHƯƠNG ABCD.A'B'C'D' (cạnh a = h)
    else:
        actual_a = a
        vertices["A"] = Vertex3D(x=0.0, y=0.0, z=0.0)
        vertices["B"] = Vertex3D(x=round(actual_a, 4), y=0.0, z=0.0)
        vertices["C"] = Vertex3D(x=round(actual_a, 4), y=round(actual_a, 4), z=0.0)
        vertices["D"] = Vertex3D(x=0.0, y=round(actual_a, 4), z=0.0)
        vertices["A'"] = Vertex3D(x=0.0, y=0.0, z=round(actual_a, 4))
        vertices["B'"] = Vertex3D(x=round(actual_a, 4), y=0.0, z=round(actual_a, 4))
        vertices["C'"] = Vertex3D(x=round(actual_a, 4), y=round(actual_a, 4), z=round(actual_a, 4))
        vertices["D'"] = Vertex3D(x=0.0, y=round(actual_a, 4), z=round(actual_a, 4))

        apex = Vertex3D(x=0.0, y=0.0, z=round(actual_a, 4))
        base_area = actual_a * actual_a
        volume = actual_a * actual_a * actual_a
        diag = actual_a * math.sqrt(3.0)

        measurements = {
            "base_area": round(base_area, 4),
            "height": round(actual_a, 4),
            "volume": round(volume, 4),
            "space_diagonal": round(diag, 4),
            "total_surface_area": round(6.0 * base_area, 4)
        }

    return ParametricGeometryResponse(
        polyhedron_type=norm_type,
        height=round(h, 4),
        base_edge=round(a, 4),
        apex_coordinates=apex,
        vertices=vertices,
        measurements=measurements
    )


def get_apex_coordinates(height: float) -> Dict:
    """Trả về tọa độ đỉnh chóp S(0, 0, h) theo ký hiệu giải tích Descartes SGK"""
    h_val = round(max(0.5, min(20.0, float(height))), 4)
    return {
        "apex_name": "S",
        "coordinates": {"x": 0.0, "y": 0.0, "z": h_val},
        "descartes_notation": f"S(0.0, 0.0, {h_val})"
    }


def get_polyhedron_edge_topology(polyhedron_type: str = "pyramid_square") -> Dict:
    """
    Task 13.1: Xác định cấu trúc cạnh thấy (nét liền) và cạnh khuất (nét đứt) chuẩn SGK GDPT 2018.
    Quy chuẩn SGK:
    - Cạnh khuất (hidden_edges): Bị các mặt phẳng của khối che khuất khỏi góc nhìn quan sát chuẩn -> vẽ Nét Đứt.
    - Cạnh thấy (visible_edges): Nằm ở phía trước/bên ngoài tầm nhìn -> vẽ Nét Liền.
    - Cạnh phụ trợ (auxiliary_dashed_edges): Đường chéo đáy, đường cao phụ bên trong khối -> vẽ Nét Đứt.
    """
    norm_type = str(polyhedron_type or "pyramid_square").lower().strip()

    if norm_type in ("pyramid_square", "rectangular_pyramid", "pyramid4", "pyramid"):
        return {
            "polyhedron_type": "pyramid_square",
            "name": "Hình Chóp Tứ Giác S.ABCD (SA ⊥ Đáy)",
            "hidden_edges": [["A", "B"], ["A", "D"], ["S", "A"]],
            "visible_edges": [["B", "C"], ["C", "D"], ["S", "B"], ["S", "C"], ["S", "D"]],
            "auxiliary_dashed_edges": [["A", "C"], ["B", "D"]],
            "total_edges_count": 8,
            "hidden_count": 3,
            "visible_count": 5,
            "rule": "SA vuông góc đáy, chân A ở góc sau-trái nên 3 cạnh xuất phát từ A (AB, AD, SA) là cạnh khuất nét đứt."
        }
    elif norm_type in ("pyramid_triangle", "triangular_pyramid", "pyramid3", "tetrahedron"):
        return {
            "polyhedron_type": "pyramid_triangle",
            "name": "Hình Chóp Tam Giác S.ABC (SA ⊥ Đáy)",
            "hidden_edges": [["A", "B"], ["A", "C"], ["S", "A"]],
            "visible_edges": [["B", "C"], ["S", "B"], ["S", "C"], ["S", "H"]],
            "auxiliary_dashed_edges": [["A", "H"]],
            "total_edges_count": 6,
            "hidden_count": 3,
            "visible_count": 3,
            "rule": "SA vuông góc đáy, AB và AC nằm ở phía sau nên AB, AC, SA là các cạnh khuất nét đứt; AH là đường cao đáy nét đứt."
        }
    elif norm_type in ("prism_triangle", "triangular_prism", "prism"):
        return {
            "polyhedron_type": "prism_triangle",
            "name": "Lăng Trụ Đứng Tam Giác ABC.A'B'C'",
            "hidden_edges": [["A", "B"], ["A", "C"], ["A", "A'"]],
            "visible_edges": [["B", "C"], ["A'", "B'"], ["B'", "C'"], ["C'", "A'"], ["B", "B'"], ["C", "C'"]],
            "auxiliary_dashed_edges": [],
            "total_edges_count": 9,
            "hidden_count": 3,
            "visible_count": 6,
            "rule": "Cạnh bên AA' và hai cạnh đáy AB, AC khuất phía sau vẽ nét đứt; các cạnh còn lại vẽ nét liền."
        }
    else:  # cube / box
        return {
            "polyhedron_type": "cube",
            "name": "Hình Lập Phương ABCD.A'B'C'D'",
            "hidden_edges": [["A", "B"], ["A", "D"], ["A", "A'"]],
            "visible_edges": [
                ["B", "C"], ["C", "D"],
                ["A'", "B'"], ["B'", "C'"], ["C'", "D'"], ["D'", "A'"],
                ["B", "B'"], ["C", "C'"], ["D", "D'"]
            ],
            "auxiliary_dashed_edges": [["A", "C"]],
            "total_edges_count": 12,
            "hidden_count": 3,
            "visible_count": 9,
            "rule": "Đỉnh A ở góc sau-dưới-trái, 3 cạnh AB, AD, AA' hội tụ tại A là các cạnh khuất nét đứt; 9 cạnh còn lại vẽ nét liền."
        }


# ==============================================================================
# TASK 13.3: HÌNH KHAI TRIỂN PHẲNG 2D (UNFOLDED NET) & DIỆN TÍCH XUNG QUANH S_xq
# ==============================================================================

class Point2D(BaseModel):
    """Tọa độ 2 chiều (x, y) trên mặt phẳng khai triển"""
    x: float
    y: float

    def to_tuple(self):
        return (self.x, self.y)


class UnfoldedFace(BaseModel):
    """Một mảnh mặt phẳng trong bản vẽ khai triển 2D (Net Face)"""
    id: str
    name: str
    face_type: str = "lateral"  # "base" | "lateral"
    points: List[Point2D]
    labels: List[str]
    area: float
    area_formula: str
    fill_color: str
    stroke_color: str


class UnfoldedNetResponse(BaseModel):
    """Dữ liệu bản vẽ khai triển phẳng 2D phục vụ trực quan hóa diện tích xung quanh S_xq"""
    polyhedron_type: str
    name: str
    height: float
    base_edge: float
    faces: List[UnfoldedFace]
    fold_lines: List[List[Point2D]]
    bounding_box: Dict[str, float]
    measurements: Dict[str, float]
    formulas: Dict[str, str]


def get_unfolded_net_topology(
    polyhedron_type: str = "pyramid_square",
    height: float = 4.0,
    base_edge: float = 4.0
) -> Dict[str, Any]:
    """
    Task 13.3: Tính toán tọa độ bản vẽ Khai Triển Phẳng 2D (Unfolded Net) song song với hình 3D.
    Mục đích sư phạm:
    - Trực quan hóa diện tích xung quanh S_xq = tổng diện tích các mặt bên được bung phẳng.
    - Trực quan hóa diện tích toàn phần S_tp = S_xq + diện tích đáy.
    - Thể hiện rõ các nếp gấp (fold lines) nét đứt và các đường cắt biên (cut boundaries) nét liền.
    """
    h = max(0.5, min(20.0, float(height)))
    a = max(0.5, min(20.0, float(base_edge)))
    norm_type = str(polyhedron_type or "pyramid_square").lower().strip()

    faces: List[Dict[str, Any]] = []
    fold_lines: List[List[Dict[str, float]]] = []
    measurements: Dict[str, float] = {}
    formulas: Dict[str, str] = {}
    all_points: List[Dict[str, float]] = []

    # 1. HÌNH CHÓP TỨ GIÁC S.ABCD (SA ⊥ Đáy, đáy hình vuông cạnh a)
    if norm_type in ("pyramid_square", "rectangular_pyramid", "pyramid4", "pyramid"):
        name = "Hình Khai Triển Chóp Tứ Giác S.ABCD (SA ⊥ Đáy)"
        # Đáy vuông ABCD ở tâm: tọa độ từ -a/2 đến a/2
        half_a = a / 2.0
        pA = {"x": round(-half_a, 3), "y": round(-half_a, 3)}
        pB = {"x": round(half_a, 3), "y": round(-half_a, 3)}
        pC = {"x": round(half_a, 3), "y": round(half_a, 3)}
        pD = {"x": round(-half_a, 3), "y": round(half_a, 3)}

        base_area = a * a
        faces.append({
            "id": "face_base",
            "name": "Mặt Đáy ABCD (Hình vuông)",
            "face_type": "base",
            "points": [pA, pB, pC, pD],
            "labels": ["A", "B", "C", "D"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = a^2",
            "fill_color": "rgba(245, 158, 11, 0.22)",  # Amber
            "stroke_color": "#f59e0b"
        })

        # Mặt bên 1: SAB (vuông tại A, gắn với cạnh AB)
        # S1 bung thẳng xuống từ A: (x = -a/2, y = -a/2 - h)
        pS1 = {"x": round(-half_a, 3), "y": round(-half_a - h, 3)}
        s_sab = 0.5 * a * h
        faces.append({
            "id": "face_sab",
            "name": "Mặt Bên SAB (Tam giác vuông tại A)",
            "face_type": "lateral",
            "points": [pA, pB, pS1],
            "labels": ["A", "B", "S₁"],
            "area": round(s_sab, 3),
            "area_formula": "S_{SAB} = \\frac{1}{2} a \\cdot h",
            "fill_color": "rgba(59, 130, 246, 0.20)",  # Blue
            "stroke_color": "#3b82f6"
        })

        # Mặt bên 2: SBC (vuông tại B, BC ⊥ SB với SB = sqrt(a^2 + h^2))
        # S2 bung sang phải từ B: (x = a/2 + sqrt(a^2 + h^2), y = -a/2)
        sb_len = math.sqrt(a * a + h * h)
        pS2 = {"x": round(half_a + sb_len, 3), "y": round(-half_a, 3)}
        s_sbc = 0.5 * a * sb_len
        faces.append({
            "id": "face_sbc",
            "name": "Mặt Bên SBC (Tam giác vuông tại B)",
            "face_type": "lateral",
            "points": [pB, pC, pS2],
            "labels": ["B", "C", "S₂"],
            "area": round(s_sbc, 3),
            "area_formula": "S_{SBC} = \\frac{1}{2} a \\sqrt{a^2 + h^2}",
            "fill_color": "rgba(16, 185, 129, 0.20)",  # Emerald
            "stroke_color": "#10b981"
        })

        # Mặt bên 3: SCD (vuông tại D, CD ⊥ SD với SD = sqrt(a^2 + h^2))
        # S3 bung lên trên từ D: (x = -a/2, y = a/2 + sqrt(a^2 + h^2))
        pS3 = {"x": round(-half_a, 3), "y": round(half_a + sb_len, 3)}
        s_scd = 0.5 * a * sb_len
        faces.append({
            "id": "face_scd",
            "name": "Mặt Bên SCD (Tam giác vuông tại D)",
            "face_type": "lateral",
            "points": [pD, pC, pS3],
            "labels": ["D", "C", "S₃"],
            "area": round(s_scd, 3),
            "area_formula": "S_{SCD} = \\frac{1}{2} a \\sqrt{a^2 + h^2}",
            "fill_color": "rgba(139, 92, 246, 0.20)",  # Violet
            "stroke_color": "#8b5cf6"
        })

        # Mặt bên 4: SDA (vuông tại A, gắn với cạnh DA)
        # S4 bung sang trái từ A: (x = -a/2 - h, y = -a/2)
        pS4 = {"x": round(-half_a - h, 3), "y": round(-half_a, 3)}
        s_sda = 0.5 * a * h
        faces.append({
            "id": "face_sda",
            "name": "Mặt Bên SDA (Tam giác vuông tại A)",
            "face_type": "lateral",
            "points": [pD, pA, pS4],
            "labels": ["D", "A", "S₄"],
            "area": round(s_sda, 3),
            "area_formula": "S_{SDA} = \\frac{1}{2} a \\cdot h",
            "fill_color": "rgba(236, 72, 153, 0.20)",  # Pink
            "stroke_color": "#ec4899"
        })

        # Nếp gấp (Fold lines): 4 cạnh đáy
        fold_lines = [
            [pA, pB], [pB, pC], [pC, pD], [pD, pA]
        ]

        lateral_area = 2.0 * s_sab + 2.0 * s_sbc
        total_area = lateral_area + base_area

        measurements = {
            "base_area": round(base_area, 3),
            "lateral_area": round(lateral_area, 3),
            "total_area": round(total_area, 3),
            "slant_height": round(sb_len, 3)
        }
        formulas = {
            "latex_sxq": "S_{xq} = S_{SAB} + S_{SBC} + S_{SCD} + S_{SDA} = ah + a\\sqrt{a^2 + h^2}",
            "latex_stp": "S_{tp} = S_{xq} + S_{đáy} = ah + a\\sqrt{a^2 + h^2} + a^2",
            "explanation": "Hình chóp có 4 tam giác mặt bên gấp vào đáy hình vuông ABCD. 4 đỉnh S₁, S₂, S₃, S₄ chụm lại thành đỉnh S(0,0,h)."
        }

    # 2. LĂNG TRỤ ĐỨNG TAM GIÁC ABC.A'B'C' (Đáy tam giác vuông cân tại A)
    elif norm_type in ("prism_triangle", "triangular_prism", "prism"):
        name = "Hình Khai Triển Lăng Trụ Đứng Tam Giác ABC.A'B'C'"
        c = a * math.sqrt(2.0)  # Cạnh huyền đáy
        base_area = 0.5 * a * a

        # Mặt bên 1: ABB'A' [0, a] x [0, h]
        f1_p = [{"x": 0.0, "y": 0.0}, {"x": round(a, 3), "y": 0.0}, {"x": round(a, 3), "y": round(h, 3)}, {"x": 0.0, "y": round(h, 3)}]
        faces.append({
            "id": "face_lat1",
            "name": "Mặt Bên ABB'A' (Hình chữ nhật a x h)",
            "face_type": "lateral",
            "points": f1_p,
            "labels": ["A", "B", "B'", "A'"],
            "area": round(a * h, 3),
            "area_formula": "S_1 = a \\cdot h",
            "fill_color": "rgba(59, 130, 246, 0.20)",
            "stroke_color": "#3b82f6"
        })

        # Mặt bên 2: ACC'A' [a, 2a] x [0, h]
        f2_p = [{"x": round(a, 3), "y": 0.0}, {"x": round(2.0 * a, 3), "y": 0.0}, {"x": round(2.0 * a, 3), "y": round(h, 3)}, {"x": round(a, 3), "y": round(h, 3)}]
        faces.append({
            "id": "face_lat2",
            "name": "Mặt Bên ACC'A' (Hình chữ nhật a x h)",
            "face_type": "lateral",
            "points": f2_p,
            "labels": ["A", "C", "C'", "A'"],
            "area": round(a * h, 3),
            "area_formula": "S_2 = a \\cdot h",
            "fill_color": "rgba(16, 185, 129, 0.20)",
            "stroke_color": "#10b981"
        })

        # Mặt bên 3: BCC'B' [2a, 2a + c] x [0, h]
        f3_p = [{"x": round(2.0 * a, 3), "y": 0.0}, {"x": round(2.0 * a + c, 3), "y": 0.0}, {"x": round(2.0 * a + c, 3), "y": round(h, 3)}, {"x": round(2.0 * a, 3), "y": round(h, 3)}]
        faces.append({
            "id": "face_lat3",
            "name": "Mặt Bên BCC'B' (Hình chữ nhật c x h)",
            "face_type": "lateral",
            "points": f3_p,
            "labels": ["B", "C", "C'", "B'"],
            "area": round(c * h, 3),
            "area_formula": "S_3 = a\\sqrt{2} \\cdot h",
            "fill_color": "rgba(139, 92, 246, 0.20)",
            "stroke_color": "#8b5cf6"
        })

        # Đáy dưới ABC (gắn dưới cạnh AB của mặt 1)
        base_bot_p = [{"x": 0.0, "y": 0.0}, {"x": round(a, 3), "y": 0.0}, {"x": 0.0, "y": round(-a, 3)}]
        faces.append({
            "id": "face_base_bottom",
            "name": "Mặt Đáy Dưới ABC (Tam giác vuông cân tại A)",
            "face_type": "base",
            "points": base_bot_p,
            "labels": ["A", "B", "C"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = \\frac{1}{2} a^2",
            "fill_color": "rgba(245, 158, 11, 0.22)",
            "stroke_color": "#f59e0b"
        })

        # Đáy trên A'B'C' (gắn trên cạnh A'B' của mặt 1)
        base_top_p = [{"x": 0.0, "y": round(h, 3)}, {"x": round(a, 3), "y": round(h, 3)}, {"x": 0.0, "y": round(h + a, 3)}]
        faces.append({
            "id": "face_base_top",
            "name": "Mặt Đáy Trên A'B'C' (Tam giác vuông cân tại A')",
            "face_type": "base",
            "points": base_top_p,
            "labels": ["A'", "B'", "C'"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = \\frac{1}{2} a^2",
            "fill_color": "rgba(245, 158, 11, 0.22)",
            "stroke_color": "#f59e0b"
        })

        # Nếp gấp: Cạnh giữa mặt 1-2, 2-3 và các mép đáy
        fold_lines = [
            [{"x": round(a, 3), "y": 0.0}, {"x": round(a, 3), "y": round(h, 3)}],
            [{"x": round(2.0 * a, 3), "y": 0.0}, {"x": round(2.0 * a, 3), "y": round(h, 3)}],
            [{"x": 0.0, "y": 0.0}, {"x": round(a, 3), "y": 0.0}],
            [{"x": 0.0, "y": round(h, 3)}, {"x": round(a, 3), "y": round(h, 3)}]
        ]

        lateral_area = (2.0 * a + c) * h
        total_area = lateral_area + 2.0 * base_area
        measurements = {
            "base_area": round(base_area, 3),
            "lateral_area": round(lateral_area, 3),
            "total_area": round(total_area, 3),
            "perimeter_base": round(2.0 * a + c, 3)
        }
        formulas = {
            "latex_sxq": "S_{xq} = C_{đáy} \\cdot h = (2a + a\\sqrt{2}) \\cdot h",
            "latex_stp": "S_{tp} = S_{xq} + 2S_{đáy} = (2a + a\\sqrt{2})h + a^2",
            "explanation": "Khai triển gồm 1 dải chữ nhật kích thước C_đáy x h và 2 đáy tam giác ở hai biên."
        }

    # 3. HÌNH LẬP PHƯƠNG ABCD.A'B'C'D' (Cube cạnh a = h)
    elif norm_type in ("cube", "cube_box", "box"):
        name = "Hình Khai Triển Hình Lập Phương ABCD.A'B'C'D'"
        actual_a = a
        base_area = actual_a * actual_a

        # 4 mặt ngang: từ x = -a đến x = 3a, y = [0, a]
        labels_map = [
            ("face_left", "Mặt Trái ADD'A'", -actual_a, 0.0, ["A", "D", "D'", "A'"]),
            ("face_front", "Mặt Trước ABB'A'", 0.0, actual_a, ["A", "B", "B'", "A'"]),
            ("face_right", "Mặt Phải BCC'B'", actual_a, 2.0 * actual_a, ["B", "C", "C'", "B'"]),
            ("face_back", "Mặt Sau CDD'C'", 2.0 * actual_a, 3.0 * actual_a, ["C", "D", "D'", "C'"])
        ]
        for f_id, f_name, x0, x1, lbs in labels_map:
            faces.append({
                "id": f_id,
                "name": f_name,
                "face_type": "lateral",
                "points": [
                    {"x": round(x0, 3), "y": 0.0},
                    {"x": round(x1, 3), "y": 0.0},
                    {"x": round(x1, 3), "y": round(actual_a, 3)},
                    {"x": round(x0, 3), "y": round(actual_a, 3)}
                ],
                "labels": lbs,
                "area": round(base_area, 3),
                "area_formula": "S_{mặt} = a^2",
                "fill_color": "rgba(59, 130, 246, 0.20)",
                "stroke_color": "#3b82f6"
            })

        # Đáy trên A'B'C'D' (nằm trên mặt trước)
        faces.append({
            "id": "face_top",
            "name": "Mặt Đáy Trên A'B'C'D'",
            "face_type": "base",
            "points": [
                {"x": 0.0, "y": round(actual_a, 3)},
                {"x": round(actual_a, 3), "y": round(actual_a, 3)},
                {"x": round(actual_a, 3), "y": round(2.0 * actual_a, 3)},
                {"x": 0.0, "y": round(2.0 * actual_a, 3)}
            ],
            "labels": ["A'", "B'", "C'", "D'"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = a^2",
            "fill_color": "rgba(245, 158, 11, 0.25)",
            "stroke_color": "#f59e0b"
        })

        # Đáy dưới ABCD (nằm dưới mặt trước)
        faces.append({
            "id": "face_bottom",
            "name": "Mặt Đáy Dưới ABCD",
            "face_type": "base",
            "points": [
                {"x": 0.0, "y": round(-actual_a, 3)},
                {"x": round(actual_a, 3), "y": round(-actual_a, 3)},
                {"x": round(actual_a, 3), "y": 0.0},
                {"x": 0.0, "y": 0.0}
            ],
            "labels": ["A", "B", "C", "D"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = a^2",
            "fill_color": "rgba(245, 158, 11, 0.25)",
            "stroke_color": "#f59e0b"
        })

        fold_lines = [
            [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": round(actual_a, 3)}],
            [{"x": round(actual_a, 3), "y": 0.0}, {"x": round(actual_a, 3), "y": round(actual_a, 3)}],
            [{"x": round(2.0 * actual_a, 3), "y": 0.0}, {"x": round(2.0 * actual_a, 3), "y": round(actual_a, 3)}],
            [{"x": 0.0, "y": 0.0}, {"x": round(actual_a, 3), "y": 0.0}],
            [{"x": 0.0, "y": round(actual_a, 3)}, {"x": round(actual_a, 3), "y": round(actual_a, 3)}]
        ]

        lateral_area = 4.0 * base_area
        total_area = 6.0 * base_area
        measurements = {
            "base_area": round(base_area, 3),
            "lateral_area": round(lateral_area, 3),
            "total_area": round(total_area, 3)
        }
        formulas = {
            "latex_sxq": "S_{xq} = 4 \\cdot a^2",
            "latex_stp": "S_{tp} = 6 \\cdot a^2",
            "explanation": "Khai triển dạng chữ Thập gồm 4 mặt xung quanh và 2 mặt đáy vuông bằng nhau."
        }

    # 4. HÌNH CHÓP TAM GIÁC S.ABC (SA ⊥ Đáy vuông cân tại A)
    else:
        name = "Hình Khai Triển Chóp Tam Giác S.ABC (SA ⊥ Đáy)"
        base_area = 0.5 * a * a

        # Đáy ABC: A(0,0), B(a,0), C(0,a)
        pA = {"x": 0.0, "y": 0.0}
        pB = {"x": round(a, 3), "y": 0.0}
        pC = {"x": 0.0, "y": round(a, 3)}
        faces.append({
            "id": "face_base",
            "name": "Mặt Đáy ABC (Tam giác vuông cân tại A)",
            "face_type": "base",
            "points": [pA, pB, pC],
            "labels": ["A", "B", "C"],
            "area": round(base_area, 3),
            "area_formula": "S_{đáy} = \\frac{1}{2} a^2",
            "fill_color": "rgba(245, 158, 11, 0.22)",
            "stroke_color": "#f59e0b"
        })

        # Mặt SAB (vuông tại A, gắn với cạnh AB): bung xuống (0, -h)
        pS1 = {"x": 0.0, "y": round(-h, 3)}
        s_sab = 0.5 * a * h
        faces.append({
            "id": "face_sab",
            "name": "Mặt Bên SAB (Tam giác vuông tại A)",
            "face_type": "lateral",
            "points": [pA, pB, pS1],
            "labels": ["A", "B", "S₁"],
            "area": round(s_sab, 3),
            "area_formula": "S_{SAB} = \\frac{1}{2} a \\cdot h",
            "fill_color": "rgba(59, 130, 246, 0.20)",
            "stroke_color": "#3b82f6"
        })

        # Mặt SAC (vuông tại A, gắn với cạnh AC): bung sang trái (-h, 0)
        pS2 = {"x": round(-h, 3), "y": 0.0}
        s_sac = 0.5 * a * h
        faces.append({
            "id": "face_sac",
            "name": "Mặt Bên SAC (Tam giác vuông tại A)",
            "face_type": "lateral",
            "points": [pA, pC, pS2],
            "labels": ["A", "C", "S₂"],
            "area": round(s_sac, 3),
            "area_formula": "S_{SAC} = \\frac{1}{2} a \\cdot h",
            "fill_color": "rgba(16, 185, 129, 0.20)",
            "stroke_color": "#10b981"
        })

        # Mặt SBC gắn vào cạnh huyền BC:
        # H là trung điểm BC: (a/2, a/2), SH = sqrt(h^2 + a^2/2)
        sh_len = math.sqrt(h * h + 0.5 * a * a)
        pS3 = {"x": round(0.5 * a + sh_len / math.sqrt(2.0), 3), "y": round(0.5 * a + sh_len / math.sqrt(2.0), 3)}
        s_sbc = 0.5 * a * math.sqrt(2.0) * sh_len
        faces.append({
            "id": "face_sbc",
            "name": "Mặt Bên SBC",
            "face_type": "lateral",
            "points": [pB, pC, pS3],
            "labels": ["B", "C", "S₃"],
            "area": round(s_sbc, 3),
            "area_formula": "S_{SBC} = \\frac{1}{2} a\\sqrt{2} \\sqrt{h^2 + \\frac{a^2}{2}}",
            "fill_color": "rgba(139, 92, 246, 0.20)",
            "stroke_color": "#8b5cf6"
        })

        fold_lines = [[pA, pB], [pA, pC], [pB, pC]]
        lateral_area = s_sab + s_sac + s_sbc
        total_area = lateral_area + base_area
        measurements = {
            "base_area": round(base_area, 3),
            "lateral_area": round(lateral_area, 3),
            "total_area": round(total_area, 3),
            "slant_height": round(sh_len, 3)
        }
        formulas = {
            "latex_sxq": "S_{xq} = ah + \\frac{1}{2}a\\sqrt{2}\\sqrt{h^2 + \\frac{a^2}{2}}",
            "latex_stp": "S_{tp} = S_{xq} + \\frac{1}{2}a^2",
            "explanation": "Hình chóp tam giác bung 3 mặt bên ra ngoài; các đỉnh S₁, S₂, S₃ chụm lại thành đỉnh S."
        }

    # Tính toán bounding box chuẩn xác cho việc căn chỉnh Canvas / SVG
    for f in faces:
        for pt in f["points"]:
            all_points.append(pt)

    min_x = min(pt["x"] for pt in all_points) if all_points else -5.0
    max_x = max(pt["x"] for pt in all_points) if all_points else 5.0
    min_y = min(pt["y"] for pt in all_points) if all_points else -5.0
    max_y = max(pt["y"] for pt in all_points) if all_points else 5.0

    pad = 0.5
    bounding_box = {
        "min_x": round(min_x - pad, 3),
        "max_x": round(max_x + pad, 3),
        "min_y": round(min_y - pad, 3),
        "max_y": round(max_y + pad, 3),
        "width": round((max_x - min_x) + 2.0 * pad, 3),
        "height": round((max_y - min_y) + 2.0 * pad, 3)
    }

    return {
        "polyhedron_type": norm_type,
        "name": name,
        "height": round(h, 3),
        "base_edge": round(a, 3),
        "faces": faces,
        "fold_lines": fold_lines,
        "bounding_box": bounding_box,
        "measurements": measurements,
        "formulas": formulas
    }


# ==============================================================================
# TASK 13.4: BẬT/TẮT NHÃN TÊN CÁC ĐỈNH (VERTEX LABELS S, A, B, C, D...)
# ==============================================================================

def get_polyhedron_vertex_labels(polyhedron_type: str = "pyramid_square") -> Dict[str, Any]:
    """
    Task 13.4: Truy vấn danh mục tên các đỉnh (S, A, B, C, D...) và vai trò hình học chuẩn SGK.
    """
    norm_type = str(polyhedron_type or "pyramid_square").lower().strip()

    if norm_type in ("pyramid_square", "rectangular_pyramid", "pyramid4", "pyramid"):
        return {
            "polyhedron_type": "pyramid_square",
            "name": "Hình Chóp Tứ Giác S.ABCD (SA ⊥ Đáy)",
            "vertex_count": 6,
            "vertex_labels": ["S", "A", "B", "C", "D", "O"],
            "vertices_info": [
                {"label": "S", "role": "Apex", "description": "Đỉnh chóp S(0, 0, h)"},
                {"label": "A", "role": "Origin / Foot", "description": "Gốc tọa độ O(0,0,0) và chân đường cao SA ⊥ đáy"},
                {"label": "B", "role": "Base Vertex", "description": "Đỉnh đáy trên trục Ox"},
                {"label": "C", "role": "Base Vertex", "description": "Đỉnh đối diện chân đường cao"},
                {"label": "D", "role": "Base Vertex", "description": "Đỉnh đáy trên trục Oy"},
                {"label": "O", "role": "Base Center", "description": "Tâm mặt đáy (giao điểm hai đường chéo AC và BD)"}
            ]
        }
    elif norm_type in ("pyramid_triangle", "triangular_pyramid", "pyramid3", "tetrahedron"):
        return {
            "polyhedron_type": "pyramid_triangle",
            "name": "Hình Chóp Tam Giác S.ABC (SA ⊥ Đáy)",
            "vertex_count": 5,
            "vertex_labels": ["S", "A", "B", "C", "H"],
            "vertices_info": [
                {"label": "S", "role": "Apex", "description": "Đỉnh chóp S(0, 0, h)"},
                {"label": "A", "role": "Origin / Foot", "description": "Gốc tọa độ và chân đường cao SA ⊥ đáy"},
                {"label": "B", "role": "Base Vertex", "description": "Đỉnh góc nhọn đáy trên trục Ox"},
                {"label": "C", "role": "Base Vertex", "description": "Đỉnh góc nhọn đáy trên trục Oy"},
                {"label": "H", "role": "Midpoint / Altitude Foot", "description": "Trung điểm cạnh huyền BC, chân đường cao AH ⊥ BC"}
            ]
        }
    elif norm_type in ("prism_triangle", "triangular_prism", "prism"):
        return {
            "polyhedron_type": "prism_triangle",
            "name": "Lăng Trụ Đứng Tam Giác ABC.A'B'C'",
            "vertex_count": 6,
            "vertex_labels": ["A", "B", "C", "A'", "B'", "C'"],
            "vertices_info": [
                {"label": "A", "role": "Bottom Base Vertex / Origin", "description": "Đỉnh đáy dưới tại gốc tọa độ"},
                {"label": "B", "role": "Bottom Base Vertex", "description": "Đỉnh đáy dưới trên trục Ox"},
                {"label": "C", "role": "Bottom Base Vertex", "description": "Đỉnh đáy dưới trên trục Oy"},
                {"label": "A'", "role": "Top Base Vertex", "description": "Đỉnh đáy trên tương ứng đỉnh A"},
                {"label": "B'", "role": "Top Base Vertex", "description": "Đỉnh đáy trên tương ứng đỉnh B"},
                {"label": "C'", "role": "Top Base Vertex", "description": "Đỉnh đáy trên tương ứng đỉnh C"}
            ]
        }
    else:  # cube / box
        return {
            "polyhedron_type": "cube",
            "name": "Hình Lập Phương ABCD.A'B'C'D'",
            "vertex_count": 8,
            "vertex_labels": ["A", "B", "C", "D", "A'", "B'", "C'", "D'"],
            "vertices_info": [
                {"label": "A", "role": "Bottom Base / Origin", "description": "Đỉnh đáy dưới góc sau-trái (0,0,0)"},
                {"label": "B", "role": "Bottom Base", "description": "Đỉnh đáy dưới góc trước-trái (a,0,0)"},
                {"label": "C", "role": "Bottom Base", "description": "Đỉnh đáy dưới góc trước-phải (a,a,0)"},
                {"label": "D", "role": "Bottom Base", "description": "Đỉnh đáy dưới góc sau-phải (0,a,0)"},
                {"label": "A'", "role": "Top Base", "description": "Đỉnh đáy trên (0,0,a)"},
                {"label": "B'", "role": "Top Base", "description": "Đỉnh đáy trên (a,0,a)"},
                {"label": "C'", "role": "Top Base", "description": "Đỉnh đáy trên (a,a,a)"},
                {"label": "D'", "role": "Top Base", "description": "Đỉnh đáy trên (0,a,a)"}
            ]
        }


# ==============================================================================
# TASK 13.5: GIẢI THUẬT RAYCASTING & KHỬ MẶT KHUẤT (HIDDEN SURFACE REMOVAL)
# ==============================================================================

def ray_triangle_intersect(
    ray_origin: tuple,
    ray_dir: tuple,
    v0: tuple,
    v1: tuple,
    v2: tuple,
    eps: float = 1e-7
) -> Optional[float]:
    """
    Thuật toán Möller–Trumbore tính giao điểm giữa tia Ray(t) = Origin + t * Dir
    và tam giác (v0, v1, v2) trong không gian 3D.
    Trả về khoảng cách t (nếu có giao điểm t > eps), ngược lại trả về None.
    """
    e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

    p = (
        ray_dir[1] * e2[2] - ray_dir[2] * e2[1],
        ray_dir[2] * e2[0] - ray_dir[0] * e2[2],
        ray_dir[0] * e2[1] - ray_dir[1] * e2[0]
    )

    det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2]
    if abs(det) < eps:
        return None

    inv_det = 1.0 / det
    tvec = (ray_origin[0] - v0[0], ray_origin[1] - v0[1], ray_origin[2] - v0[2])
    u = (tvec[0] * p[0] + tvec[1] * p[1] + tvec[2] * p[2]) * inv_det
    if u < 0.0 or u > 1.0:
        return None

    q = (
        tvec[1] * e1[2] - tvec[2] * e1[1],
        tvec[2] * e1[0] - tvec[0] * e1[2],
        tvec[0] * e1[1] - tvec[1] * e1[0]
    )
    v = (ray_dir[0] * q[0] + ray_dir[1] * q[1] + ray_dir[2] * q[2]) * inv_det
    if v < 0.0 or u + v > 1.0:
        return None

    t = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv_det
    if t > eps:
        return t
    return None


def compute_hidden_surface_raycasting(
    polyhedron_type: str = "pyramid_square",
    camera_position: tuple = (6.0, 7.0, 9.0),
    height: float = 4.0,
    base_edge: float = 4.0
) -> Dict[str, Any]:
    """
    Task 13.5: Cài đặt thuật toán Raycasting xác định cạnh khuất (Hidden Surface Removal)
    bằng cách phóng tia từ camera tới điểm giữa của từng cạnh và kiểm tra va chạm với các mặt.
    """
    norm_type = str(polyhedron_type or "pyramid_square").lower().strip()
    geom = calculate_parametric_geometry(norm_type, height, base_edge)
    verts = {k: v.to_tuple() for k, v in geom.vertices.items()}

    triangles: List[tuple] = []
    edges: List[tuple] = []

    if norm_type in ("pyramid_square", "rectangular_pyramid", "pyramid4", "pyramid"):
        edges = [
            ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
            ("S", "A"), ("S", "B"), ("S", "C"), ("S", "D")
        ]
        triangles = [
            ("A", "B", "C"), ("A", "C", "D"),
            ("S", "A", "B"), ("S", "B", "C"), ("S", "C", "D"), ("S", "D", "A")
        ]
    elif norm_type in ("pyramid_triangle", "triangular_pyramid", "pyramid3", "tetrahedron"):
        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),
            ("S", "A"), ("S", "B"), ("S", "C")
        ]
        triangles = [
            ("A", "B", "C"),
            ("S", "A", "B"), ("S", "B", "C"), ("S", "C", "A")
        ]
    elif norm_type in ("prism_triangle", "triangular_prism", "prism"):
        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),
            ("A'", "B'"), ("B'", "C'"), ("C'", "A'"),
            ("A", "A'"), ("B", "B'"), ("C", "C'")
        ]
        triangles = [
            ("A", "B", "C"), ("A'", "B'", "C'"),
            ("A", "B", "B'"), ("A", "B'", "A'"),
            ("B", "C", "C'"), ("B", "C'", "B'"),
            ("C", "A", "A'"), ("C", "A'", "C'")
        ]
    else:  # cube
        edges = [
            ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
            ("A'", "B'"), ("B'", "C'"), ("C'", "D'"), ("D'", "A'"),
            ("A", "A'"), ("B", "B'"), ("C", "C'"), ("D", "D'")
        ]
        triangles = [
            ("A", "B", "C"), ("A", "C", "D"),
            ("A'", "B'", "C'"), ("A'", "C'", "D'"),
            ("A", "B", "B'"), ("A", "B'", "A'"),
            ("B", "C", "C'"), ("B", "C'", "B'"),
            ("C", "D", "D'"), ("C", "D'", "C'"),
            ("D", "A", "A'"), ("D", "A'", "D'")
        ]

    tested_edges: List[Dict[str, Any]] = []
    occluded_count = 0
    visible_count = 0

    cam_pos = camera_position

    for p1_name, p2_name in edges:
        p1 = verts[p1_name]
        p2 = verts[p2_name]
        mid = (
            (p1[0] + p2[0]) * 0.5,
            (p1[1] + p2[1]) * 0.5,
            (p1[2] + p2[2]) * 0.5
        )

        dx = mid[0] - cam_pos[0]
        dy = mid[1] - cam_pos[1]
        dz = mid[2] - cam_pos[2]
        dist_to_mid = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist_to_mid < 1e-6:
            ray_dir = (0.0, 0.0, 1.0)
        else:
            ray_dir = (dx / dist_to_mid, dy / dist_to_mid, dz / dist_to_mid)

        is_occluded = False
        occluding_face = None

        for t_v0, t_v1, t_v2 in triangles:
            face_verts = {t_v0, t_v1, t_v2}
            if p1_name in face_verts and p2_name in face_verts:
                continue

            t_hit = ray_triangle_intersect(
                cam_pos,
                ray_dir,
                verts[t_v0],
                verts[t_v1],
                verts[t_v2]
            )

            if t_hit is not None and 0.05 < t_hit < (dist_to_mid - 0.05):
                is_occluded = True
                occluding_face = f"Δ{t_v0}{t_v1}{t_v2}"
                break

        if is_occluded:
            occluded_count += 1
        else:
            visible_count += 1

        tested_edges.append({
            "edge": [p1_name, p2_name],
            "is_occluded": is_occluded,
            "render_style": "dashed" if is_occluded else "solid",
            "occluding_face": occluding_face,
            "midpoint": {"x": round(mid[0], 2), "y": round(mid[1], 2), "z": round(mid[2], 2)}
        })

    return {
        "polyhedron_type": norm_type,
        "camera_position": {"x": cam_pos[0], "y": cam_pos[1], "z": cam_pos[2]},
        "total_edges": len(edges),
        "occluded_count": occluded_count,
        "visible_count": visible_count,
        "edges_status": tested_edges,
        "algorithm": "Möller–Trumbore Ray-Triangle Occlusion Intersection",
        "pedagogical_rule": "Cạnh bị mặt phẳng che khuất khỏi góc nhìn Camera được gán render_style = 'dashed' (Nét Đứt)."
    }





