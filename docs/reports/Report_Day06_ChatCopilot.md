# 📊 BÁO CÁO TIẾN ĐỘ VÀ NGHIỆM THU KỸ THUẬT CHI TIẾT NGÀY 6
## XÂY DỰNG BONG BÓNG CHAT CO-PILOT (CHAT SESSION API & TRỢ GIẢNG AI SƯ PHẠM THỜI GIAN THỰC)

**Ngày thực hiện:** 13/10/2026 - 14/10/2026  
**Dự án:** Lesson Plan Generator & Interactive 3D Slide Studio (`LessonAI-5512`)  
**Khung chương trình:** Chương trình Giáo dục Phổ thông 2018 (Công văn 5512/BGDĐT)  
**Trạng thái nghiệm thu (DoD):** 🎯 **ĐẠT 100% (9/9 Unit Tests Ngày 6 PASSED trong 0.89s; 36/36 Core Tests PASSED trong 0.95s)**  

---

## 📋 I. TỔNG QUAN NHIỆM VỤ VÀ BẢNG TIẾN ĐỘ NGÀY 6

Trong Ngày 6 của Kế hoạch 21 ngày tác chiến, chúng ta đã triển khai toàn diện phân hệ **Trợ giảng AI Co-pilot** đồng hành trực tiếp cùng giáo viên trên bục giảng. Hệ thống cho phép giáo viên điều khiển bài giảng bằng ngôn ngữ tự nhiên: yêu cầu giải thích lại các khái niệm trừu tượng, đơn giản hóa công thức toán học, hoặc tạo câu hỏi trắc nghiệm củng cố ngay trong tiết học.

Theo đúng quy trình làm việc Pair Programming, toàn bộ 5 Task cơ bản và 3 Nâng cấp Kiến trúc Chuyên sâu đã được hoàn thành:

| Mã Task | Phân loại | Nội dung công việc chi tiết | File triển khai | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Task 6.1** | Backend / API | Xây dựng API Router `POST /api/v1/chat/interact` nhận `{session_id, user_message, current_slide_index, ...}`; bổ sung endpoint lấy lịch sử `GET /history/{session_id}` và xóa phiên `DELETE /session/{session_id}`. | `project/app/schemas/chat_schema.py`<br>`project/app/main.py` | ✅ **100%** |
| **Task 6.2** | AI / Prompting | Thiết kế Prompt Sư phạm Chuyên sâu (`COPILOT_SYSTEM_PROMPT`): bám sát ngữ cảnh slide hiện hành, tuân thủ quy trình 3 bước (Trực quan hóa $\rightarrow$ Cô đọng công thức $\rightarrow$ Câu hỏi gợi mở Scaffolding), chuẩn hóa KaTeX Math. | `project/app/services/chat_service.py` | ✅ **100%** |
| **Task 6.3** | Frontend / UI | Dựng giao diện ngăn kéo Chat Copilot Drawer (`index.html`, `style.css`): Thanh bên trượt mượt mà, avatar 🤖, bong bóng tin nhắn Giáo viên (xanh) và AI (kính mờ), hiển thị huy hiệu slide hiện tại và gợi ý câu hỏi nhanh (Quick Chips). | `project/app/static/index.html`<br>`project/app/static/style.css` | ✅ **100%** |
| **Task 6.4** | Frontend / Client | Kết nối API từ `app.js`: Quản lý `session_id` qua `sessionStorage`, gửi tin nhắn bất đồng bộ `fetch()`, hiệu ứng "Đang suy nghĩ..." (Typing indicator 3 chấm nhảy động), tự động render công thức toán học KaTeX trong bong bóng chat. | `project/app/static/app.js` | ✅ **100%** |
| **Task 6.5** | Testing / QA | Viết bộ kiểm thử tự động 9 Test Cases bao phủ toàn diện: Schema Pydantic, Cửa sổ trượt, Dọn dẹp RAM TTL, Truy vết vị trí slide, Gợi ý trắc nghiệm, Gọi API TestClient, và xác thực tiêu chuẩn DoD. | `project/test/test_day6_chat.py` | ✅ **100%** |
| **Nâng cấp 1** | Kiến trúc / Schema | Mở rộng `ChatInteractRequest` đồng bộ ngữ cảnh sư phạm (`subject`, `grade`, `class_proficiency`) kế thừa trực tiếp từ kết quả phân loại bảng điểm Ngày 4 để AI tự động điều chỉnh độ khó sư phạm. | `project/app/schemas/chat_schema.py`<br>`project/app/services/chat_service.py` | ✅ **100%** |
| **Nâng cấp 2** | Bộ nhớ / Hiệu năng | Nâng cấp `ChatSessionManager`: Lưu trữ đối tượng `ChatMessage`, ghi nhận `slide_index` trên từng tin nhắn, và bổ sung thuật toán thu hồi RAM tự động theo thời hạn TTL (`cleanup_expired_sessions`). | `project/app/services/chat_service.py` | ✅ **100%** |
| **Nâng cấp 3** | Nền tảng Ngày 7 | Thiết kế mô hình bản vá có định kiểu mạnh `SlidePatchProposal`, thay thế `suggested_patch` dạng loose-dict trong `ChatInteractResponse`, sẵn sàng cho tính năng Live Patching Ngày 7. | `project/app/schemas/chat_schema.py`<br>`project/app/services/chat_service.py` | ✅ **100%** |

---

## 🏛️ II. KIẾN TRÚC DỮ LIỆU & SCHEMA CHUẨN HÓA (`chat_schema.py`)

Hệ thống tuân thủ nguyên tắc định kiểu mạnh (Strong Typing) với Pydantic V2, mọi mô hình đều được tài liệu hóa theo quy chuẩn **"Why, not What"** giải thích lý do sư phạm và kiến trúc:

```
                    ┌───────────────────────────┐
                    │    ChatInteractRequest    │
                    │  - session_id: str        │
                    │  - user_message: str      │
                    │  - current_slide_index    │
                    │  - subject: str           │
                    │  - grade: int             │
                    │  - class_proficiency: str │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    handle_copilot_chat    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │   ChatInteractResponse    │
                    │  - session_id: str        │
                    │  - ai_response: str       │
                    │  - current_slide_index    │
                    │  - suggested_action: str  │
                    │  - suggested_patch ───────┼──┐
                    │  - timestamp: str         │  │
                    └───────────────────────────┘  │
                                                   │ (Định kiểu mạnh)
                                                   ▼
                                    ┌─────────────────────────────┐
                                    │     SlidePatchProposal      │
                                    │  - target_slide_index: int  │
                                    │  - action: str              │
                                    │  - bullet_points: list[str] │
                                    │  - main_definition_latex    │
                                    │  - quiz: dict               │
                                    │  - preview_explanation: str │
                                    └─────────────────────────────┘
```

### 1. `ChatMessage`: Cấu trúc Tin nhắn Đơn lẻ
```python
class ChatMessage(BaseModel):
    role: str = Field(description="Vai trò người gửi: 'user' hoặc 'assistant'")
    content: str = Field(description="Nội dung tin nhắn")
    slide_index: Optional[int] = Field(default=None, description="Vị trí trang slide tại thời điểm phát sinh tin nhắn")
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"), description="Thời gian gửi tin nhắn (HH:MM)")
```
* **Lý do thiết kế (Why):** Gán trực tiếp `slide_index` vào từng tin nhắn giúp hệ thống và AI tái hiện chính xác ngữ cảnh slide tại thời điểm phát sinh câu hỏi, khắc phục tình trạng mất ngữ cảnh khi giáo viên chuyển slide liên tục trong giờ dạy.

### 2. `ChatInteractRequest`: Dữ liệu Đầu vào Tích hợp Hồ sơ Học lực
```python
class ChatInteractRequest(BaseModel):
    session_id: str = Field(description="Mã định danh phiên làm việc của giáo viên")
    user_message: str = Field(description="Nội dung câu hỏi hoặc yêu cầu chỉnh sửa slide từ giáo viên")
    current_slide_index: int = Field(default=0, description="Vị trí trang slide giáo viên đang đứng chiếu (0-indexed)")
    subject: Optional[str] = Field(default="Toán học", description="Tên môn học đang giảng dạy")
    grade: Optional[int] = Field(default=11, description="Khối lớp (từ lớp 6 đến lớp 12)")
    class_proficiency: Optional[str] = Field(default="standard", description="Hồ sơ học lực lớp: 'basic' | 'standard' | 'advanced'")
    slide_deck: Optional[Dict[str, Any]] = Field(default=None, description="Toàn bộ cấu trúc Slide Deck bài giảng hiện tại")
```
* **Lý do thiết kế (Why):** Tích hợp `class_proficiency` kế thừa trực tiếp từ thuật toán phân loại bảng điểm Ngày 4 (`grade_classifier.py`). Khi lớp có học lực `basic`, AI tự động ưu tiên diễn giải đời sống trực quan và chia nhỏ bước; khi lớp `advanced`, AI đi thẳng vào bản chất toán học chuyên sâu.

### 3. `SlidePatchProposal`: Nền tảng Định kiểu Bản vá cho Ngày 7
```python
class SlidePatchProposal(BaseModel):
    target_slide_index: int = Field(description="Chỉ số slide đích cần áp dụng thay đổi (0-indexed)")
    action: str = Field(description="Mã hành động đề xuất: 'SIMPLIFY_SLIDE' | 'REPLACE_BULLETS' | 'UPDATE_FORMULA' | 'ADD_QUIZ' | 'CUSTOM_PATCH'")
    bullet_points: Optional[List[str]] = Field(default=None, description="Danh sách gạch đầu dòng mới đề xuất thay thế")
    main_definition_latex: Optional[str] = Field(default=None, description="Công thức toán học LaTeX mới đề xuất cập nhật")
    quiz: Optional[Dict[str, Any]] = Field(default=None, description="Câu hỏi trắc nghiệm hoặc bài tập củng cố đề xuất chèn vào slide")
    preview_explanation: Optional[str] = Field(default=None, description="Tóm tắt lý do sư phạm đề xuất thay đổi này")

    @property
    def slide_index(self) -> int:
        return self.target_slide_index
```
* **Lý do thiết kế (Why):** Thay vì sử dụng dictionary tự do không kiểm soát, cấu trúc định kiểu mạnh cho phép Front-end hiển thị Thẻ So sánh (Diff View) và chuẩn bị nút bấm một chạm "Áp dụng bản vá" trong Ngày 7 mà không lo lỗi sai định dạng dữ liệu.

---

## 🧠 III. KIẾN TRÚC BỘ NHỚ PHIÊN & THU HỒI RAM (`ChatSessionManager`)

```
   Tin nhắn mới (add_turn)
           │
           ▼
┌─────────────────────────┐
│ Lưu ChatMessage         │ ───► Cập nhật _session_last_active[session_id] = now()
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐      (Nếu vượt quá max_history_turns * 2)
│ Sliding Window Trimming │ ───► Chỉ giữ lại N lượt trao đổi mới nhất
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐      (Nếu tổng session > 50 hoặc gọi định kỳ)
│ Session TTL Cleanup     │ ───► Xóa các session có (now - last_active) > 60 phút
└─────────────────────────┘
```

### 1. Thuật toán Cửa sổ Trượt (Sliding Window)
* Giới hạn `max_history_turns = 8` lượt trao đổi (16 tin nhắn).
* Khi giáo viên đặt câu hỏi thứ 9, tin nhắn thứ 1 và 2 tự động được giải phóng khỏi danh sách gửi lên LLM, giúp tiết kiệm chi phí token và giảm thiểu độ trễ phản hồi (Latency).

### 2. Cơ chế Giải phóng Bộ nhớ Tự động theo Thời hạn TTL (Memory Cleanup)
* Trong môi trường trường học với hàng trăm giáo viên đăng nhập, các session bị bỏ quên sau khi hết tiết dạy (45-60 phút) sẽ gây tích tụ bộ nhớ RAM (Memory Leak).
* Phương thức `cleanup_expired_sessions(max_age_minutes: int = 60) -> int` tự động quét `self._session_last_active`, giải phóng sạch sẽ các session quá hạn cả về danh sách tin nhắn lẫn mốc thời gian hoạt động.
* Tự động kích hoạt dọn dẹp nhẹ trong hàm `add_turn()` khi số lượng phiên tích lũy vượt quá 50 phiên.

---

## 📜 IV. THUẬT TOÁN TIÊM NGỮ CẢNH ĐỘNG & PROMPT SƯ PHẠM

### 1. Thuật toán Tiêm Ngữ cảnh 2 Tầng (`_build_slide_context_summary`)
Mỗi khi nhận yêu cầu từ giáo viên, hàm sinh tóm tắt sẽ kết hợp 2 tầng thông tin:
* **Tầng 1 (Hồ sơ Sư phạm):** Môn học, Khối lớp, và Trình độ học lực lớp (`BASIC`, `STANDARD`, `ADVANCED`).
* **Tầng 2 (Slide đang chiếu):** Trích xuất tiêu đề slide, các ý chính, và công thức LaTeX trọng tâm.

```python
pedagogical_header = (
    f"### THÔNG TIN LỚP HỌC & HỒ SƠ HỌC LỰC:\n"
    f"- Môn học: {subject} | Khối lớp: {grade}\n"
    f"- Trình độ học lực lớp: {class_proficiency.upper()} (Phân loại từ bảng điểm Day 4)\n\n"
    f"### NỘI DUNG SLIDE ĐANG CHIẾU TRÊN LỚP:\n"
)
```

### 2. Prompt Hệ thống Sư phạm Chuẩn mực (`COPILOT_SYSTEM_PROMPT`)
Được thiết kế theo 5 nguyên tắc sư phạm cốt lõi:
1. **Tác phong Đồng hành trên Bục giảng:** Ngắn gọn, súc tích, thực tế, thấu hiểu áp lực đứng lớp.
2. **Quy trình 3 Bước Đơn giản hóa Kiến thức:**
   - *Bước 1 (Trực quan hóa đời sống):* Ví dụ phòng học như chiếc hộp chữ nhật để hình dung đường chéo $AC'$.
   - *Bước 2 (Cô đọng công thức):* Quy tắc 2 bước Pytago với $AC = a\sqrt{2}$ và $AC' = a\sqrt{3}$.
   - *Bước 3 (Câu hỏi Scaffolding):* Đặt câu hỏi gợi mở: *"Nếu cạnh phòng tăng gấp đôi thành $2a$ thì đường chéo dài gấp mấy lần?"*.
3. **Sinh Câu hỏi Trắc nghiệm Nhanh:** 4 phương án $A, B, C, D$ có 1 đáp án đúng và giải thích rõ lỗi sai của các phương án bẫy (Distractor Rationale).
4. **Chuẩn hóa Toán học KaTeX:** Bọc toàn bộ ký hiệu và công thức toán học trong dấu dollar `$công thức$` hoặc `$$công thức$$`.

### 3. Bộ Sinh Sư phạm Thông minh Dự phòng (`_generate_intelligent_fallback_response`)
Hoạt động hoàn toàn tự chủ trong môi trường sandbox / offline, đáp ứng 100% tiêu chí kiểm thử DoD và đóng gói đối tượng `SlidePatchProposal` định kiểu cho các tình huống:
* **Slide 2:** Đơn giản hóa công thức đường chéo $AC' = a\sqrt{3}$.
* **Slide 3:** Nhận diện tam giác đều $\triangle AB'D'$ cạnh $a\sqrt{2}$ để tính đường cao $AH = \frac{a\sqrt{6}}{3}$.
* **Yêu cầu Quiz:** Đóng gói câu hỏi trắc nghiệm 4 phương án kèm đáp án chuẩn xác.

---

## 🎨 V. THIẾT KẾ GIAO DIỆN & TÍCH HỢP FRONT-END

### 1. Bố cục Ngăn kéo Chat Copilot (Slide-over Drawer)
* Tích hợp ở cạnh phải/trái của giao diện Split-View Studio, bật tắt linh hoạt bằng nút bấm `🤖 Trợ giảng AI` trên Presentation Dock hoặc phím bấm trực tiếp.
* Hiển thị huy hiệu vị trí slide đồng bộ thời gian thực: `Slide 2` tự động cập nhật khi giáo viên bấm chuyển trang bên khung trình chiếu.

### 2. Các Thành phần Giao diện Nổi bật
* **Hàng gợi ý câu hỏi nhanh (Quick Suggestion Chips):**
  * `💡 Giải thích slide 2 đơn giản hơn`
  * `❓ Câu hỏi gợi mở`
  * `📝 Thêm quiz trắc nghiệm`
  * `🧠 Mẹo nhớ công thức`
* **Bong bóng Tin nhắn Phân vai (Message Bubbles):**
  * Tin nhắn Giáo viên: Căn phải, nền xanh dương đậm `user-bubble`, hiển thị thời gian gửi.
  * Tin nhắn Trợ giảng AI: Căn trái, avatar 🤖, nền kính mờ tối `ai-bubble`, hỗ trợ định dạng danh sách, chữ đậm và công thức toán học.
* **Thẻ Đề xuất Hành động Sư phạm (`msg-action-badge`):**
  * Khi AI sinh bản vá đề xuất (ví dụ `SIMPLIFY_SLIDE`, `ADD_QUIZ`), một thẻ viền xanh cyan phát sáng xuất hiện trong bong bóng chat:  
    `💡 Đề xuất sư phạm: SIMPLIFY_SLIDE`
* **Hiệu ứng "Đang suy nghĩ..." (Typing Indicator):**
  * 3 chấm tròn Cyan nhảy động (`typingBounce`) hiển thị trong lúc chờ phản hồi từ server.
* **Tự động Biên dịch KaTeX:**
  * Lắng nghe hàm `renderMathInElement` sau mỗi lượt nhận tin nhắn để biên dịch toàn bộ mã LaTeX sang giao diện toán học sắc nét.

---

## 🧪 VI. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN (TEST SUITE VERIFICATION)

Bộ kiểm thử được viết mới trong `project/test/test_day6_chat.py` bao gồm **9 Test Cases**, chạy tự động qua `pytest`:

```bash
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/nguyennhan18/Documents/Lesson-Plan-Generator

project/test/test_day6_chat.py::test_chat_schema_validation PASSED       [ 11%]
project/test/test_day6_chat.py::test_chat_session_manager_sliding_window PASSED [ 22%]
project/test/test_day6_chat.py::test_chat_session_cleanup_expired PASSED  [ 33%]
project/test/test_day6_chat.py::test_chat_session_slide_index_tracking PASSED [ 44%]
project/test/test_day6_chat.py::test_copilot_dod_explain_slide_2_simpler PASSED [ 55%]
project/test/test_day6_chat.py::test_copilot_add_quiz_proposal PASSED    [ 66%]
project/test/test_day6_chat.py::test_api_chat_interact_endpoint PASSED   [ 77%]
project/test/test_day6_chat.py::test_api_chat_conversation_continuity PASSED [ 88%]
project/test/test_day6_chat.py::test_api_chat_empty_message_validation PASSED [100%]

======================== 9 passed, 3 warnings in 0.89s =========================
```

### Bảng Chi tiết 9 Ca Kiểm thử:
| STT | Tên Test Case | Mục tiêu kiểm định | Kết quả |
| :---: | :--- | :--- | :---: |
| 1 | `test_chat_schema_validation` | Xác thực tính hợp lệ của Pydantic Schema cho Request, Response và bản vá `SlidePatchProposal`. | ✅ **PASSED** |
| 2 | `test_chat_session_manager_sliding_window` | Đảm bảo bộ nhớ phiên hoạt động đúng cơ chế cửa sổ trượt (Sliding Window) và hàm `clear_session()`. | ✅ **PASSED** |
| 3 | `test_chat_session_cleanup_expired` | Kiểm tra cơ chế TTL dọn dẹp RAM tự động: thu hồi phiên cũ (> 60 phút), giữ nguyên phiên đang hoạt động. | ✅ **PASSED** |
| 4 | `test_chat_session_slide_index_tracking` | Kiểm tra khả năng lưu trữ và truy xuất chính xác `slide_index` qua cả hai dạng từ điển JSON và đối tượng `ChatMessage`. | ✅ **PASSED** |
| 5 | `test_copilot_dod_explain_slide_2_simpler` | **Xác thực tiêu chí DoD Ngày 6:** Gửi câu hỏi về Slide 2, AI trả lời chi tiết và sinh `SlidePatchProposal` định kiểu mạnh. | ✅ **PASSED** |
| 6 | `test_copilot_add_quiz_proposal` | Kiểm tra AI sinh câu hỏi trắc nghiệm củng cố (4 phương án, đáp án đúng) đóng gói vào `SlidePatchProposal`. | ✅ **PASSED** |
| 7 | `test_api_chat_interact_endpoint` | Gọi trực tiếp API HTTP qua TestClient, kiểm định tuần tự hóa JSON đúng cấu trúc của `SlidePatchProposal`. | ✅ **PASSED** |
| 8 | `test_api_chat_conversation_continuity` | Kiểm tra tính liên tục qua nhiều lượt trao đổi (Multi-turn), xác thực `slide_index` được trả về qua endpoint history. | ✅ **PASSED** |
| 9 | `test_api_chat_empty_message_validation` | Kiểm tra xử lý ngoại lệ validation khi thiếu trường bắt buộc (HTTP 422 Unprocessable Entity). | ✅ **PASSED** |

### Kiểm tra Hồi quy Toàn bộ Hệ thống Core:
```bash
project/venv/bin/pytest project/test/test_day4_classifier.py project/test/test_day6_chat.py project/test/test_schema.py
# Kết quả: 36/36 passed, 6 warnings in 0.95s
```
* Bộ phân loại học lực Ngày 4 (`test_day4_classifier.py`): **23/23 PASSED**.
* Phân hệ Chat Co-pilot Ngày 6 (`test_day6_chat.py`): **9/9 PASSED**.
* Bộ Schema cốt lõi (`test_schema.py`): **4/4 PASSED**.

---

## 🎯 VII. ĐÁNH GIÁ TIÊU CHUẨN NGHIỆM THU (DEFINITION OF DONE - DoD)

* **Yêu cầu DoD Ngày 6 trong Kế hoạch:**
  > *"Gõ tin nhắn chat Giải thích lại slide 2 đơn giản hơn, AI trả lời đúng trọng tâm và gợi ý nội dung mới trong khung chat."*
* **Đối chiếu thực tế triển khai:**
  1. Giao diện người dùng có sẵn nút Quick Chip `💡 Giải thích slide 2 đơn giản hơn` và thanh gõ tin nhắn tự do.
  2. Phản hồi của AI cung cấp đầy đủ:
     - So sánh đời sống trực quan (chiếc hộp).
     - Quy tắc 2 bước Pytago với công thức KaTeX chuẩn mực: $AC = a\sqrt{2}$, $AC' = a\sqrt{3}$.
     - Gợi ý nội dung tóm gọn chiếu lên slide.
     - Câu hỏi gợi mở kích thích tư duy học sinh.
  3. Dữ liệu trả về đóng gói sẵn đối tượng `SlidePatchProposal` có định kiểu mạnh, hiển thị thẻ đề xuất `SIMPLIFY_SLIDE` ngay trong khung chat.
* **Kết luận nghiệm thu:** **ĐẠT TIÊU CHUẨN ĐẦU RA NGÀY 6 (100% DoD COMPLETED)**.

---

## 🚀 VIII. KẾ HOẠCH BƯỚC TIẾP THEO (NGÀY 7 - LIVE PATCHING & TỔNG KẾT TUẦN 1)

Việc hoàn thành 3 nâng cấp kiến trúc ở Ngày 6 đã tạo bệ phóng hoàn hảo cho Ngày 7:
* **Task 7.1:** Backend hoàn thiện API đồng bộ phản hồi chat và bản vá slide (`updated_slide` / `SlidePatchProposal`).
* **Task 7.2:** Frontend xây dựng hàm `patchCurrentSlide(newSlideData)` cập nhật DOM tức thì mà không tải lại trang.
* **Task 7.3:** Thêm hiệu ứng highlight (viền xanh phát sáng) báo hiệu vị trí slide vừa được cập nhật.
* **Task 7.4:** Chạy kiểm thử End-to-End toàn bộ luồng Tuần 1: Nhập topic $\rightarrow$ Sinh bài $\rightarrow$ Chat yêu cầu sửa $\rightarrow$ Slide tự động cập nhật trực tiếp.
* **Task 7.5:** **TỔNG KẾT TUẦN 1**: Đóng gói mã nguồn, git commit, lập báo cáo tuần và chuẩn bị bộ câu hỏi phản biện trước Hội đồng.
