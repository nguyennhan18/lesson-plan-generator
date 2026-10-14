from email import message
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """
    Cấu trúc dữ liệu chuẩn hóa của một tin nhắn trong phiên hội thoại sư phạm.

    Lý do thiết kế (Why):
    - role: Phân biệt người gửi ('user' đại diện cho Giáo viên, 'assistant' đại diện cho Trợ giảng AI).
    - content: Nội dung văn bản trao đổi hoặc mã LaTeX công thức toán.
    - slide_index: Ghi nhận vị trí slide đang trình chiếu tại thời điểm gửi tin nhắn,
                   giúp AI và hệ thống truy vết lại ngữ cảnh khi xem lại lịch sử phiên.
    - timestamp: Định dạng thời gian thực (HH:MM) hiển thị trên bong bóng giao diện.
    """
    role: str = Field(description="Vai trò người gửi: 'user' hoặc 'assistant'")
    content: str = Field(description="Nội dung tin nhắn")
    slide_index: Optional[int] = Field(default=None, description="Vị trí trang slide tại thời điểm phát sinh tin nhắn")
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"), description="Thời gian gửi tin nhắn (HH:MM)")


class ChatInteractRequest(BaseModel):
    """
    Dữ liệu yêu cầu gửi từ Front-end lên API Trợ giảng AI Co-pilot.

    Lý do thiết kế (Why):
    - Ngoài session_id và user_message, request tích hợp ngữ cảnh sư phạm đầy đủ gồm:
      vị trí slide (current_slide_index), môn học (subject), khối lớp (grade), và
      đặc biệt là hồ sơ học lực (class_proficiency: 'basic' | 'standard' | 'advanced')
      được kế thừa trực tiếp từ kết quả phân loại bảng điểm Ngày 4.
    - Nhờ có class_proficiency, Trợ giảng AI tự động điều chỉnh độ khó của câu trả lời:
      với lớp basic sẽ ưu tiên trực quan đời sống và chia nhỏ bước (scaffolding);
      với lớp advanced sẽ đi thẳng vào bản chất toán học và bài toán tham số.
    """
    session_id: str = Field(
        description="Mã định danh phiên làm việc của giáo viên",
        json_schema_extra={"example": "sess_teacher_9823"}
    )
    user_message: str = Field(
        description="Nội dung câu hỏi hoặc yêu cầu chỉnh sửa slide từ giáo viên",
        json_schema_extra={"example": "Giải thích lại slide 2 đơn giản hơn"}
    )
    current_slide_index: int = Field(
        default=0,
        description="Vị trí trang slide giáo viên đang đứng chiếu (bắt đầu từ 0)",
        json_schema_extra={"example": 1}
    )
    subject: Optional[str] = Field(
        default="Toán học",
        description="Tên môn học đang giảng dạy",
        json_schema_extra={"example": "Toán học"}
    )
    grade: Optional[int] = Field(
        default=11,
        description="Khối lớp (từ lớp 6 đến lớp 12)",
        json_schema_extra={"example": 11}
    )
    class_proficiency: Optional[str] = Field(
        default="standard",
        description="Hồ sơ học lực lớp: 'basic' | 'standard' | 'advanced' (đồng bộ từ Day 4)",
        json_schema_extra={"example": "standard"}
    )
    slide_deck: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Toàn bộ cấu trúc Slide Deck bài giảng hiện tại (nếu có)"
    )


class SlidePatchProposal(BaseModel):
    """
    Cấu trúc bản vá đề xuất chỉnh sửa nội dung slide từ Trợ giảng AI Co-pilot.

    Lý do thiết kế (Why):
    - Chuẩn bị nền tảng định kiểu mạnh (Strongly-typed schema) cho tính năng Live Patching của Ngày 7.
    - Định vị chính xác số thứ tự slide đích (target_slide_index) và loại thao tác (action) để
      Front-end có thể hiển thị hộp thoại So sánh Khác biệt (Diff View) trước khi giáo viên áp dụng trực tiếp.
    - Đóng gói dữ liệu thay đổi (bullet_points, main_definition_latex, quiz...) đồng nhất với cấu trúc SlideSchema.
    """
    target_slide_index: int = Field(
        description="Chỉ số slide đích cần áp dụng thay đổi (0-indexed)",
        json_schema_extra={"example": 1}
    )
    action: str = Field(
        description="Mã hành động đề xuất: 'SIMPLIFY_SLIDE' | 'REPLACE_BULLETS' | 'UPDATE_FORMULA' | 'ADD_QUIZ' | 'CUSTOM_PATCH'",
        json_schema_extra={"example": "SIMPLIFY_SLIDE"}
    )
    bullet_points: Optional[List[str]] = Field(
        default=None,
        description="Danh sách gạch đầu dòng mới đề xuất thay thế"
    )
    main_definition_latex: Optional[str] = Field(
        default=None,
        description="Công thức toán học LaTeX mới đề xuất cập nhật"
    )
    quiz: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Câu hỏi trắc nghiệm hoặc bài tập củng cố đề xuất chèn vào slide"
    )
    preview_explanation: Optional[str] = Field(
        default=None,
        description="Tóm tắt lý do sư phạm đề xuất thay đổi này"
    )

    @property
    def slide_index(self) -> int:
        """Thuộc tính tương thích ngược cho các đoạn mã tham chiếu slide_index thay vì target_slide_index."""
        return self.target_slide_index


class ChatInteractResponse(BaseModel):
    """
    Dữ liệu phản hồi từ Trợ giảng AI Co-pilot gửi về Front-end.

    Lý do thiết kế (Why):
    - Không chỉ dừng lại ở văn bản tư vấn (ai_response), response đóng gói sẵn
      mã hành động sư phạm (suggested_action) và khối dữ liệu đề xuất sửa đổi (suggested_patch)
      theo mô hình định kiểu chuẩn SlidePatchProposal.
    - Cấu trúc này giúp Front-end hiển thị Thẻ đề xuất trực quan và nút bấm một chạm
      để giáo viên duyệt thay đổi trực tiếp lên slide mà không cần gõ lại thủ công (chuẩn bị cho Day 7).
    """
    session_id: str = Field(description="Mã phiên hội thoại")
    ai_response: str = Field(description="Câu trả lời phản hồi từ Trợ giảng AI")
    current_slide_index: int = Field(default=0, description="Vị trí slide đang tham chiếu")
    suggested_action: Optional[str] = Field(
        default=None,
        description="Loại hành động gợi ý: SIMPLIFY_SLIDE, ADD_QUIZ, UPDATE_FORMULA, EXPLAIN_MORE, GENERAL_ADVICE"
    )
    suggested_patch: Optional[SlidePatchProposal] = Field(
        default=None,
        description="Bản vá đề xuất cập nhật vào slide với định kiểu mạnh (chuẩn bị cho Day 7 Live Patching)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%H:%M"),
        description="Thời gian trả lời (HH:MM)"
    )

class ApplyPatchRequest(BaseModel):
    slide_deck: Dict[str, Any] = Field(description="Cấu trúc slide deck bài giảng hiện đại")
    patch : SlidePatchProposal = Field(description="Bản vá đề xuất từ trợ giảng AI cần áp dụng")


class ApplyPatchResponse(BaseModel):
    success: bool = Field(default=True, description="Trạng thái áp dụng thành công")
    target_slide_index: int = Field(description="Vị trí slide vừa được cập nhật (0-indexed)")
    updated_slide: Dict[str, Any] = Field(description="Dữ liệu chi tiết của slide sau khi áp dụng bản vá")
    slide_deck: Dict[str, Any] = Field(description="Toàn bộ cấu trúc slide deck đã được cập nhật")
    message: str = Field(description="Thông báo kết quả xử lý sư phạm")
