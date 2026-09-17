# ROADMAP PHÁT TRIỂN CHI TIẾT — LessonAI-5512

*Giữ nguyên toàn bộ phạm vi theo tài liệu 50 trang. Sắp xếp theo thứ tự phụ thuộc kỹ thuật (cái gì phải xong trước mới làm được cái sau), không phải thứ tự "quan trọng nhất trước".*

Nguyên tắc xuyên suốt: mỗi giai đoạn kết thúc phải có **một bản demo chạy được thật** (không phải chỉ code xong từng phần rời rạc) — để bất cứ lúc nào họp dự án cũng có cái để show, và để bạn tự kiểm tra được tiến độ thật thay vì ảo tưởng "code xong 80%" mà không chạy được end-to-end.

---

## GIAI ĐOẠN 2.1 — Nền tảng dữ liệu & API chuẩn (Hướng 1 + 2)

**Mục tiêu ra**: Backend có DB thật, API có Auth, Postgres lưu được toàn bộ vòng đời một giáo án.

1. Dựng PostgreSQL + SQLAlchemy + Alembic. Tạo đủ 9 bảng theo ERD đã có trong báo cáo tổng hợp: `users, lesson_plans, lesson_versions, activities, slides, math_topics, question_bank, geometry_assets, audit_logs`.
2. Viết migration + seed data mẫu (1 admin, vài `math_topics` mẫu cho lớp 8-9).
3. Viết lớp Repository/DAO bọc SQLAlchemy — không để `main.py` thao tác SQL trực tiếp.
4. Nối pipeline hiện có: sau khi Gemini sinh JSON → lưu vào `lesson_plans` + `activities` thay vì chỉ trả response rồi mất.
5. Thêm Auth JWT (access + refresh token) và RBAC 3 role (Giáo viên / Tổ trưởng chuyên môn / Admin) như đã thiết kế.
6. Chuẩn hoá toàn bộ endpoint theo đúng đặc tả REST trong báo cáo tổng hợp (`POST /lesson-plans`, `/generate`, `/geometry`, `/slides/generate`, `/export`, `/approve`, `GET /jobs/{id}`), kèm `Idempotency-Key`, mã lỗi 422/401/403/409/429/502.
7. Rate limiting theo user/role, Audit log ghi vào bảng `audit_logs`.

**Test cuối giai đoạn**: gọi API thật (Postman/curl) → tạo lesson_plan → generate → kiểm tra dữ liệu nằm đúng trong DB, có version, có audit log.

---

## GIAI ĐOẠN 2.2 — Web UI cơ bản + Slide Engine native (Hướng 3 + 4, chạy song song)

**Mục tiêu ra**: Giáo viên dùng được trình duyệt để tạo giáo án và thấy slide đẹp, kéo-thả chỉnh sửa được trong PowerPoint thật.

### Nhánh UI
1. Dựng 4 màn hình React/Next.js theo đúng luồng tài liệu 50 trang: (a) form nhập bài học, (b) xem/sửa giáo án AI sinh ra, (c) tuỳ chỉnh slide, (d) preview & export.
2. Live Editor cho từng hoạt động (4 hoạt động 5512), không chỉ hiển thị JSON thô.
3. Autosave → tạo bản ghi mới trong `lesson_versions` mỗi lần sửa.
4. Panel cảnh báo validator hiển thị lỗi theo JSON path (icon + text).
5. Nút Duyệt (Approve) khoá khi còn lỗi nghiêm trọng, đồng bộ với API `approve`.

### Nhánh Slide Engine
1. Bỏ `marp_converter.py` (gọi `npx marp-cli`) — nguyên nhân slide xấu.
2. Dựng Slide Master Template bằng python-pptx: 3-4 layout chuẩn (mở đầu, kiến thức có hình, bài tập, tổng kết).
3. Map JSON Slide Schema (`slide_schema.py`) sang shape/textbox native.
4. Golden-file test: mở thử bằng PowerPoint/LibreOffice thật, đối chiếu layout không vỡ.
5. Gắn kết quả vào bảng `slides` (layout, body, artifact URI).

**Test cuối giai đoạn**: từ UI, nhập một bài học → xem giáo án → chỉnh sửa → xuất slide → mở file .pptx thật, sửa được trực tiếp trong PowerPoint.

---

## GIAI ĐOẠN 2.3 — Nâng cao chất lượng nội dung (Hướng 5 + 6 + 8)

**Mục tiêu ra**: Nội dung sinh ra được kiểm tra sư phạm thật, có hình minh hoạ, trải nghiệm chờ mượt hơn.

### Validator nâng cấp
1. Giữ rule-based validator làm lớp lọc thứ nhất (đủ 4 hoạt động, đúng thứ tự).
2. Thêm Agent "Pedagogical Reviewer" — prompt riêng, chấm theo rubric 0-2, đối chiếu `math_topics` để phát hiện lệch chương trình.
3. Auto-retry tối đa 2 lần với feedback chi tiết hơn (JSON path + lý do sư phạm).

### Geometry & hình ảnh
1. Tách MCP_Geometry thành service riêng (JSON-RPC), sinh SVG/PNG từ tham số hình học.
2. Engine tự kiểm tra ràng buộc (nhãn không chồng lấn, toạ độ hợp lý) trước khi trả kết quả.
3. Lưu vào bảng `geometry_assets`, tái sử dụng qua checksum.
4. Tích hợp API sinh ảnh (Flux/SD/DALL-E) cho minh hoạ phi hình học, tách riêng khỏi MCP_Geometry.

### Async & Streaming
1. Đưa job sinh giáo án/slide/hình ra khỏi request-response đồng bộ (Celery + Redis, hoặc BackgroundTasks nếu cần nhẹ hơn).
2. `GET /jobs/{job_id}` để poll, hoặc SSE để đẩy tiến độ real-time.
3. Idempotency-Key ở tầng job queue.

**Test cuối giai đoạn**: sinh một bài có hình học (VD: tam giác vuông) → thấy tiến độ real-time trên UI → ra giáo án có validator chấm điểm + slide có hình minh hoạ thật.

---

## GIAI ĐOẠN 2.4 — Conversation Edit + Kiểm thử & Đánh giá toàn diện (Hướng 7 + 9)

**Mục tiêu ra**: Tính năng mở rộng hoàn thiện, có số liệu đánh giá thật để đưa vào báo cáo.

1. Conversation Edit: map câu lệnh tự nhiên ("rút ngắn hoạt động 2 xuống 10 phút") → JSON patch có phạm vi rõ ràng, tạo version mới.
2. Unit test cho từng module (validator, docx_exporter, slide engine, geometry engine).
3. Integration test theo 12 use case (UC-01 → UC-12), dùng tiêu chí nghiệm thu có sẵn trong tài liệu 50 trang làm test case.
4. Chạy bộ đánh giá theo Chương 9: chủ đề bài học đa dạng (đại số/hình học/xác suất, có hình), 2 người chấm độc lập theo rubric.
5. Đo và ghi nhận đủ bộ KPI: JSON validity, đủ 4 hoạt động đúng thứ tự, rubric nội dung, geometry latency P95 & correctness, DOCX/PPTX mở được, format cốt lõi giữ nguyên.
6. Ghi rõ mẫu số, model ID, prompt version, template version khi báo cáo kết quả.

**Test cuối giai đoạn**: bộ số liệu đầy đủ, có thể đưa thẳng vào báo cáo đồ án làm Chương "Kết quả thực nghiệm".

---

## Bảng tổng hợp thứ tự phụ thuộc (vì sao đi theo thứ tự này)

| Giai đoạn | Phụ thuộc vào | Vì sao |
|---|---|---|
| 2.1 Database & API | — | Nền tảng, mọi thứ khác cần chỗ lưu và endpoint chuẩn |
| 2.2 UI & Slide Engine | 2.1 | UI cần API thật để gọi; Slide engine độc lập, chạy song song được |
| 2.3 Validator/Geometry/Async | 2.1, 2.2 | Cần DB lưu kết quả kiểm tra, cần UI hiển thị tiến độ/hình ảnh |
| 2.4 Conversation Edit & Eval | 2.1, 2.2, 2.3 | Eval toàn diện chỉ có ý nghĩa khi toàn bộ pipeline đã chạy đủ end-to-end |

Nếu ở bất kỳ họp dự án nào cần cắt bớt, đây chính là các "khối" độc lập để cắt nguyên khối (ví dụ bỏ hẳn 2.4 phần Conversation Edit) mà không ảnh hưởng phần đã làm trước đó — vì mỗi giai đoạn đã kết thúc bằng một bản demo chạy được, không phải code dở dang.
