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

from lessonai.main import app
from lessonai.schemas.schemas import LessonRequest, RAGPreviewRequest
from lessonai.rag.curriculum_registry import CurriculumRegistry
from lessonai.rag.retriever import Math12HybridRetriever


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def speed_up_offline_tests(monkeypatch):
    """Giúp test chạy tức thì (< 1s) trong môi trường kiểm thử offline không có mạng."""
    def fast_mock_llm(*args, **kwargs):
        raise ConnectionError("Offline test mode: kích hoạt nhanh Retrieval Fallback")
    monkeypatch.setattr("lessonai.llm.gateway.llm_gateway.generate_structured", fast_mock_llm)


def test_api_curriculum_math12_structure_and_stats(client, monkeypatch):
    """Kiểm tra API GET /api/v1/curriculum/math12 trả về đầy đủ 7 chương, 19 bài và kho dữ liệu RAG."""
    monkeypatch.setattr("lessonai.api.routes.curriculum.approved_units", lambda items: [])
    response = client.get("/api/v1/curriculum/math12")
    assert response.status_code == 200
    data = response.json()

    assert data["subject"] == "Toán học"
    assert data["grade"] == 12
    assert "GDPT 2018" in data["curriculum_standard"]
    assert data["total_chapters"] == 7
    assert data["total_lessons"] == 19
    assert data["total_slides"] == 0
    assert data["total_questions"] == 0

    chapters = data["chapters"]
    assert len(chapters) == 7

    # Kiểm tra Chương 1
    ch1 = chapters[0]
    assert ch1["chapter_id"] == "M12-C1"
    assert len(ch1["lessons"]) == 5
    b1 = ch1["lessons"][0]
    assert b1["lesson_id"] == "M12-C1-B1"
    assert b1["available_slides_count"] == 0
    assert b1["available_questions_count"] == 0
    assert len(b1["yccd"]) >= 3

    # Kiểm tra Chương 3 (Đã được làm giàu bài tập ở Pha 1)
    ch3 = next(c for c in chapters if c["chapter_id"] == "M12-C3")
    assert len(ch3["lessons"]) == 2
    b1_c3 = ch3["lessons"][0]
    b2_c3 = ch3["lessons"][1]
    assert b1_c3["lesson_id"] == "M12-C3-B1"
    assert b1_c3["available_slides_count"] == 0
    assert b1_c3["available_questions_count"] == 0

    assert b2_c3["lesson_id"] == "M12-C3-B2"
    assert b2_c3["available_slides_count"] == 0
    assert b2_c3["available_questions_count"] == 0


def test_api_rag_preview_is_retired(client):
    response = client.post("/api/v1/rag/preview", json={"lesson_id":"M12-C1-B1"})
    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "sample_preview_removed"
    assert "slides_preview" not in response.json()
