# 📊 BÁO CÁO TIẾN ĐỘ NGÀY 1: NÂNG CẤP DATA SCHEMA (QUIZ PHÂN TÍCH LỖI SAI & PHÂN LOẠI HỌC LỰC)

**Ngày thực hiện:** 07/10/2026  
**Trạng thái nghiệm thu (DoD):** 🎯 ĐẠT 100% (4/4 Test Cases PASSED)  

---

## 🛠️ I. NỘI DUNG CÔNG VIỆC ĐÃ HOÀN THÀNH (5/5 TASKS)

### 1. Task 1.1: Định nghĩa Data Schema cho Phương án Trắc nghiệm (`QuizOptionDetail`)
- **File chỉnh sửa:** `project/app/schemas/slide_schema.py`
- **Kết quả:** Xây dựng thành công class `QuizOptionDetail` gồm các trường:
  - `label`: Nhãn phương án (A, B, C, D).
  - `text`: Nội dung câu trả lời.
  - `is_correct`: Đánh dấu đáp án đúng (`True`) / sai (`False`).
  - `distractor_rationale`: Giải thích lý do bẫy tâm lý / nguyên nhân học sinh chọn sai phương án này.

### 2. Task 1.2: Bổ sung Trình độ Học lực & Chuẩn đầu ra (`ClassProficiency` & `target_outcome`)
- **File chỉnh sửa:** `project/app/schemas/slide_schema.py` & `project/app/schemas/schemas.py`
- **Kết quả:**
  - Định nghĩa Enum `ClassProficiency` (gồm 3 mức: `basic` - cơ bản/yếu, `standard` - trung bình/chuẩn, `advanced` - giỏi/nâng cao).
  - Thêm `class_proficiency` và `target_outcome` vào `SlideSchema` và `LessonRequest`.

### 3. Task 1.3: Cập nhật `SlideDeckSchema` & Validator Chốt chặn cho `QUIZ_OPTION`
- **File chỉnh sửa:** `project/app/schemas/slide_schema.py`
- **Kết quả:**
  - Thêm trường `quiz_options: List[QuizOptionDetail]` vào `SlideSchema`.
  - Thiết lập `@model_validator(mode="after")` kiểm tra nghiêm ngặt:
    1. Bắt buộc slide có layout `QUIZ_OPTION` phải có danh sách `quiz_options`.
    2. Bắt buộc có đúng 1 đáp án đúng (`is_correct == True`).
    3. Bắt buộc 100% phương án sai (`is_correct == False`) phải chứa nội dung `distractor_rationale` (không để rỗng hay khoảng trắng).

### 4. Task 1.4: Xây dựng Bộ Unit Test Tự động (`test_schema.py`)
- **File tạo mới:** `project/test/test_schema.py`
- **Kết quả:** Xây dựng 4 test cases kiểm thử:
  - `test_quiz_slide_valid`: Verify parse JSON slide trắc nghiệm hợp lệ.
  - `test_quiz_slide_missing_distractor_rationale`: Verify Pydantic ném `ValidationError` khi thiếu giải thích sai.
  - `test_quiz_slide_invalid_correct_count`: Verify Pydantic ném `ValidationError` khi số câu đúng != 1.
  - `test_lesson_request_with_proficiency`: Verify `LessonRequest` nhận tham số học lực.

### 5. Task 1.5: Nghiệm thu theo tiêu chuẩn DoD & Bóc tách Code
- **Kết quả:** Chạy `pytest project/test/test_schema.py` đạt **4/4 PASSED (100%)**.

---

## 🎯 II. KẾ HOẠCH BẮT ĐẦU NGÀY 2 (NÂNG CẤP AI PROMPT ENGINEERING)

**Mục tiêu Ngày 2:** Phân hóa Bài giảng & SGK trong AI Prompt Engineering
- **Task 2.1:** Cập nhật `SLIDE_SYSTEM_PROMPT` trong `ai_service.py` hỗ trợ chỉ dẫn phân loại học lực (`basic`, `standard`, `advanced`).
- **Task 2.2:** Ràng buộc Prompt ép Gemini sinh câu hỏi trắc nghiệm có bẫy học sinh kèm `distractor_rationale`.
- **Task 2.3:** Test sinh slide 2 trường hợp đối lập: *"Cấp số cộng cho lớp yếu"* vs *"Cấp số cộng cho lớp chuyên Toán"*.
- **Task 2.4:** Đảm bảo bộ lọc `fix_latex_backslashes_in_json` xử lý không bị vỡ JSON LaTeX.
- **Task 2.5:** Nghiệm thu DoD Ngày 2.
