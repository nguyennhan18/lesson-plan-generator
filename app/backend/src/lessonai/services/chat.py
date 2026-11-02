import copy
from typing import Optional, Dict, Any, List
from datetime import datetime


from lessonai.schemas.chat_schema import (
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
from lessonai.prompts.chat import COPILOT_SYSTEM_PROMPT


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
        return pedagogical_header + "- Chưa có dữ liệu slide; không suy đoán bài học."

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
    """M0: offline advice must not invent lesson content or a slide patch."""
    return {
        "ai_response": (
            "Chưa thể tạo giải thích đã kiểm chứng cho nội dung đang chọn. "
            "Thầy/Cô có thể kiểm tra lại giả thiết, yêu cầu và từng bước giải trên slide. "
            "Đề xuất tự động sửa slide đang tạm ngắt; nội dung bản soạn được giữ nguyên."
        ),
        "suggested_action": "GENERAL_ADVICE",
        "suggested_patch": None,
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

    # M0: no sample patches, including when the text-only gateway succeeds.
    fallback_res = _generate_intelligent_fallback_response(
        user_message=user_message,
        current_slide_index=current_slide_index,
        slide_context_str=slide_context
    )
    suggested_action = fallback_res.get("suggested_action", "GENERAL_ADVICE")
    suggested_patch = fallback_res.get("suggested_patch")

    try:
        from lessonai.llm.gateway import llm_gateway

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
        print(f"[ChatService] Không gọi được LLM Gateway: {type(e).__name__}. Trả thông báo giữ bản nháp.")

    # 5. Khi gateway không trả nội dung, báo trạng thái và giữ bản nháp.
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

