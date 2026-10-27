"""
test_phase5_e2e_rag_system.py
Kiểm thử Toàn diện Pha 5 (End-to-End Pedagogical RAG System):
1. API GET /api/v1/curriculum/math12: Cây 7 Chương -> 19 Bài -> YCCĐ + Thống kê số lượng Slide & Câu hỏi RAG.
2. API POST /api/v1/rag/preview: Xem trước Dàn ý (Skeleton), Slide mẫu KNTT 12 và Ngân hàng câu hỏi có lời giải 3 bước.
3. Sinh Kế hoạch bài dạy 5512 và SlideDeck có gắn huy hiệu nguồn RAG (source_refs).
4. Xuất trọn bộ Dual-Package ZIP (Word + PowerPoint) đồng bộ từ dữ liệu RAG Toán 12.
"""

import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.schemas import LessonRequest, RAGPreviewRequest
from rag.curriculum_registry import CurriculumRegistry
from rag.retriever import Math12HybridRetriever


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def speed_up_offline_tests(monkeypatch):
    """Giúp test chạy tức thì (< 1s) trong môi trường kiểm thử offline không có mạng."""
    def fast_mock_llm(*args, **kwargs):
        raise ConnectionError("Offline test mode: kích hoạt nhanh Retrieval Fallback")
    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", fast_mock_llm)


def test_api_curriculum_math12_structure_and_stats(client):
    """Kiểm tra API GET /api/v1/curriculum/math12 trả về đầy đủ 7 chương, 19 bài và kho dữ liệu RAG."""
    response = client.get("/api/v1/curriculum/math12")
    assert response.status_code == 200
    data = response.json()

    assert data["subject"] == "Toán học"
    assert data["grade"] == 12
    assert "GDPT 2018" in data["curriculum_standard"]
    assert data["total_chapters"] == 7
    assert data["total_lessons"] == 19
    assert data["total_slides"] >= 1840
    assert data["total_questions"] >= 890

    chapters = data["chapters"]
    assert len(chapters) == 7

    # Kiểm tra Chương 1
    ch1 = chapters[0]
    assert ch1["chapter_id"] == "M12-C1"
    assert len(ch1["lessons"]) == 5
    b1 = ch1["lessons"][0]
    assert b1["lesson_id"] == "M12-C1-B1"
    assert b1["available_slides_count"] > 50
    assert b1["available_questions_count"] > 100
    assert len(b1["yccd"]) >= 3

    # Kiểm tra Chương 3 (Đã được làm giàu bài tập ở Pha 1)
    ch3 = next(c for c in chapters if c["chapter_id"] == "M12-C3")
    assert len(ch3["lessons"]) == 2
    b1_c3 = ch3["lessons"][0]
    b2_c3 = ch3["lessons"][1]
    assert b1_c3["lesson_id"] == "M12-C3-B1"
    assert b1_c3["available_slides_count"] >= 50
    assert b1_c3["available_questions_count"] >= 13

    assert b2_c3["lesson_id"] == "M12-C3-B2"
    assert b2_c3["available_slides_count"] >= 50
    assert b2_c3["available_questions_count"] >= 14


def test_api_rag_preview_with_explicit_and_inferred_lesson(client):
    """Kiểm tra API POST /api/v1/rag/preview hoạt động chuẩn xác với cả mã bài trực tiếp và suy luận từ topic."""
    # 1. Truy vấn trực tiếp bằng lesson_id
    payload_explicit = {
        "lesson_id": "M12-C1-B1",
        "proficiency": "standard",
        "k_slides": 3,
        "k_questions": 3
    }
    resp1 = client.post("/api/v1/rag/preview", json=payload_explicit)
    assert resp1.status_code == 200
    data1 = resp1.json()

    assert data1["lesson_id"] == "M12-C1-B1"
    assert data1["chapter_id"] == "M12-C1"
    assert len(data1["yccd"]) >= 3
    assert len(data1["deck_outline"]) > 0
    assert len(data1["slides_preview"]) == 3
    assert len(data1["questions_preview"]) == 3
    assert data1["total_available_slides"] >= 80
    assert data1["total_available_questions"] >= 200

    # Kiểm tra nội dung slide mẫu
    sample_slide = data1["slides_preview"][0]
    assert "slide_id" in sample_slide
    assert "title" in sample_slide
    assert "activity_type" in sample_slide
    assert "bullet_points" in sample_slide

    # Kiểm tra nội dung câu hỏi mẫu có lời giải 3 bước
    sample_q = data1["questions_preview"][0]
    assert "question_id" in sample_q
    assert "question" in sample_q
    assert "quiz_options" in sample_q
    assert len(sample_q["worked_solution_steps"]) > 0

    # 2. Suy luận tự động từ topic
    payload_inferred = {
        "topic": "Hệ trục tọa độ trong không gian Oxyz",
        "proficiency": "advanced",
        "k_slides": 2,
        "k_questions": 2
    }
    resp2 = client.post("/api/v1/rag/preview", json=payload_inferred)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["lesson_id"] == "M12-C2-B2"
    assert data2["chapter_id"] == "M12-C2"
    assert len(data2["slides_preview"]) == 2
    assert len(data2["questions_preview"]) == 2


def test_api_e2e_rag_generation_and_source_refs(client):
    """Kiểm tra trọn vẹn luồng sinh Giáo án & SlideDeck có gắn huy hiệu RAG source_refs."""
    # 1. Sinh Kế hoạch bài dạy
    lesson_req = {
        "topic": "Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm",
        "subject": "Toán học",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "use_rag": True,
        "class_proficiency": "standard"
    }
    lp_res = client.post("/api/v1/lesson-plan/generate", json=lesson_req)
    assert lp_res.status_code == 200
    lp_data = lp_res.json()
    assert lp_data["is_valid"] is True
    plan = lp_data["plan"]
    assert plan["grade"] == 12
    assert len(plan["activities"]) == 4

    # 2. Sinh SlideDeck tương ứng từ giáo án vừa sinh
    slide_req = {
        "topic": "Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm",
        "subject": "Toán học",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "use_rag": True,
        "plan": plan
    }
    sd_res = client.post("/api/v1/slide/generate", json=slide_req)
    assert sd_res.status_code == 200
    deck = sd_res.json()

    assert len(deck["slides"]) >= 4
    # Kiểm tra sự xuất hiện của source_refs trên slide
    has_source_refs = any(
        s.get("source_refs") and len(s.get("source_refs")) > 0
        for s in deck["slides"]
    )
    assert has_source_refs, "Ít nhất một slide phải được gắn nguồn RAG source_refs"

    # Kiểm tra cấu trúc phân bố hoạt động sư phạm
    activity_types = [s.get("activity_type") for s in deck["slides"] if s.get("activity_type")]
    assert any("khoi_dong" in a or "hinh_thanh" in a for a in activity_types)
    assert any("luyen_tap" in a or "van_dung" in a for a in activity_types)


def test_api_e2e_dual_package_export_with_rag_deck(client):
    """Kiểm tra xuất gói kép Dual-Package ZIP (Word + PowerPoint) hoàn chỉnh từ dữ liệu RAG."""
    # Lấy dữ liệu giáo án & slide chuẩn RAG từ Fallback / AI
    lesson_req = {
        "topic": "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm",
        "subject": "Toán học",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "use_rag": True
    }
    lp_res = client.post("/api/v1/lesson-plan/generate", json=lesson_req)
    sd_res = client.post("/api/v1/slide/generate", json=lesson_req)

    plan = lp_res.json()["plan"]
    deck = sd_res.json()

    # Gửi payload Dual-Package
    export_payload = {
        "lesson_plan": plan,
        "slide_deck": deck,
        "topic": "Phương sai và độ lệch chuẩn",
        "subject": "Toán học",
        "grade": 12
    }
    dual_res = client.post("/api/v1/lesson-plan/export-dual-package", json=export_payload)
    assert dual_res.status_code == 200
    assert dual_res.headers["content-type"] == "application/zip"
    assert "X-Dual-Package-SHA256" in dual_res.headers
    assert "X-Docx-SHA256" in dual_res.headers
    assert "X-Pptx-SHA256" in dual_res.headers

    # Xác thực tính toàn vẹn của tệp ZIP
    zip_bytes = dual_res.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        file_list = zf.namelist()
        assert any(f.endswith(".docx") for f in file_list), "Tệp ZIP phải chứa file Word .docx"
        assert any(f.endswith(".pptx") for f in file_list), "Tệp ZIP phải chứa file PowerPoint .pptx"
