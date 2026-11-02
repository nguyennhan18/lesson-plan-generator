from fastapi import HTTPException
from lessonai.services.geometry import calculate_parametric_geometry, ParametricGeometryRequest, ParametricGeometryResponse, get_polyhedron_edge_topology, get_unfolded_net_topology, get_polyhedron_vertex_labels, compute_hidden_surface_raycasting
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/geometry', tags=['Geometry & 3D Parametric'])

@router.post("/parametric-coordinates", response_model=ParametricGeometryResponse)
def get_parametric_coordinates_endpoint(req: ParametricGeometryRequest):
    """
    Task 12.2: Endpoint tính toán tọa độ đỉnh chóp S(0, 0, h) và các thông số hình học động
    theo thời gian thực khi Giáo viên / Học sinh kéo các thanh trượt UI (Slider Controls).
    """
    try:
        return calculate_parametric_geometry(
            polyhedron_type=req.polyhedron_type,
            height=req.height,
            base_edge=req.base_edge
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tính toán tọa độ hình học: {str(e)}"
        )


@router.get("/apex-coordinates", response_model=ParametricGeometryResponse)
def get_apex_coordinates_get_endpoint(
    polyhedron_type: str = "pyramid_square",
    height: float = 4.0,
    base_edge: float = 4.0
):
    """
    Task 12.2: Endpoint GET hỗ trợ truy vấn nhanh tọa độ đỉnh S(0, 0, h) qua Query Params.
    """
    try:
        return calculate_parametric_geometry(
            polyhedron_type=polyhedron_type,
            height=height,
            base_edge=base_edge
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tính toán tọa độ hình học: {str(e)}"
        )


@router.get("/edge-topology")
def get_edge_topology_endpoint(polyhedron_type: str = "pyramid_square"):
    """
    Task 13.1: Endpoint truy vấn danh mục cạnh thấy (nét liền) và cạnh khuất (nét đứt) chuẩn SGK.
    """
    try:
        return get_polyhedron_edge_topology(polyhedron_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi truy vấn cấu trúc cạnh: {str(e)}"
        )


@router.get("/unfolded-net")
def get_unfolded_net_endpoint(
    polyhedron_type: str = "pyramid_square",
    height: float = 4.0,
    base_edge: float = 4.0
):
    """
    Task 13.3: Endpoint trả về cấu trúc bản vẽ Khai Triển Phẳng 2D (Unfolded Net)
    phục vụ trực quan hóa diện tích xung quanh S_xq và diện tích toàn phần S_tp.
    """
    try:
        return get_unfolded_net_topology(
            polyhedron_type=polyhedron_type,
            height=height,
            base_edge=base_edge
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tính toán hình khai triển phẳng: {str(e)}"
        )


@router.get("/vertex-labels")
def get_vertex_labels_endpoint(polyhedron_type: str = "pyramid_square"):
    """
    Task 13.4: Endpoint truy vấn danh mục tên các đỉnh (S, A, B, C, D) và ý nghĩa hình học SGK.
    """
    try:
        return get_polyhedron_vertex_labels(polyhedron_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi truy vấn danh sách đỉnh: {str(e)}"
        )


@router.get("/raycast-occlusion")
def get_raycast_occlusion_endpoint(
    polyhedron_type: str = "pyramid_square",
    cam_x: float = 6.0,
    cam_y: float = 7.0,
    cam_z: float = 9.0,
    height: float = 4.0,
    base_edge: float = 4.0
):
    """
    Task 13.5: Endpoint tính toán khử mặt khuất bằng giải thuật Raycasting (Möller–Trumbore)
    xác định chính xác các cạnh khuất nét đứt từ tọa độ Camera quan sát.
    """
    try:
        return compute_hidden_surface_raycasting(
            polyhedron_type=polyhedron_type,
            camera_position=(cam_x, cam_y, cam_z),
            height=height,
            base_edge=base_edge
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tính toán Raycasting: {str(e)}"
        )

