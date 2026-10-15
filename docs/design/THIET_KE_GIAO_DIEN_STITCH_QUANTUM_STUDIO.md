# 📐 BẢN ĐẶC TẢ THIẾT KẾ GIAO DIỆN CHUYÊN NGHIỆP DÀNH CHO STITCH
## DỰ ÁN: QUANTUM STUDIO - HỆ SINH THÁI BÀI GIẢNG TOÁN HỌC & GIÁO ÁN CV 5512
> **Phiên bản:** 6.0 Professional Design System Spec  
> **Phong cách chủ đạo:** Cyber-Academic Glassmorphism & Clean Ergonomic EdTech  
> **Mục tiêu:** Bản mô tả chi tiết từng màn hình Dashboard độc lập (tách biệt công năng), tối ưu hóa trải nghiệm giảng dạy thực chiến trên lớp với buồng lái trình chiếu 3 phân vùng (Chatbox GV + Sân khấu 16:9 + Thanh công cụ 3D/Đồ thị).

---

## 📑 MỤC LỤC
1. [Triết Lý Thiết Kế & Hệ Thống Design Tokens](#1-triết-lý-thiết-kế--hệ-thống-design-tokens)
2. [Kiến Trúc Điều Hướng Toàn Cục (Global Shell & Navigation)](#2-kiến-trúc-điều-hướng-toàn-cục-global-shell--navigation)
3. [MÀN HÌNH 1: Sân Khấu Trình Chiếu Giảng Dạy (Presentation Cockpit Stage)](#3-màn-hình-1-sân-khấu-trình-chiếu-giảng-dạy-presentation-cockpit-stage)
4. [MÀN HÌNH 2: Dashboard Soạn Kế Hoạch Bài Dạy 5512 (Lesson Plan Studio)](#4-màn-hình-2-dashboard-soạn-kế-hoạch-bài-dạy-5512-lesson-plan-studio)
5. [MÀN HÌNH 3: Dashboard Xưởng Biên Tập Slide & Đồ Thị (Slide Deck Editor)](#5-màn-hình-3-dashboard-xưởng-biên-tập-slide--đồ-thị-slide-deck-editor)
6. [MÀN HÌNH 4: Dashboard Trung Tâm Phân Tích Lớp Học (Class Analytics)](#6-màn-hình-4-dashboard-trung-tâm-phân-tích-lớp-học-class-analytics)
7. [MÀN HÌNH 5: Dashboard Quản Trị Kho Tri Thức & Cấu Hình AI (Knowledge Hub)](#7-màn-hình-5-dashboard-quản-trị-kho-tri-thức--cấu-hình-ai-knowledge-hub)
8. [Bộ Prompt Mẫu Dành Cho Stitch / Figma AI / UI Generator](#8-bộ-prompt-mẫu-dành-cho-stitch--figma-ai--ui-generator)

---

## 1. TRIẾT LÝ THIẾT KẾ & HỆ THỐNG DESIGN TOKENS

### 1.1. Triết lý "Không Nhồi Nhét - Đúng Ngữ Cảnh (Contextual Focus)"
- **Vấn đề thực tế của Giáo viên:** Khi đang đứng lớp, giáo viên cần một không gian trình chiếu thoáng đãng, tập trung cao độ, không bị phân tâm bởi các nút bấm kỹ thuật hay bảng biểu nhập liệu. Tuy nhiên, giáo viên lại **rất cần 2 trợ thủ tức thì**:
  1. Một **Ô Chatbox Trợ Giảng AI** để giải đáp thắc mắc, gợi mở câu hỏi hoặc sửa đổi slide theo diễn biến lớp học.
  2. Một **Thanh Công Cụ 3D & Đồ Thị** để trực tiếp điều khiển khối đa diện (xoay, cắt thiết diện, đổi góc nhìn) hoặc vẽ đồ thị hàm số theo yêu cầu học sinh.
- **Giải pháp Đa Màn Hình (Multi-Screen Architecture):** Tách bạch thành **5 Dashboard chuyên biệt**. Khi ở màn hình trình chiếu, áp dụng cấu trúc **Buồng lái 3 Phân Vùng (Dockable Cockpit)** với cơ chế thu gọn/mở rộng một chạm (`[◀]` / `[▶]`) và phím tắt (`C`, `T`, `F5`).

### 1.2. Design Tokens Chuẩn (Dark Cyber-Academic Theme)
- **Bảng Màu (Color Palette):**
  - **Background Base:** `#050811` (Xanh đêm không gian sâu, chống mỏi mắt cho màn hình máy chiếu/TV lớn).
  - **Surface / Card (Glassmorphism):** `rgba(15, 23, 42, 0.75)` kèm `backdrop-filter: blur(16px)`, viền `1px solid rgba(255, 255, 255, 0.08)`.
  - **Primary Cyan Accent:** `#38bdf8` (Điểm nhấn nhận diện, tạo cảm giác công nghệ cao).
  - **Secondary Indigo:** `#818cf8` (Dành cho các nút hành động AI, badge).
  - **Success Emerald:** `#10b981` (Dành cho đáp án đúng, học sinh đạt chuẩn, trạng thái online).
  - **Warning Amber:** `#f59e0b` (Dành cho câu hỏi thảo luận, lưu ý sư phạm, độ lệch chuẩn).
  - **Danger / Alert Rose:** `#f43f5e` (Dành cho học sinh cần phụ đạo, cảnh báo lỗi sai, nét kẻ đường chéo nổi bật).
- **Typography:**
  - **Font chính:** Inter / SF Pro Display / Roboto (Sans-serif hiện đại, nét chữ sắc nét ở độ phân giải cao).
  - **Font Toán học:** KaTeX / Computer Modern / Latin Modern Math (Chuẩn mực toán học quốc tế).
  - **Font Code / Thông số:** JetBrains Mono / Fira Code (Hiển thị tọa độ, số liệu thống kê).
- **Elevation & Shadows:**
  - `shadow-cockpit`: `0 10px 30px -5px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.15)`.

---

## 2. KIẾN TRÚC ĐIỀU HƯỚNG TOÀN CỤC (GLOBAL SHELL & NAVIGATION)

Thanh Top Navigation Bar luôn cố định phía trên cùng (chiều cao 56px), hoạt động như một trung tâm điều phối nhanh:

```
+----------------------------------------------------------------------------------------------------+
| [⚡ QUANTUM STUDIO v6.0]  [🎬 Trình Chiếu] [📝 Soạn 5512] [🛠️ Xưởng Slide] [📊 Phân Tích] [🗄️ Kho] |
|                                             [⏱️ 45:20] [🤖 Chat (C)] [🧊 Công Cụ (T)] [⛶ Toàn Màn] |
+----------------------------------------------------------------------------------------------------+
```

- **Logo Brand:** Biểu tượng tia chớp năng lượng kèm huy hiệu phiên bản "CV 5512 v6.0".
- **Bộ 5 Tab Điều Hướng (Nav Pills):**
  - Tab 1: `🎬 Trình Chiếu Giảng Dạy` (Active mặc định).
  - Tab 2: `📝 Soạn Giáo Án 5512`.
  - Tab 3: `🛠️ Xưởng Biên Tập Slide`.
  - Tab 4: `📊 Phân Tích Lớp Học`.
  - Tab 5: `🗄️ Kho Tri Thức & AI`.
- **Nhóm Điều Khiển Nhanh (Right Control Group):**
  - **Đồng hồ đếm tiết:** `⏱️ 45:20` (Đếm ngược thời gian 1 tiết học 45 phút).
  - **Nút Bật/Tắt Chat Co-pilot:** Đèn trạng thái xanh nhấp nháy, phím tắt `C`.
  - **Nút Bật/Tắt Công Cụ 3D/Đồ Thị:** Phím tắt `T`.
  - **Nút Trình Chiếu Toàn Màn Hình:** Phím tắt `F5` hoặc `F`.

---

## 3. MÀN HÌNH 1: SÂN KHẤU TRÌNH CHIẾU GIẢNG DẠY (PRESENTATION COCKPIT STAGE)
> **Mục đích:** Đem lại trải nghiệm làm chủ hoàn toàn lớp học cho giáo viên. Tỉ lệ vàng 16:9 cho nội dung chính, kèm 2 cánh gà thông minh phục vụ tương tác trực tiếp.

### 3.1. Sơ Đồ Bố Cục Không Gian (3-Panel Cockpit Wireframe)

```
+-------------------+---------------------------------------------+-------------------+
| 🤖 KHUNG CHAT GV  | 📽️ SÂN KHẤU SLIDE 16:9 CINEMA              | ⚙️ CÔNG CỤ GIẢNG DẠY|
| (Left Dock - 22%) | (Center Viewport - 56%)                     | (Right Dock - 22%)|
|                   |                                             |                   |
| • Header AI       | +-----------------------------------------+ | [🧊 3D] [📈 Đồ thị]|
| • Trạng thái Slide| | Hoạt động 1: Khởi động & Đặt vấn đề     | |                   |
| • Gợi ý nhanh:    | | [Khái niệm]        | [Khung 3D Canvas]  | | • Chọn khối hình  |
|   - Giải thích lại| | • Cạnh a = 4.0 cm  | 🧊 Hình lập phương | | • Trượt cạnh a    |
|   - Câu hỏi gợi mở| | • AC = a√2         |   kéo xoay 360°    | | • Góc nhìn SGK    |
|   - Thêm quiz     | | • AC' = a√3        |   chuột/touch      | | • Nét đứt, trục O |
|                   | +-----------------------------------------+ | • Thao tác nhanh: |
| • Luồng tin nhắn  |                                             |   📐 Kẻ chéo AC'  |
|   User & AI       | [◄ Trước]  [1/5]  [Sau ►]  [Slide Jump...]      |   📏 Hạ đường cao |
| • Ô gõ có KaTeX   | Phím tắt: [←] [→] [C: Chat] [T: Tools] [F5] |   ▱ Cắt thiết diện|
+-------------------+---------------------------------------------+-------------------+
```

### 3.2. Chi Tiết Cột Trái: Ô Chatbox Giáo Viên (`#presLeftChatDock`)
- **Độ rộng:** 320px (chiếm ~22% bề ngang màn hình).
- **Nút Thu gọn:** Nút `[◀]` ở góc trên bên phải hoặc phím tắt `C`. Khi thu gọn, bảng trượt mượt sang trái (CSS `transform: translateX(-100%)`), nhường 100% không gian cho Slide chính.
- **Thành phần giao diện:**
  1. **Header Trợ Giảng:** Avatar robot AI 3D, đèn LED xanh báo `Online`, huy hiệu ngữ cảnh `Slide 1/5`. Nút thùng rác `🗑️` làm mới cuộc trò chuyện.
  2. **Gợi ý nhanh 1 chạm (Quick Suggestion Chips):**
     - `💡 Giải thích slide 2 đơn giản hơn`
     - `❓ Câu hỏi gợi mở cho học sinh`
     - `📝 Thêm câu hỏi trắc nghiệm củng cố`
     - `🧠 Mẹo ghi nhớ công thức`
  3. **Vùng stream tin nhắn (Scrollable Container):**
     - Tin nhắn AI: Nền xám đen mờ, avatar xanh, chữ trắng ngà, định dạng bullet point rõ ràng, công thức KaTeX render sắc nét.
     - Tin nhắn Giáo viên: Bong bóng xanh gradient, căn phải.
     - Hiệu ứng gõ chữ (Typing Indicator): 3 dấu chấm nhảy động kèm chữ *"Trợ giảng AI đang suy nghĩ..."*.
  4. **Thanh nhập liệu (Chat Input Bar):**
     - Ô input bo tròn với placeholder: *"Nhắn cho trợ giảng (VD: Thêm bài tập vận dụng)..."*.
     - Hỗ trợ gõ công thức toán `$x^2 + 2x = 0$`.
     - Nút gửi hình phi thuyền phát sáng xanh khi có ký tự.

### 3.3. Chi Tiết Khu Vực Trung Tâm: Sân Khấu Slide 16:9 Cinema
- **Tỉ lệ hiển thị:** Cố định chuẩn 16:9, tự động co giãn theo độ phân giải màn hình máy chiếu ($1920\times 1080$, $2K$, $4K$).
- **Bố cục nội dung trong Slide:**
  - **Slide 1 - Khởi động:** Nửa trái trình bày bài toán thực tế & giả thiết hình học; nửa phải là khung Canvas 3D tương tác hình lập phương $ABCD.A'B'C'D'$.
  - **Slide 2 - Hình thành kiến thức:** Chứng minh từng bước định lý Pytago không gian $AC' = \sqrt{AC^2 + CC'^2} = a\sqrt{3}$, công thức highlight viền vàng.
  - **Slide 3 - Quan hệ vuông góc:** Dựng đoạn vuông góc chung $AH \perp B'D'$, mô hình 3D tự động hiển thị đoạn thẳng đỏ nổi bật.
  - **Slide 4 - Thiết diện không gian:** Cắt mặt phẳng $(A'BD)$, mô hình 3D tô màu cyan bán trong suốt (alpha 0.25) diện tích tam giác đều $S = \frac{a^2\sqrt{3}}{2}$.
  - **Slide 5 - Live Quiz Poll:** 
    - Câu hỏi trắc nghiệm: *"Góc giữa hai đường thẳng AC và A'D bằng bao nhiêu?"*.
    - 4 Thẻ phương án A (60°), B (90°), C (45°), D (120°) có thanh tiến trình động (%) nhảy thời gian thực khi học sinh nộp bài.
    - Hộp thoại giải thích chi tiết: Bấm nút sổ xuống `▼` để phân tích lý do chọn A đúng (tam giác $A'C'D$ đều) và bẫy sai lầm của đáp án D.
- **Thanh Điều Khiển Đáy (Bottom Navigation Dock):**
  - Danh sách nút chuyển nhanh theo tên hoạt động (1. Khởi động, 2. Đường chéo, 3. Vuông góc, 4. Thiết diện, 5. Quiz).
  - Bộ đếm slide: `[◀ Trước] 1 / 5 [Sau ▶]`.

### 3.4. Chi Tiết Cột Phải: Thanh Công Cụ 3D & Đồ Thị (`#presRightToolsDock`)
- **Độ rộng:** 330px (chiếm ~22% bề ngang màn hình).
- **Cơ chế thu gọn:** Nút `[▶]` hoặc phím tắt `T`.
- **Hệ thống 2 Sub-tab:**
  - **Sub-tab 1: 🧊 Hình Học Không Gian 3D:**
    - *Chọn khối đa diện:* Dropdown gồm Hình Lập Phương, Hình Chóp đáy chữ nhật ($S.ABCD$), Hình Chóp tam giác ($S.ABC$), Lăng Trụ Đứng ($ABC.A'B'C'$).
    - *Thanh trượt kích thước:* Cạnh $a$ từ $2.0 \rightarrow 6.0\text{ cm}$.
    - *Góc nhìn camera SGK chuẩn:* 3 nút 1-click: `Góc Chuẩn SGK (Isometry)`, `Nhìn Từ Đỉnh (Top)`, `Nhìn Trực Diện (Front)`.
    - *Tùy chọn hiển thị:* Checkbox nét đứt khuất, checkbox nhãn đỉnh ($A, B, C...$), checkbox hệ trục toạ độ $Oxyz$.
    - *Nút tác vụ hình học nhanh:*
      + `📐 Kẻ đường chéo AC' = a√3`
      + `📏 Hạ vuông góc AH ⊥ B'D'`
      + `▱ Cắt thiết diện mặt phẳng (A'BD)`
  - **Sub-tab 2: 📈 Đồ Thị Hàm Số & Biểu Đồ 2D:**
    - *Hàm số mẫu:* Dropdown gồm Bậc ba ($y = x^3 - 3x$), Bậc hai ($y = x^2 - 4$), Bậc nhất ($y = 2x$), Lượng giác ($y = \sin x$), Phân thức ($y = \frac{1}{x}$).
    - *Ô nhập hàm số tuỳ ý:* Giáo viên có thể gõ bất kỳ biểu thức $f(x)$ nào.
    - *Khoảng khảo sát:* $[x_{min}, x_{max}]$.
    - *Khung vẽ Canvas 2D:* Hiển thị lưới toạ độ ô vuông, trục hoành $Ox$, trục tung $Oy$, gốc toạ độ $O$ và đường cong màu cyan phát sáng.
    - *Nút vẽ:* `🎨 Vẽ Đồ Thị Tức Thì`.

---

## 4. MÀN HÌNH 2: DASHBOARD SOẠN KẾ HOẠCH BÀI DẠY 5512 (LESSON PLAN STUDIO)
> **Mục đích:** Hỗ trợ giáo viên soạn thảo, chuẩn hóa giáo án theo Công văn 5512 của Bộ Giáo dục & Đào tạo với sự hỗ trợ của AI phân hóa học lực.

### 4.1. Bố Cục 2 Cột Chức Năng (Studio 2-Column Split)
- **Cột Trái (40%) - Thiết Lập Hồ Sơ & Ingest Dữ Liệu:**
  - **Tiêu đề bài dạy:** Input text lớn (VD: *Hình lập phương & Quan hệ vuông góc trong không gian*).
  - **Bộ chọn Môn học & Khối lớp:** Toán học / Vật lý / Hóa học; Khối 10, 11, 12.
  - **Mức độ phân hóa học lực (3 Pills):**
    - `🟢 Cơ bản (Basic)`: Dành cho lớp học sinh mất gốc / đại trà; tập trung nhận biết, thông hiểu.
    - `🔵 Chuẩn (Standard)`: Đạt chuẩn chương trình GDPT 2018.
    - `🟣 Nâng cao (Advanced)`: Dành cho lớp chọn, chuyên Toán; tăng cường vận dụng cao.
  - **Hộp kéo thả Ingestion đa năng (Dropzone):**
    - Kéo thả file Word (`.docx`) hoặc PowerPoint (`.pptx`) bài giảng cũ để AI bóc tách nội dung kế thừa.
    - Kéo thả bảng điểm lớp học (`.xlsx`, `.csv`) để AI tự động tính toán Z-Score và đề xuất mức phân hóa.
  - **Yêu cầu cần đạt (Chuẩn đầu ra):** Textarea mô tả kiến thức, năng lực, phẩm chất.
  - **Nút hành động chính:** `🚀 Sinh Kế Hoạch Bài Dạy 5512 Bằng AI`.

- **Cột Phải (60%) - Trình Xem Trước & Thẩm Định Kế Hoạch 5512:**
  - Header hiển thị huy hiệu xác thực: `✅ Đạt Chuẩn Công Văn 5512 (0 Lỗi, 0 Cảnh Báo)`.
  - Cấu trúc 4 hoạt động dạy học được chia thành các accordion card rõ ràng:
    1. **Hoạt động 1: Mở đầu / Khởi động (7 phút)**: Mục tiêu, Nội dung, Sản phẩm, Tổ chức thực hiện.
    2. **Hoạt động 2: Hình thành kiến thức mới (18 phút)**: Chia chi tiết Hoạt động của Giáo viên và Hoạt động của Học sinh.
    3. **Hoạt động 3: Luyện tập (12 phút)**: Hệ thống bài tập phân bậc nhận thức.
    4. **Hoạt động 4: Vận dụng (8 phút)**: Bài tập thực tế, hướng dẫn tự học.
  - Bộ nút xuất tài liệu: `📥 Xuất File Word (.docx) Chuẩn 5512` và `🔄 Chuyển Sang Xưởng Tạo Slide`.

---

## 5. MÀN HÌNH 3: DASHBOARD XƯỞNG BIÊN TẬP SLIDE & ĐỒ THỊ (SLIDE DECK EDITOR)
> **Mục đích:** Môi trường soạn thảo WYSIWYG chi tiết từng slide, chỉnh sửa công thức KaTeX, thiết lập câu hỏi trắc nghiệm phân tích lỗi sai và cấu hình ghi chú bài giảng (Teacher Notes).

### 5.1. Bố Cục 3 Cột Chuyên Nghiệp (Figma-Style 3-Column Layout)
- **Cột 1 (18%) - Danh Sách Slide Filmstrip:**
  - Hiển thị danh sách ảnh thu nhỏ (thumbnails) của các slide từ Slide 1 đến Slide N.
  - Kéo thả (Drag-and-Drop) để đổi thứ tự slide.
  - Nút `+ Thêm Slide Mới`, nút nhân bản (`Duplicate`), nút xoá (`Delete`).
- **Cột 2 (52%) - Khung Soạn Thảo WYSIWYG & Xem Trước Live:**
  - Hiển thị slide đang chọn dưới dạng Canvas trực quan.
  - Cho phép click trực tiếp để sửa Tiêu đề, Danh sách ý (Bullet Points).
  - Khung gõ công thức Toán học trực quan: Khi click vào công thức, mở popup bàn phím ảo toán học (phân số, tích phân, căn bậc $n$, ma trận) không cần thuộc mã LaTeX.
  - Bộ chọn layout: `2 Cột (Nội dung + Mô hình)`, `1 Cột Toàn Cảnh`, `Slide Trắc Nghiệm Live Quiz`.
- **Cột 3 (30%) - Thanh Inspector Tùy Biến Chuyên Sâu:**
  - **Phần Ghi chú riêng cho Giáo viên (Teacher Notes):** Lời thoại gợi ý giảng dạy, nhấn mạnh điểm học sinh hay nhầm lẫn (không hiện lên màn hình chiếu của học sinh).
  - **Phần Cấu hình Quiz & Phân tích lỗi sai (Distractor Rationales):**
    - Câu hỏi trắc nghiệm.
    - Phương án đúng A.
    - Phương án B, C, D kèm ô nhập: *"Tại sao học sinh chọn phương án này là sai? Lỗi tư duy gì?"*.
  - **Nút xuất bản:** `📥 Xuất File PowerPoint (.pptx) Kèm Ghi Chú & Đồ Thị`.

---

## 6. MÀN HÌNH 4: DASHBOARD TRUNG TÂM PHÂN TÍCH LỚP HỌC (CLASS ANALYTICS)
> **Mục đích:** Phân tích dữ liệu học tập thông minh dựa trên thống kê học lực chuẩn hóa, giúp giáo viên nắm bắt phổ điểm lớp và áp dụng phương pháp dạy học phân hóa.

### 6.1. Các Khối Dữ Liệu Trọng Tâm (Analytics Grid)
- **Hàng 1: 4 Thẻ KPI Tổng Thể:**
  - **Sĩ số lớp:** `42 Học sinh` (Tỉ lệ tham gia 100%).
  - **Điểm trung bình ($\mu$):** `7.42 / 10` (Phổ điểm khá tốt).
  - **Độ lệch chuẩn ($\sigma$):** `1.38` (Độ phân tán vừa phải).
  - **Xếp loại lớp chuẩn hóa:** `CHUẨN (STANDARD)` (68% học sinh đạt từ điểm chuẩn trở lên).
- **Hàng 2: Biểu Đồ Phân Phối Điểm & Đường Cong Gauss:**
  - Biểu đồ cột phân vị điểm từ 0 đến 10 kèm đường cong phân phối chuẩn (Normal Distribution Curve).
  - Chỉ rõ vùng học sinh cần quan tâm đặc biệt.
- **Hàng 3: Khuyến Nghị Sư Phạm 3 Nhóm Học Lực:**
  - **Nhóm Cần Phụ Đạo (Điểm < 5.0) - 4 Học sinh (9.5%):** Khuyến nghị dùng mô hình 3D xoay trực quan để nhận biết hình học, giảm tải bài tập tính toán phức tạp.
  - **Nhóm Đạt Chuẩn (Điểm 5.0 - 8.0) - 26 Học sinh (61.9%):** Khuyến nghị rèn luyện kỹ năng vẽ thêm đường phụ và tính khoảng cách.
  - **Nhóm Nâng Cao (Điểm > 8.0) - 12 Học sinh (28.6%):** Khuyến nghị giao thêm bài toán cực trị không gian và thiết diện biến thiên.
- **Hàng 4: Bảng Điểm Chuẩn Hóa Học Sinh (Matrix Table):**
  - Cột: STT, Họ và Tên, Điểm gốc, Điểm Z-Score ($Z = \frac{X - \mu}{\sigma}$), Điểm T-Score ($T = 50 + 10Z$), Phân vị thứ hạng %, Nhóm đề xuất.

---

## 7. MÀN HÌNH 5: DASHBOARD QUẢN TRỊ KHO TRI THỨC & CẤU HÌNH AI (KNOWLEDGE HUB)
> **Mục đích:** Quản lý kho lưu trữ bài giảng số, ngân hàng câu hỏi và cấu hình mô hình trí tuệ nhân tạo.

### 7.1. Cấu Trúc Chức Năng
- **Kho Giáo Án & Slide Đã Tạo:** Thẻ bài giảng dạng lưới (Grid Cards), hiển thị môn học, khối lớp, ngày tạo, nút tải lại hoặc xuất bản nhanh.
- **Ngân Hàng Câu Hỏi Trắc Nghiệm Đã Kiểm Định:** Tìm kiếm câu hỏi theo chủ đề, lọc theo mức độ nhận thức (Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
- **Cấu hình Trí Tuệ Nhân Tạo (AI Control Panel):**
  - Chọn model xử lý: `Gemini 2.5 Flash` (Tối ưu tốc độ realtime) hoặc `Gemini Pro` (Tối ưu suy luận toán học sâu).
  - Thanh trượt nhiệt độ sáng tạo (Temperature): Mặc định `0.2` (đảm bảo độ chính xác tuyệt đối của công thức toán).
  - Xem và tùy chỉnh System Prompts của Trợ Giảng AI.

---

## 8. BỘ PROMPT MẪU DÀNH CHO STITCH / FIGMA AI / UI GENERATOR

Dưới đây là các prompt chuẩn xác được thiết kế để copy-paste trực tiếp vào các công cụ thiết kế tự động như **Google Stitch, Figma AI, v0, Tailwind UI Generator**:

### 🎯 Prompt 1: Màn Hình Trình Chiếu Giảng Dạy (Presentation Cockpit Stage)
```text
Design a professional high-tech dark mode Web Presentation Cockpit for high school Math teachers, inspired by modern flight simulator dashboards and Apple Keynote. 
Aspect Ratio: Full desktop widescreen (1920x1080).
Color Theme: Deep Cyber Navy (#050811), slate glassmorphic cards (rgba(15,23,42,0.8) with 16px blur and cyan borders), glowing neon accents (#38bdf8 cyan, #10b981 emerald, #f59e0b amber).

Layout Structure:
1. Top Navigation Bar (Height 56px):
   - Brand logo "QUANTUM STUDIO v6.0" with lightning icon.
   - 4 sleek navigation pill tabs: "🎬 Trình Chiếu Giảng Dạy" (Active), "📝 Soạn Giáo Án 5512", "🛠️ Xưởng Slide", "📊 Phân Tích Lớp".
   - Right utilities: Countdown timer pill "45:20", "🤖 Chat AI (Key C)", "⚙️ Công Cụ (Key T)", "⛶ Toàn Màn Hình (F5)".

2. 3-Panel Main Presentation Layout:
   - Left Panel (Width 22%, Collapsible with toggle button [◀] or key C): Teacher AI Co-pilot Chat Drawer. Contains AI avatar with green online badge, quick suggestion chips ("💡 Giải thích slide 2 đơn giản", "❓ Câu hỏi gợi mở", "📝 Thêm quiz trắc nghiệm"), message chat stream with KaTeX formulas, and rounded input bar with math symbol button.
   - Center Viewport (Width 56%): 16:9 Cinema Presentation Slide Stage. Displays lesson activity badge "HOẠT ĐỘNG 1: KHỞI ĐỘNG", split-view with mathematical properties on left and interactive 3D WebGL Cube canvas on right (ABCD.A'B'C'D' with rotatable axes and vertex tags). Bottom floating dock with slide thumbnails (1. Khởi động, 2. Đường chéo, 3. Vuông góc, 4. Thiết diện, 5. Live Quiz) and navigation buttons [◀ Trước] 1/5 [Sau ▶].
   - Right Panel (Width 22%, Collapsible with toggle button [▶] or key T): Teaching Tools Dock with 2 sub-tabs:
     * Sub-tab 1 "🧊 Hình Học 3D": Polyhedron selector (Cube, Pyramid S.ABCD, Prism), edge length slider (2.0 to 6.0 cm), textbook camera presets (SGK Iso, Top, Front), hidden lines toggle, and quick geometric action buttons ("📐 Kẻ đường chéo AC'", "📏 Hạ vuông góc AH", "▱ Cắt thiết diện (A'BD)").
     * Sub-tab 2 "📈 Đồ Thị Hàm Số": Function preset dropdown (y = x³ - 3x, y = x² - 4, y = sin(x)), math expression input, and a dark 2D Cartesian coordinate grid canvas (Oxy) showing glowing cyan curve.
```

### 🎯 Prompt 2: Màn Hình Soạn Kế Hoạch Bài Dạy 5512 (Lesson Plan Studio)
```text
Design a modern pedagogical desktop dashboard for Vietnamese teachers creating official lesson plans under Ministry Dispatch 5512 (Công văn 5512).
Theme: Deep dark slate (#090d16) with glassmorphism, cyan (#38bdf8) and amber accents.
Layout: 2-column split layout.
Left Column (40% width): Lesson Profile & Ingest Configuration Card.
- Inputs for Lesson Topic ("Hình lập phương & Quan hệ vuông góc"), Subject dropdown (Toán học, Vật lý), Grade level (Lớp 11).
- 3 Differentiation Pills: "🟢 Cơ bản (Basic)", "🔵 Chuẩn (Standard)", "🟣 Nâng cao (Advanced)".
- Multi-file Ingestion Dropzone with dashed neon border for uploading previous .docx/.pptx teaching files and .xlsx grade sheets.
- Target learning outcomes textarea.
- Prominent glowing action button: "🚀 Sinh Kế Hoạch Bài Dạy 5512 Bằng AI".

Right Column (60% width): Official 5512 Lesson Plan Preview.
- Header with green badge "✅ Chuẩn Công Văn 5512 (0 Lỗi, 0 Cảnh Báo)" and "📥 Xuất File Word (.docx)".
- Structured cards for the 4 Mandatory Activities:
  1. Hoạt động 1: Mở đầu / Khởi động (7 mins)
  2. Hoạt động 2: Hình thành kiến thức mới (18 mins) with split table of Teacher actions vs Student actions.
  3. Hoạt động 3: Luyện tập (12 mins) with graded exercises.
  4. Hoạt động 4: Vận dụng (8 mins) with real-world problems.
KaTeX math formulas rendered beautifully throughout.
```

### 🎯 Prompt 3: Màn Hình Phân Tích Lớp Học & Học Lực (Class Analytics)
```text
Design an executive EdTech Analytics Dashboard for teacher insights and class differentiation.
Theme: Dark cybernetic theme with clean data visualization charts.
Key Sections:
1. 4 Metric KPI Cards across top:
   - "Sĩ Số Lớp": 42 Học sinh (100% submitted)
   - "Điểm Trung Bình (μ)": 7.42 / 10 (Cyan highlight)
   - "Độ Lệch Chuẩn (σ)": 1.38 (Amber highlight)
   - "Trình Độ Chuẩn Hóa": CHUẨN (STANDARD) (Emerald badge)

2. Center Visual Data:
   - Normal Distribution Curve (Đường cong Gauss) overlaying a score frequency histogram (0 to 10 points).
   - 3 Pedagogical Strategy Cards for student differentiation:
     * Red border card: "Nhóm Cần Phụ Đạo (< 5.0) - 4 HS" with recommendations to use 3D visual models.
     * Cyan border card: "Nhóm Đạt Chuẩn (5.0 - 8.0) - 26 HS" focusing on core theorems.
     * Emerald border card: "Nhóm Nâng Cao (> 8.0) - 12 HS" focusing on space cross-sections and optimization.

3. Detailed Student Ranking Matrix Table:
   - Table columns: STT, Student Name, Raw Score, Z-Score (+1.51), T-Score (65.1), Percentile %, Recommended Tier.
   - Glassmorphic table design with alternating subtle row highlights.
```
