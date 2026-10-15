# LessonAI-5512 (Lesson Plan & Presentation Studio)

Hệ thống AI hỗ trợ giáo viên tự động soạn Kế hoạch bài dạy theo chuẩn Công văn 5512/BGDĐT và thiết kế Slide bài giảng toán học tương tác (PowerPoint Native, LaTeX, 3D Canvas, Copilot Chat).

---

## 🏗️ Cấu trúc dự án (Monorepo Layout)

```text
Lesson-Plan-Generator/
├── app/
│   ├── backend/                     # FastAPI Backend Server & AI Engine
│   │   ├── .env                     # Biến môi trường (GEMINI_API_KEY, ...)
│   │   ├── pytest.ini               # Cấu hình test runner (pythonpath = src)
│   │   ├── requirements.txt         # Thư viện phụ thuộc Python
│   │   ├── src/                     # Mã nguồn Backend
│   │   │   ├── main.py              # Entrypoint FastAPI Server & Static mount
│   │   │   ├── schemas/             # Pydantic Schemas (Giáo án, Slide, Chat)
│   │   │   ├── services/            # AI Generator, Chat Copilot, Classifier, Validator
│   │   │   ├── parsers/             # Bộ phân tích trích xuất DOCX và PPTX
│   │   │   ├── exporters/           # Bộ kết xuất DOCX và PowerPoint (Native python-pptx)
│   │   │   └── templates/           # PowerPoint master templates (1, 2, 3, 5512)
│   │   ├── tests/                   # Bộ kiểm thử tự động (Unit & Integration tests)
│   │   │   └── fixtures/            # File mẫu test DOCX/PPTX
│   │   ├── scripts/                 # Scripts chạy batch test & demo
│   │   └── output/                  # Thư mục chứa file sinh ra khi chạy test
│   │
│   └── frontend/                    # Giao diện Web Studio (React 19, TailwindCSS, Vite)
│       ├── package.json
│       ├── vite.config.js
│       └── src/
│           ├── components/          # SlideEditor, PresentationStage, ChatDock, Plotter...
│           └── App.jsx
│
├── docs/                            # Toàn bộ tài liệu dự án, báo cáo & thiết kế
│   ├── design/                      # Bản vẽ và ý tưởng thiết kế giao diện
│   ├── reports/                     # Báo cáo tiến độ từng ngày (Report_Day01..06)
│   └── *.docx, *.md, *.pdf          # Đặc tả yêu cầu (SRS), kế hoạch phát triển 5512
│
├── DATN.code-workspace              # VS Code Multi-root Workspace
└── .gitignore
```

---

## 🚀 Hướng dẫn khởi chạy

### 1. Khởi chạy Backend

```bash
# Di chuyển vào thư mục backend
cd app/backend

# Kích hoạt virtual environment
source venv/bin/activate

# Chạy server FastAPI (chế độ reload)
uvicorn main:app --app-dir src --reload --port 8000
```
- Swagger UI tài liệu API: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### 2. Khởi chạy Frontend (React Dev Server)

```bash
# Di chuyển vào thư mục frontend
cd app/frontend

# Khởi chạy Vite dev server
npm run dev
```
- Ứng dụng chạy tại: `http://localhost:5173`
- Đã cấu hình proxy chuyển tiếp `/api` sang backend `http://localhost:8000`.

### 3. Build Frontend cho Production

```bash
cd app/frontend
npm run build
```
Bản build sẽ được xuất vào `app/frontend/dist/`. Khi backend chạy `main.py`, FastAPI sẽ tự động nạp và phục vụ trực tiếp giao diện này tại `http://localhost:8000/`.

---

## 🧪 Chạy Kiểm thử (Pytest)

```bash
cd app/backend
venv/bin/python -m pytest
```
