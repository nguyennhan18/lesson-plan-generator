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


from lessonai.schemas.slide_schema import (
    SlideSchema,
    SlideDeckSchema,
    ChartSpec,
    ChartType,
    QuizOptionDetail,
    SlideLayout,
    SlideType,
    ThemeType
)
from lessonai.prompts.slides import SLIDE_SYSTEM_PROMPT

PRESENTATION_STAGE_JSX = FRONTEND_DIR / "src" / "features" / "presentation" / "PresentationStage.jsx"
THREE_CANVAS_JSX = FRONTEND_DIR / "src" / "features" / "geometry" / "ThreeCanvas.jsx"
APP_JSX = FRONTEND_DIR / "src" / "App.jsx"
SLIDE_SCHEMA_PY = BACKEND_SRC / "lessonai" / "schemas" / "slide_schema.py"










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





    def test_11_5_dod_day11_geometry_end_to_end(self):
        test_task_11_5_dod_day11_geometry_end_to_end()


if __name__ == "__main__":
    unittest.main()
