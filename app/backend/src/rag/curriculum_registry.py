"""
curriculum_registry.py
Quản lý và tra cứu Khung chương trình Toán 12 (CT GDPT 2018 - SGK Kết nối tri thức).
Cung cấp chức năng:
- Tra cứu danh sách Chương, Bài học, Yêu cầu cần đạt (YCCĐ), Từ khóa.
- Tra cứu dàn ý bài giảng chuẩn giáo viên (deck_skeleton) từ decks_kntt12.json.
- Tự động suy luận bài học (infer_lesson_id) từ chuỗi văn bản người dùng nhập tự do.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class CurriculumRegistry:
    _instance = None

    def __init__(self):
        self.base_dir = self._find_data_dir()
        self.curriculum = self._load_json(self.base_dir / "curriculum" / "math12_ct2018.json")
        self.nls_catalog = self._load_json(self.base_dir / "curriculum" / "nls_catalog.json")
        self.decks = self._load_json(self.base_dir / "slides_kntt12" / "decks_kntt12.json")
        
        # Tạo bảng tra cứu nhanh theo lesson_id
        self.lessons_by_id: Dict[str, Dict[str, Any]] = {}
        self._build_indexes()

    @classmethod
    def get_instance(cls) -> "CurriculumRegistry":
        if cls._instance is None:
            cls._instance = CurriculumRegistry()
        return cls._instance

    def _find_data_dir(self) -> Path:
        """Tìm thư mục data ưu tiên app/backend/data, fallback root/data."""
        # __file__ = app/backend/src/rag/curriculum_registry.py
        current = Path(__file__).resolve()
        backend_data = current.parent.parent.parent / "data"
        if (backend_data / "curriculum" / "math12_ct2018.json").exists():
            return backend_data
        
        root_data = current.parent.parent.parent.parent / "data"
        if (root_data / "curriculum" / "math12_ct2018.json").exists():
            return root_data

        return backend_data

    def _load_json(self, path: Path) -> Any:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CurriculumRegistry] Lỗi đọc {path}: {e}")
        return {}

    def _build_indexes(self):
        """Xây dựng chỉ mục tra cứu bài học."""
        chapters = self.curriculum.get("chapters", [])
        for ch in chapters:
            ch_id = ch.get("chapter_id")
            ch_title = ch.get("title")
            for l in ch.get("lessons", []):
                lid = l.get("lesson_id")
                if lid:
                    l_entry = dict(l)
                    l_entry["chapter_id"] = ch_id
                    l_entry["chapter_title"] = ch_title
                    self.lessons_by_id[lid] = l_entry

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        return list(self.lessons_by_id.values())

    def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        return self.lessons_by_id.get(lesson_id)

    def get_deck_skeleton(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Trả về cấu trúc slide dàn ý bài giảng chuẩn từ decks_kntt12.json."""
        if not self.decks:
            return None
        # decks_kntt12 có thể là list hoặc dict
        if isinstance(self.decks, dict):
            return self.decks.get(lesson_id)
        elif isinstance(self.decks, list):
            for d in self.decks:
                if d.get("lesson_id") == lesson_id:
                    return d
        return None

    def infer_lesson_id(self, topic: Optional[str]) -> str:
        """
        Tự động suy luận lesson_id từ tiêu đề topic người dùng nhập.
        Hỗ trợ:
        - Nhập mã trực tiếp: 'M12-C1-B1' -> 'M12-C1-B1'
        - Nhập tên bài / từ khóa tự do: 'Khảo sát hàm số' -> 'M12-C1-B4'
        - Fallback an toàn: 'M12-C1-B1'
        """
        if not topic:
            return "M12-C1-B1"

        raw = topic.strip()
        
        # 1. Nếu người dùng nhập trực tiếp mã bài học
        norm_code = raw.upper().replace(" ", "").replace("_", "-")
        for lid in self.lessons_by_id.keys():
            if norm_code == lid or norm_code in lid:
                return lid

        # 2. Chuẩn hóa chuỗi tìm kiếm (chữ thường)
        q = raw.lower()

        # Quy tắc so khớp chuyên sâu các thuật ngữ Toán 12 thường gặp
        SPECIFIC_MAPPINGS = [
            # Chương 1
            (["đơn điệu", "đồng biến", "nghịch biến", "cực trị", "cực đại", "cực tiểu"], "M12-C1-B1"),
            (["giá trị lớn nhất", "giá trị nhỏ nhất", "gtln", "gtnn", "max min", "lớn nhất nhỏ nhất"], "M12-C1-B2"),
            (["tiệm cận", "tiệm cận đứng", "tiệm cận ngang", "tiệm cận xiên"], "M12-C1-B3"),
            (["khảo sát", "bảng biến thiên", "vẽ đồ thị", "bậc ba", "bậc 3", "phân thức"], "M12-C1-B4"),
            (["ứng dụng đạo hàm", "tối ưu chi phí", "tối ưu lợi nhuận", "bài toán thực tế đạo hàm"], "M12-C1-B5"),
            
            # Chương 2
            (["vectơ trong không gian", "vector trong không gian", "quy tắc hình hộp", "đồng phẳng"], "M12-C2-B1"),
            (["hệ tọa độ trong không gian", "tọa độ trong không gian", "hệ trục oxyz", "tọa độ oxyz", "tọa độ không gian"], "M12-C2-B2"),
            
            # Chương 3
            (["phương sai", "độ lệch chuẩn", "giá trị đại diện", "độ phân tán"], "M12-C3-B2"),
            (["khoảng biến thiên", "khoảng tứ phân vị", "tứ phân vị", "biến thiên ghép nhóm"], "M12-C3-B1"),
            
            # Chương 4
            (["nguyên hàm", "bảng nguyên hàm", "họ nguyên hàm"], "M12-C4-B1"),
            (["tích phân", "newton-leibniz", "cận tích phân"], "M12-C4-B2"),
            (["diện tích hình phẳng", "thể tích khối tròn xoay", "ứng dụng tích phân", "hình phẳng"], "M12-C4-B3"),
            
            # Chương 5
            (["mặt phẳng", "phương trình mặt phẳng", "vectơ pháp tuyến", "khoảng cách đến mặt phẳng"], "M12-C5-B1"),
            (["đường thẳng trong không gian", "phương trình đường thẳng", "vectơ chỉ phương", "chính tắc"], "M12-C5-B2"),
            (["mặt cầu", "phương trình mặt cầu", "bán kính mặt cầu", "tâm mặt cầu", "góc trong không gian"], "M12-C5-B3"),
            
            # Chương 6
            (["xác suất có điều kiện", "công thức nhân xác suất", "điều kiện"], "M12-C6-B1"),
            (["xác suất toàn phần", "công thức bayes", "bayes", "toàn phần"], "M12-C6-B2"),

            # Chuyên đề THPT & hình học 3D
            (["thể tích khối chóp", "khối lăng trụ", "khối đa diện", "hình lập phương", "hình chóp"], "M12-CD-B1"),
            (["mặt nón", "mặt trụ", "khối nón", "khối trụ", "mũ", "logarit", "mũ và logarit"], "M12-CD-B2"),

            # Trường hợp bài toán phổ thông khác (VD: Phương trình bậc hai -> M12-C1-B1)
            (["phương trình bậc hai", "bậc hai", "tam thức"], "M12-C1-B1"),
            (["cấp số cộng", "cấp số nhân", "dãy số"], "M12-C1-B1")
        ]

        for keywords, target_lid in SPECIFIC_MAPPINGS:
            for kw in keywords:
                if kw in q:
                    return target_lid

        # 3. So khớp từ khóa với metadata trong curriculum registry
        STOP_WORDS = {"bài", "chủ", "đề", "của", "và", "các", "một", "số", "trong", "để", "cho", "với", "là", "tìm", "về", "có", "những"}
        meaningful_words = [w for w in q.split() if len(w) > 2 and w not in STOP_WORDS]

        best_match = None
        max_score = 0
        for lid, l in self.lessons_by_id.items():
            score = 0
            title = l.get("title", "").lower()
            if meaningful_words and any(word in title for word in meaningful_words):
                score += 3
            for kw in l.get("keywords", []):
                if kw.lower() in q:
                    score += 5
            if score > max_score:
                max_score = score
                best_match = lid

        if best_match and max_score >= 5:
            return best_match

        # 4. Fallback mặc định
        return "M12-C1-B1"


def infer_lesson_id(topic: Optional[str]) -> str:
    """Hàm tiện ích toàn cục gọi CurriculumRegistry singleton."""
    return CurriculumRegistry.get_instance().infer_lesson_id(topic)
