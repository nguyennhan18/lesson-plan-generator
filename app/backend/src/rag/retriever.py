"""
retriever.py
Tầng Pedagogical RAG - Bộ truy xuất lai (Hybrid Retriever) cho Toán 12 CT GDPT 2018.
- Nạp toàn bộ 1.847 slide bài giảng KNTT 12 và 894 câu hỏi RAG vào RAM (~4MB).
- Tốc độ truy xuất siêu tốc (< 30ms, thực tế < 5ms).
- Kết hợp Lọc cứng Metadata (lesson_id, activity_type, difficulty) + Okapi BM25 tiếng Việt + Chấm điểm chất lượng sư phạm.
"""

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from rag.curriculum_registry import CurriculumRegistry


STOP_WORDS = {
    "là", "và", "của", "các", "một", "trong", "để", "cho", "với", "có", "này", "đó",
    "thì", "sẽ", "ở", "được", "bài", "chủ", "đề", "sau", "đây", "hãy", "khi", "những"
}


def tokenize(text: Optional[str]) -> List[str]:
    """Tách từ tiếng Việt kết hợp bảo toàn ký hiệu toán học LaTeX."""
    if not text:
        return []
    # Tách từ tiếng Việt, số, và các lệnh toán LaTeX (\int, \frac, \vec, \Delta_Q, Oxyz)
    tokens = re.findall(r"\\[a-zA-Z]+|[a-zA-Z0-9_\u00C0-\u024F\u1EA0-\u1EF9]+|\S", text.lower())
    result = []
    for t in tokens:
        if t in STOP_WORDS:
            continue
        if len(t) > 1 or t in {"x", "y", "z", "r", "s", "q", "v", "a", "b", "c", "d"}:
            result.append(t)
    return result


class SimpleBM25:
    """Cài đặt Okapi BM25 thuần Python tối ưu hiệu năng cao, zero dependency."""
    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.doc_lens = [len(doc) for doc in corpus_tokens]
        self.avg_doc_len = (sum(self.doc_lens) / self.corpus_size) if self.corpus_size > 0 else 1.0
        
        # Tính Inverted Document Frequency (IDF)
        df = Counter()
        for doc in corpus_tokens:
            df.update(set(doc))
        self.idf = {}
        for word, freq in df.items():
            self.idf[word] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def score(self, query_tokens: List[str], doc_tokens: List[str], doc_len: int) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        tf = Counter(doc_tokens)
        score = 0.0
        for q in query_tokens:
            if q in tf:
                freq = tf[q]
                idf_val = self.idf.get(q, 0.0)
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                score += idf_val * (numerator / denominator)
        return score


class Math12HybridRetriever:
    _instance = None

    def __init__(self):
        self.base_dir = self._find_data_dir()
        self.registry = CurriculumRegistry.get_instance()
        
        # 1. Kho Slide 1.847 slides
        self.slides: List[Dict[str, Any]] = []
        self.slides_by_lesson: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.slide_tokens: List[List[str]] = []
        
        # 2. Kho Câu hỏi 894 câu
        self.questions: List[Dict[str, Any]] = []
        self.questions_by_lesson: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.question_tokens: List[List[str]] = []
        
        # 3. Chỉ mục BM25
        self.slide_bm25: Optional[SimpleBM25] = None
        self.question_bm25: Optional[SimpleBM25] = None
        
        # Nạp dữ liệu vào bộ nhớ
        self._load_corpus()

    @classmethod
    def get_instance(cls) -> "Math12HybridRetriever":
        if cls._instance is None:
            cls._instance = Math12HybridRetriever()
        return cls._instance

    def _find_data_dir(self) -> Path:
        current = Path(__file__).resolve()
        backend_data = current.parent.parent.parent / "data"
        if (backend_data / "slides_kntt12" / "slides_kntt12_cleaned.jsonl").exists():
            return backend_data
        root_data = current.parent.parent.parent.parent / "data"
        if (root_data / "slides_kntt12" / "slides_kntt12_cleaned.jsonl").exists():
            return root_data
        return backend_data

    def _load_corpus(self):
        """Nạp toàn bộ dữ liệu vào RAM và dựng chỉ mục."""
        # 1. Nạp Slides
        slides_path = self.base_dir / "slides_kntt12" / "slides_kntt12_cleaned.jsonl"
        if slides_path.exists():
            with open(slides_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        slide = json.loads(line)
                        # Đảm bảo có slide_id duy nhất
                        if not slide.get("slide_id"):
                            doc_id = slide.get("doc_id", "KNTT12")
                            slide_no = slide.get("slide_no", 1)
                            slide["slide_id"] = f"{doc_id}#S{slide_no}"
                        
                        # Tính quality score sư phạm
                        slide["quality_score"] = self._compute_slide_quality(slide)
                        
                        # Tokenize văn bản
                        text_to_idx = f"{slide.get('title', '')} {' '.join(slide.get('bullet_points', []))} {slide.get('full_text', '')}"
                        tokens = tokenize(text_to_idx)
                        slide["tokens"] = tokens

                        self.slides.append(slide)
                        lid = slide.get("lesson_id")
                        if lid:
                            self.slides_by_lesson[lid].append(slide)
                        self.slide_tokens.append(tokens)
                    except Exception:
                        continue

            if self.slide_tokens:
                self.slide_bm25 = SimpleBM25(self.slide_tokens)

        # 2. Nạp Câu hỏi
        questions_path = self.base_dir / "questions" / "questions_math12_rag.jsonl"
        if questions_path.exists():
            with open(questions_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        q = json.loads(line)
                        text_to_idx = f"{q.get('question', '')} {q.get('topic', '')} {q.get('solution', '')}"
                        tokens = tokenize(text_to_idx)
                        q["tokens"] = tokens

                        self.questions.append(q)
                        lid = q.get("lesson_id")
                        if lid:
                            self.questions_by_lesson[lid].append(q)
                        self.question_tokens.append(tokens)
                    except Exception:
                        continue

            if self.question_tokens:
                self.question_bm25 = SimpleBM25(self.question_tokens)

        print(f"[Math12HybridRetriever] Sẵn sàng: {len(self.slides)} slides, {len(self.questions)} câu hỏi Toán 12.")

    def _compute_slide_quality(self, slide: Dict[str, Any]) -> float:
        """Đánh giá điểm chất lượng sư phạm của slide (0.0 -> 1.0)."""
        score = 0.5
        layout = slide.get("layout_hint", "")
        title = slide.get("title", "")
        bullets = slide.get("bullet_points", [])

        # Ưu tiên các bố cục chuẩn giáo án điện tử
        if layout == "TWO_COLUMN":
            score += 0.25
        elif layout == "QUIZ_OPTION":
            score += 0.25
        elif layout == "CONCEPT_HIGHLIGHT":
            score += 0.2

        # Có ví dụ hoặc lời giải chi tiết
        full_text = " ".join(bullets) + " " + title
        if any(kw in full_text for kw in ["Ví dụ", "Luyện tập", "Giải:", "Bước 1", "Ta có:", "$"]):
            score += 0.15

        # Trừ điểm slide chào đầu hoặc slide dặn dò
        if any(kw in title.upper() for kw in ["CHÀO MỪNG", "HƯỚNG DẪN VỀ NHÀ", "BÀI TẬP VỀ NHÀ"]):
            score -= 0.3

        return max(0.1, min(1.0, score))

    # =========================================================================
    # 3 HÀM TRUY XUẤT CỐT LÕI (< 30ms)
    # =========================================================================

    def retrieve_lesson_skeleton(self, lesson_id: str) -> Dict[str, Any]:
        """Lấy YCCĐ và dàn ý bài giảng chuẩn từ Khung CT 2018 và decks_kntt12."""
        lesson_meta = self.registry.get_lesson(lesson_id)
        deck_meta = self.registry.get_deck_skeleton(lesson_id)

        return {
            "lesson_id": lesson_id,
            "title": lesson_meta.get("title", "") if lesson_meta else "",
            "chapter_id": lesson_meta.get("chapter_id", "") if lesson_meta else "",
            "chapter_title": lesson_meta.get("chapter_title", "") if lesson_meta else "",
            "periods": lesson_meta.get("periods", 2) if lesson_meta else 2,
            "yccd": lesson_meta.get("yccd", []) if lesson_meta else [],
            "keywords": lesson_meta.get("keywords", []) if lesson_meta else [],
            "deck_outline": deck_meta.get("sample_titles", []) if deck_meta else [],
            "activity_distribution": deck_meta.get("activity_distribution", {}) if deck_meta else {}
        }

    def retrieve_exemplar_slides(
        self,
        lesson_id: str,
        activity_type: Optional[str] = None,
        query: Optional[str] = None,
        k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Truy xuất k slide mẫu đẹp nhất của bài học.
        Có thể lọc theo activity_type (khoi_dong, hinh_thanh_kien_thuc, luyen_tap, van_dung).
        """
        candidates = self.slides_by_lesson.get(lesson_id, [])
        if not candidates:
            # Fallback nếu bài học chưa có slide riêng
            candidates = self.slides[:20]

        # 1. Lọc cứng theo activity_type nếu có
        if activity_type:
            filtered = [s for s in candidates if s.get("activity_type") == activity_type]
            if filtered:
                candidates = filtered

        # 2. Tính điểm lai (Hybrid: BM25 + Quality Score)
        query_toks = tokenize(query) if query else []
        scored_candidates = []

        for slide in candidates:
            bm25_score = 0.0
            if query_toks and self.slide_bm25:
                doc_len = len(slide.get("tokens", []))
                bm25_score = self.slide_bm25.score(query_toks, slide.get("tokens", []), doc_len)
            
            # Kết hợp điểm BM25 và quality_score
            quality = slide.get("quality_score", 0.5)
            final_score = (0.6 * min(bm25_score, 10.0) / 10.0) + (0.4 * quality)
            scored_candidates.append((final_score, slide))

        # Sắp xếp điểm giảm dần
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_candidates[:k]]

    def retrieve_questions(
        self,
        lesson_id: str,
        proficiency: str = "standard",
        query: Optional[str] = None,
        k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Truy xuất k câu hỏi thật phân hóa theo học lực lớp (basic, standard, advanced).
        Đầy đủ worked_solution_steps và quiz_options.
        """
        candidates = self.questions_by_lesson.get(lesson_id, [])
        if not candidates:
            # Fallback lấy từ Chương tương ứng hoặc kho chung
            candidates = self.questions[:20]

        # Phân hóa độ khó theo học lực
        diff_weights = {
            "basic": {"easy": 1.0, "medium": 0.6, "hard": 0.2},
            "standard": {"easy": 0.7, "medium": 1.0, "hard": 0.8},
            "advanced": {"easy": 0.3, "medium": 0.8, "hard": 1.0}
        }.get(proficiency, {"easy": 0.7, "medium": 1.0, "hard": 0.8})

        query_toks = tokenize(query) if query else []
        scored_questions = []

        for q in candidates:
            bm25_score = 0.0
            if query_toks and self.question_bm25:
                doc_len = len(q.get("tokens", []))
                bm25_score = self.question_bm25.score(query_toks, q.get("tokens", []), doc_len)

            diff = q.get("difficulty", "medium")
            diff_weight = diff_weights.get(diff, 0.7)

            # Ưu tiên câu hỏi có đầy đủ 3 bước giải và bẫy trắc nghiệm
            has_steps = 0.3 if q.get("worked_solution_steps") else 0.0
            has_rationales = 0.2 if any(opt.get("distractor_rationale") for opt in q.get("quiz_options", [])) else 0.0

            final_score = (0.4 * min(bm25_score, 10.0) / 10.0) + (0.3 * diff_weight) + has_steps + has_rationales
            scored_questions.append((final_score, q))

        scored_questions.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_questions[:k]]
