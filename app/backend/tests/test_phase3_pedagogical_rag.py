import time
import pytest
from lessonai.rag.retriever import Math12HybridRetriever
from lessonai.rag.context_builder import PedagogicalContextBuilder
from lessonai.rag.curriculum_registry import CurriculumRegistry


@pytest.fixture(scope="module")
def retriever():
    return Math12HybridRetriever.get_instance()


def test_retriever_initialization_and_corpus_size(retriever):
    """Kiểm tra tầng RAG nạp đúng kích thước kho dữ liệu Toán 12"""
    assert len(retriever.slides) == 1847, "Thiếu slides trong kho slides_kntt12_cleaned.jsonl"
    assert len(retriever.questions) >= 894, "Thiếu câu hỏi trong kho questions_math12_rag.jsonl"
    assert len(retriever.slides_by_lesson) >= 19, "Số bài học có slide ít hơn 19 bài"


def test_retrieval_latency_under_30ms(retriever):
    """Kiểm tra thời gian truy xuất hoàn tất dưới 30ms (kể cả hybrid scoring)"""
    test_lessons = ["M12-C1-B1", "M12-C2-B2", "M12-C3-B1", "M12-C3-B2", "M12-C5-B1"]
    
    for lid in test_lessons:
        t0 = time.time()
        # 1. Dàn ý bài học
        skel = retriever.retrieve_lesson_skeleton(lid)
        # 2. Slide mẫu Khởi động & Luyện tập
        slides = retriever.retrieve_exemplar_slides(lid, activity_type="luyen_tap", query="bài tập ví dụ", k=2)
        # 3. Câu hỏi thật
        questions = retriever.retrieve_questions(lid, proficiency="standard", query="tính toán", k=3)
        t_elapsed = (time.time() - t0) * 1000

        assert t_elapsed < 30.0, f"Truy xuất cho bài {lid} mất {t_elapsed:.2f}ms (> 30ms)"
        assert skel["title"] != "", f"Không tìm thấy tiêu đề cho bài {lid}"
        assert len(slides) > 0, f"Không tìm thấy slide cho bài {lid}"
        assert len(questions) > 0, f"Không tìm thấy câu hỏi cho bài {lid}"


def test_hard_metadata_filtering(retriever):
    """Kiểm tra tính chính xác của bộ lọc cứng: đúng bài, đúng hoạt động"""
    # 1. Kiểm tra Chương 3 - Bài 10 (M12-C3-B2)
    lid = "M12-C3-B2"
    slides = retriever.retrieve_exemplar_slides(lid, activity_type="hinh_thanh_kien_thuc", k=3)
    for s in slides:
        assert s.get("lesson_id") == lid, f"Slide sai bài học: {s.get('lesson_id')}"
        assert s.get("activity_type") == "hinh_thanh_kien_thuc", f"Slide sai hoạt động: {s.get('activity_type')}"

    # 2. Kiểm tra câu hỏi của M12-C3-B2
    questions = retriever.retrieve_questions(lid, k=4)
    for q in questions:
        assert q.get("lesson_id") == lid, f"Câu hỏi sai bài học: {q.get('lesson_id')}"


def test_differentiation_by_proficiency(retriever):
    """Kiểm tra phân hóa độ khó theo trình độ lớp học"""
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
    from lessonai.rag.context_builder import PedagogicalContextBuilder
    text,refs=PedagogicalContextBuilder.build_lesson_plan_context('M12-C3-B2')
    envelope=json.loads(text)
    assert envelope['curriculum']['lesson_id']=='M12-C3-B2'
    assert all(unit['sha256'] for unit in envelope['source_units'])
    assert len(refs)==len(envelope['source_units'])
    assert 'chưa được duyệt' in envelope['notice']


def test_pedagogical_context_builder_slide_deck():
    import json
    from lessonai.rag.context_builder import PedagogicalContextBuilder
    text,refs=PedagogicalContextBuilder.build_slide_deck_context('M12-C3-B2')
    envelope=json.loads(text)
    assert envelope['curriculum']['lesson_id']=='M12-C3-B2'
    assert all(unit['sha256'] for unit in envelope['source_units'])
    assert len(refs)==len(envelope['source_units'])
    assert 'chưa được duyệt' in envelope['notice']
