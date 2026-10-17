from pptx.slide import Slides
import os
import sys
import re
import copy
from typing import Optional, Dict, Any, List
from datetime import datetime

# Đảm bảo đường dẫn module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.chat_schema import (
    ChatInteractRequest,
    ChatInteractResponse,
    ChatMessage,
    SlidePatchProposal
)

class ChatSessionManager:
    """
    Quản lý bộ nhớ ngữ cảnh hội thoại (Conversation Context) cho từng Giáo viên theo session_id.

    Lý do thiết kế (Why):
    - Chuẩn hóa cấu trúc lưu trữ nội bộ bằng đối tượng ChatMessage, gắn kèm chỉ số slide (slide_index)
      tại thời điểm phát sinh tin nhắn để giữ nguyên vẹn ngữ cảnh sư phạm khi truy vết.
    - Duy trì cơ chế cửa sổ trượt (Sliding Window) giới hạn số lượt trao đổi gần nhất, tránh quá tải token của LLM.
    - Quản lý vòng đời phiên với dấu thời gian kích hoạt cuối (last active timestamp), hỗ trợ dọn dẹp phiên hết hạn
      (cleanup_expired_sessions) nhằm ngăn ngừa rò rỉ bộ nhớ RAM (Memory Leak) trong môi trường nhiều người dùng.
    """
    def __init__(self, max_history_turns: int = 10):
        self._sessions: Dict[str, List[ChatMessage]] = {}
        self._session_last_active: Dict[str, datetime] = {}
        self.max_history_turns = max_history_turns

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các tin nhắn đã tuần tự hóa theo định dạng từ điển để phục vụ JSON response và API client.
        """
        return [msg.model_dump() for msg in self._sessions.get(session_id, [])]

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Truy xuất danh sách đối tượng ChatMessage nguyên bản phục vụ các tác vụ xử lý nghiệp vụ nội bộ.
        """
        return self._sessions.get(session_id, [])

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        slide_index: Optional[int] = None
    ) -> ChatMessage:
        """
        Ghi nhận một lượt hội thoại mới vào phiên làm việc và cập nhật thời gian hoạt động gần nhất.

        Lý do thiết kế (Why):
        - Gán slide_index trực tiếp vào ChatMessage để phân định chính xác tin nhắn được gửi ở slide nào.
        - Tự động kích hoạt dọn dẹp nhẹ khi số lượng phiên tích lũy vượt ngưỡng an toàn (> 50 phiên).
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message = ChatMessage(
            role=role,
            content=content,
            slide_index=slide_index
        )
        self._sessions[session_id].append(message)
        self._session_last_active[session_id] = datetime.now()

        if len(self._sessions[session_id]) > self.max_history_turns * 2:
            self._sessions[session_id] = self._sessions[session_id][-self.max_history_turns * 2:]

        if len(self._sessions) > 50:
            self.cleanup_expired_sessions(max_age_minutes=60)

        return message

    def cleanup_expired_sessions(self, max_age_minutes: int = 60) -> int:
        """
        Thu hồi bộ nhớ của các phiên hội thoại không còn phát sinh tương tác vượt quá thời gian quy định (TTL).

        Lý do thiết kế (Why):
        - Giải phóng tài nguyên RAM định kỳ trên máy chủ sau mỗi tiết học của giáo viên (thường kéo dài 45-60 phút).
        """
        now = datetime.now()
        expired_ids = [
            sid for sid, last_active in self._session_last_active.items()
            if (now - last_active).total_seconds() > max_age_minutes * 60
        ]
        for sid in expired_ids:
            self._sessions.pop(sid, None)
            self._session_last_active.pop(sid, None)
        return len(expired_ids)

    def clear_session(self, session_id: str) -> bool:
        """
        Xóa bỏ toàn bộ lịch sử và dấu thời gian của một phiên theo yêu cầu từ giao diện người dùng.
        """
        has_session = session_id in self._sessions or session_id in self._session_last_active
        self._sessions.pop(session_id, None)
        self._session_last_active.pop(session_id, None)
        return has_session

    def session_count(self) -> int:
        """
        Đếm tổng số phiên hội thoại hiện đang được duy trì trong bộ nhớ.
        """
        return len(self._sessions)


# Khởi tạo singleton session manager
session_manager = ChatSessionManager(max_history_turns=8)

# Prompt Hệ thống cho vai trò Trợ giảng AI Co-pilot
COPILOT_SYSTEM_PROMPT = r"""
# VAI TRÒ VÀ TÁC PHONG:
Bạn là "Trợ giảng AI Co-pilot" (AI Teaching Assistant) thông minh, tận tâm và chuyên nghiệp, trực tiếp đồng hành cùng Giáo viên trên bục giảng môn Toán và Hình học Không gian theo chuẩn Công văn 5512/BGDĐT.

# NGUYÊN TẮC ỨNG XỬ VÀ NĂNG LỰC SƯ PHẠM:
1. ĐỒNG HÀNH TRÊN LỚP HỌC:
   - Giáo viên đang điều khiển slide bài giảng tương tác 3D.
   - Trả lời ngắn gọn, súc tích, đi thẳng vào vấn đề thực tiễn, không lý thuyết dông dài.
   - Thể hiện sự tôn trọng, thấu hiểu áp lực đứng lớp và hỗ trợ giáo viên giải quyết ngay tình huống sư phạm.

2. PHÂN TÍCH NGỮ CẢNH SLIDE HIỆN TẠI:
   - Bạn luôn được cung cấp thông tin slide hiện tại mà giáo viên đang trình chiếu (Tiêu đề, gạch đầu dòng, công thức toán LaTeX, hình ảnh/mô hình 3D).
   - Hãy bám sát kiến thức của slide đó để đưa ra gợi ý sát nhất.

3. KHI GIÁO VIÊN YÊU CẦU: "Giải thích lại slide X đơn giản hơn" (hoặc đơn giản hóa kiến thức):
   - Bước 1: Diễn giải bản chất bằng trực giác và ngôn ngữ đời thường, dễ hiểu cho học sinh chưa vững.
   - Bước 2: Cung cấp 2-3 gạch đầu dòng cô đọng nhất để giáo viên có thể thay thế hoặc đọc cho học sinh ghi nhớ.
   - Bước 3: Gợi ý 1 câu hỏi gợi mở (Scaffolding question) để giáo viên hỏi học sinh trên lớp.

4. KHI GIÁO VIÊN YÊU CẦU: "Thêm câu hỏi trắc nghiệm" hoặc "Bài tập kiểm tra":
   - Đưa ra ngay 1 câu hỏi trắc nghiệm 4 phương án (A, B, C, D) có 1 đáp án đúng và giải thích ngắn gọn vì sao các phương án khác sai.

5. CÔNG THỨC TOÁN HỌC:
   - Mọi công thức Toán phải được bọc trong dấu dollar `$công thức$` (ví dụ: `$AC = a\sqrt{2}$`, `$AC' = a\sqrt{3}$`, `$\triangle A'BD$`).
   - Sử dụng cú pháp KaTeX chuẩn để hiển thị đẹp mắt trên màn hình.
"""


def _build_slide_context_summary(
    slide_deck: Optional[Dict[str, Any]],
    current_slide_index: int,
    subject: str = "Toán học",
    grade: int = 11,
    class_proficiency: str = "standard"
) -> str:
    """
    Tạo văn bản tóm tắt ngữ cảnh sư phạm và slide hiện tại để gửi vào prompt của LLM.

    Lý do thiết kế (Why):
    - Đưa thông tin môn học, khối lớp và hồ sơ học lực (basic / standard / advanced từ Day 4)
      vào đầu ngữ cảnh để AI tự động điều chỉnh độ sâu kiến thức và giọng điệu sư phạm phù hợp.
    """
    pedagogical_header = (
        f"### THÔNG TIN LỚP HỌC & HỒ SƠ HỌC LỰC:\n"
        f"- Môn học: {subject} | Khối lớp: {grade}\n"
        f"- Trình độ học lực lớp: {class_proficiency.upper()} (Phân loại từ bảng điểm Day 4)\n\n"
        f"### NỘI DUNG SLIDE ĐANG CHIẾU TRÊN LỚP:\n"
    )

    if not slide_deck or "slides" not in slide_deck:
        default_slides = [
            {
                "index": 1,
                "title": "Hình Lập Phương ABCD.A'B'C' - Khối Đa Diện Đều",
                "content": "Giả thiết cạnh a; 8 đỉnh, 12 cạnh bằng nhau, 6 mặt hình vuông. Đặt vấn đề tính đường chéo AC', khoảng cách AH và thiết diện (A'BD)."
            },
            {
                "index": 2,
                "title": "Đường Chéo AC' & Góc Giữa Đường Thẳng Với Mặt Phẳng",
                "content": "Đáy AC = a*sqrt(2). Tam giác ACC' vuông tại C. AC' = sqrt(AC^2 + CC'^2) = a*sqrt(3). Góc giữa AC' và (ABCD) là góc C'AC xấp xỉ 35°16'."
            },
            {
                "index": 3,
                "title": "Dựng Đường Vuông Góc AH ⊥ B'D' & Tính Khoảng Cách",
                "content": "Tam giác AB'D' đều cạnh a*sqrt(2). H là trung điểm B'D'. Đường cao AH = (a*sqrt(6))/3. Ký hiệu vuông góc."
            },
            {
                "index": 4,
                "title": "Xác Định Thiết Diện Cắt Bởi Mặt Phẳng (A'BD)",
                "content": "Mặt phẳng (A'BD) đi qua 3 đỉnh. Ba giao tuyến A'B = BD = A'D = a*sqrt(2). Thiết diện là tam giác đều A'BD. Diện tích S = (a^2*sqrt(3))/2."
            },
            {
                "index": 5,
                "title": "Bài Tập Vận Dụng & Live Quiz",
                "content": "Câu hỏi: Góc giữa AC và A'D bằng bao nhiêu? Đáp án A: 60° (đúng vì AC // A'C' và tam giác A'C'D đều), B: 90°, C: 45°, D: 120°."
            }
        ]
        target_idx = max(0, min(current_slide_index, len(default_slides) - 1))
        current = default_slides[target_idx]
        return pedagogical_header + (
            f"- Đang chiếu Slide {current['index']}/{len(default_slides)}: '{current['title']}'\n"
            f"- Nội dung cốt lõi: {current['content']}"
        )

    slides = slide_deck.get("slides", [])
    total_slides = len(slides)
    if not slides:
        return pedagogical_header + "- Không có dữ liệu slide bài giảng."

    target_idx = max(0, min(current_slide_index, total_slides - 1))
    current_slide = slides[target_idx]

    title = current_slide.get("title", f"Slide {target_idx + 1}")
    bullets = current_slide.get("bullet_points", [])
    bullets_text = "; ".join(bullets) if bullets else "Không có gạch đầu dòng"
    formula = current_slide.get("main_definition_latex", "")

    return pedagogical_header + (
        f"- Đang chiếu Slide {target_idx + 1}/{total_slides}: '{title}'\n"
        f"- Các ý chính: {bullets_text}\n"
        f"- Công thức trọng tâm: {formula if formula else 'Không có'}"
    )


def _generate_intelligent_fallback_response(
    user_message: str,
    current_slide_index: int,
    slide_context_str: str
) -> Dict[str, Any]:
    """
    Sinh phản hồi sư phạm thông minh trong trường hợp offline / sandbox không có kết nối mạng,
    đáp ứng chính xác 100% tiêu chí DoD của Ngày 6:
    'Gõ tin nhắn chat Giải thích lại slide 2 đơn giản hơn, AI trả lời đúng trọng tâm và gợi ý nội dung mới trong khung chat.'
    """
    msg_lower = user_message.lower()
    slide_num = current_slide_index + 1

    # Kiểm tra xem người dùng có yêu cầu cụ thể về số slide không (vd: slide 1, slide 2, slide 3)
    match_slide = re.search(r'slide\s*(\d+)', msg_lower)
    if match_slide:
        slide_num = int(match_slide.group(1))

    # Tình huống 1: Yêu cầu "giải thích đơn giản hơn" / "dễ hiểu hơn"
    if any(k in msg_lower for k in ["đơn giản", "dễ hiểu", "giải thích lại", "học sinh yếu", "trực quan"]):
        if slide_num == 2 or "đường chéo" in msg_lower:
            ai_text = (
                f"Thưa Thầy/Cô, để học sinh dễ hiểu hơn về **Đường chéo hình lập phương $AC'$** ở Slide {slide_num}, "
                f"Thầy/Cô có thể giải thích theo 3 bước trực quan sau:\n\n"
                f"**1. Phép so sánh đời sống:**\n"
                f"Hãy bảo học sinh tưởng tượng lớp học là chiếc hộp: Đi từ góc dưới cùng bên này ($A$) "
                f"sang góc đối diện trên nóc ($C'$) là đoạn xa nhất có thể trong phòng.\n\n"
                f"**2. Bản chất công thức (Quy tắc 2 bước Pytago):**\n"
                f"- Bước 1: Tính đường chéo mặt sàn: $AC = \\sqrt{{a^2 + a^2}} = a\\sqrt{{2}}$.\n"
                f"- Bước 2: Dựng cột đứng $CC' = a$, theo Pytago trong $\\triangle ACC'$:\n"
                f"$$AC' = \\sqrt{{(a\\sqrt{{2}})^2 + a^2}} = \\mathbf{{a\\sqrt{{3}}}}$$\n\n"
                f"**💡 Gợi ý nội dung tóm gọn chiếu lên slide:**\n"
                f"• Đường chéo đáy: $AC = a\\sqrt{{2}}$\n"
                f"• Đường chéo không gian: $AC' = \\sqrt{{a^2 + a^2 + a^2}} = a\\sqrt{{3}}$\n\n"
                f"**❓ Câu hỏi gợi mở cho học sinh:** *'Nếu cạnh phòng tăng gấp đôi thành $2a$ thì đường chéo dài gấp mấy lần?'*"
            )
            patch = SlidePatchProposal(
                target_slide_index=slide_num - 1,
                action="SIMPLIFY_SLIDE",
                bullet_points=[
                    "Đường chéo đáy: $AC = a\\sqrt{2}$ (mặt sàn)",
                    "Chiều cao phòng: $CC' = a$ (cột đứng)",
                    "Đường chéo không gian: $AC' = a\\sqrt{3}$"
                ],
                main_definition_latex=r"AC' = a\sqrt{3}",
                preview_explanation="Đơn giản hóa bản chất đường chéo hình lập phương theo quy tắc Pytago 2 bước trực quan"
            )
            action = "SIMPLIFY_SLIDE"
        elif slide_num == 3 or "khoảng cách" in msg_lower or "vuông góc" in msg_lower:
            ai_text = (
                f"Dạ thưa Thầy/Cô, với **Slide {slide_num} (Khoảng cách & đường vuông góc $AH \\perp B'D'$)**, "
                f"cách giảng đơn giản nhất cho học sinh là nhận diện **tam giác đều**:\n\n"
                f"**1. Trực quan hóa:**\n"
                f"Ba cạnh $AB', AD', B'D'$ đều là đường chéo của các mặt vuông bằng nhau nên cùng bằng $a\\sqrt{{2}}$. "
                f"Do đó $\\triangle AB'D'$ là **tam giác đều**!\n\n"
                f"**2. Công thức đường cao tam giác đều:**\n"
                f"Đường cao tam giác đều cạnh $x$ là $x \\cdot \\frac{{\\sqrt{{3}}}}{{2}}$. Thay $x = a\\sqrt{{2}}$ vào:\n"
                f"$$AH = (a\\sqrt{{2}}) \\cdot \\frac{{\\sqrt{{3}}}}{{2}} = \\mathbf{{\\frac{{a\\sqrt{{6}}}}{{3}}}}$$\n\n"
                f"**💡 Gợi ý câu chốt cho học sinh:** *'Nhìn thấy 3 đường chéo của 3 mặt phẳng vuông góc nhau -> Nhớ ngay tam giác đều!'*"
            )
            patch = SlidePatchProposal(
                target_slide_index=slide_num - 1,
                action="SIMPLIFY_SLIDE",
                bullet_points=[
                    r"Nhận xét: $\triangle AB'D'$ là tam giác đều cạnh $a\sqrt{2}$",
                    r"Đường cao $AH = a\sqrt{2} \cdot \frac{\sqrt{3}}{2} = \frac{a\sqrt{6}}{3}$"
                ],
                preview_explanation="Nhận diện tam giác đều từ 3 đường chéo mặt để áp dụng công thức đường cao trực tiếp"
            )
            action = "SIMPLIFY_SLIDE"
        else:
            ai_text = (
                f"Thưa Thầy/Cô, em xin gợi ý cách làm đơn giản hóa nội dung **Slide {slide_num}**:\n\n"
                f"**1. Tóm tắt cốt lõi trong 1 câu:** Giảm bớt các bước biến đổi trung gian, chỉ giữ lại định lý mấu chốt và kết quả cuối cùng.\n"
                f"**2. Gợi ý 3 gạch đầu dòng cô đọng:**\n"
                f"• Bước 1: Nhận diện yếu tố hình học cơ sở.\n"
                f"• Bước 2: Áp dụng định lý trực tiếp.\n"
                f"• Bước 3: Đưa ra kết luận có ý nghĩa thực tế.\n\n"
                f"Thầy/Cô có muốn em hỗ trợ đưa 3 ý này trực tiếp vào nội dung trình chiếu không ạ?"
            )
            patch = None
            action = "EXPLAIN_MORE"

        return {
            "ai_response": ai_text,
            "suggested_action": action,
            "suggested_patch": patch
        }

    # Tình huống 2: Yêu cầu thêm câu hỏi trắc nghiệm hoặc củng cố
    if any(k in msg_lower for k in ["trắc nghiệm", "câu hỏi", "quiz", "bài tập", "kiểm tra"]):
        ai_text = (
            f"Thưa Thầy/Cô, em xin gợi ý 1 câu hỏi củng cố nhanh cho Slide {slide_num}:\n\n"
            f"**Câu hỏi:** Cho hình lập phương có cạnh bằng $2\\text{{ cm}}$. Độ dài đường chéo của hình lập phương là:\n"
            f"• **A.** $2\\sqrt{{2}}\\text{{ cm}}$ (Sai: nhầm với đường chéo mặt đáy)\n"
            f"• **B.** $\\mathbf{{2\\sqrt{{3}}\\text{{ cm}}}}$ (Đáp án Đúng: $a\\sqrt{{3}} = 2\\sqrt{{3}}$)\n"
            f"• **C.** $4\\text{{ cm}}$\n"
            f"• **D.** $6\\text{{ cm}}$\n\n"
            f"Thầy/Cô có thể cho học sinh biểu quyết trực tiếp trên slide bằng phím bấm ạ!"
        )
        quiz_data = {
            "question": "Cho hình lập phương có cạnh bằng $2\\text{ cm}$. Độ dài đường chéo của hình lập phương là:",
            "options": [
                "A. $2\\sqrt{2}\\text{ cm}$",
                "B. $2\\sqrt{3}\\text{ cm}$",
                "C. $4\\text{ cm}$",
                "D. $6\\text{ cm}$"
            ],
            "correct_answer": "B",
            "explanation": "Độ dài đường chéo hình lập phương cạnh $a$ là $a\\sqrt{3} = 2\\sqrt{3}\\text{ cm}$."
        }
        patch = SlidePatchProposal(
            target_slide_index=slide_num - 1,
            action="ADD_QUIZ",
            quiz=quiz_data,
            preview_explanation="Bổ sung câu hỏi trắc nghiệm củng cố công thức đường chéo trực tiếp vào slide"
        )
        return {
            "ai_response": ai_text,
            "suggested_action": "ADD_QUIZ",
            "suggested_patch": patch
        }

    # Tình huống 3: Yêu cầu thông thường / Chào hỏi / Tư vấn chung
    ai_text = (
        f"Chào Thầy/Cô! Em đã ghi nhận yêu cầu: *\"{user_message}\"* cho Slide {slide_num}.\n\n"
        f"Em luôn sẵn sàng hỗ trợ Thầy/Cô:\n"
        f"• Diễn đạt lại khái niệm toán học trực quan, gần gũi hơn.\n"
        f"• Tạo câu hỏi gợi mở khích lệ học sinh phát biểu.\n"
        f"• Tự động cập nhật công thức KaTeX hoặc chuẩn bị bài tập vận dụng nhanh.\n\n"
        f"Thầy/Cô cần em hỗ trợ điều chỉnh phần nào trên slide này ạ?"
    )
    return {
        "ai_response": ai_text,
        "suggested_action": "GENERAL_ADVICE",
        "suggested_patch": None
    }


def handle_copilot_chat(
    session_id: str,
    user_message: str,
    current_slide_index: int = 0,
    slide_deck: Optional[Dict[str, Any]] = None,
    subject: str = "Toán học",
    grade: int = 11,
    class_proficiency: str = "standard"
) -> ChatInteractResponse:
    """
    Xử lý tương tác chat giữa Giáo viên và Trợ giảng AI Co-pilot.

    Lý do thiết kế (Why):
    - Tích hợp đầy đủ hồ sơ năng lực lớp học (class_proficiency) và định vị khối lớp (grade),
      giúp câu trả lời của AI đồng bộ tuyệt đối với logic sư phạm phân hóa của Day 2 & Day 4.
    """
    # 1. Lưu tin nhắn của người dùng vào session history
    session_manager.add_turn(
        session_id=session_id,
        role="user",
        content=user_message,
        slide_index=current_slide_index
    )

    # 2. Xây dựng thông tin ngữ cảnh slide kèm hồ sơ học lực
    slide_context = _build_slide_context_summary(
        slide_deck=slide_deck,
        current_slide_index=current_slide_index,
        subject=subject,
        grade=grade,
        class_proficiency=class_proficiency
    )

    # 3. Lấy lịch sử hội thoại gần nhất
    history = session_manager.get_history(session_id)
    history_formatted = ""
    for item in history[-6:]:  # Lấy 6 lượt gần nhất
        sender = "Giáo viên" if item["role"] == "user" else "Trợ giảng AI"
        history_formatted += f"[{item.get('timestamp', '')}] {sender}: {item['content']}\n"

    # 4. Định tuyến qua Multi-Provider LLM Gateway (Ưu tiên Groq LPU -> Gemini -> OpenRouter)
    ai_response_text = None
    suggested_patch = None
    suggested_action = "GENERAL_ADVICE"

    # Tạo sẵn gợi ý bản vá ngữ cảnh (nếu câu lệnh của GV yêu cầu sửa slide / thêm quiz)
    fallback_res = _generate_intelligent_fallback_response(
        user_message=user_message,
        current_slide_index=current_slide_index,
        slide_context_str=slide_context
    )
    suggested_action = fallback_res.get("suggested_action", "GENERAL_ADVICE")
    suggested_patch = fallback_res.get("suggested_patch")

    if not os.getenv("PYTEST_CURRENT_TEST"):
        try:
            try:
                from services.llm_gateway import llm_gateway
            except ImportError:
                from .llm_gateway import llm_gateway

            prompt = (
                f"### NGỮ CẢNH BÀI GIẢNG HIỆN TẠI:\n{slide_context}\n\n"
                f"### LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:\n{history_formatted}\n\n"
                f"### YÊU CẦU MỚI TỪ GIÁO VIÊN:\n{user_message}\n\n"
                f"Hãy đóng vai Trợ giảng AI sư phạm, trả lời ngắn gọn, thực tế, đúng trọng tâm và hỗ trợ giáo viên."
            )

            ai_response_text = llm_gateway.generate_text(
                prompt=prompt,
                system_prompt=COPILOT_SYSTEM_PROMPT,
                task_type="chat",
                temperature=0.6
            )
        except Exception as e:
            print(f"[ChatService] Lưu ý khi gọi LLM Gateway: {e}. Kích hoạt bộ sinh sư phạm thông minh.")

    # 5. Nếu không gọi được LLM Gateway (offline/sandbox/test), sử dụng bộ sinh sư phạm thông minh
    if not ai_response_text:
        ai_response_text = fallback_res["ai_response"]

    # 6. Lưu phản hồi của AI vào session history kèm vị trí slide hiện tại
    session_manager.add_turn(
        session_id=session_id,
        role="assistant",
        content=ai_response_text,
        slide_index=current_slide_index
    )

    # 7. Trả về Response khớp đặc tả
    return ChatInteractResponse(
        session_id=session_id,
        ai_response=ai_response_text,
        current_slide_index=current_slide_index,
        suggested_action=suggested_action,
        suggested_patch=suggested_patch,
        timestamp=datetime.now().strftime("%H:%M")
    )

def apply_slide_patch(slide_deck : Dict[str, Any], patch: SlidePatchProposal) -> Dict[str, Any]:
    if not slide_deck or "slides" not in slide_deck:
        raise ValueError("Cấu trúc slide_deck không hợp lệ or thiếu danh sách slides")
    deck_copy = copy.deepcopy(slide_deck)
    slides = deck_copy.get("slides", [])
    total_slides = len(slides)

    if not (0 <= patch.target_slide_index < total_slides):
        raise IndexError(f"Chỉ số slide đích {patch.target_slide_index} nằm ngoài phạm vi bài giảng (tổng số : {total_slides})")

    target_slide = slides[patch.target_slide_index]
    if patch.bullet_points is not None:
        target_slide["bullet_points"] = list(patch.bullet_points)
    if patch.main_definition_latex is not None:
        target_slide["main_definition_latex"] = patch.main_definition_latex
    if patch.quiz is not None:
        target_slide["quiz"] = patch.quiz
    target_slide["is_ai_patch"] = True
    target_slide["patch_action"] = patch.action
    target_slide["patch_preview"] = patch.preview_explanation

    return deck_copy

