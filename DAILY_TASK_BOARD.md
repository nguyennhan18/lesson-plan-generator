# 📋 DAILY TASK BOARD: 21 NGÀY TÁC CHIẾN (ZERO-SPILLOVER)
> **Nguyên tắc Kỷ luật Thép:** Hoàn thành dứt điểm trong ngày, tick `[x]` và nghiệm thu chạy thử trước khi tắt máy. Tuyệt đối không để dồn việc sang ngày hôm sau!

---

## ⏰ KHUNG THỜI GIAN CHUẨN MỖI NGÀY (8 TIẾNG LÀM VIỆC)

* **08:30 - 09:00 (30p) | Khởi động & Briefing**: Thống nhất kiến trúc, giải thuật, đọc tài liệu/mã nguồn liên quan.
* **09:00 - 12:00 (3h) | Block 1 - Core Implementation**: Viết mã nguồn Backend/Logic chính, comment giải thích.
* **13:30 - 15:30 (2h) | Block 2 - Frontend & Integration**: Kết nối giao diện, đồng bộ dữ liệu.
* **15:30 - 16:30 (1h) | Block 3 - Testing & Debugging**: Chạy test case thực tế, sửa lỗi phát sinh.
* **16:30 - 17:30 (1h) | Nghiệm thu & Defense Prep**: Bóc tách code chống mù code, ghi chép câu hỏi phản biện, `git commit`.

---

# 📅 CHI TIẾT TASK TỪNG NGÀY (DAY-BY-DAY CHECKLIST)

---

## 🟢 TUẦN 1: NỀN TẢNG DỮ LIỆU, PARSER ĐẦU VÀO & BONG BÓNG CHAT CO-PILOT

### 📌 NGÀY 1: Nâng cấp Data Schema (Quiz Phân tích Lỗi sai & Phân loại Học lực)
- [ ] **Task 1.1 (Sáng)**: Định nghĩa class `QuizOptionDetail` trong `project/app/schemas/slide_schema.py` (chứa: `label`, `text`, `is_correct`, `distractor_rationale`).
- [ ] **Task 1.2 (Sáng)**: Thêm trường `class_proficiency` (`basic`, `standard`, `advanced`) và `target_outcome` vào `SlideSchema` và `LessonRequest`.
- [ ] **Task 1.3 (Chiều)**: Cập nhật `SlideDeckSchema` hỗ trợ danh sách `QuizOptionDetail` khi layout là `QUIZ_OPTION`.
- [ ] **Task 1.4 (Chiều)**: Viết script test `test/test_day1_schema.py` kiểm tra Pydantic parse đúng JSON mẫu có câu hỏi và giải thích sai.
- [ ] **Task 1.5 (Cuối ngày)**: Nghiệm thu & Phiếu bàn giao: Nắm vững Pydantic V2 `BaseModel`, `Field`, enum và schema serialization.
- **🎯 DoD (Definition of Done)**: Chạy test pass 100%, Pydantic ném lỗi nếu thiếu trường `distractor_rationale` trong quiz slide.

---

### 📌 NGÀY 2: Nâng cấp AI Prompt Engineering (Phân hóa Bài giảng & SGK)
- [ ] **Task 2.1 (Sáng)**: Cập nhật `SLIDE_SYSTEM_PROMPT` trong `project/app/services/ai_service.py` với các chỉ dẫn sư phạm phân loại học lực (Yếu $\rightarrow$ Cơ bản; Giỏi $\rightarrow$ Vận dụng cao).
- [ ] **Task 2.2 (Sáng)**: Thêm ràng buộc ép LLM sinh câu hỏi trắc nghiệm có bẫy học sinh kèm lời giải thích tại sao sai dựa trên tâm lý học sinh THPT.
- [ ] **Task 2.3 (Chiều)**: Test gọi Gemini sinh slide cho 2 trường hợp đối lập: *"Cấp số cộng cho lớp yếu"* vs *"Cấp số cộng cho lớp chuyên Toán"*.
- [ ] **Task 2.4 (Chiều)**: Đảm bảo bộ lọc `fix_latex_backslashes_in_json` xử lý trơn tru không bị vỡ JSON khi có LaTeX trong câu hỏi trắc nghiệm.
- [ ] **Task 2.5 (Cuối ngày)**: Nghiệm thu: Đối chiếu 2 bộ slide sinh ra, đảm bảo độ phân hóa rõ rệt; ghi chép kỹ thuật Prompt.
- **🎯 DoD**: Sinh thành công bộ slide JSON chứa ít nhất 2 câu hỏi trắc nghiệm có đầy đủ 4 phương án kèm phân tích lỗi sai mà không bị lỗi JSON decode.

---

### 📌 NGÀY 3: Parser Tiếp nhận File Cũ (PPTX Parser & DOCX Parser)
- [ ] **Task 3.1 (Sáng)**: Tạo thư mục `project/app/parsers/` và file `pptx_parser.py`: dùng `python-pptx` quét Slide $\rightarrow$ Shape $\rightarrow$ gom toàn bộ text và notes.
- [ ] **Task 3.2 (Sáng)**: Viết `docx_parser.py`: dùng `python-docx` bóc tách các đoạn văn (paragraphs) và bảng biểu (tables) trong giáo án Word có sẵn.
- [ ] **Task 3.3 (Chiều)**: Tạo API endpoint `/api/v1/ingest/parse-document` nhận file tải lên (`UploadFile`) và trả về text nội dung đã làm sạch.
- [ ] **Task 3.4 (Chiều)**: Viết test thử nghiệm với file Word/PowerPoint bài giảng có sẵn trong thư mục `document/`.
- [ ] **Task 3.5 (Cuối ngày)**: Nghiệm thu: Hiểu rõ cấu trúc cây đối tượng OpenXML của Word và PowerPoint; commit code.
- **🎯 DoD**: Gửi 1 file PPTX và 1 file DOCX lên Swagger UI `/docs`, nhận về JSON chứa tiêu đề và toàn bộ nội dung văn bản sạch sẽ.

---

### 📌 NGÀY 4: Module Phân loại Học lực Lớp từ Bảng điểm
- [ ] **Task 4.1 (Sáng)**: Viết module `project/app/services/grade_classifier.py`: đọc file Excel/CSV bảng điểm lớp học.
- [ ] **Task 4.2 (Sáng)**: Xây dựng thuật toán thống kê: Tính Điểm trung bình, Độ lệch chuẩn, Tỉ lệ điểm < 5.0, điểm 8+.
- [ ] **Task 4.3 (Chiều)**: Hàm gán nhãn: Tự động kết luận trình độ lớp (`Lớp yếu giải tích`, `Lớp trung bình`, `Lớp nâng cao`) và gợi ý trọng tâm bài dạy.
- [ ] **Task 4.4 (Chiều)**: Tích hợp kết quả phân loại vào endpoint sinh bài giảng của `main.py`.
- [ ] **Task 4.5 (Cuối ngày)**: Nghiệm thu: Chạy thử với 2 file bảng điểm mẫu giả lập; hiểu rõ thuật toán phân loại.
- **🎯 DoD**: Đưa 1 file Excel bảng điểm vào, hệ thống tự động suy ra profile học lực và chuyển profile đó làm tham số cho Gemini AI sinh bài phù hợp.

---

### 📌 NGÀY 5: Tái cấu trúc UI Split-View Studio (Giao diện 2 Cột)
- [ ] **Task 5.1 (Sáng)**: Thiết kế lại `project/app/static/index.html`: chia bố cục 2 cột (Cột trái: Sidebar điều khiển & Chat; Cột phải: Khung trình chiếu Slide).
- [ ] **Task 5.2 (Sáng)**: Cập nhật `style.css`: Responsive layout, màu sắc hiện đại chuẩn EdTech, hỗ trợ thanh trượt danh sách thumbnail slide bên dưới.
- [ ] **Task 5.3 (Chiều)**: Chuyển toàn bộ logic render preview slide cũ sang khung bên phải, giữ nguyên hỗ trợ KaTeX.
- [ ] **Task 5.4 (Chiều)**: Thêm nút chuyển slide (Previous/Next) mượt mà bằng phím mũi tên hoặc nút bấm.
- [ ] **Task 5.5 (Cuối ngày)**: Nghiệm thu: Giao diện hiển thị chuyên nghiệp, không vỡ layout trên màn hình máy tính; hiểu rõ cấu trúc DOM.
- **🎯 DoD**: Mở trình duyệt tại `http://localhost:8000/`, hiển thị giao diện 2 cột sắc nét, chuyển qua lại các trang slide mượt mà.

---

### 📌 NGÀY 6: Xây dựng Bong bóng Chat Co-pilot (Chat Session API)
- [ ] **Task 6.1 (Sáng)**: Tạo API endpoint `/api/v1/chat/interact` nhận `{session_id, user_message, current_slide_index, slide_deck}`.
- [ ] **Task 6.2 (Sáng)**: Viết prompt cho vai trò "Trợ giảng AI": Lắng nghe yêu cầu của GV, phân tích xem GV muốn sửa slide nào hay thêm nội dung gì.
- [ ] **Task 6.3 (Chiều)**: Dựng giao diện Bong bóng Chat ở cột trái (tin nhắn người dùng màu xanh, tin nhắn AI màu xám, hiển thị thời gian).
- [ ] **Task 6.4 (Chiều)**: Kết nối API từ `app.js`: gửi tin nhắn và hiển thị phản hồi của AI kèm trạng thái "Đang suy nghĩ...".
- [ ] **Task 6.5 (Cuối ngày)**: Nghiệm thu: Hiểu rõ cơ chế duy trì ngữ cảnh (Conversation Context) trong LLM.
- **🎯 DoD**: Gõ tin nhắn chat *"Giải thích lại slide 2 đơn giản hơn"*, AI trả lời đúng trọng tâm và gợi ý nội dung mới trong khung chat.

---

### 📌 NGÀY 7: Đồng bộ hóa Chatbot với Slide Preview (Live Patching)
- [ ] **Task 7.1 (Sáng)**: Viết hàm Backend trả về cả câu trả lời chat VÀ dữ liệu slide cập nhật (`updated_slide`).
- [ ] **Task 7.2 (Sáng)**: Viết hàm Frontend `patchCurrentSlide(newSlideData)`: tự động cập nhật đúng slide trên màn hình mà không tải lại toàn trang.
- [ ] **Task 7.3 (Chiều)**: Thêm hiệu ứng highlight (viền xanh phát sáng) báo hiệu cho giáo viên biết slide vừa được sửa đổi.
- [ ] **Task 7.4 (Chiều)**: Chạy test End-to-End toàn bộ tính năng Tuần 1: Nhập topic $\rightarrow$ Sinh bài $\rightarrow$ Chat yêu cầu sửa $\rightarrow$ Slide tự đổi.
- [ ] **Task 7.5 (Cuối ngày)**: **TỔNG KẾT TUẦN 1**: Đóng gói mã nguồn, git commit, tự trả lời bộ câu hỏi Hội đồng Tuần 1.
- **🎯 DoD**: Sau khi chat yêu cầu sửa nội dung, slide bên phải tự động thay đổi nội dung mới ngay tức khắc mà không làm mất các slide khác.

---

## 🟡 TUẦN 2: BIÊN TẬP TOÁN TRỰC QUAN & HÌNH HỌC KHÔNG GIAN 3D

### 📌 NGÀY 8: Nhúng Trình gõ Toán Trực quan (MathLive)
- [ ] **Task 8.1 (Sáng)**: Tích hợp thư viện CDN `mathlive` vào `index.html` (sử dụng web component `<math-field>`).
- [ ] **Task 8.2 (Sáng)**: Dựng Modal Popup chỉnh sửa công thức: Khi giáo viên nhấp đúp vào công thức trên slide, popup MathLive mở ra.
- [ ] **Task 8.3 (Chiều)**: Cấu hình bàn phím ảo toán học tiếng Việt (các nút bấm: phân số, tích phân, căn, vectơ, giới hạn).
- [ ] **Task 8.4 (Chiều)**: Bắt sự kiện gõ công thức trên MathLive và xem trước kết quả tức thì.
- [ ] **Task 8.5 (Cuối ngày)**: Nghiệm thu: Hiểu cách thức hoạt động của Web Components `<math-field>` và cây AST công thức toán.
- **🎯 DoD**: Bấm đúp vào công thức trên slide $\rightarrow$ Bật popup có bàn phím toán ảo $\rightarrow$ Bấm nút chèn căn bậc hai hiển thị trực quan không lỗi.

---

### 📌 NGÀY 9: Cơ chế Đồng bộ 2 Chiều (MathLive $\leftrightarrow$ Slide JSON)
- [ ] **Task 9.1 (Sáng)**: Viết logic JavaScript: Khi GV bấm "Lưu công thức", lấy chuỗi LaTeX từ `mathfield.getValue('latex-expanded')`.
- [ ] **Task 9.2 (Sáng)**: Cập nhật chuỗi LaTeX mới vào cấu trúc Slide JSON đang lưu trữ trong bộ nhớ trình duyệt.
- [ ] **Task 9.3 (Chiều)**: Render lại ngay công thức đó bằng KaTeX trên slide preview để GV thấy kết quả cuối cùng.
- [ ] **Task 9.4 (Chiều)**: Viết hàm kiểm tra cú pháp LaTeX hợp lệ trước khi lưu để tránh hỏng slide.
- [ ] **Task 9.5 (Cuối ngày)**: Nghiệm thu: Hiểu cơ chế Two-way Data Binding và chuẩn serialization LaTeX.
- **🎯 DoD**: Sửa công thức từ $y = 2x$ thành $y = x^2 + 1$ bằng MathLive $\rightarrow$ Nhấn Lưu $\rightarrow$ Slide hiển thị đúng $y = x^2 + 1$ bằng KaTeX.

---

### 📌 NGÀY 10: Xây dựng Bộ lọc Kiểm duyệt Sư phạm (AI Linter & Proofreader)
- [ ] **Task 10.1 (Sáng)**: Viết endpoint `/api/v1/validation/audit-deck` trong `validation.py`: Quét toàn bộ slide tìm lỗi chính tả tiếng Việt thường gặp.
- [ ] **Task 10.2 (Sáng)**: Tích hợp SymPy kiểm tra biến đổi đại số cơ bản (đảm bảo hai vế phương trình có tương đương không).
- [ ] **Task 10.3 (Chiều)**: Prompt AI đối chiếu công thức với định lý SGK, trả về mảng `warnings: [{slide_index, message, severity}]`.
- [ ] **Task 10.4 (Chiều)**: Thiết kế giao diện "Danh sách Cảnh báo": Hiển thị biểu tượng ⚠️ màu vàng trên slide có lỗi, click vào sẽ gợi ý cách sửa mà KHÔNG tự ý ghi đè bài của GV.
- [ ] **Task 10.5 (Cuối ngày)**: Nghiệm thu: Hiểu sâu nguyên tắc Human-in-the-loop trong sư phạm; ghi chép kỹ thuật.
- **🎯 DoD**: Đưa một slide cố tình gõ sai từ "học xinh" và công thức sai dấu $\rightarrow$ Hệ thống hiện bảng cảnh báo vàng để GV tự sửa.

---

### 📌 NGÀY 11: Nhúng Thư viện Hình học Không gian 3D Tương tác
- [ ] **Task 11.1 (Sáng)**: Tích hợp **GeoGebra Web Component (GGBApplet)** hoặc Three.js canvas vào slide layout `IMAGE_TEXT`.
- [ ] **Task 11.2 (Sáng)**: Viết script nạp mô hình mẫu 3D: Hình chóp tam giác ($S.ABC$) và hình chóp tứ giác ($S.ABCD$).
- [ ] **Task 11.3 (Chiều)**: Kích hoạt điều khiển chuột: Cho phép xoay 360 độ quanh trục $Ox, Oy, Oz$, cuộn chuột phóng to/thu nhỏ.
- [ ] **Task 11.4 (Chiều)**: Cấu hình trục toạ độ không gian $Oxyz$ và mặt phẳng đáy $Oxy$.
- [ ] **Task 11.5 (Cuối ngày)**: Nghiệm thu: Hiểu cơ chế WebGL/Canvas rendering và hệ toạ độ Descartes 3 chiều.
- **🎯 DoD**: Trên slide Hình học không gian, xuất hiện khung 3D cho phép dùng chuột kéo xoay khối chóp mượt mà không giật lag.

---

### 📌 NGÀY 12: Thêm Thanh Điều khiển Tham số Hình học (Slider Controls)
- [ ] **Task 12.1 (Sáng)**: Tạo các thanh trượt UI (Slider): Chiều cao $h$ (từ 1 đến 10), Cạnh đáy $a$ (từ 1 đến 8).
- [ ] **Task 12.2 (Sáng)**: Bắt sự kiện `oninput` của slider: Gọi API cập nhật toạ độ đỉnh chóp $S(0, 0, h)$ theo thời gian thực.
- [ ] **Task 12.3 (Chiều)**: Hiển thị bảng thông số động bên cạnh hình: Thể tích $V = \frac{1}{3} S_{đáy} \cdot h$ tự động nhảy số theo thanh trượt.
- [ ] **Task 12.4 (Chiều)**: Tối ưu hiệu năng render: Dùng `requestAnimationFrame` để kéo thanh trượt mượt mà 60 FPS.
- [ ] **Task 12.5 (Cuối ngày)**: Nghiệm thu: Nắm vững kỹ thuật Parametric Modeling (Hình học tham số).
- **🎯 DoD**: Kéo thanh trượt chiều cao $\rightarrow$ Hình chóp cao lên ngay lập tức $\rightarrow$ Con số thể tích $V$ tính toán lại chuẩn xác.

---

### 📌 NGÀY 13: Xử lý Đường Nét đứt (Hidden Lines) & Nhiều Góc nhìn
- [ ] **Task 13.1 (Sáng)**: Cấu hình thuật toán hiển thị nét đứt cho các cạnh khuất nằm phía sau mặt phẳng trong mô hình 3D.
- [ ] **Task 13.2 (Sáng)**: Thêm nút chuyển đổi nhanh góc nhìn: *Góc nhìn phối cảnh chuẩn*, *Hình chiếu đứng (nhìn từ trước)*, *Hình chiếu bằng (nhìn từ trên)*.
- [ ] **Task 13.3 (Chiều)**: Bổ sung chế độ xem "Hình khai triển phẳng 2D" song song với hình 3D để học sinh dễ hình dung diện tích xung quanh.
- [ ] **Task 13.4 (Chiều)**: Thêm nút bật/tắt hiển thị tên các đỉnh ($S, A, B, C, D$).
- [ ] **Task 13.5 (Cuối ngày)**: Nghiệm thu: Hiểu thuật toán Raycasting / Hidden Surface Removal trong đồ họa máy tính.
- **🎯 DoD**: Bấm nút "Hình chiếu bằng" $\rightarrow$ Khối chóp tự xoay về góc nhìn thẳng từ trên xuống đáy; các cạnh khuất hiển thị nét đứt rõ ràng.

---

### 📌 NGÀY 14: Cầu nối Chụp ảnh Snapshot 3D gửi về Backend
- [ ] **Task 14.1 (Sáng)**: Viết hàm JavaScript `capture3DSnapshot()` sử dụng `canvas.toDataURL('image/png')` chụp lại khung hình 3D hiện tại.
- [ ] **Task 14.2 (Sáng)**: Gửi chuỗi Base64 ảnh vừa chụp về Backend qua endpoint `/api/v1/slide/sync-snapshot`.
- [ ] **Task 14.3 (Chiều)**: Backend gán Base64 này vào `slide.chart_image_base64` để chuẩn bị cho việc xuất file PPTX.
- [ ] **Task 14.4 (Chiều)**: Chạy test kiểm tra ảnh chụp không bị méo tỉ lệ hoặc mất nền trong suốt.
- [ ] **Task 14.5 (Cuối ngày)**: **TỔNG KẾT TUẦN 2**: Đóng gói mã nguồn, git commit, tự trả lời bộ câu hỏi Hội đồng Tuần 2.
- **🎯 DoD**: Bấm nút "Lưu góc nhìn này" $\rightarrow$ Backend nhận được file ảnh PNG chụp đúng góc xoay 3D vừa chọn và hiển thị ảnh thumbnail thành công.

---

## 🔴 TUẦN 3: TRÌNH CHIẾU TƯƠNG TÁC, XUẤT PPTX HOÀN CHỈNH & VỀ ĐÍCH

### 📌 NGÀY 15: Chế độ Trình chiếu Toàn màn hình (Web Presentation Mode)
- [ ] **Task 15.1 (Sáng)**: Thêm nút "Bắt đầu Tiết học" (Start Presentation) gọi HTML5 Fullscreen API (`document.documentElement.requestFullscreen()`).
- [ ] **Task 15.2 (Sáng)**: Thiết kế giao diện Trình chiếu: Ẩn thanh sidebar và bong bóng chat, căn chỉnh slide tràn màn hình tỉ lệ 16:9 sắc nét.
- [ ] **Task 15.3 (Chiều)**: Cài đặt phím tắt bàn phím: Mũi tên trái/phải để lùi/tiến slide, phím `ESC` để thoát, phím `B` làm tối màn hình để thu hút sự chú ý.
- [ ] **Task 15.4 (Chiều)**: Thêm thanh điều khiển mờ (floating control bar) ở đáy màn hình có đồng hồ đếm thời gian tiết dạy (45 phút).
- [ ] **Task 15.5 (Cuối ngày)**: Nghiệm thu: Nắm vững Fullscreen API và UX trình chiếu sư phạm.
- **🎯 DoD**: Bấm nút trình chiếu $\rightarrow$ Trình duyệt chuyển toàn màn hình đen chuyên nghiệp như PowerPoint, bấm phím mũi tên chuyển slide mượt mà.

---

### 📌 NGÀY 16: Câu hỏi Trắc nghiệm Tương tác & Giải thích Lỗi sai
- [ ] **Task 16.1 (Sáng)**: Dựng component trắc nghiệm trên slide trình chiếu: 4 nút bấm phương án A, B, C, D to rõ ràng.
- [ ] **Task 16.2 (Sáng)**: Bắt sự kiện bấm chọn: Nếu chọn đáp án đúng $\rightarrow$ Nút đổi màu xanh lá cây + âm thanh/hiệu ứng chúc mừng.
- [ ] **Task 16.3 (Chiều)**: **Tính năng cốt lõi**: Nếu chọn đáp án sai $\rightarrow$ Nút đổi màu đỏ + **Bật hộp thoại giải thích chi tiết tại sao sai** (lấy từ `distractor_rationale`).
- [ ] **Task 16.4 (Chiều)**: Nút "Xem Lời giải Chi tiết": Hiển thị từng bước biến đổi chuẩn mực của bài toán để học sinh ghi chép.
- [ ] **Task 16.5 (Cuối ngày)**: Nghiệm thu: Hiểu rõ cơ chế Interactive Feedback Loop trong dạy học tích cực.
- **🎯 DoD**: Bấm vào đáp án sai $\rightarrow$ Màn hình hiện ngay popup: *"Bạn chọn sai vì quên đổi dấu khi chuyển vế. Lưu ý quy tắc..."* đúng như ý tưởng thiết kế.

---

### 📌 NGÀY 17: Tinh chỉnh Lời giải Chuẩn SGK & Bộ Prompt Mẫu
- [ ] **Task 17.1 (Sáng)**: Xây dựng tập prompt mẫu (Few-shot Prompting) dựa trên cấu trúc lời giải chuẩn của VietJack, Loigiaihay, Toanmath.
- [ ] **Task 17.2 (Sáng)**: Quy chuẩn định dạng lời giải tự luận: *Bước 1: Điều kiện/Tập xác định $\rightarrow$ Bước 2: Biến đổi/Đạo hàm $\rightarrow$ Bước 3: Kết luận*.
- [ ] **Task 17.3 (Chiều)**: Kiểm thử chất lượng lời giải với 3 dạng toán kinh điển: *Khảo sát đơn điệu hàm số, Tìm số hạng cấp số cộng, Tính khoảng cách trong không gian*.
- [ ] **Task 17.4 (Chiều)**: Tối ưu thời gian sinh bài của Gemini (giảm latency bằng cách tinh gọn schema và token).
- [ ] **Task 17.5 (Cuối ngày)**: Nghiệm thu: Nắm vững kỹ thuật Prompt Curation và chuẩn hóa văn phong sư phạm.
- **🎯 DoD**: Mọi bài giải mẫu do AI sinh ra đều có cấu trúc bước giải rõ ràng, dùng đúng thuật ngữ trong SGK Toán GDPT 2018.

---

### 📌 NGÀY 18: Nâng cấp Toàn diện Module Xuất PowerPoint (`slide_exporter.py`)
- [ ] **Task 18.1 (Sáng)**: Bổ sung layout cho Slide Trắc nghiệm trong `slide_exporter.py`: Vẽ 4 ô đáp án A, B, C, D bằng Shape PowerPoint có viền màu đẹp mắt.
- [ ] **Task 18.2 (Sáng)**: Tự động nhúng ảnh chụp Snapshot 3D (từ Ngày 14) vào khung minh họa của file PPTX.
- [ ] **Task 18.3 (Chiều)**: Nhúng `teacher_note` (lời thoại giảng dạy) và toàn bộ phần phân tích lý do sai vào phần **Notes** (Ghi chú dưới slide) của PowerPoint.
- [ ] **Task 18.4 (Chiều)**: Kiểm tra file PPTX xuất ra: Đảm bảo không bị tràn chữ, không lệch khung, công thức toán hiển thị rõ nét.
- [ ] **Task 18.5 (Cuối ngày)**: Nghiệm thu: Nắm vững thư viện `python-pptx`, slide notes slide relationship và coordinate system.
- **🎯 DoD**: Tải file PowerPoint về máy $\rightarrow$ Mở trên Microsoft PowerPoint: Các câu hỏi trắc nghiệm, hình vẽ 3D và lời nhắc GV dưới Notes hiển thị hoàn hảo.

---

### 📌 NGÀY 19: Đồng bộ Xuất File Word (`docx_exporter.py`) & Hoàn thiện Luồng Dual-Mode
- [ ] **Task 19.1 (Sáng)**: Kiểm tra lại `docx_exporter.py`: Đảm bảo đồng bộ 100% nội dung giữa Kế hoạch bài dạy (Word CV 5512) và Slide bài giảng.
- [ ] **Task 19.2 (Sáng)**: Tích hợp nút bấm tải về trên giao diện Web Studio: "Tải Giáo án Word (.docx)" và "Tải Bài giảng PowerPoint (.pptx)".
- [ ] **Task 19.3 (Chiều)**: Tối ưu luồng dữ liệu Dual-Mode: Dạy trực tiếp trên Web $\leftrightarrow$ Xuất file lưu trữ sau giờ học.
- [ ] **Task 19.4 (Chiều)**: Viết script dọn dẹp file tạm trên server để tránh rác ổ cứng.
- [ ] **Task 19.5 (Cuối ngày)**: Nghiệm thu: Nắm vững toàn bộ pipeline chuyển đổi đa định dạng (Multi-format Export Pipeline).
- **🎯 DoD**: Bấm một nút tải được cả file Word chuẩn CV 5512 và file PowerPoint có nội dung khớp nhau 100%.

---

### 📌 NGÀY 20: Chạy Kiểm thử Toàn diện (End-to-End Testing)
- [ ] **Task 20.1 (Sáng)**: Chạy test bài dạy Lớp 10: *Hệ bất phương trình bậc nhất 2 ẩn*.
- [ ] **Task 20.2 (Sáng)**: Chạy test bài dạy Lớp 11: *Cấp số cộng - Quan hệ vuông góc trong không gian*.
- [ ] **Task 20.3 (Chiều)**: Chạy test bài dạy Lớp 12: *Tính đơn điệu và cực trị hàm số - Thể tích khối chóp*.
- [ ] **Task 20.4 (Chiều)**: Sửa triệt để các lỗi edge-cases (công thức quá dài, tên bài có ký tự đặc biệt, kết nối mạng chập chờn).
- [ ] **Task 20.5 (Cuối ngày)**: Nghiệm thu: Toàn bộ hệ thống chạy ổn định, không ném exception `500 Internal Server Error`.
- **🎯 DoD**: Chạy trơn tru 3 bài dạy mẫu thuộc 3 khối lớp khác nhau từ đầu vào đến đầu ra mà không gặp bất kỳ lỗi nào.

---

### 📌 NGÀY 21: Đóng gói Sản phẩm & Kịch bản Bảo vệ Đồ án Điểm 10
- [ ] **Task 21.1 (Sáng)**: Viết tài liệu `README.md` hoàn chỉnh: Kiến trúc hệ thống, sơ đồ khối, hướng dẫn cài đặt chạy trong 1 câu lệnh.
- [ ] **Task 21.2 (Sáng)**: Xây dựng kịch bản Demo 5 phút đỉnh cao:
  * *Phút 1*: Tải giáo án/slide cũ lên $\rightarrow$ AI đọc và phân loại học lực lớp.
  * *Phút 2*: Chat với Co-pilot yêu cầu đổi bài tập $\rightarrow$ Slide tự động cập nhật.
  * *Phút 3*: Mở MathLive sửa công thức trực tiếp trên slide.
  * *Phút 4*: Bật Trình chiếu Web $\rightarrow$ Xoay khối 3D $\rightarrow$ Bấm trắc nghiệm giải thích vì sao sai.
  * *Phút 5*: Tải file PowerPoint và Word về máy chứng minh tính ứng dụng thực tế.
- [ ] **Task 21.3 (Chiều)**: Đóng gói bộ câu hỏi & câu trả lời phản biện trước Hội đồng.
- [ ] **Task 21.4 (Chiều)**: Tổng duyệt lần cuối toàn bộ mã nguồn.
- [ ] **Task 21.5 (Cuối ngày)**: **HOÀN THÀNH 100% DỰ ÁN - TỰ TIN BẢO VỆ VÀ ĐẠT ĐIỂM XUẤT SẮC!** 🎉
