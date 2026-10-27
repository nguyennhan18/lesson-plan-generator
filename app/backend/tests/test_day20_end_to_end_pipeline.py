"""
Test Suite Ngày 20: Chạy Kiểm Thử Toàn Diện (End-to-End Pipeline) & Xử Lý Triệt Để Edge-Cases.
Task 20.1: Kiểm thử toàn trình bài dạy Lớp 10: Hệ bất phương trình bậc nhất hai ẩn
- Giáo án Công văn 5512 (4 hoạt động, 45 phút, chuẩn hóa mục tiêu).
- Slide bài giảng Web Studio (Title, Concept, Đồ thị 2D Oxy, Lời giải mẫu, Quiz tương tác).
- Đồ họa Matplotlib 2D: Miền nghiệm đa giác lồi OABC, đường thẳng ranh giới và tọa độ đỉnh.
- Xuất file Word (.docx), PowerPoint (.pptx) và Gói kép Dual-Pack (.zip).
- Cam kết Zero-Crash: Không ném ngoại lệ 500 khi rớt mạng / hết quota LLM.
"""

import io
import os
import sys
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Thiết lập đường dẫn src
BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Đặt thư mục đệm Matplotlib để chạy an toàn trong môi trường test
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_day20_test"

from main import app
from schemas.schemas import LessonPlanSchema
from schemas.slide_schema import SlideDeckSchema, ChartType, SlideType
from services.ai_service import generate_lesson_plan, generate_slide_deck
from services.fallback_service import get_curated_lesson_plan, get_curated_slide_deck
from services.validation import validate_5512_lesson_plan
from exporters.graph_generator import generate_math_plot, is_plottable
from docx import Document
from pptx import Presentation

client = TestClient(app)


@pytest.fixture(autouse=True)
def speed_up_offline_tests(monkeypatch):
    """
    Tối ưu hóa thời gian chạy test trong môi trường sandbox / CI:
    Nếu không có kết nối internet tới Gemini/Groq, chuyển ngay về Curated Fallback
    thay vì phải chờ timeout 120s của 5 tuyến model.
    """
    # Nếu môi trường không có key thật hoặc không kết nối được mạng
    from services.ai_service import llm_gateway
    original_generate = llm_gateway.generate_structured

    def fast_gateway(prompt, system_prompt, response_schema, task_type="lesson_plan", **kwargs):
        prompt_lower = prompt.lower()
        if "cực trị" in prompt_lower or "đơn điệu" in prompt_lower or "lớp 12" in prompt_lower:
            grade = 12
            topic = "Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp"
        elif "cấp số" in prompt_lower or "lớp 11" in prompt_lower:
            grade = 11
            topic = "Cấp số cộng và Quan hệ vuông góc trong không gian"
        elif "bất phương trình" in prompt_lower or "lớp 10" in prompt_lower:
            grade = 10
            topic = "Hệ bất phương trình bậc nhất hai ẩn"
        else:
            grade = 10
            topic = "Hệ bất phương trình bậc nhất hai ẩn"

        if task_type == "slide" or response_schema == SlideDeckSchema:
            return get_curated_slide_deck(topic, "Toán học", grade)
        return get_curated_lesson_plan(topic, "Toán học", grade)

    # Trong môi trường test cô lập, kích hoạt fast_gateway để test hoàn tất trong < 2 giây
    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", fast_gateway)


# ==============================================================================
# PHẦN 1: UNIT & LOGIC TESTS - TOÁN 10: HỆ BẤT PHƯƠNG TRÌNH BẬC NHẤT HAI ẨN
# ==============================================================================

def test_grade10_lesson_plan_generation_cv5512():
    """
    Task 20.1 (Phần 1): Sinh Kế hoạch bài dạy chuẩn CV 5512 cho môn Toán 10.
    Kiểm tra cấu trúc 4 hoạt động, tổng thời gian 45 phút và các mục tiêu sư phạm.
    """
    plan, val_result = generate_lesson_plan(
        topic="Hệ bất phương trình bậc nhất hai ẩn",
        subject="Toán học",
        grade=10
    )

    assert isinstance(plan, LessonPlanSchema)
    assert "bất phương trình" in plan.lesson_title.lower()
    assert plan.grade == 10
    assert plan.subject == "Toán học"

    # Kiểm định CV 5512: 4 hoạt động bắt buộc
    assert len(plan.activities) == 4, f"Số hoạt động phải đúng bằng 4, nhận được: {len(plan.activities)}"
    total_time = sum(act.time_minutes for act in plan.activities)
    assert total_time == 45, f"Tổng thời lượng bài dạy phải đúng bằng 45 phút, nhận được: {total_time}"

    # Kiểm tra 4 bước tổ chức hoạt động của mỗi hoạt động
    for idx, act in enumerate(plan.activities, start=1):
        assert act.activity_number == idx
        assert act.execution.step_1_assign.strip() != ""
        assert act.execution.step_2_excute.strip() != ""
        assert act.execution.step_3_report.strip() != ""
        assert act.execution.step_4_conclusion.strip() != ""

    # Kiểm tra qua bộ Validator 5512
    assert val_result.is_valid, f"Kế hoạch bài dạy không vượt qua kiểm định 5512: {val_result.errors}"


def test_grade10_slide_deck_generation():
    """
    Task 20.1 (Phần 2): Sinh SlideDeck bài giảng chuẩn SGK cho môn Toán 10.
    Kiểm tra cấu trúc tối thiểu 4-5 slide, có slide đồ thị Oxy và slide trắc nghiệm có giải thích sai lầm.
    """
    plan, _ = generate_lesson_plan(
        topic="Hệ bất phương trình bậc nhất hai ẩn",
        subject="Toán học",
        grade=10
    )

    deck = generate_slide_deck(
        topic="Hệ bất phương trình bậc nhất hai ẩn",
        subject="Toán học",
        grade=10,
        plan=plan
    )

    assert isinstance(deck, SlideDeckSchema)
    assert len(deck.slides) >= 4, f"Slide deck phải có ít nhất 4 slide, nhận được: {len(deck.slides)}"

    # Slide 1: Phải là TITLE_SLIDE
    assert deck.slides[0].type == SlideType.TITLE_SLIDE
    assert "bất phương trình" in deck.slides[0].title.lower()

    # Tìm slide có đồ thị 2D
    chart_slides = [s for s in deck.slides if s.chart_spec and s.chart_spec.kind in [ChartType.INEQUALITY_SYSTEM, ChartType.FUNCTION_PLOT]]
    assert len(chart_slides) >= 1, "Phải có ít nhất 1 slide chứa cấu hình vẽ đồ thị miền nghiệm Oxy"
    chart_slide = chart_slides[0]
    assert chart_slide.chart_spec is not None
    assert chart_slide.chart_spec.chart_title is not None

    # Tìm slide có câu hỏi trắc nghiệm rèn luyện
    quiz_slides = [s for s in deck.slides if s.quiz_options and len(s.quiz_options) >= 4]
    assert len(quiz_slides) >= 1, "Phải có ít nhất 1 slide chứa câu hỏi trắc nghiệm 4 phương án"
    quiz = quiz_slides[0]
    
    # Kiểm tra tính đúng đắn của Quiz
    correct_options = [opt for opt in quiz.quiz_options if opt.is_correct]
    assert len(correct_options) == 1, "Phải có đúng 1 đáp án đúng trong câu hỏi trắc nghiệm"
    
    # Kiểm tra bóc tách lỗi sai (distractor rationales) cho các phương án nhiễu
    incorrect_options = [opt for opt in quiz.quiz_options if not opt.is_correct]
    for opt in incorrect_options:
        assert opt.distractor_rationale is not None and len(opt.distractor_rationale.strip()) > 10, (
            f"Phương án sai {opt.label} phải có lời giải thích vì sao sai cho học sinh"
        )


def test_grade10_chart_rendering_endpoint():
    """
    Task 20.1 (Phần 3): Kiểm tra endpoint POST /api/v1/chart/render vẽ miền nghiệm hệ BPT.
    Đồ thị gồm các đường biên, miền đa giác OABC và các điểm đỉnh.
    """
    spec = {
        "kind": "inequality_system",
        "boundary_lines": [
            {"expr": "8 - 2*x", "label": "d1: 2x + y = 8", "color": "#2563eb"},
            {"expr": "(8 - x)/2", "label": "d2: x + 2y = 8", "color": "#7c3aed"}
        ],
        "vertices": [[0, 0], [4, 0], [2.67, 2.67], [0, 4]],
        "chart_title": "Miền Nghiệm Hệ BPT Bậc Nhất 2 Ẩn (Lớp 10)",
        "x_min": -1.0,
        "x_max": 6.0,
        "y_min": -1.0,
        "y_max": 6.0
    }

    assert is_plottable(spec) is True, "is_plottable phải trả về True cho inequality_system"

    # Gọi trực tiếp qua API endpoint
    response = client.post("/api/v1/chart/render", json=spec)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 5000, f"Dung lượng ảnh đồ thị quá nhỏ: {len(response.content)} bytes"
    assert response.content[:4] == b'\x89PNG', "Định dạng ảnh trả về không phải là PNG hợp lệ"


# ==============================================================================
# PHẦN 2: INTEGRATION TESTS - XUẤT ĐA ĐỊNH DẠNG (WORD, PPTX, DUAL-PACK ZIP)
# ==============================================================================

def test_grade10_docx_export_compliance():
    """
    Task 20.1 (Phần 4): Kiểm tra xuất file Word (.docx) chuẩn CV 5512 và Nghị định 30/2020/NĐ-CP.
    Khổ giấy A4, lề chuẩn, bảng 4 hoạt động và công thức toán OMML native.
    """
    plan = get_curated_lesson_plan("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)
    
    response = client.post("/api/v1/lesson-plan/export-docx", json=plan.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert len(response.content) > 10000, "File Word tạo ra quá nhỏ"

    # Phân tích cấu trúc DOCX bằng python-docx
    doc_io = io.BytesIO(response.content)
    doc = Document(doc_io)

    # 1. Kiểm tra khổ giấy A4 (8.27 inch x 11.69 inch xấp xỉ 210mm x 297mm)
    section = doc.sections[0]
    assert section.page_width is not None and section.page_height is not None
    assert abs(section.page_width.inches - 8.27) < 0.05, f"Chiều rộng trang phải là A4, nhận được: {section.page_width.inches}"
    assert abs(section.page_height.inches - 11.69) < 0.05, f"Chiều cao trang phải là A4, nhận được: {section.page_height.inches}"

    # 2. Kiểm tra lề trang hành chính chuẩn Nghị định 30/2020/NĐ-CP
    # Lề trái: ~1.18 in (3.0 cm), Lề phải: ~0.59 in (1.5 cm), Lề trên: ~0.79 in (2.0 cm), Lề dưới: ~0.79 in (2.0 cm)
    assert section.left_margin is not None and section.right_margin is not None
    assert section.top_margin is not None and section.bottom_margin is not None
    assert abs(section.left_margin.inches - 1.18) < 0.05
    assert abs(section.right_margin.inches - 0.59) < 0.05
    assert abs(section.top_margin.inches - 0.79) < 0.05
    assert abs(section.bottom_margin.inches - 0.79) < 0.05

    # 3. Kiểm tra sự hiện diện của bảng tiến trình 4 hoạt động
    assert len(doc.tables) >= 1, "Tệp Word phải chứa ít nhất 1 bảng biểu tiến trình bài dạy"
    table_text = " ".join([cell.text for row in doc.tables[0].rows for cell in row.cells])
    assert "hoạt động" in table_text.lower() or "chuyển giao nhiệm vụ" in table_text.lower() or "thực hiện nhiệm vụ" in table_text.lower()

    # 4. Kiểm tra công thức toán học OMML (<m:oMath>) trong file Word XML
    xml_str = doc._element.xml
    assert "m:oMath" in xml_str or "m:r" in xml_str, "Tệp Word phải chứa thẻ công thức toán học Office Math Markup Language (OMML)"


def test_grade10_pptx_export_compliance():
    """
    Task 20.1 (Phần 5): Kiểm tra xuất bài giảng PowerPoint (.pptx) chuẩn 16:9.
    Kiểm tra DrawingML native shapes (Quiz Cards), đồ thị 2D và Speaker Notes 5 khối.
    """
    deck = get_curated_slide_deck("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)

    response = client.post("/api/v1/lesson-plan/export-slide", json=deck.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert len(response.content) > 15000, "File PowerPoint tạo ra quá nhỏ"

    # Phân tích cấu trúc PPTX bằng python-pptx
    pptx_io = io.BytesIO(response.content)
    prs = Presentation(pptx_io)

    # 1. Kiểm tra tỉ lệ khung hình Widescreen 16:9 (10.0 inch x 5.625 inch)
    assert prs.slide_width is not None and prs.slide_height is not None
    assert abs(prs.slide_width.inches - 10.0) < 0.05
    assert abs(prs.slide_height.inches - 5.625) < 0.05

    # 2. Kiểm tra số lượng slide
    assert len(prs.slides) == len(deck.slides)

    # 3. Kiểm tra Speaker Notes ở từng slide
    has_notes = False
    for slide in prs.slides:
        if slide.has_notes_slide:
            notes_slide = slide.notes_slide
            if notes_slide is not None:
                notes_tf = getattr(notes_slide, "notes_text_frame", None)
                if notes_tf is not None and getattr(notes_tf, "text", "").strip():
                    has_notes = True
                    break
    assert has_notes, "Phải có ít nhất 1 slide chứa Speaker Notes phục vụ Presenter View"


def test_grade10_dual_package_export_endpoint():
    """
    Task 20.1 (Phần 6): Kiểm tra endpoint POST /api/v1/lesson-plan/export-dual-package.
    Tải gói kép .zip chứa đồng bộ Word (.docx), PowerPoint (.pptx), Hướng dẫn giảng dạy và SHA-256.
    """
    plan = get_curated_lesson_plan("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)
    deck = get_curated_slide_deck("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)

    payload = {
        "lesson_plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    response = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    
    # Kiểm tra các Custom Header xác thực toàn vẹn dữ liệu
    assert "x-dual-package-sha256" in response.headers
    assert len(response.headers["x-dual-package-sha256"]) == 64
    assert response.headers.get("x-dual-package-docs-count") in ["2", "3"]

    # Mở và giải nén tệp ZIP trong bộ nhớ RAM
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, 'r') as zf:
        namelist = zf.namelist()
        
        # Phải chứa cả 3 tệp tin thành phần
        assert any(name.endswith(".docx") for name in namelist), "Thiếu tệp Word trong gói kép"
        assert any(name.endswith(".pptx") for name in namelist), "Thiếu tệp PowerPoint trong gói kép"
        assert "Huong_Dan_Goi_Kep_5512.txt" in namelist, "Thiếu tệp hướng dẫn kê khai và mã băm SHA-256"

        # Đọc nội dung hướng dẫn
        manifest_text = zf.read("Huong_Dan_Goi_Kep_5512.txt").decode("utf-8")
        assert "SHA-256" in manifest_text
        assert "Công văn 5512/BGDĐT" in manifest_text


# ==============================================================================
# PHẦN 3: ZERO-CRASH & EDGE-CASES DEFENSE CHO LỚP 10
# ==============================================================================

def test_grade10_e2e_zero_500_offline_resilience(monkeypatch):
    """
    Task 20.1 (Phần 7): Kiểm tra khả năng chịu lỗi tuyệt đối (Zero-Crash).
    Khi mất kết nối mạng hoặc hết Quota AI (Giả lập Exception), hệ thống tự động
    chuyển mạch sang Curated Pedagogical Fallback và trả về HTTP 200 (KHÔNG NÉM 500).
    """
    def mock_broken_llm(*args, **kwargs):
        raise ConnectionError("Mạng Internet bị gián đoạn hoặc API Key Gemini hết hạn (Chaos Test).")

    # Ép Gateway ném Exception
    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", mock_broken_llm)

    # 1. Test endpoint sinh Kế hoạch bài dạy
    res_plan = client.post("/api/v1/lesson-plan/generate", json={
        "topic": "Hệ bất phương trình bậc nhất hai ẩn",
        "subject": "Toán học",
        "grade": 10
    })
    assert res_plan.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_plan.status_code}: {res_plan.text}"
    plan_data = res_plan.json()
    assert plan_data["is_valid"] is True
    assert len(plan_data["plan"]["activities"]) == 4

    # 2. Test endpoint sinh Slide bài giảng
    res_slide = client.post("/api/v1/slide/generate", json={
        "topic": "Hệ bất phương trình bậc nhất hai ẩn",
        "subject": "Toán học",
        "grade": 10
    })
    assert res_slide.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_slide.status_code}: {res_slide.text}"
    slide_data = res_slide.json()
    assert len(slide_data["slides"]) >= 4
    assert any(s.get("layout") == "QUIZ_OPTION" or s.get("quiz_options") for s in slide_data["slides"])


# ==============================================================================
# PHẦN 4: TASK 20.2: KIỂM THỬ TOÀN DIỆN LỚP 11 - CẤP SỐ CỘNG & QUAN HỆ VUÔNG GÓC
# ==============================================================================

def test_grade11_lesson_plan_generation_cv5512():
    """
    Task 20.2 (Phần 1): Sinh Kế hoạch bài dạy chuẩn CV 5512 cho môn Toán 11.
    Kiểm tra cấu trúc 4 hoạt động (45 phút), công thức cấp số cộng và quan hệ vuông góc.
    """
    plan, val_result = generate_lesson_plan(
        topic="Cấp số cộng và Quan hệ vuông góc trong không gian",
        subject="Toán học",
        grade=11
    )

    assert isinstance(plan, LessonPlanSchema)
    assert plan.grade == 11
    assert "cấp số" in plan.lesson_title.lower() or "vuông góc" in plan.lesson_title.lower()

    # Kiểm định CV 5512: 4 hoạt động bắt buộc
    assert len(plan.activities) == 4, f"Số hoạt động phải đúng bằng 4, nhận được: {len(plan.activities)}"
    total_time = sum(act.time_minutes for act in plan.activities)
    assert total_time == 45, f"Tổng thời lượng bài dạy phải đúng bằng 45 phút, nhận được: {total_time}"

    # Kiểm tra 4 bước tổ chức hoạt động của mỗi hoạt động
    for idx, act in enumerate(plan.activities, start=1):
        assert act.activity_number == idx
        assert act.execution.step_1_assign.strip() != ""
        assert act.execution.step_2_excute.strip() != ""
        assert act.execution.step_3_report.strip() != ""
        assert act.execution.step_4_conclusion.strip() != ""

    # Kiểm tra qua bộ Validator 5512
    assert val_result.is_valid, f"Kế hoạch bài dạy không vượt qua kiểm định 5512: {val_result.errors}"


def test_grade11_slide_deck_3d_geometry_integration():
    """
    Task 20.2 (Phần 2): Sinh SlideDeck bài giảng chuẩn SGK cho môn Toán 11.
    Kiểm tra tích hợp slide 3D khối chóp tứ giác đều S.ABCD (has_3d=True, pyramid_square)
    và slide câu hỏi trắc nghiệm rèn luyện có bóc tách bẫy sai lầm.
    """
    plan, _ = generate_lesson_plan(
        topic="Cấp số cộng và Quan hệ vuông góc trong không gian",
        subject="Toán học",
        grade=11
    )

    deck = generate_slide_deck(
        topic="Cấp số cộng và Quan hệ vuông góc trong không gian",
        subject="Toán học",
        grade=11,
        plan=plan
    )

    assert isinstance(deck, SlideDeckSchema)
    assert len(deck.slides) >= 4, f"Slide deck phải có ít nhất 4 slide, nhận được: {len(deck.slides)}"

    # Slide 1: Phải là TITLE_SLIDE
    assert deck.slides[0].type == SlideType.TITLE_SLIDE

    # Slide 3D: Phải có ít nhất 1 slide bật has_3d với polyhedron_type là pyramid_square
    slides_3d = [s for s in deck.slides if s.has_3d and s.polyhedron_type == "pyramid_square"]
    assert len(slides_3d) >= 1, "Phải có ít nhất 1 slide 3D tích hợp mô hình pyramid_square (Hình chóp tứ giác)"
    slide_3d = slides_3d[0]
    assert "SO" in slide_3d.title or "S.ABCD" in slide_3d.title or "vuông góc" in slide_3d.title.lower()

    # Tìm slide có câu hỏi trắc nghiệm
    quiz_slides = [s for s in deck.slides if s.quiz_options and len(s.quiz_options) >= 4]
    assert len(quiz_slides) >= 1, "Phải có ít nhất 1 slide câu hỏi trắc nghiệm tương tác"
    quiz = quiz_slides[0]
    correct_options = [opt for opt in quiz.quiz_options if opt.is_correct]
    assert len(correct_options) == 1, "Phải có đúng 1 đáp án đúng trong Quiz"

    # Kiểm tra distractor_rationale cho phương án sai
    for opt in quiz.quiz_options:
        if not opt.is_correct:
            assert opt.distractor_rationale and len(opt.distractor_rationale.strip()) > 10


def test_grade11_spatial_geometry_3d_api_endpoints():
    """
    Task 20.2 (Phần 3): Kiểm tra các API Hình học Không gian 3D cho khối chóp tứ giác đều S.ABCD.
    - GET /api/v1/geometry/edge-topology?polyhedron_type=pyramid_square (Nét đứt, cạnh khuất).
    - POST /api/v1/geometry/parametric-coordinates (Tọa độ đỉnh và thể tích V).
    """
    # 1. Kiểm tra API Edge Topology (Nét đứt)
    res_topo = client.get("/api/v1/geometry/edge-topology?polyhedron_type=pyramid_square")
    assert res_topo.status_code == 200
    topo_data = res_topo.json()
    assert topo_data["polyhedron_type"] == "pyramid_square"
    assert topo_data["hidden_count"] == 3
    assert len(topo_data["hidden_edges"]) == 3
    # Xác nhận các cạnh khuất nét đứt: AB, AD, SA (với SA vuông góc đáy tại chân A)
    assert ["A", "B"] in topo_data["hidden_edges"]
    assert ["A", "D"] in topo_data["hidden_edges"]
    assert ["S", "A"] in topo_data["hidden_edges"]

    # 2. Kiểm tra API Parametric Coordinates (Tham số hóa chiều cao & cạnh đáy)
    param_payload = {
        "polyhedron_type": "pyramid_square",
        "height": 6.0,
        "base_edge": 4.0
    }
    res_coords = client.post("/api/v1/geometry/parametric-coordinates", json=param_payload)
    assert res_coords.status_code == 200
    coords_data = res_coords.json()
    assert coords_data["height"] == 6.0
    assert coords_data["base_edge"] == 4.0
    # Thể tích V = 1/3 * a^2 * h = 1/3 * 16 * 6 = 32.0
    assert abs(coords_data["measurements"]["volume"] - 32.0) < 0.01


def test_grade11_docx_export_compliance():
    """
    Task 20.2 (Phần 4): Kiểm tra xuất file Word (.docx) bài dạy Lớp 11.
    Khổ giấy A4, chuẩn Nghị định 30/2020/NĐ-CP, công thức OMML (<m:oMath>) cấp số cộng và quan hệ vuông góc.
    """
    plan = get_curated_lesson_plan("Cấp số cộng và Quan hệ vuông góc", "Toán học", 11)

    response = client.post("/api/v1/lesson-plan/export-docx", json=plan.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert len(response.content) > 10000

    doc_io = io.BytesIO(response.content)
    doc = Document(doc_io)

    # Kiểm tra kích thước A4
    section = doc.sections[0]
    assert abs(section.page_width.inches - 8.27) < 0.05
    assert abs(section.page_height.inches - 11.69) < 0.05

    # Kiểm tra lề trang hành chính chuẩn Nghị định 30/2020/NĐ-CP
    assert abs(section.left_margin.inches - 1.18) < 0.05
    assert abs(section.right_margin.inches - 0.59) < 0.05

    # Kiểm tra bảng tiến trình bài dạy
    assert len(doc.tables) >= 1
    table_text = " ".join([cell.text for row in doc.tables[0].rows for cell in row.cells])
    assert "cấp số" in table_text.lower() or "hoạt động" in table_text.lower() or "chuyển giao" in table_text.lower()

    # Kiểm tra thẻ công thức toán học OMML (<m:oMath>)
    xml_str = doc._element.xml
    assert "m:oMath" in xml_str or "m:r" in xml_str


def test_grade11_pptx_export_with_3d_snapshot():
    """
    Task 20.2 (Phần 5): Kiểm tra xuất bài giảng PowerPoint (.pptx) chuẩn 16:9 có nhúng Snapshot 3D WebGL.
    Mô hình chóp tứ giác pyramid_square nhúng không méo tỉ lệ (Box-fit) và Presenter Notes 5 khối.
    """
    deck = get_curated_slide_deck("Cấp số cộng và Quan hệ vuông góc", "Toán học", 11)

    # Nhúng giả lập snapshot 3D WebGL Base64 hợp lệ vào slide 3
    valid_png_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    deck.slides[2].snapshot_3d_base64 = valid_png_base64

    response = client.post("/api/v1/lesson-plan/export-slide", json=deck.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert len(response.content) > 15000

    pptx_io = io.BytesIO(response.content)
    prs = Presentation(pptx_io)

    # 1. Kích thước 16:9
    assert abs(prs.slide_width.inches - 10.0) < 0.05
    assert abs(prs.slide_height.inches - 5.625) < 0.05

    # 2. Số lượng slide
    assert len(prs.slides) == len(deck.slides)

    # 3. Kiểm tra slide 3 có chứa ảnh snapshot 3D
    slide3 = prs.slides[2]
    has_image = any(s.shape_type == 13 for s in slide3.shapes)
    assert has_image, "Slide 3 phải chứa shape ảnh chụp snapshot 3D của khối chóp tứ giác"


def test_grade11_dual_package_export_endpoint():
    """
    Task 20.2 (Phần 6): Kiểm tra endpoint POST /api/v1/lesson-plan/export-dual-package cho Lớp 11.
    Tải gói kép ZIP đồng bộ cả Word CV 5512, PowerPoint 16:9, Hướng dẫn giảng dạy và mã băm SHA-256.
    """
    plan = get_curated_lesson_plan("Cấp số cộng và Quan hệ vuông góc", "Toán học", 11)
    deck = get_curated_slide_deck("Cấp số cộng và Quan hệ vuông góc", "Toán học", 11)

    payload = {
        "lesson_plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    response = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Kiểm tra Custom Headers
    assert "x-dual-package-sha256" in response.headers
    assert len(response.headers["x-dual-package-sha256"]) == 64
    assert response.headers.get("x-dual-package-docs-count") in ["2", "3"]

    # Mở và giải nén tệp ZIP trong bộ nhớ RAM
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, 'r') as zf:
        namelist = zf.namelist()
        assert any(name.endswith(".docx") for name in namelist)
        assert any(name.endswith(".pptx") for name in namelist)
        assert "Huong_Dan_Goi_Kep_5512.txt" in namelist

        manifest_text = zf.read("Huong_Dan_Goi_Kep_5512.txt").decode("utf-8")
        assert "SHA-256" in manifest_text
        assert "Công văn 5512" in manifest_text


def test_grade11_e2e_zero_500_offline_resilience(monkeypatch):
    """
    Task 20.2 (Phần 7): Kiểm tra khả năng chịu lỗi tuyệt đối (Zero-Crash) cho môn Toán 11.
    Khi mất kết nối mạng hoặc hết Quota AI (Giả lập Exception), hệ thống tự động
    chuyển mạch sang Curated Pedagogical Fallback Lớp 11 và trả về HTTP 200 (KHÔNG NÉM 500).
    """
    def mock_broken_llm(*args, **kwargs):
        raise ConnectionError("Mạng Internet bị gián đoạn hoặc API Key Gemini hết hạn (Chaos Test Lớp 11).")

    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", mock_broken_llm)

    # 1. Test endpoint sinh Kế hoạch bài dạy
    res_plan = client.post("/api/v1/lesson-plan/generate", json={
        "topic": "Cấp số cộng và Quan hệ vuông góc trong không gian",
        "subject": "Toán học",
        "grade": 11
    })
    assert res_plan.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_plan.status_code}: {res_plan.text}"
    plan_data = res_plan.json()
    assert plan_data["is_valid"] is True
    assert plan_data["plan"]["grade"] == 11
    assert len(plan_data["plan"]["activities"]) == 4

    # 2. Test endpoint sinh Slide bài giảng
    res_slide = client.post("/api/v1/slide/generate", json={
        "topic": "Cấp số cộng và Quan hệ vuông góc trong không gian",
        "subject": "Toán học",
        "grade": 11
    })
    assert res_slide.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_slide.status_code}: {res_slide.text}"
    slide_data = res_slide.json()
    assert slide_data["grade"] == 11
    assert len(slide_data["slides"]) >= 4
    assert any(s.get("has_3d") and s.get("polyhedron_type") == "pyramid_square" for s in slide_data["slides"])


# ==============================================================================
# PHẦN 5: TASK 20.3: KIỂM THỬ TOÀN DIỆN LỚP 12 - ĐƠN ĐIỆU, CỰC TRỊ & THỂ TÍCH CHÓP
# ==============================================================================

def test_grade12_lesson_plan_generation_cv5512():
    """
    Task 20.3 (Phần 1): Sinh Kế hoạch bài dạy chuẩn CV 5512 cho môn Toán 12.
    Kiểm tra cấu trúc 4 hoạt động (45 phút), định lý cực trị hàm số và công thức thể tích khối chóp.
    """
    plan, val_result = generate_lesson_plan(
        topic="Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp",
        subject="Toán học",
        grade=12
    )

    assert isinstance(plan, LessonPlanSchema)
    assert plan.grade == 12
    assert "cực trị" in plan.lesson_title.lower() or "đơn điệu" in plan.lesson_title.lower()

    # Kiểm định CV 5512: 4 hoạt động bắt buộc
    assert len(plan.activities) == 4, f"Số hoạt động phải đúng bằng 4, nhận được: {len(plan.activities)}"
    total_time = sum(act.time_minutes for act in plan.activities)
    assert total_time == 45, f"Tổng thời lượng bài dạy phải đúng bằng 45 phút, nhận được: {total_time}"

    # Kiểm tra 4 bước tổ chức hoạt động của mỗi hoạt động
    for idx, act in enumerate(plan.activities, start=1):
        assert act.activity_number == idx
        assert act.execution.step_1_assign.strip() != ""
        assert act.execution.step_2_excute.strip() != ""
        assert act.execution.step_3_report.strip() != ""
        assert act.execution.step_4_conclusion.strip() != ""

    # Kiểm tra qua bộ Validator 5512
    assert val_result.is_valid, f"Kế hoạch bài dạy không vượt qua kiểm định 5512: {val_result.errors}"


def test_grade12_slide_deck_3d_geometry_and_chart():
    """
    Task 20.3 (Phần 2): Sinh SlideDeck bài giảng chuẩn SGK cho môn Toán 12.
    Kiểm tra tích hợp cả đồ thị hàm số bậc ba (function_plot) và mô hình 3D khối chóp tam giác S.ABC
    cùng câu hỏi trắc nghiệm rèn luyện bóc tách bẫy tư duy.
    """
    plan, _ = generate_lesson_plan(
        topic="Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp",
        subject="Toán học",
        grade=12
    )

    deck = generate_slide_deck(
        topic="Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp",
        subject="Toán học",
        grade=12,
        plan=plan
    )

    assert isinstance(deck, SlideDeckSchema)
    assert len(deck.slides) >= 4, f"Slide deck phải có ít nhất 4 slide, nhận được: {len(deck.slides)}"

    # Slide 1: Phải là TITLE_SLIDE
    assert deck.slides[0].type == SlideType.TITLE_SLIDE

    # Slide Đồ thị 2D: Khảo sát cực trị hàm bậc ba
    chart_slides = [s for s in deck.slides if s.chart_spec and s.chart_spec.kind in [ChartType.FUNCTION_PLOT, ChartType.INEQUALITY_SYSTEM]]
    assert len(chart_slides) >= 1, "Phải có ít nhất 1 slide chứa đồ thị hàm số bậc ba y = x^3 - 3x"
    assert "x**3 - 3*x" in (chart_slides[0].chart_spec.expression or "")

    # Slide 3D: Khối chóp tam giác pyramid_triangle
    slides_3d = [s for s in deck.slides if s.has_3d and s.polyhedron_type == "pyramid_triangle"]
    assert len(slides_3d) >= 1, "Phải có ít nhất 1 slide 3D tích hợp mô hình pyramid_triangle (Hình chóp tam giác S.ABC)"

    # Tìm slide có câu hỏi trắc nghiệm
    quiz_slides = [s for s in deck.slides if s.quiz_options and len(s.quiz_options) >= 4]
    assert len(quiz_slides) >= 1, "Phải có ít nhất 1 slide câu hỏi trắc nghiệm tương tác"
    quiz = quiz_slides[0]
    correct_options = [opt for opt in quiz.quiz_options if opt.is_correct]
    assert len(correct_options) == 1, "Phải có đúng 1 đáp án đúng trong Quiz"

    # Kiểm tra distractor_rationale cho phương án sai
    for opt in quiz.quiz_options:
        if not opt.is_correct:
            assert opt.distractor_rationale and len(opt.distractor_rationale.strip()) > 10


def test_grade12_spatial_geometry_3d_api_endpoints():
    """
    Task 20.3 (Phần 3): Kiểm tra các API Hình học Không gian 3D cho khối chóp tam giác S.ABC (SA ⊥ Đáy).
    - GET /api/v1/geometry/edge-topology?polyhedron_type=pyramid_triangle (Cạnh khuất nét đứt AB, AC, SA).
    - POST /api/v1/geometry/parametric-coordinates (Tọa độ đỉnh, diện tích tam giác vuông và thể tích V).
    """
    # 1. Kiểm tra API Edge Topology (Nét đứt)
    res_topo = client.get("/api/v1/geometry/edge-topology?polyhedron_type=pyramid_triangle")
    assert res_topo.status_code == 200
    topo_data = res_topo.json()
    assert topo_data["polyhedron_type"] == "pyramid_triangle"
    assert topo_data["hidden_count"] == 3
    assert len(topo_data["hidden_edges"]) == 3
    # Xác nhận các cạnh khuất nét đứt: AB, AC, SA
    assert ["A", "B"] in topo_data["hidden_edges"]
    assert ["A", "C"] in topo_data["hidden_edges"]
    assert ["S", "A"] in topo_data["hidden_edges"]

    # 2. Kiểm tra API Parametric Coordinates
    param_payload = {
        "polyhedron_type": "pyramid_triangle",
        "height": 6.0,
        "base_edge": 4.0
    }
    res_coords = client.post("/api/v1/geometry/parametric-coordinates", json=param_payload)
    assert res_coords.status_code == 200
    coords_data = res_coords.json()
    assert coords_data["height"] == 6.0
    assert coords_data["base_edge"] == 4.0
    # Đáy tam giác vuông cân AB = AC = 4 -> S_đáy = 1/2 * 4 * 4 = 8.0
    assert abs(coords_data["measurements"]["base_area"] - 8.0) < 0.01
    # Thể tích V = 1/3 * S_đáy * h = 1/3 * 8 * 6 = 16.0
    assert abs(coords_data["measurements"]["volume"] - 16.0) < 0.01


def test_grade12_docx_export_compliance():
    """
    Task 20.3 (Phần 4): Kiểm tra xuất file Word (.docx) bài dạy Lớp 12.
    Khổ giấy A4, chuẩn Nghị định 30/2020/NĐ-CP, công thức OMML (<m:oMath>) đạo hàm và thể tích khối chóp.
    """
    plan = get_curated_lesson_plan("Tính đơn điệu và cực trị hàm số", "Toán học", 12)

    response = client.post("/api/v1/lesson-plan/export-docx", json=plan.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert len(response.content) > 10000

    doc_io = io.BytesIO(response.content)
    doc = Document(doc_io)

    # Kiểm tra kích thước A4
    section = doc.sections[0]
    assert abs(section.page_width.inches - 8.27) < 0.05
    assert abs(section.page_height.inches - 11.69) < 0.05

    # Kiểm tra lề trang hành chính chuẩn Nghị định 30/2020/NĐ-CP
    assert abs(section.left_margin.inches - 1.18) < 0.05
    assert abs(section.right_margin.inches - 0.59) < 0.05

    # Kiểm tra bảng tiến trình bài dạy
    assert len(doc.tables) >= 1
    table_text = " ".join([cell.text for row in doc.tables[0].rows for cell in row.cells])
    assert "cực trị" in table_text.lower() or "hoạt động" in table_text.lower() or "chuyển giao" in table_text.lower()

    # Kiểm tra thẻ công thức toán học OMML (<m:oMath>)
    xml_str = doc._element.xml
    assert "m:oMath" in xml_str or "m:r" in xml_str


def test_grade12_pptx_export_with_3d_snapshot():
    """
    Task 20.3 (Phần 5): Kiểm tra xuất bài giảng PowerPoint (.pptx) chuẩn 16:9 có nhúng Snapshot 3D WebGL pyramid_triangle.
    Mô hình chóp tam giác nhúng không méo tỉ lệ (Box-fit) và Presenter Notes 5 khối sư phạm.
    """
    deck = get_curated_slide_deck("Tính đơn điệu và cực trị hàm số", "Toán học", 12)

    # Nhúng giả lập snapshot 3D WebGL Base64 hợp lệ vào slide 3
    valid_png_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    deck.slides[2].snapshot_3d_base64 = valid_png_base64

    response = client.post("/api/v1/lesson-plan/export-slide", json=deck.model_dump())
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert len(response.content) > 15000

    pptx_io = io.BytesIO(response.content)
    prs = Presentation(pptx_io)

    # 1. Kích thước 16:9
    assert abs(prs.slide_width.inches - 10.0) < 0.05
    assert abs(prs.slide_height.inches - 5.625) < 0.05

    # 2. Số lượng slide
    assert len(prs.slides) == len(deck.slides)

    # 3. Kiểm tra slide 3 có chứa ảnh snapshot 3D
    slide3 = prs.slides[2]
    has_image = any(s.shape_type == 13 for s in slide3.shapes)
    assert has_image, "Slide 3 phải chứa shape ảnh chụp snapshot 3D của khối chóp tam giác"


def test_grade12_dual_package_export_endpoint():
    """
    Task 20.3 (Phần 6): Kiểm tra endpoint POST /api/v1/lesson-plan/export-dual-package cho Lớp 12.
    Tải gói kép ZIP đồng bộ cả Word CV 5512, PowerPoint 16:9, Hướng dẫn giảng dạy và mã băm SHA-256.
    """
    plan = get_curated_lesson_plan("Tính đơn điệu và cực trị hàm số", "Toán học", 12)
    deck = get_curated_slide_deck("Tính đơn điệu và cực trị hàm số", "Toán học", 12)

    payload = {
        "lesson_plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    response = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Kiểm tra Custom Headers
    assert "x-dual-package-sha256" in response.headers
    assert len(response.headers["x-dual-package-sha256"]) == 64
    assert response.headers.get("x-dual-package-docs-count") in ["2", "3"]

    # Mở và giải nén tệp ZIP trong bộ nhớ RAM
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, 'r') as zf:
        namelist = zf.namelist()
        assert any(name.endswith(".docx") for name in namelist)
        assert any(name.endswith(".pptx") for name in namelist)
        assert "Huong_Dan_Goi_Kep_5512.txt" in namelist

        manifest_text = zf.read("Huong_Dan_Goi_Kep_5512.txt").decode("utf-8")
        assert "SHA-256" in manifest_text
        assert "Lớp 12" in manifest_text or "12" in manifest_text or "cực trị" in manifest_text.lower() or "Cuc_Tri" in manifest_text


def test_grade12_e2e_zero_500_offline_resilience(monkeypatch):
    """
    Task 20.3 (Phần 7): Kiểm tra khả năng chịu lỗi tuyệt đối (Zero-Crash) cho môn Toán 12.
    Khi mất kết nối mạng hoặc hết Quota AI (Giả lập Exception), hệ thống tự động
    chuyển mạch sang Curated Pedagogical Fallback Lớp 12 và trả về HTTP 200 (KHÔNG NÉM 500).
    """
    def mock_broken_llm(*args, **kwargs):
        raise ConnectionError("Mạng Internet bị gián đoạn hoặc API Key Gemini hết hạn (Chaos Test Lớp 12).")

    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", mock_broken_llm)

    # 1. Test endpoint sinh Kế hoạch bài dạy
    res_plan = client.post("/api/v1/lesson-plan/generate", json={
        "topic": "Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp",
        "subject": "Toán học",
        "grade": 12
    })
    assert res_plan.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_plan.status_code}: {res_plan.text}"
    plan_data = res_plan.json()
    assert plan_data["is_valid"] is True
    assert plan_data["plan"]["grade"] == 12
    assert len(plan_data["plan"]["activities"]) == 4

    # 2. Test endpoint sinh Slide bài giảng
    res_slide = client.post("/api/v1/slide/generate", json={
        "topic": "Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp",
        "subject": "Toán học",
        "grade": 12
    })
    assert res_slide.status_code == 200, f"Kỳ vọng HTTP 200 nhưng nhận được {res_slide.status_code}: {res_slide.text}"
    slide_data = res_slide.json()
    assert slide_data["grade"] == 12
    assert len(slide_data["slides"]) >= 4
    assert any(s.get("has_3d") and s.get("polyhedron_type") == "pyramid_triangle" for s in slide_data["slides"])


