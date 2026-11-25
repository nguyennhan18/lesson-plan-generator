import time
import statistics
import pytest
from lessonai.rag import content_units
from lessonai.rag.retriever import Math12HybridRetriever
from lessonai.rag.context_builder import PedagogicalContextBuilder
from lessonai.rag.curriculum_registry import CurriculumRegistry


TEST_LESSONS = ("M12-C1-B1", "M12-C2-B2", "M12-C3-B1", "M12-C3-B2", "M12-C5-B1")


@pytest.fixture(scope="module")
def retriever():
    return Math12HybridRetriever.get_instance()


@pytest.fixture()
def isolated_approved_test_lessons(tmp_path, monkeypatch, retriever):
    """
    Cấp phê duyệt tạm thời trong `tmp_path` cho các đơn vị thuộc 5 bài học kiểm thử
    để đo hiệu năng BM25, lọc cứng metadata và phân hóa độ khó mà không sửa
    `app/backend/data/reviewed_sources.json` thật.
    """
    monkeypatch.setattr(content_units, "DATA_DIR", tmp_path)
    candidates = retriever.get_corpus_candidates_for_review()
    records = []
    for source_type in ("slide_kntt12", "question_bank_rag"):
        for item in candidates.get(source_type) or []:
            if item.get("lesson_id") not in TEST_LESSONS:
                continue
            try:
                assets = content_units.asset_manifest(item)
            except ValueError:
                continue
            records.append({
                "hash_version": content_units.HASH_VERSION,
                "source_id": item.get("source_id") or item.get("id") or item.get("slide_id") or item.get("question_id"),
                "source_type": source_type,
                "document_version": item.get("document_version") or item.get("version") or "unknown",
                "status": "approved",
                "sha256": content_units.source_hash(item),
                "reviewer": "fixture-test-reviewer",
                "reviewed_at": "2026-11-10T00:00:00+00:00",
                "revoked": False,
                "revoked_at": None,
                "revocation_reason": None,
                "asset_hashes": assets,
            })
    content_units.save_approval_registry({"schema_version": 1, "sources": records})
    return tmp_path


# Cần corpus RAG cục bộ (app/backend/data hoặc LESSONAI_DATA_DIR), không có trong Git (ADR 0012).
@pytest.mark.corpus_integration
def test_retriever_initialization_and_corpus_size(retriever):
    """Kiểm tra tầng RAG nạp đúng kích thước kho dữ liệu Toán 12 và chặn truy xuất khi chưa duyệt."""
    candidates = retriever.get_corpus_candidates_for_review()
    assert len(candidates["slide_kntt12"]) == 1847, "Thiếu slides trong kho slides_kntt12_cleaned.jsonl"
    assert len(candidates["question_bank_rag"]) >= 894, "Thiếu câu hỏi trong kho questions_math12_rag.jsonl"
    lesson_ids = {s.get("lesson_id") for s in candidates["slide_kntt12"] if s.get("lesson_id")}
    assert len(lesson_ids) >= 19, "Số bài học có slide ít hơn 19 bài"
    # Khi reviewed_sources.json trống, thuộc tính công khai phải trả về rỗng
    assert retriever.slides == []
    assert retriever.questions == []


# Cần corpus RAG cục bộ (app/backend/data hoặc LESSONAI_DATA_DIR), không có trong Git (ADR 0012).
@pytest.mark.corpus_integration
def test_retrieval_latency_under_30ms(retriever, isolated_approved_test_lessons):
    """Kiểm tra thời gian truy xuất hoàn tất dưới 30ms (kể cả hybrid scoring và kiểm tra hash duyệt)."""
    for lid in TEST_LESSONS:
        samples = []
        for _ in range(20):
            t0 = time.perf_counter_ns()
            skel = retriever.retrieve_lesson_skeleton(lid)
            slides = retriever.retrieve_exemplar_slides(lid, activity_type="luyen_tap", query="bài tập ví dụ", k=2)
            questions = retriever.retrieve_questions(lid, proficiency="standard", query="tính toán", k=3)
            samples.append((time.perf_counter_ns() - t0) / 1e6)
        t_elapsed = statistics.median(samples)

        assert t_elapsed < 30.0, f"Truy xuất cho bài {lid} mất {t_elapsed:.2f}ms (> 30ms)"
        assert skel["title"] != "", f"Không tìm thấy tiêu đề cho bài {lid}"
        assert len(slides) > 0, f"Không tìm thấy slide đã duyệt cho bài {lid}"
        assert len(questions) > 0, f"Không tìm thấy câu hỏi đã duyệt cho bài {lid}"


# Cần corpus RAG cục bộ (app/backend/data hoặc LESSONAI_DATA_DIR), không có trong Git (ADR 0012).
@pytest.mark.corpus_integration
def test_hard_metadata_filtering(retriever, isolated_approved_test_lessons):
    """Kiểm tra tính chính xác của bộ lọc cứng: đúng bài, đúng hoạt động."""
    lid = "M12-C3-B2"
    slides = retriever.retrieve_exemplar_slides(lid, activity_type="hinh_thanh_kien_thuc", k=3)
    assert len(slides) > 0
    for s in slides:
        assert s.get("lesson_id") == lid, f"Slide sai bài học: {s.get('lesson_id')}"
        assert s.get("activity_type") == "hinh_thanh_kien_thuc", f"Slide sai hoạt động: {s.get('activity_type')}"

    questions = retriever.retrieve_questions(lid, k=4)
    assert len(questions) > 0
    for q in questions:
        assert q.get("lesson_id") == lid, f"Câu hỏi sai bài học: {q.get('lesson_id')}"


# Cần corpus RAG cục bộ (app/backend/data hoặc LESSONAI_DATA_DIR), không có trong Git (ADR 0012).
@pytest.mark.corpus_integration
def test_differentiation_by_proficiency(retriever, isolated_approved_test_lessons):
    """Kiểm tra phân hóa độ khó theo trình độ lớp học."""
    lid = "M12-C1-B1"

    # Lớp cơ bản: ưu tiên câu dễ
    basic_qs = retriever.retrieve_questions(lid, proficiency="basic", k=4)
    difficulties = [q.get("difficulty") for q in basic_qs]
    assert "easy" in difficulties or "medium" in difficulties

    # Lớp nâng cao: ưu tiên câu khó
    adv_qs = retriever.retrieve_questions(lid, proficiency="advanced", k=4)
    adv_diffs = [q.get("difficulty") for q in adv_qs]
    assert "hard" in adv_diffs or "medium" in adv_diffs


def test_pedagogical_context_builder_lesson_plan():
    import json
    text, refs = PedagogicalContextBuilder.build_lesson_plan_context("M12-C3-B2")
    envelope = json.loads(text)
    assert envelope["curriculum"]["lesson_id"] == "M12-C3-B2"
    assert all(unit["sha256"] for unit in envelope["source_units"])
    assert len(refs) == len(envelope["source_units"])
    assert "chưa được duyệt" in envelope["notice"]


def test_pedagogical_context_builder_slide_deck():
    import json
    text, refs = PedagogicalContextBuilder.build_slide_deck_context("M12-C3-B2")
    envelope = json.loads(text)
    assert envelope["curriculum"]["lesson_id"] == "M12-C3-B2"
    assert all(unit["sha256"] for unit in envelope["source_units"])
    assert len(refs) == len(envelope["source_units"])
    assert "chưa được duyệt" in envelope["notice"]
