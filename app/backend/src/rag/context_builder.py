"""
context_builder.py
Tầng Pedagogical RAG - Đóng gói Ngữ cảnh Sư phạm Toán 12 (CT GDPT 2018 - SGK Kết nối tri thức).
Nhiệm vụ:
- Tiếp nhận yêu cầu soạn bài (lesson_id, proficiency, topic).
- Truy xuất tri thức từ Math12HybridRetriever.
- Tạo khối prompt văn bản chuẩn mực để bơm vào LLM Gemini.
- Trích xuất danh sách source_refs minh bạch dữ liệu.
"""

from typing import Dict, Any, List, Optional, Tuple
from rag.retriever import Math12HybridRetriever


class PedagogicalContextBuilder:
    @classmethod
    def build_lesson_plan_context(
        cls,
        lesson_id: str,
        topic: Optional[str] = None,
        proficiency: str = "standard"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Đóng gói ngữ cảnh sư phạm để sinh Kế hoạch bài dạy (Giáo án CV 5512).
        Trả về: (context_text, source_refs)
        """
        retriever = Math12HybridRetriever.get_instance()
        skel = retriever.retrieve_lesson_skeleton(lesson_id)
        
        # 1. Slide khởi động (Tình huống mở đầu thực tế)
        warmup_slides = retriever.retrieve_exemplar_slides(lesson_id, activity_type="khoi_dong", k=1)
        
        # 2. Slide hình thành kiến thức trọng tâm
        concept_slides = retriever.retrieve_exemplar_slides(lesson_id, activity_type="hinh_thanh_kien_thuc", k=2)
        
        # 3. Câu hỏi và bài tập thực tế (có 3 bước giải và bẫy trắc nghiệm)
        questions = retriever.retrieve_questions(lesson_id, proficiency=proficiency, query=topic, k=3)
        
        source_refs: List[Dict[str, Any]] = [
            {
                "source_type": "curriculum",
                "id": lesson_id,
                "title": skel.get("title", ""),
                "chapter": skel.get("chapter_title", "")
            }
        ]

        lines = [
            "=== NGỮ CẢNH SƯ PHẠM TOÁN 12 (CT GDPT 2018 - SGK KẾT NỐI TRI THỨC) ===",
            f"[BÀI HỌC]: {skel.get('title')} ({skel.get('chapter_title')}) - Thời lượng: {skel.get('periods')} tiết",
            "",
            "[I. MỤC TIÊU YÊU CẦU CẦN ĐẠT (YCCĐ BẮT BUỘC TUÂN THỦ)]:"
        ]

        for y in skel.get("yccd", []):
            lines.append(f"  • {y}")

        if skel.get("keywords"):
            lines.append(f"  • Từ khóa trọng tâm: {', '.join(skel.get('keywords', []))}")

        # Tình huống khởi động
        lines.append("\n[II. TÌNH HUỐNG KHỞI ĐỘNG THỰC TẾ (HOẠT ĐỘNG 1 - MỞ ĐẦU)]:")
        if warmup_slides:
            s = warmup_slides[0]
            lines.append(f"  • Tiêu đề gợi ý: {s.get('title')}")
            for b in s.get("bullet_points", [])[:4]:
                lines.append(f"    - {b}")
            source_refs.append({
                "source_type": "slide_kntt12",
                "id": s.get("slide_id"),
                "title": s.get("title"),
                "activity_type": s.get("activity_type")
            })
        else:
            lines.append("  • Dẫn dắt từ một tình huống thực tiễn gắn với đời sống hoặc bài toán mô hình hóa toán học.")

        # Khái niệm và định lý
        lines.append("\n[III. KIẾN THỨC VÀ ĐỊNH LÝ CỐT LÕI (HOẠT ĐỘNG 2 - HÌNH THÀNH KIẾN THỨC)]:")
        for s in concept_slides:
            lines.append(f"  • {s.get('title')}:")
            for b in s.get("bullet_points", [])[:3]:
                lines.append(f"    - {b}")
            source_refs.append({
                "source_type": "slide_kntt12",
                "id": s.get("slide_id"),
                "title": s.get("title"),
                "activity_type": s.get("activity_type")
            })

        # Bài tập thực tế có lời giải mẫu
        lines.append("\n[IV. BÀI TẬP VÀ VÍ DỤ GIẢI MẪU THẬT (HOẠT ĐỘNG 3 - LUYỆN TẬP & HOẠT ĐỘNG 4 - VẬN DỤNG)]:")
        for idx, q in enumerate(questions, 1):
            lines.append(f"  Ví dụ {idx} (Mã đề: {q.get('id')} - Độ khó: {q.get('difficulty')}):")
            lines.append(f"  Đề bài: {q.get('question')}")
            if q.get("worked_solution_steps"):
                lines.append("  Các bước giải mẫu chuẩn SGK:")
                for step in q.get("worked_solution_steps", []):
                    lines.append(f"    + {step.get('step')}: {step.get('math')} (Lưu ý: {step.get('note')})")
            elif q.get("solution"):
                lines.append(f"  Lời giải: {q.get('solution')}")
            
            source_refs.append({
                "source_type": "question_bank_rag",
                "id": q.get("id"),
                "topic": q.get("topic"),
                "difficulty": q.get("difficulty")
            })

        lines.append("\n[YÊU CẦU ĐẶC BIỆT KHI SOẠN GIÁO ÁN]:")
        lines.append("1. Phần I (Mục tiêu) phải dẫn xuất trực tiếp từ danh sách YCCĐ ở trên.")
        lines.append("2. Hoạt động 1 (Khởi động) phải sử dụng đúng tình huống thực tế được gợi ý.")
        lines.append("3. Hoạt động 3 (Luyện tập) bắt buộc sử dụng các bài tập và ví dụ giải mẫu có sẵn ở trên, không tự bịa số liệu.")
        lines.append("=== HẾT NGỮ CẢNH SƯ PHẠM ===")

        return "\n".join(lines), source_refs

    @classmethod
    def build_slide_deck_context(
        cls,
        lesson_id: str,
        topic: Optional[str] = None,
        proficiency: str = "standard"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Đóng gói ngữ cảnh sư phạm để sinh Bộ Slide bài giảng (SlideDeckSchema).
        Trả về: (context_text, source_refs)
        """
        retriever = Math12HybridRetriever.get_instance()
        skel = retriever.retrieve_lesson_skeleton(lesson_id)
        
        # 1. Slide mẫu cho 4 hoạt động
        warmup_slides = retriever.retrieve_exemplar_slides(lesson_id, activity_type="khoi_dong", k=1)
        concept_slides = retriever.retrieve_exemplar_slides(lesson_id, activity_type="hinh_thanh_kien_thuc", k=2)
        practice_slides = retriever.retrieve_exemplar_slides(lesson_id, activity_type="luyen_tap", k=2)
        
        # 2. Câu hỏi thực tế kèm phương án và bẫy
        questions = retriever.retrieve_questions(lesson_id, proficiency=proficiency, query=topic, k=4)
        
        source_refs: List[Dict[str, Any]] = [
            {
                "source_type": "curriculum",
                "id": lesson_id,
                "title": skel.get("title", ""),
                "chapter": skel.get("chapter_title", "")
            }
        ]

        lines = [
            "=== NGỮ CẢNH SƯ PHẠM TOÁN 12 - THIẾT KẾ SLIDE BÀI GIẢNG ===",
            f"[BÀI HỌC]: {skel.get('title')} ({skel.get('chapter_title')})",
            f"[YCCĐ]: {'; '.join(skel.get('yccd', []))}",
            "",
            "[CẤU TRÚC SLIDE MẪU TỪ KHO KNTT 12 ĐÃ LÀM SẠCH (FEW-SHOT EXEMPLARS)]:"
        ]

        all_slides = warmup_slides + concept_slides + practice_slides
        for s in all_slides:
            lines.append(f"  • Slide ID: {s.get('slide_id')} | Hoạt động: {s.get('activity_type')} | Layout: {s.get('layout_hint')}")
            lines.append(f"    Tiêu đề: {s.get('title')}")
            for b in s.get("bullet_points", [])[:3]:
                lines.append(f"    - {b}")
            source_refs.append({
                "source_type": "slide_kntt12",
                "id": s.get("slide_id"),
                "title": s.get("title"),
                "layout_hint": s.get("layout_hint"),
                "activity_type": s.get("activity_type")
            })

        lines.append("\n[NGÂN HÀNG CÂU HỎI THẬT CÓ LỜI GIẢI 3 BƯỚC & BẪY TRẮC NGHIỆM]:")
        for idx, q in enumerate(questions, 1):
            lines.append(f"\n  Câu hỏi {idx} (ID: {q.get('id')}) - Dạng: {q.get('question_type')} - Độ khó: {q.get('difficulty')}")
            lines.append(f"  Đề bài: {q.get('question')}")
            
            # worked_solution_steps
            if q.get("worked_solution_steps"):
                lines.append("  3 Bước giải tự luận mẫu (hiển thị cột phải layout TWO_COLUMN):")
                for st in q.get("worked_solution_steps", []):
                    lines.append(f"    - {st.get('step')}: ${st.get('math')}$ -> {st.get('note')}")

            # quiz_options kèm bẫy
            if q.get("quiz_options"):
                lines.append("  Phương án trắc nghiệm (cho layout QUIZ_OPTION):")
                for opt in q.get("quiz_options", []):
                    correct_tag = "[ĐÚNG]" if opt.get("is_correct") else "[SAI]"
                    rationale = f" (Giải thích bẫy sai lầm: {opt.get('distractor_rationale')})" if opt.get("distractor_rationale") else ""
                    lines.append(f"    + Phương án {opt.get('option')}: {opt.get('text')} {correct_tag}{rationale}")

            source_refs.append({
                "source_type": "question_bank_rag",
                "id": q.get("id"),
                "topic": q.get("topic"),
                "difficulty": q.get("difficulty")
            })

        lines.append("\n[QUY TẮC BẮT BUỘC KHI XUẤT SLIDE]:")
        lines.append("1. Với slide Khởi động: Áp dụng tình huống thực tế của KNTT 12.")
        lines.append("2. Với slide Khái niệm: Dùng layout CONCEPT_HIGHLIGHT, công thức trọng tâm đặt trong main_definition_latex.")
        lines.append("3. Với slide Bài tập tự luận: Dùng layout TWO_COLUMN, cột trái ghi đề bài, cột phải đặt 3 bước worked_solution_steps.")
        lines.append("4. Với slide Trắc nghiệm: Dùng layout QUIZ_OPTION, nạp đầy đủ quiz_options với distractor_rationale đã cho.")
        lines.append("5. Gắn danh sách source_refs vào trường source_refs của từng slide tương ứng.")
        lines.append("=== HẾT NGỮ CẢNH SLIDE ===")

        return "\n".join(lines), source_refs
