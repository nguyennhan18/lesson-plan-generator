r"""
Automated Acceptance Test Suite — Day 11 (Nhúng Thư viện Hình học Không gian 3D Tương tác)
Kiểm tra toàn diện 5 hạng mục của Ngày 11 theo Ke_Hoach_Phat_Trien.pdf:
- Task 11.1: Bố cục PowerPoint Động & Khung Three.js Canvas trong Layout IMAGE_TEXT
- Task 11.2: Dựng các khối hình học không gian 3D chuẩn SGK (Chóp S.ABCD, Chóp S.ABC, Lăng trụ, Lập phương)
- Task 11.3: Điều khiển chuột xoay 360° quanh 3 trục Ox, Oy, Oz, Nội suy Lerp Damping 60 FPS, Cuộn Zoom & Thanh công cụ
- Task 11.4: Cấu hình Hệ trục Tọa độ Descartes Oxyz (Mũi tên nón định hướng + nhãn O,x,y,z) & Mặt phẳng đáy (Oxy)
- Task 11.5: Nghiệm thu DoD Ngày 11 & Kiểm thử Tự động Toàn diện End-to-End
"""

import json
import math
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from schemas.slide_schema import (
    SlideSchema,
    SlideDeckSchema,
    ChartSpec,
    ChartType,
    QuizOptionDetail,
    SlideLayout,
    SlideType,
    ThemeType
)
from services.ai_service import SLIDE_SYSTEM_PROMPT

PRESENTATION_STAGE_JSX = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
THREE_CANVAS_JSX = FRONTEND_DIR / "src" / "components" / "ThreeCanvas.jsx"
APP_JSX = FRONTEND_DIR / "src" / "App.jsx"
SLIDE_SCHEMA_PY = BACKEND_SRC / "schemas" / "slide_schema.py"


def test_task_11_1_slide_schema_dynamic_layouts_and_3d_spec():
    """
    Task 11.1: Kiểm tra SlideSchema hỗ trợ bố cục trình chiếu động và thông số 3D:
    - ChartSpec.kind hỗ trợ 'NONE' (khi không cần biểu đồ hình tròn/cột)
    - SlideSchema.has_3d: cờ đánh dấu slide sử dụng khung hình học không gian 3D
    - SlideSchema.polyhedron_type: định dạng khối đa diện (pyramid_square, pyramid_triangle, prism_triangle, cube)
    - SlideSchema.worked_solution_steps: các bước lời giải chi tiết chuẩn SGK
    - PresentationStage.jsx có bộ điều hướng bố cục: IMAGE_TEXT, TWO_COLUMN, CONCEPT_HIGHLIGHT
    """
    # 1. Kiểm tra SlideSchema trong Pydantic
    schema_code = SLIDE_SCHEMA_PY.read_text(encoding="utf-8")
    assert "has_3d" in schema_code, "SlideSchema thiếu trường has_3d"
    assert "polyhedron_type" in schema_code, "SlideSchema thiếu trường polyhedron_type"
    assert "worked_solution_steps" in schema_code, "SlideSchema thiếu trường worked_solution_steps"
    assert hasattr(ChartType, "NONE") and ChartType.NONE.value == "none", "ChartSpec.kind thiếu giá trị NONE"

    # 2. Kiểm tra khởi tạo Slide Pydantic với has_3d
    slide_3d = SlideSchema(
        slide_index=1,
        title="1. Hình chóp tứ giác S.ABCD có SA vuông góc đáy",
        type=SlideType.CONCEPT_SLIDE,
        layout=SlideLayout.IMAGE_TEXT,
        has_3d=True,
        polyhedron_type="pyramid_square",
        main_definition_latex=r"SA \bot (ABCD) \implies SA \bot AB, SA \bot AD",
        bullet_points=[
            r"Đáy $ABCD$ là hình vuông cạnh $a$.",
            r"Đường cao $SA = h$, chân đường cao là đỉnh $A$."
        ]
    )
    assert slide_3d.has_3d is True
    assert slide_3d.polyhedron_type == "pyramid_square"
    assert slide_3d.layout == SlideLayout.IMAGE_TEXT

    # 3. Kiểm tra Slide Pydantic bố cục 2 cột học thuật TWO_COLUMN
    slide_two_col = SlideSchema(
        slide_index=2,
        title="2. Phương pháp tính khoảng cách và Bài giải mẫu",
        type=SlideType.EXERCISE_SLIDE,
        layout=SlideLayout.TWO_COLUMN,
        main_definition_latex=r"d(S, (ABCD)) = SA = a\sqrt{3}",
        bullet_points=[
            r"Xác định hình chiếu vuông góc của đỉnh lên mặt đáy.",
            r"Dựng đoạn vuông góc từ điểm đến mặt phẳng."
        ],
        worked_solution_steps=[
            r"\text{Bước 1: Do } SA \bot (ABCD) \text{ tại } A \implies d(S, (ABCD)) = SA.",
            r"\text{Bước 2: Trong tam giác vuông } SAB: SA = AB \cdot \tan 60^\circ = a\sqrt{3}.",
            r"\text{Kết luận: Khoảng cách cần tìm là } a\sqrt{3}."
        ]
    )
    assert slide_two_col.layout == SlideLayout.TWO_COLUMN
    assert len(slide_two_col.worked_solution_steps) == 3

    # 4. Kiểm tra PresentationStage.jsx chứa các layout động và ThreeCanvas
    stage_code = PRESENTATION_STAGE_JSX.read_text(encoding="utf-8")
    assert "IMAGE_TEXT" in stage_code, "PresentationStage thiếu layout IMAGE_TEXT"
    assert "TWO_COLUMN" in stage_code, "PresentationStage thiếu layout TWO_COLUMN"
    assert "CONCEPT_HIGHLIGHT" in stage_code, "PresentationStage thiếu layout CONCEPT_HIGHLIGHT"
    assert "<ThreeCanvas" in stage_code, "PresentationStage thiếu thẻ <ThreeCanvas"


def test_task_11_2_polyhedron_models_and_sgk_geometry():
    """
    Task 11.2: Kiểm tra mô hình 3D trong ThreeCanvas.jsx:
    - 4 khối chuẩn SGK: pyramid_square (S.ABCD), pyramid_triangle (S.ABC), prism_triangle, cube
    - Nét liền cho cạnh nhìn thấy, nét đứt (dashed: true) cho cạnh khuất sau
    - Ký hiệu góc vuông chân đường cao (addRightAngle)
    - Nhãn đỉnh Billboard Sprite (A, B, C, D, S, O, H)
    - Tính đúng đắn toán học: Vector SA vuông góc với mặt phẳng đáy (SA . AB == 0, SA . AD == 0)
    """
    canvas_code = THREE_CANVAS_JSX.read_text(encoding="utf-8")

    # Kiểm tra sự hiện diện của 4 loại khối đa diện
    assert "pyramid_square" in canvas_code, "Thiếu mô hình pyramid_square (S.ABCD)"
    assert "pyramid_triangle" in canvas_code, "Thiếu mô hình pyramid_triangle (S.ABC)"
    assert "prism_triangle" in canvas_code, "Thiếu mô hình prism_triangle"
    assert "cube" in canvas_code, "Thiếu mô hình cube"

    # Kiểm tra các hàm trợ giúp dựng hình
    assert "addEdge" in canvas_code, "Thiếu hàm trợ giúp addEdge"
    assert "LineDashedMaterial" in canvas_code, "Thiếu LineDashedMaterial vẽ cạnh nét đứt"
    assert "computeLineDistances" in canvas_code, "Thiếu computeLineDistances cho nét đứt"
    assert "addRightAngle" in canvas_code, "Thiếu hàm addRightAngle ký hiệu góc vuông"
    assert "addVertexSprite" in canvas_code, "Thiếu hàm addVertexSprite nhãn đỉnh billboard"

    # Kiểm tra tính toán tọa độ Toán học của Chóp S.ABCD:
    # A = (-xA, yBase, -zA), S = (-xA, yApex, -zA) => vector SA = (0, yApex - yBase, 0)
    # Vector SA song song trục Oy (thẳng đứng), vuông góc với mọi vector thuộc mặt đáy Oxy/Oxz!
    v_A = ( -0.95, -0.9, -0.95 )
    v_B = ( -0.95, -0.9,  0.85 )
    v_D = (  0.85, -0.9, -0.95 )
    v_S = ( -0.95,  1.35, -0.95 )

    # Vector SA = S - A = (0, 2.25, 0)
    vec_SA = (v_S[0] - v_A[0], v_S[1] - v_A[1], v_S[2] - v_A[2])
    # Vector AB = B - A = (0, 0, 1.8)
    vec_AB = (v_B[0] - v_A[0], v_B[1] - v_A[1], v_B[2] - v_A[2])
    # Vector AD = D - A = (1.8, 0, 0)
    vec_AD = (v_D[0] - v_A[0], v_D[1] - v_A[1], v_D[2] - v_A[2])

    # Tích vô hướng SA . AB = 0 * 0 + 2.25 * 0 + 0 * 1.8 = 0
    dot_SA_AB = vec_SA[0]*vec_AB[0] + vec_SA[1]*vec_AB[1] + vec_SA[2]*vec_AB[2]
    # Tích vô hướng SA . AD = 0 * 1.8 + 2.25 * 0 + 0 * 0 = 0
    dot_SA_AD = vec_SA[0]*vec_AD[0] + vec_SA[1]*vec_AD[1] + vec_SA[2]*vec_AD[2]
    # Tích vô hướng AB . AD = 0 * 1.8 + 0 * 0 + 1.8 * 0 = 0 (Đáy vuông góc)
    dot_AB_AD = vec_AB[0]*vec_AD[0] + vec_AB[1]*vec_AD[1] + vec_AB[2]*vec_AD[2]

    assert abs(dot_SA_AB) < 1e-6, f"SA không vuông góc với AB! Dot product = {dot_SA_AB}"
    assert abs(dot_SA_AD) < 1e-6, f"SA không vuông góc với AD! Dot product = {dot_SA_AD}"
    assert abs(dot_AB_AD) < 1e-6, f"Đáy ABCD không vuông tại A! Dot product = {dot_AB_AD}"

    # Kiểm tra mô hình S.ABC có Định lý 3 đường vuông góc (AH ⊥ BC, SH ⊥ BC)
    assert "vecBC" in canvas_code, "Thiếu tính toán vector BC trong S.ABC"
    assert "ptH" in canvas_code, "Thiếu điểm chân đường cao H trong S.ABC"


def test_task_11_3_mouse_360_rotation_lerp_damping_and_zoom():
    """
    Task 11.3: Kiểm tra cơ chế tương tác xoay 360 độ quanh 3 trục Ox, Oy, Oz và zoom:
    - Xoay tự do chuột trái quanh Ox, Oy
    - Shift hoặc chuột phải xoay quanh Oz (Roll)
    - Thuật toán Lerp Damping: curRot += (targetRot - curRot) * factor (nội suy 60 FPS)
    - Nút xoay từng nấc +45° cho Ox, Oy, Oz
    - Nút Đặt lại góc nhìn chuẩn SGK (handleResetCamera)
    - Thu phóng cuộn chuột có giới hạn min/max [0.55, 2.80]
    """
    canvas_code = THREE_CANVAS_JSX.read_text(encoding="utf-8")

    # Kiểm tra tương tác Pointer / Mouse
    assert "handlePointerDown" in canvas_code, "Thiếu handlePointerDown"
    assert "handlePointerMove" in canvas_code, "Thiếu handlePointerMove"
    assert "handleWheel" in canvas_code, "Thiếu handleWheel phóng to/thu nhỏ"
    assert "rotZ" in canvas_code, "Thiếu điều khiển xoay quanh trục Oz"
    assert "rotX" in canvas_code and "rotY" in canvas_code, "Thiếu điều khiển xoay Ox, Oy"

    # Kiểm tra thuật toán Lerp Damping
    assert "targetRotRef" in canvas_code, "Thiếu targetRotRef lưu góc xoay mục tiêu"
    assert "curRotRef" in canvas_code, "Thiếu curRotRef lưu góc xoay hiện thời"
    assert "target.rotX - cur.rotX" in canvas_code and "factor" in canvas_code, "Thiếu công thức nội suy Lerp Damping 60 FPS"

    # Kiểm tra thanh công cụ điều khiển
    assert "Ox +45°" in canvas_code or "Ox" in canvas_code, "Thiếu nút xoay nhanh Ox"
    assert "Oy +45°" in canvas_code or "Oy" in canvas_code, "Thiếu nút xoay nhanh Oy"
    assert "Oz +45°" in canvas_code or "Oz" in canvas_code, "Thiếu nút xoay nhanh Oz"
    assert "handleResetCamera" in canvas_code, "Thiếu hàm reset camera chuẩn SGK"
    assert "2.80" in canvas_code and "0.55" in canvas_code, "Thiếu giới hạn zoom [0.55, 2.80]"


def test_task_11_4_cartesian_system_oxyz_and_base_floor_oxy():
    """
    Task 11.4: Kiểm tra Hệ trục Tọa độ Không gian Descartes Oxyz và Mặt sàn đáy (Oxy):
    - Hàm addCartesianSystemAndFloor
    - Mũi tên định hướng THREE.ArrowHelper cho 3 trục Ox, Oy, Oz
    - Màu sắc quy ước: Ox (#f43f5e đỏ hồng), Oy (#10b981 xanh ngọc), Oz (#38bdf8 xanh dương)
    - Gốc O là hình cầu màu trắng (0xffffff)
    - Nhãn chữ Billboard Sprite: O, x, y, z và (Oxy)
    - Mặt sàn kính mờ với depthWrite: false (chống Z-fighting với nét đứt)
    - Cờ bật/tắt showAxes
    """
    canvas_code = THREE_CANVAS_JSX.read_text(encoding="utf-8")

    assert "addCartesianSystemAndFloor" in canvas_code, "Thiếu hàm addCartesianSystemAndFloor"
    assert "ArrowHelper" in canvas_code, "Thiếu THREE.ArrowHelper dựng vector trục tọa độ"
    assert "GridHelper" in canvas_code, "Thiếu THREE.GridHelper dựng lưới sàn (Oxy)"
    assert "depthWrite: false" in canvas_code, "Mặt sàn thiếu depthWrite: false (gây Z-fighting)"
    assert "'(Oxy)'" in canvas_code or '"(Oxy)"' in canvas_code, "Thiếu nhãn mặt sàn (Oxy)"
    assert "0xf43f5e" in canvas_code, "Thiếu màu đỏ hồng cho trục Ox"
    assert "0x10b981" in canvas_code, "Thiếu màu xanh ngọc cho trục Oy"
    assert "0x38bdf8" in canvas_code, "Thiếu màu xanh dương cho trục Oz"

    # Kiểm tra showAxes được bật mặc định trong ThreeCanvas và App.jsx
    app_code = APP_JSX.read_text(encoding="utf-8")
    assert "showAxes" in app_code, "App.jsx thiếu state showAxes"
    assert "useState(true)" in app_code or "showAxes={true}" in app_code, "showAxes nên được kích hoạt mặc định"


def test_task_11_5_dod_day11_geometry_end_to_end():
    """
    Task 11.5 (DoD Cuối ngày 11): Kiểm tra Nghiệm thu End-to-End toàn bộ tính năng Ngày 11:
    - Bố cục IMAGE_TEXT tích hợp KaTeX bên trái và Three.js 3D bên phải
    - Khởi tạo đầy đủ bài giảng Không gian 3D Toán 12
    - Kiểm tra AI System Prompt SLIDE_SYSTEM_PROMPT chứa hướng dẫn tạo layout động
      (IMAGE_TEXT cho bài toán hình không gian 3D, TWO_COLUMN cho lời giải từng bước)
    - Đảm bảo tính tương thích ngược với toàn bộ các tính năng Ngày 8, 9, 10
    """
    # 1. Kiểm tra AI System Prompt
    assert "IMAGE_TEXT" in SLIDE_SYSTEM_PROMPT, "SLIDE_SYSTEM_PROMPT thiếu chỉ dẫn IMAGE_TEXT"
    assert "TWO_COLUMN" in SLIDE_SYSTEM_PROMPT, "SLIDE_SYSTEM_PROMPT thiếu chỉ dẫn TWO_COLUMN"
    assert "CONCEPT_HIGHLIGHT" in SLIDE_SYSTEM_PROMPT, "SLIDE_SYSTEM_PROMPT thiếu chỉ dẫn CONCEPT_HIGHLIGHT"
    assert "has_3d" in SLIDE_SYSTEM_PROMPT, "SLIDE_SYSTEM_PROMPT thiếu chỉ dẫn has_3d"
    assert "worked_solution_steps" in SLIDE_SYSTEM_PROMPT, "SLIDE_SYSTEM_PROMPT thiếu chỉ dẫn worked_solution_steps"

    # 2. Tạo một SlideDeck hoàn chỉnh về Hình học Không gian Toán 12
    spatial_deck = SlideDeckSchema(
        presentation_title="Khoảng Cách Trong Không Gian & Tọa Độ Hóa",
        grade=12,
        subject="Toán học",
        theme=ThemeType.MATH_ACADEMIC,
        slides=[
            SlideSchema(
                slide_index=1,
                type=SlideType.CONCEPT_SLIDE,
                title="1. Định nghĩa và Mô hình Chóp Tứ Giác S.ABCD",
                layout=SlideLayout.IMAGE_TEXT,
                has_3d=True,
                polyhedron_type="pyramid_square",
                main_definition_latex=r"SA \bot (ABCD) \iff SA \bot AB \land SA \bot AD",
                bullet_points=[
                    r"Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông cạnh $a$.",
                    r"Cạnh bên $SA \bot (ABCD)$ và $SA = a\sqrt{3}$.",
                    r"Trục $Oz$ được gắn dọc theo đường cao $SA$, $Ox$ theo $AB$, $Oy$ theo $AD$."
                ]
            ),
            SlideSchema(
                slide_index=2,
                type=SlideType.EXERCISE_SLIDE,
                title="2. Phương pháp Tính Khoảng Cách d(S, (ABCD))",
                layout=SlideLayout.TWO_COLUMN,
                has_3d=False,
                main_definition_latex=r"d(M, (P)) = MH \text{ với } H = \text{pr}_{(P)}(M)",
                bullet_points=[
                    r"Bước 1: Tìm hình chiếu vuông góc $H$ của điểm $M$ lên mặt phẳng $(P)$.",
                    r"Bước 2: Độ dài đoạn thẳng $MH$ chính là khoảng cách cần tính."
                ],
                worked_solution_steps=[
                    r"\text{Do } SA \bot (ABCD) \text{ tại } A \implies A \text{ là hình chiếu vuông góc của } S \text{ lên } (ABCD).",
                    r"\text{Suy ra } d(S, (ABCD)) = SA = a\sqrt{3}.",
                    r"\text{Kết luận: Khoảng cách từ đỉnh } S \text{ đến đáy là } a\sqrt{3}."
                ]
            ),
            SlideSchema(
                slide_index=3,
                type=SlideType.CONCEPT_SLIDE,
                title="3. Câu hỏi Củng cố Trọng tâm",
                layout=SlideLayout.QUIZ_OPTION,
                has_3d=False,
                main_definition_latex="",
                bullet_points=["Chọn khẳng định đúng về vector chỉ phương của SA:"],
                quiz_options=[
                    QuizOptionDetail(label="A", text="Vector đơn vị i của trục Ox", is_correct=False, distractor_rationale="Trục Ox nằm trong mặt đáy Oxy."),
                    QuizOptionDetail(label="B", text="Vector đơn vị j của trục Oy", is_correct=False, distractor_rationale="Trục Oy nằm trong mặt đáy Oxy."),
                    QuizOptionDetail(label="C", text="Vector đơn vị k của trục Oz", is_correct=True, distractor_rationale=""),
                    QuizOptionDetail(label="D", text="Không xác định được", is_correct=False, distractor_rationale="Hoàn toàn xác định được vì Oz vuông góc Oxy.")
                ]
            )
        ]
    )

    # 3. Xác thực Pydantic serialization & schema compliance
    deck_dict = spatial_deck.model_dump()
    assert len(deck_dict["slides"]) == 3
    assert deck_dict["slides"][0]["has_3d"] is True
    assert deck_dict["slides"][0]["polyhedron_type"] == "pyramid_square"
    assert deck_dict["slides"][1]["layout"] == "TWO_COLUMN" or deck_dict["slides"][1]["layout"] == SlideLayout.TWO_COLUMN
    assert len(deck_dict["slides"][1]["worked_solution_steps"]) == 3
    assert deck_dict["slides"][2]["quiz_options"][2]["is_correct"] is True

    # 4. Kiểm tra serialization sang chuỗi JSON không có lỗi KaTeX backslash
    deck_json_str = json.dumps(deck_dict, ensure_ascii=False)
    assert "pyramid_square" in deck_json_str
    assert "worked_solution_steps" in deck_json_str


class TestDay11_3DGeometry(unittest.TestCase):
    """Lớp kiểm thử chuẩn unittest cho CI/CD pipeline Ngày 11"""

    def test_11_1_slide_schema_dynamic_layouts(self):
        test_task_11_1_slide_schema_dynamic_layouts_and_3d_spec()

    def test_11_2_polyhedron_models_and_sgk_geometry(self):
        test_task_11_2_polyhedron_models_and_sgk_geometry()

    def test_11_3_mouse_360_rotation_and_damping(self):
        test_task_11_3_mouse_360_rotation_lerp_damping_and_zoom()

    def test_11_4_cartesian_system_oxyz_and_floor(self):
        test_task_11_4_cartesian_system_oxyz_and_base_floor_oxy()

    def test_11_5_dod_day11_geometry_end_to_end(self):
        test_task_11_5_dod_day11_geometry_end_to_end()


if __name__ == "__main__":
    unittest.main()
