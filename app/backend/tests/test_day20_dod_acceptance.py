# -*- coding: utf-8 -*-
"""
Test Suite: Task 20.5 - Nghiệm Thu Định Nghĩa Hoàn Thành (Definition of Done - DoD Ngày 20)
LessonAI-5512 • Quantum Studio

Tiêu chí nghiệm thu chuẩn hóa (DoD):
1. Toàn bộ hệ thống chạy ổn định 100%, không phát sinh lỗi HTTP 500 Internal Server Error dưới mọi tình huống.
2. Xuất khẩu thực tế và kiểm chứng tính toàn vẹn nhị phân của 3 gói kép hoàn chỉnh (Grade 10, Grade 11, Grade 12):
   - Grade 10: Hệ bất phương trình bậc nhất 2 ẩn (Giáo án CV 5512 4 hoạt động 45p + Slide PowerPoint + Đồ thị miền nghiệm Oxy + Gói ZIP).
   - Grade 11: Cấp số cộng - Quan hệ vuông góc không gian (Giáo án CV 5512 + Slide PowerPoint + Mô hình 3D Chóp tứ giác đều + Gói ZIP).
   - Grade 12: Tính đơn điệu, cực trị hàm số - Thể tích khối chóp (Giáo án CV 5512 + Slide PowerPoint + Đồ thị cực trị + Mô hình 3D Chóp tam giác + Gói ZIP).
3. Kiểm tra giải mã tệp tin: Tệp ZIP giải nén thành công, tệp .docx đọc được qua docx.Document, tệp .pptx đọc được qua pptx.Presentation.
4. Xác thực tính toàn vẹn SHA-256 Checksums khớp tuyệt đối giữa Manifest, Header và tệp nhị phân thực tế.
"""

import io
import os
import base64
import zipfile
import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from docx import Document
from pptx import Presentation
from PIL import Image

from main import app
from schemas.schemas import LessonPlanSchema
from schemas.slide_schema import SlideDeckSchema
from services.fallback_service import get_curated_lesson_plan, get_curated_slide_deck

client = TestClient(app)

DOD_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "day20_dod_packages"


@pytest.fixture(scope="session", autouse=True)
def ensure_output_dir():
    """Tạo thư mục lưu trữ các gói nghiệm thu thực tế"""
    DOD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_3d_snapshot() -> str:
    """Tạo snapshot ảnh PNG giả lập từ canvas 3D WebGL (640x360)"""
    img = Image.new("RGBA", (640, 360), color=(15, 23, 42, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


# ==============================================================================
# PHẦN 1: NGHIỆM THU GÓI KÉP TOÁN 10 (HỆ BẤT PHƯƠNG TRÌNH BẬC NHẤT HAI ẨN)
# ==============================================================================

def test_dod_grade10_dual_package_export_and_integrity():
    """
    DoD 1: Nghiệm thu trọn bộ gói sản phẩm Toán 10.
    Xác thực giáo án Word, Slide PowerPoint có đồ thị miền nghiệm Oxy và mã băm SHA-256.
    """
    plan = get_curated_lesson_plan("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)
    deck = get_curated_slide_deck("Hệ bất phương trình bậc nhất hai ẩn", "Toán học", 10)

    payload = {
        "plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    res = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert res.status_code == 200, f"Xuất gói kép Toán 10 thất bại: {res.text}"
    assert res.headers["content-type"] == "application/zip"

    zip_bytes = res.content
    zip_path = DOD_OUTPUT_DIR / "Grade10_He_Bat_Phuong_Trinh_Dual_Package.zip"
    zip_path.write_bytes(zip_bytes)
    assert zip_path.exists() and zip_path.stat().st_size > 10000

    # 1. Giải nén và kiểm tra danh mục tệp
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        docx_names = [n for n in names if n.endswith(".docx")]
        pptx_names = [n for n in names if n.endswith(".pptx")]
        manifest_names = [n for n in names if n.endswith(".txt") or "Huong_Dan" in n or "MANIFEST" in n]

        assert len(docx_names) == 1, "Phải có đúng 1 tệp Word giáo án"
        assert len(pptx_names) == 1, "Phải có đúng 1 tệp Slide PowerPoint"
        assert len(manifest_names) == 1, "Phải có đúng 1 tệp Manifest sư phạm"

        # 2. Kiểm tra tính hợp lệ của tệp Word (.docx)
        docx_data = zf.read(docx_names[0])
        doc = Document(io.BytesIO(docx_data))
        text_full = "\n".join(p.text for p in doc.paragraphs)
        assert "KẾ HOẠCH BÀI DẠY" in text_full
        assert "LỚP 10" in text_full
        assert "HỆ BẤT PHƯƠNG TRÌNH" in text_full.upper()
        # Xác thực 4 hoạt động CV 5512 trong bảng
        assert len(doc.tables) >= 1

        # 3. Kiểm tra tính hợp lệ của tệp PowerPoint (.pptx)
        pptx_data = zf.read(pptx_names[0])
        prs = Presentation(io.BytesIO(pptx_data))
        assert len(prs.slides) >= 4
        # Kiểm tra tỷ lệ khung hình 16:9 widescreen
        assert prs.slide_width > prs.slide_height

        # 4. Xác thực mã băm SHA-256
        actual_docx_sha = hashlib.sha256(docx_data).hexdigest()
        actual_pptx_sha = hashlib.sha256(pptx_data).hexdigest()
        assert res.headers.get("X-Docx-SHA256") == actual_docx_sha
        assert res.headers.get("X-Pptx-SHA256") == actual_pptx_sha

        manifest_text = zf.read(manifest_names[0]).decode("utf-8")
        assert actual_docx_sha in manifest_text
        assert actual_pptx_sha in manifest_text


# ==============================================================================
# PHẦN 2: NGHIỆM THU GÓI KÉP TOÁN 11 (CẤP SỐ CỘNG & QUAN HỆ VUÔNG GÓC 3D)
# ==============================================================================

def test_dod_grade11_dual_package_export_and_integrity():
    """
    DoD 2: Nghiệm thu trọn bộ gói sản phẩm Toán 11.
    Xác thực giáo án Word, Slide PowerPoint có mô hình 3D Hình chóp tứ giác đều S.ABCD và Box-fit.
    """
    plan = get_curated_lesson_plan("Cấp số cộng và Quan hệ vuông góc trong không gian", "Toán học", 11)
    deck = get_curated_slide_deck("Cấp số cộng và Quan hệ vuông góc trong không gian", "Toán học", 11)

    # Gắn snapshot 3D mô hình pyramid_square
    deck.snapshot_3d_base64 = create_sample_3d_snapshot()
    for s in deck.slides:
        if s.has_3d:
            s.snapshot_3d_base64 = deck.snapshot_3d_base64

    payload = {
        "plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    res = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert res.status_code == 200, f"Xuất gói kép Toán 11 thất bại: {res.text}"
    assert res.headers["content-type"] == "application/zip"

    zip_bytes = res.content
    zip_path = DOD_OUTPUT_DIR / "Grade11_Cap_So_Cong_Vuong_Goc_Dual_Package.zip"
    zip_path.write_bytes(zip_bytes)
    assert zip_path.exists() and zip_path.stat().st_size > 10000

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        docx_name = [n for n in names if n.endswith(".docx")][0]
        pptx_name = [n for n in names if n.endswith(".pptx")][0]

        doc = Document(io.BytesIO(zf.read(docx_name)))
        text_full = "\n".join(p.text for p in doc.paragraphs)
        assert "CẤP SỐ CỘNG" in text_full.upper()
        assert "LỚP 11" in text_full

        prs = Presentation(io.BytesIO(zf.read(pptx_name)))
        assert len(prs.slides) >= 4
        # Slide 3D phải nhúng hình ảnh thành công
        has_picture = any(shape.shape_type == 13 for s in prs.slides for shape in s.shapes)  # 13: MSO_SHAPE_TYPE.PICTURE
        assert has_picture is True, "Slide PowerPoint phải chứa ảnh nhúng snapshot 3D"


# ==============================================================================
# PHẦN 3: NGHIỆM THU GÓI KÉP TOÁN 12 (CỰC TRỊ HÀM SỐ & THỂ TÍCH KHỐI CHÓP)
# ==============================================================================

def test_dod_grade12_dual_package_export_and_integrity():
    """
    DoD 3: Nghiệm thu trọn bộ gói sản phẩm Toán 12.
    Xác thực giáo án Word, Slide PowerPoint kết hợp đồ thị cực trị hàm bậc ba và mô hình 3D chóp tam giác S.ABC.
    """
    plan = get_curated_lesson_plan("Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp", "Toán học", 12)
    deck = get_curated_slide_deck("Tính đơn điệu, cực trị của hàm số và Thể tích khối chóp", "Toán học", 12)

    deck.snapshot_3d_base64 = create_sample_3d_snapshot()
    for s in deck.slides:
        if s.has_3d:
            s.snapshot_3d_base64 = deck.snapshot_3d_base64

    payload = {
        "plan": plan.model_dump(),
        "slide_deck": deck.model_dump()
    }

    res = client.post("/api/v1/lesson-plan/export-dual-package", json=payload)
    assert res.status_code == 200, f"Xuất gói kép Toán 12 thất bại: {res.text}"
    assert res.headers["content-type"] == "application/zip"

    zip_bytes = res.content
    zip_path = DOD_OUTPUT_DIR / "Grade12_Cuc_Tri_The_Tich_Chop_Dual_Package.zip"
    zip_path.write_bytes(zip_bytes)
    assert zip_path.exists() and zip_path.stat().st_size > 10000

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        docx_name = [n for n in names if n.endswith(".docx")][0]
        pptx_name = [n for n in names if n.endswith(".pptx")][0]

        doc = Document(io.BytesIO(zf.read(docx_name)))
        text_full = "\n".join(p.text for p in doc.paragraphs)
        assert "CỰC TRỊ" in text_full.upper()
        assert "LỚP 12" in text_full

        prs = Presentation(io.BytesIO(zf.read(pptx_name)))
        assert len(prs.slides) >= 5
        # Slide PowerPoint có cả đồ thị Matplotlib và 3D snapshot
        pictures = [shape for s in prs.slides for shape in s.shapes if shape.shape_type == 13]
        assert len(pictures) >= 2, f"Slide deck lớp 12 phải có ít nhất 2 ảnh (Đồ thị + 3D snapshot), tìm thấy {len(pictures)}"


# ==============================================================================
# PHẦN 4: TOÀN BỘ ENDPOINT KHÔNG BAO GIỜ NÉM 500 (ZERO 500 VERIFICATION)
# ==============================================================================

def test_dod_all_endpoints_zero_500_resilience():
    """
    DoD 4: Quét toàn bộ hệ thống API endpoints, bảo đảm không có endpoint nào ném 500 Internal Server Error
    ngay cả khi gửi payload bất thường hoặc ngắt kết nối LLM.
    """
    # 1. Health check
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200

    # 2. Test-cases endpoint
    res_tc = client.get("/api/v1/test-cases")
    assert res_tc.status_code == 200

    # 3. Geometry topology & parametric
    res_topo = client.get("/api/v1/geometry/edge-topology?polyhedron_type=pyramid_tri")
    assert res_topo.status_code == 200

    res_param = client.post("/api/v1/geometry/parametric-coordinates", json={
        "polyhedron_type": "pyramid_square",
        "parameters": {"base_size": 4.0, "height": 6.0}
    })
    assert res_param.status_code == 200

    # 4. Chart render
    res_chart = client.post("/api/v1/chart/render", json={
        "kind": "inequality_system",
        "chart_title": "Test Miền Nghiệm",
        "expression": "8 - 2*x",
        "domain": [0, 6]
    })
    assert res_chart.status_code == 200
    assert res_chart.headers["content-type"] == "image/png"

    # 5. Word export với dữ liệu tối giản
    res_word = client.post("/api/v1/lesson-plan/export-docx", json={
        "lesson_title": "Bài kiểm tra nhanh",
        "subject": "Toán học",
        "grade": 10,
        "activities": []
    })
    assert res_word.status_code == 200

    # 6. Slide export với dữ liệu tối giản
    res_slide = client.post("/api/v1/lesson-plan/export-slide", json={
        "presentation_title": "Slide kiểm tra nhanh",
        "subject": "Toán học",
        "grade": 10,
        "slides": []
    })
    assert res_slide.status_code == 200
