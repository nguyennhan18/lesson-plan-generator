# PIPELINE WORK CHI TIẾT — LessonAI-5512 (Giai đoạn 2)

*Tổng hợp từ 3 tài liệu: Báo cáo thẩm định GĐ1, Báo cáo tổng hợp dự án, Tài liệu chuẩn bị sơ khai 50 trang.*

Hiện trạng (theo Báo cáo thẩm định GĐ1): dự án đang ở mức **POC/khung backend thô (~30-35%)**. Luồng đã chạy được: Request → Gemini 2.5 Flash (Structured Output) → JSON → xuất Word (`docx_exporter.py`, đã làm tốt phần OMML Math) / PPTX qua Marp CLI (còn xấu). Chưa có: UI, Database, Auth, Validator sư phạm thật, hình ảnh minh họa thật, streaming.

Tài liệu 50 trang + báo cáo tổng hợp đã vẽ ra kiến trúc đích: **modular monolith + async worker**, 8 module nghiệp vụ, 12 use case, ERD đầy đủ, MCP_Geometry tách riêng. Đây là "bản đồ" — pipeline dưới đây là cách đi tới đó theo từng hướng, có thể chạy song song bởi các phần việc khác nhau nếu có nhiều người, hoặc làm tuần tự theo thứ tự ưu tiên nếu làm một mình.

**Thứ tự ưu tiên đề xuất nếu làm một mình:** 1 (Database) → 2 (Auth/API chuẩn) → 3 (UI cơ bản) → 4 (Slide native) → 5 (Validator LLM) → 6 (Geometry) → 7 (Conversation Edit) → 8 (Streaming/Queue) → 9 (Test & Deploy). Lý do: không có DB thì UI và versioning không có chỗ lưu; không có Auth/API chuẩn thì UI không có gì để gọi.

---

## HƯỚNG 1 — Database & Data Model (nền tảng bắt buộc trước tiên)

Đây là lỗ hổng nghiêm trọng nhất theo báo cáo GĐ1 (0% — hoàn toàn pure-prompt, không có dòng CSDL nào).

1. **Chọn stack**: PostgreSQL + SQLAlchemy (Alembic cho migration) — khớp với đề xuất trong báo cáo tổng hợp và tài liệu 50 trang.
2. **Dựng ERD theo đúng 9 bảng đã thiết kế sẵn** trong báo cáo tổng hợp (đỡ phải thiết kế lại từ đầu):
   `users`, `lesson_plans`, `lesson_versions`, `activities`, `slides`, `math_topics`, `question_bank`, `geometry_assets`, `audit_logs`.
3. **Ràng buộc nghiệp vụ cần code hoá ngay ở tầng DB/ORM**: `activities.ordinal` phải là 1–4, `type` lần lượt `opening → knowledge_formation → practice → application` (đây chính là điều mà `validation.py` hiện tại chỉ check bằng từ khoá — giờ ép luôn ở schema/constraint).
4. **Tách lưu trữ**: artifact lớn (file .docx/.pptx/.svg) → Object Storage (S3-compatible hoặc local MinIO nếu không có ngân sách); DB chỉ lưu URI, MIME, size, checksum.
5. **Viết lớp Repository/DAO** bọc quanh SQLAlchemy để `main.py` không thao tác SQL trực tiếp — chuẩn bị sẵn cho việc thêm Auth và versioning ở Hướng 2.
6. **Migration đầu tiên**: tạo bảng, seed thử 1 user admin, 1 lesson_plan mẫu để test toàn luồng insert/read.

## HƯỚNG 2 — API chuẩn hoá, Auth & Backend production-ready

Báo cáo GĐ1 chỉ rõ: 4 endpoint hiện tại "không Auth, không Rate Limit, mới dừng ở mức router chuyển tiếp".

1. **Auth**: JWT (access + refresh token), bảng `users` đã có sẵn trong ERD. Middleware RBAC theo 3 role đã định nghĩa trong tài liệu 50 trang: Giáo viên / Tổ trưởng chuyên môn / Admin.
2. **Chuẩn hoá REST theo đúng đặc tả đã có sẵn** trong báo cáo tổng hợp (Chương 6) — không cần thiết kế lại:
   - `POST /api/v1/lesson-plans`
   - `POST /lesson-plans/{id}/generate`
   - `POST /lesson-plans/{id}/geometry`
   - `POST /lesson-plans/{id}/slides/generate`
   - `POST /lesson-plans/{id}/export`
   - `POST /lesson-plans/{id}/approve`
   - `GET /jobs/{job_id}`
   - Header bắt buộc: `Bearer token` + `Idempotency-Key` (tránh sinh trùng khi retry mạng).
3. **Mã lỗi chuẩn hoá**: 422 (validator, kèm JSON path lỗi), 400, 401/403, 409 (version conflict), 429 (quota), 502/504 (lỗi phụ thuộc Gemini). Đây là điểm hiện `main.py` hoàn toàn chưa có.
4. **Rate limiting** theo user/role (chặn spam gọi Gemini gây tốn quota — vấn đề đã nêu trong GĐ1).
5. **Audit log**: mọi thao tác generate/approve/export ghi vào bảng `audit_logs`.

## HƯỚNG 3 — Web UI (React/Next.js) — điểm yếu lớn nhất hiện tại (0%)

Theo tài liệu 50 trang, luồng màn hình chuẩn là: Đăng nhập → Nhập thông tin bài học → Chọn mục tiêu/thời lượng/template → Sinh giáo án AI → Kiểm tra 5512 → Xem/Sửa → Tuỳ chỉnh slide → Preview → Export.

1. **Giai đoạn 1 (MVP UI, không cần đẹp)**: 4 màn hình bắt buộc theo đúng tài liệu — (a) form nhập bài học, (b) xem/sửa giáo án AI sinh ra, (c) tuỳ chỉnh slide, (d) preview & export. Dùng UI đơn giản trước, không cần Figma đầy đủ.
2. **Live Editor cho giáo án**: cho giáo viên sửa trực tiếp từng hoạt động (4 hoạt động 5512) thay vì chỉ xem JSON thô — đây là khoảng trống lớn nhất khiến sản phẩm "chưa dùng được".
3. **Autosave + version**: mỗi lần sửa tạo một bản ghi trong `lesson_versions` (đã có sẵn trong ERD) — chuẩn bị cho UC-12 "Xem lịch sử và khôi phục version" trong tài liệu 50 trang.
4. **Panel cảnh báo validator**: hiển thị lỗi 5512 theo JSON path (không chỉ dùng màu — tài liệu yêu cầu có icon + text, vì lý do accessibility).
5. **Nút Duyệt (Approve) bị khoá** khi còn lỗi nghiêm trọng — logic này cần đồng bộ với trạng thái trả về từ API `approve`.
6. **Component phân biệt rõ 3 nguồn nội dung**: phần AI sinh / phần engine tính toán (hình học) / phần giáo viên đã tự sửa — yêu cầu UX cụ thể có trong tài liệu, dễ bị bỏ sót nếu code UI vội.

## HƯỚNG 4 — Thay Marp CLI bằng Slide Engine native (python-pptx)

Đây là điểm yếu thẩm mỹ nghiêm trọng nhất theo đánh giá GĐ1: "slide xấu, đơn điệu như ghi chú, không kéo thả chỉnh sửa được".

1. **Bỏ hoàn toàn `marp_converter.py`** (subprocess gọi `npx marp-cli`) — đây là nguyên nhân khiến slide bị "đóng băng" như ảnh tĩnh.
2. **Thiết kế Slide Master Template bằng python-pptx**: dựng sẵn 3–4 layout chuẩn (slide mở đầu, slide kiến thức có hình, slide bài tập, slide tổng kết) với màu sắc/logo/font cố định.
3. **Map JSON Slide Schema (đã có sẵn từ `slide_schema.py`) sang shape/textbox native** thay vì render qua Markdown trung gian — giữ được khả năng kéo-thả chỉnh sửa trong PowerPoint thật.
4. **Test golden-file**: dựng bộ slide mẫu, so sánh mở bằng PowerPoint/LibreOffice thật để đảm bảo không vỡ layout (đúng tinh thần "Format cốt lõi ≥95%" trong bộ KPI của báo cáo tổng hợp).
5. Gắn vào bảng `slides` trong DB (layout, body, artifact URI).

## HƯỚNG 5 — Nâng cấp Validator 5512 bằng LLM Evaluator

GĐ1 chỉ rõ lỗ hổng: validator hiện tại chỉ đếm ký tự >10 và match từ khoá — nội dung vô nghĩa vẫn "hợp lệ" nếu chứa đúng từ khoá.

1. **Giữ lại rule-based validator** (nhanh, rẻ) làm lớp lọc thứ nhất: đủ 4 hoạt động, đúng thứ tự `opening/knowledge_formation/practice/application`.
2. **Thêm Agent AI thứ hai đóng vai "Pedagogical Reviewer"**: prompt riêng, chấm điểm theo rubric (đúng chương trình, thời lượng hợp lý, không mâu thuẫn logic) — trả về điểm 0–2 theo đúng thang trong Chương 9 báo cáo tổng hợp (mục tiêu ≥90%).
3. **Kiểm tra hallucination cơ bản**: đối chiếu chủ đề sinh ra với `math_topics` (bảng danh mục chương trình đã có trong ERD) để phát hiện nội dung lệch chương trình.
4. **Auto-retry có giới hạn** (giữ nguyên cơ chế hiện tại, tối đa 2 lần theo đúng NFR "Tin cậy" trong báo cáo tổng hợp) nhưng feedback lỗi giờ chi tiết hơn (kèm JSON path + lý do sư phạm, không chỉ "thiếu từ khoá").
5. **Bộ 30 đề kiểm thử** (đề xuất có sẵn trong Chương 9: 30 đề, ≥10 đề có hình, 2 giáo viên chấm độc lập, 3 lần chạy có schema + 1 lần baseline) dùng để đo hiệu quả validator mới so với bản cũ.

## HƯỚNG 6 — MCP_Geometry & hình ảnh minh hoạ thật

GĐ1: "chưa chèn được hình ảnh minh hoạ thật vào slide, chỉ có text `image_prompt`". Tài liệu 50 trang có hẳn UC-10 riêng cho việc này.

1. **Tách MCP_Geometry thành service riêng** (đúng kiến trúc modular monolith + MCP đã thiết kế) — nhận tham số hình học (điểm, vuông góc/song song, độ dài, góc, nhãn, hệ toạ độ) qua JSON-RPC, trả về SVG/PNG + metadata.
2. **Engine phải tự kiểm tra ràng buộc hình học** (tránh nhãn chồng lấn, toạ độ vô lý) trước khi trả kết quả — không phó mặc cho LLM tính toán hình học (LLM chỉ sinh tham số, engine mới là nguồn chân lý).
3. **Lưu vào bảng `geometry_assets`** (tham số, SVG/PNG, checksum) để tái sử dụng, tránh gọi lại engine mỗi lần export.
4. **KPI cụ thể cần đạt** (đã có sẵn trong Chương 9): latency P95 < 5 giây, độ chính xác hình học ≥95%.
5. **Với hình minh hoạ phi hình học** (ảnh minh hoạ chủ đề, không phải sơ đồ toán): tích hợp API sinh ảnh (Flux/Stable Diffusion/DALL-E theo đề xuất GĐ1) — tách riêng khỏi MCP_Geometry vì bản chất khác nhau (một bên là tính toán xác định, một bên là sinh ảnh xác suất).

## HƯỚNG 7 — Conversation Edit (chỉnh sửa bằng chat)

Đây là module UC-06 trong tài liệu 50 trang, chưa được nhắc trong báo cáo GĐ1 — hướng mở rộng giá trị sau khi có UI cơ bản.

1. Cho giáo viên chỉnh sửa giáo án bằng câu lệnh tự nhiên ("rút ngắn hoạt động 2 xuống 10 phút") thay vì chỉ sửa tay từng field.
2. Map câu lệnh → JSON patch có phạm vi rõ ràng (chỉ được sửa field được chỉ định, không cho AI viết lại toàn bộ giáo án ngoài ý muốn).
3. Mỗi patch qua chat cũng tạo một bản ghi trong `lesson_versions` — dùng chung cơ chế versioning với Hướng 3.

## HƯỚNG 8 — Hạ tầng bất đồng bộ: Async Task Queue + Streaming (SSE)

GĐ1: gọi Gemini + retry khiến API chờ 10–20 giây, không có streaming, "cảm giác app bị treo".

1. **Đưa job sinh giáo án/slide/hình ra khỏi request-response đồng bộ**: dùng Celery + Redis (hoặc FastAPI BackgroundTasks nếu muốn nhẹ hơn ở giai đoạn đầu) — endpoint `POST /generate` trả `job_id` ngay, không block.
2. **`GET /jobs/{job_id}`** (đã có trong đặc tả API) để client poll trạng thái, hoặc:
3. **SSE (Server-Sent Events)** để đẩy tiến độ real-time (đề xuất trong cả GĐ1 và kiến trúc modular monolith) — quan trọng vì latency sinh JSON dài + retry hiện tại là điểm gây trải nghiệm tệ nhất.
4. **Idempotency-Key** ở tầng job queue để tránh sinh trùng khi client retry do timeout.

## HƯỚNG 9 — Kiểm thử & Đánh giá (trước khi coi là "hoàn thiện")

Bộ KPI đã được thiết kế sẵn trong báo cáo tổng hợp (Chương 9) — dùng luôn làm tiêu chí nghiệm thu cuối:

| Chỉ số | Mục tiêu |
|---|---|
| JSON schema validity | ≥95% |
| Đủ 4 hoạt động đúng thứ tự | 100% sau kiểm tra |
| Rubric nội dung (giáo viên chấm) | ≥90% |
| Geometry latency P95 | <5 giây |
| Geometry correctness | ≥95% |
| DOCX/PPTX mở được | 100% |
| Format cốt lõi giữ nguyên | ≥95% |

1. Unit test cho từng module (validator, docx_exporter, slide engine, geometry engine).
2. Integration test theo từng use case (UC-01 đến UC-12 trong tài liệu 50 trang) — mỗi UC đã có sẵn "Tiêu chí nghiệm thu sơ khai", dùng trực tiếp làm test case.
3. Golden-file test cho export (so khớp định dạng, không chỉ so nội dung).
4. Chạy bộ 30 đề Toán với 2 giáo viên chấm độc lập — đây là bước duy nhất không thể tự động hoá, cần lên lịch trước.
5. Ghi rõ mẫu số, model ID, prompt version, template version khi báo cáo kết quả (yêu cầu minh bạch đã nêu trong Chương 9 — tránh báo cáo "tô hồng" như GĐ1 đã cảnh báo).

---

### Gợi ý dùng tài liệu 50 trang trong lúc code

Tài liệu này đã có sẵn **12 use case chi tiết (UC-01 → UC-12)**, mỗi UC có Sequence Diagram mô tả bằng lời, Activity Diagram, và Tiêu chí nghiệm thu — nên dùng trực tiếp làm ticket/backlog thay vì viết lại từ đầu. Phần "CHƯƠNG 22 — Thiết kế giao diện" trong tài liệu đang **để trống** (wireframe, sitemap, design system, prototype Figma) — đây là phần cần bổ sung trước khi bắt tay code UI ở Hướng 3.
