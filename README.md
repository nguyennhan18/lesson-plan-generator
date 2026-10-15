# LessonAI-5512

> **Studio AI Tự Động Soạn Kế Hoạch Bài Dạy Chuẩn 5512 & Thiết Kế Slide Bài Giảng Tương Tác**

LessonAI-5512 là nền tảng AI thông minh dành cho giáo viên và các nhà sư phạm toán học, hỗ trợ tự động biên soạn Kế hoạch bài dạy chuẩn theo Công văn 5512/BGDĐT, đồng thời kết xuất Slide trình chiếu PowerPoint chuyên nghiệp với công thức toán LaTeX (OMML), đồ thị hàm số 2D và mô hình không gian 3D tương tác. Hệ thống tích hợp Trợ lý AI Copilot đồng hành giúp giáo viên dễ dàng tinh chỉnh nội dung từng slide và tiết kiệm đến 80% thời gian chuẩn bị bài giảng.

---

## Điều kiện tiên quyết (Prerequisites)

Trước khi tiếp tục, hãy đảm bảo bạn đáp ứng đầy đủ các yêu cầu và công cụ sau:

- **Công cụ & Môi trường runtime:**
  - Đã cài đặt **Python 3.10** trở lên (Khuyến nghị Python 3.11 hoặc 3.12).
  - Đã cài đặt **Node.js 18.0** trở lên kèm trình quản lý gói **npm**.
  - Hệ điều hành: Hỗ trợ đầy đủ trên **macOS**, **Linux** và **Windows** (khuyến nghị chạy trên Terminal Unix/macOS hoặc WSL2 trên Windows).
- **Khóa chứng thực API (API Keys):**
  - **Google Gemini API Key** (Bắt buộc tối thiểu để vận hành AI Engine) - Đăng ký miễn phí tại [Google AI Studio](https://aistudio.google.com/).
  - *(Tùy chọn nâng cao)* **Groq API Key** và **OpenRouter API Key** nếu muốn kích hoạt cơ chế chuyển mạch dự phòng đa mô hình (Multi-Provider Auto-Fallback).
- **Kiến thức nền tảng:**
  - Kỹ năng thao tác dòng lệnh cơ bản (Terminal / Command Prompt / PowerShell).
  - Nắm được cấu trúc cơ bản của bài dạy theo định hướng phát triển năng lực của Bộ Giáo dục & Đào tạo (Công văn 5512/BGDĐT).

---

## Cách cài đặt (Installation)

Thực hiện cài đặt hệ thống từng bước theo thứ tự đánh số dưới đây:

### Bước 1: Sao chép (Clone) kho lưu trữ mã nguồn
```bash
git clone https://github.com/NguyenNhan18/Lesson-Plan-Generator.git
cd Lesson-Plan-Generator
```

### Bước 2: Thiết lập môi trường ảo và cài đặt Backend
```bash
# Di chuyển vào thư mục backend
cd app/backend

# Tạo môi trường ảo Python
python3 -m venv venv

# Kích hoạt môi trường ảo
# Trên macOS / Linux:
source venv/bin/activate
# Trên Windows:
# venv\Scripts\activate

# Nâng cấp pip và cài đặt toàn bộ gói phụ thuộc
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` từ file mẫu `.env.example` và điền khóa API của bạn:
```bash
# Đang đứng tại thư mục app/backend:
cp .env.example .env
```
Mở file `.env` bằng trình chỉnh sửa và cập nhật API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
# Tùy chọn bổ sung để dự phòng:
GROQ_API_KEY=
OPENROUTER_API_KEY=
```

### Bước 4: Cài đặt các gói phụ thuộc Frontend
Mở một cửa sổ Terminal mới từ thư mục gốc của dự án:
```bash
# Di chuyển vào thư mục frontend
cd app/frontend

# Cài đặt toàn bộ thư viện npm
npm install
```

---

## Cách sử dụng (Usage)

### 1. Khởi chạy hệ thống

#### Khởi chạy Backend Server (FastAPI)
Đảm bảo môi trường ảo Python đã được kích hoạt trong thư mục `app/backend`:
```bash
cd app/backend
source venv/bin/activate

# Chạy server với chế độ tự động reload khi sửa code
uvicorn main:app --app-dir src --reload --host 127.0.0.1 --port 8000
```
- **Các tùy chọn lệnh (Flags giải thích):**
  - `--app-dir src`: Chỉ định thư mục gốc chứa mã nguồn ứng dụng FastAPI (`src/main.py`).
  - `--reload`: Tự động tải lại server khi có thay đổi trong file Python (rất hữu ích khi phát triển).
  - `--port 8000`: Chỉ định cổng lắng nghe của backend server (mặc định là 8000).

#### Khởi chạy Frontend Studio (Vite + React)
Trong cửa sổ terminal của thư mục `app/frontend`:
```bash
cd app/frontend
npm run dev
```
- Vite Dev Server sẽ khởi chạy tại: `http://localhost:5173`
- Mọi cuộc gọi API dạng `/api/*` sẽ được tự động proxy sang backend `http://localhost:8000`.

---

### 2. Quy trình làm việc trên giao diện Studio

1. **Khởi tạo nội dung:** Mở trình duyệt tại `http://localhost:5173`, nhập tên bài dạy (ví dụ: *Cấp số cộng*, *Đạo hàm*), chọn môn học và khối lớp.
2. **Sinh Kế hoạch bài dạy 5512:** Nhấn **"Tạo Giáo Án 5512"**. Hệ thống tự động phân loại khối lớp, kích hoạt LLM Gateway và chạy qua bộ kiểm định (Validator 5512) để đảm bảo đủ 4 hoạt động bắt buộc.
3. **Thiết kế & Xem trước Slide:** Chuyển sang màn hình **Slide Studio**, xem trước từng slide bài giảng với công thức toán học KaTeX rõ nét, đồ thị hàm số 2D và khung hình học 3D tương tác.
4. **Trợ lý Copilot AI:** Sử dụng thanh công cụ chat bên phải để yêu cầu AI mở rộng bài tập, tạo thêm câu hỏi trắc nghiệm hoặc sửa nội dung từng phần trực tiếp trên slide.
5. **Xuất bản:**
   - Tải file Word: Tải Kế hoạch bài dạy định dạng `.docx` chuẩn mẫu văn bản hành chính.
   - Tải file PowerPoint: Tải slide trình chiếu `.pptx` Native với công thức toán học dạng OMML có thể chỉnh sửa trực tiếp trên Microsoft PowerPoint.

---

### 3. Đóng gói Production (Tùy chọn)

Nếu bạn muốn đóng gói giao diện frontend vào backend để chạy duy nhất trên một port:
```bash
cd app/frontend
npm run build
```
Bản build sẽ xuất hiện tại `app/frontend/dist/`. Khi bạn khởi động FastAPI server (`uvicorn main:app --app-dir src`), backend sẽ tự động nạp và phục vụ trực tiếp giao diện Web tại `http://localhost:8000/`.

---

### 4. Bảng tham chiếu API chính

| Phương thức | Đường dẫn API | Mục đích |
| :--- | :--- | :--- |
| `GET` | `/docs` | Swagger UI tương tác và thử nghiệm toàn bộ API |
| `GET` | `/api/v1/health` | Kiểm tra trạng thái máy chủ và kết nối API key |
| `POST` | `/api/v1/lesson-plan/generate` | Sinh dữ liệu Giáo án 5512 kèm kết quả kiểm định |
| `POST` | `/api/v1/lesson-plan/export-docx` | Kết xuất Giáo án ra file Word (`.docx`) |
| `POST` | `/api/v1/slide/generate` | Sinh cấu trúc bộ Slide bài giảng theo giáo án |
| `POST` | `/api/v1/slide/export-slide` | Kết xuất Slide ra file PowerPoint (`.pptx`) |
| `POST` | `/api/v1/chart/render` | Render trực tiếp ảnh đồ thị hàm số từ công thức toán |
| `POST` | `/api/v1/chat/interact` | Tương tác với Trợ lý AI Copilot theo ngữ cảnh slide |

> 📖 **Tài liệu chuyên sâu:** Xem thêm tài liệu kiến trúc kỹ thuật Multi-Provider LLM Gateway tại [plan_multi_provider.md](plan_multi_provider.md) và các tài liệu đặc tả yêu cầu trong thư mục [docs/](docs/).

---

## Làm thế nào để đóng góp (Contributing)

Chúng tôi luôn chào đón mọi sự đóng góp từ cộng đồng để phát triển dự án ngày một tốt hơn! Bạn có thể đóng góp theo các bước sau:

1. **Fork** kho lưu trữ về tài khoản GitHub của bạn.
2. Tạo nhánh tính năng mới:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Thực hiện các thay đổi và commit theo định dạng Conventional Commits:
   ```bash
   git commit -m "feat: bổ sung tính năng xuất bản mẫu slide mới"
   ```
4. Chạy kiểm thử tự động để đảm bảo toàn bộ mã nguồn hoạt động chính xác:
   ```bash
   cd app/backend
   pytest
   ```
5. Đẩy nhánh lên GitHub và tạo một **Pull Request (PR)** mới.

👉 Vui lòng đọc kỹ hướng dẫn đóng góp chi tiết tại [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Tác giả & Đóng góp (Contributors)

- **Nguyễn Nhân** ([@NguyenNhan18](https://github.com/NguyenNhan18)) - *Tác giả chính & Kiến trúc sư phát triển hệ thống*
- Xin chân thành cảm ơn tất cả các thầy cô giáo bộ môn Toán, bạn bè và những người đóng góp đã hỗ trợ thử nghiệm, phản biện sư phạm và hoàn thiện chuẩn đầu ra của dự án.

---

## Nguồn dẫn chứng & Tri ân (Acknowledgments)

Dự án có sử dụng và dựa trên các nền tảng, nghiên cứu và thư viện mã nguồn mở sau:

- **Bộ Giáo dục và Đào tạo:** Khung kế hoạch bài dạy chuẩn theo **Công văn số 5512/BGDĐT-GDTrH**.
- **Các nhà cung cấp AI & Mô hình ngôn ngữ lớn:**
  - [Google AI Studio](https://aistudio.google.com/) (Gemini 2.5 Flash)
  - [Groq Cloud](https://groq.com/) (LPU Inference Engine cho tốc độ siêu tốc)
  - [OpenRouter](https://openrouter.ai/) (Hệ sinh thái mã nguồn mở Qwen, DeepSeek)
- **Thư viện & Công cụ mã nguồn mở:**
  - [python-docx](https://python-docx.readthedocs.io/) & [python-pptx](https://python-pptx.readthedocs.io/) - Bộ xử lý tài liệu Office Native & công thức toán OMML.
  - [FastAPI](https://fastapi.tiangolo.com/) & [Pydantic v2](https://docs.pydantic.dev/) - Nền tảng Backend API hiệu năng cao.
  - [React 19](https://react.dev/), [Vite](https://vitejs.dev/) & [TailwindCSS](https://tailwindcss.com/) - Nền tảng giao diện người dùng hiện đại.
  - [KaTeX](https://katex.org/) - Bộ kết xuất công thức toán học tốc độ cao.
  - [Three.js](https://threejs.org/) - Dựng hình học không gian 3D tương tác.
  - [Matplotlib](https://matplotlib.org/) & [SymPy](https://www.sympy.org/) - Tính toán biểu thức ký hiệu và vẽ đồ thị hàm số.

---

## Thông tin liên hệ (Contact)

Nếu bạn có bất kỳ câu hỏi nào, muốn trao đổi hợp tác, phản hồi góp ý về mặt sư phạm hoặc cơ hội nghề nghiệp, xin vui lòng liên hệ:

<div align="center">

### **Nguyen Van Nhan**
📧 **Email:** [nhan18112005@gmail.com](mailto:nhan18112005@gmail.com)
🐙 **GitHub:** [https://github.com/NguyenNhan18](https://github.com/NguyenNhan18)
📂 **Project Repository:** [https://github.com/NguyenNhan18/Lesson-Plan-Generator](https://github.com/NguyenNhan18/Lesson-Plan-Generator)

</div>

---

## Bản quyền (License)

Dự án được phân phối dưới giấy phép mã nguồn mở **MIT License**. Xem file [LICENSE](LICENSE) để biết thêm thông tin chi tiết.
