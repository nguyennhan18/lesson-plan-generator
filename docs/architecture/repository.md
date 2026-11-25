# Cấu trúc repo LessonAI-5512

## Điểm bắt đầu

- Frontend: [`App.jsx`](../../app/frontend/src/App.jsx) kết nối các màn hình và giữ trạng thái dùng chung.
- Backend: [`lessonai/main.py`](../../app/backend/src/lessonai/main.py) khởi tạo FastAPI và đăng ký router.
- Cấu hình, đường dẫn: [`core/config.py`](../../app/backend/src/lessonai/core/config.py).
- Học liệu runtime: [`app/backend/data`](../../app/backend/data).

## Frontend

Mỗi thư mục trong `app/frontend/src/features` sở hữu giao diện và xử lý của một chức năng:

| Thư mục | Nội dung |
| --- | --- |
| `dashboard` | Khởi tạo bài giảng |
| `generation` | Dàn ý, sinh giáo án và slide, nội dung dự phòng |
| `lesson-plan` | Xem và biên tập giáo án |
| `slide-editor` | Biên tập bộ slide |
| `presentation` | Sân khấu trình chiếu, phím tắt, quiz, bảng vẽ |
| `geometry` | Mô hình 3D, công cụ hình học và khai triển |
| `chat` | Trợ giảng AI và đề xuất chỉnh sửa |
| `analytics` | Nhập bảng điểm và phân tích trình độ lớp |
| `exports` | Chuẩn bị ảnh 3D, xuất Word, PowerPoint, ZIP |

`shared` chứa phần được nhiều chức năng dùng: thành phần giao diện, công thức toán,
kiểm định nội dung, lưu trữ trình duyệt và vận chuyển HTTP. Các yêu cầu JSON POST
đi qua `shared/api/client.js`; từng chức năng quyết định cách thông báo lỗi.
Yêu cầu tải lên dạng multipart vẫn do chức năng nhập dữ liệu xử lý.

Trạng thái của bài giảng, slide hiện tại, tham số 3D và chế độ trình chiếu tiếp tục
được quản lý trong `App.jsx`. Các action nhận giá trị và hàm cập nhật từ `App`.
Mỗi lần render tạo lại action để nhận dữ liệu hiện tại. Không thêm một bản trạng
thái thứ hai trong module chức năng.

Chỉ tạo thư mục con khi có nhu cầu thật. Tệp dài nhưng cùng phục vụ một nhiệm vụ,
chẳng hạn dựng PowerPoint hoặc mô tả nội dung dự phòng, không phải tự động chia nhỏ.

## Backend

Luồng chính: `api/routes → services → llm, rag, parsers hoặc exporters → schemas`.

- `api/routes`: nhận yêu cầu, xác thực đầu vào bằng schema, trả JSON hoặc tệp và lỗi HTTP.
- `services/generation`: tách riêng sinh giáo án, slide, dàn ý và nội dung dự phòng.
- `services`: chat, hình học, phân tích bảng điểm, kiểm định và bổ sung ảnh cho slide.
- `llm`: gateway, chọn nhà cung cấp, retry và chuẩn hóa phản hồi AI.
- `prompts`: nội dung hướng dẫn AI cho giáo án, slide, chat và kiểm định.
- `rag`: chỉ mục chương trình, truy xuất học liệu và tạo ngữ cảnh.
- `parsers`, `exporters`, `templates`: đọc và tạo tài liệu Office.
- `core`: nạp `.env`, logging và đường dẫn tài nguyên.

Import nội bộ dùng tên package `lessonai`. Không thêm `sys.path` trong module hoặc
script. Cài editable một lần trong môi trường ảo:

```bash
app/backend/venv/bin/python -m pip install -e ./app/backend
```

Lệnh chạy chính là `uvicorn lessonai.main:app --app-dir src` từ `app/backend`.
`src/main.py` giữ tương thích cho lệnh cũ `uvicorn main:app --app-dir src`.
Các URL, request/response schema và tên tệp tải xuống được giữ khi tái cấu trúc.

## Dữ liệu

- `data/raw/`: học liệu nguồn, bản trích xuất và các bản dữ liệu nhập trước đây;
  không được Git theo dõi.
- `data/fixtures/`: Golden Set nhỏ, được Git theo dõi để kiểm thử.
- `app/backend/data/`: nguồn chuẩn của dữ liệu đã xử lý mà ứng dụng đọc;
  được Git theo dõi. Ứng dụng không đọc dự phòng từ `data/raw`.
- `data/processed/`: đầu ra thử nghiệm của pipeline chuẩn bị dữ liệu, được bỏ qua trong Git.
- `reports/data/`: báo cáo kiểm kê và chất lượng dữ liệu.

Ví dụ chuẩn bị một bản dữ liệu để rà soát:

```bash
app/backend/venv/bin/python scripts/data/build_packaged_data.py --output /tmp/lessonai-data-review
```

Script từ chối ghi vào thư mục đích đã có nội dung. Kết quả staging không tự động
ghi đè dữ liệu runtime; cần rà soát thay đổi, gồm các câu hỏi đã làm giàu, trước khi
cập nhật dữ liệu chuẩn. `enrich_chapter3_questions.py` chỉ cập nhật dữ liệu runtime.

Đường dẫn runtime có thể cấu hình bằng `LESSONAI_DATA_DIR`, `LESSONAI_OUTPUT_DIR`.
Dùng đường dẫn tuyệt đối khi cấu hình. `.env` mặc định nằm trong `app/backend`.
Khi triển khai từ checkout, cần mang theo `app/backend/data`; học liệu gốc không
bắt buộc để chạy API.

## Cấu trúc thư mục các phân vùng

- `app/`: mã nguồn ứng dụng (backend FastAPI và frontend React 19).
- `docs/`: tài liệu kỹ thuật (`architecture/`, `design/`, `requirements/`).
- `project-management/`: quản trị dự án (`PROGRESS.md`, `decisions/`, `roadmap/`, `phases/`, `release-gates/`).
- `quality/`: kiểm định chất lượng (`audits/`, `issue-registries/`, `acceptance/`, `test-reports/`, `README.md`).
- `reports/`: bằng chứng thực nghiệm và nhật ký kiểm thử bất biến theo thời gian.
- `data/`: kho dữ liệu gốc và fixtures (`fixtures/golden_set.json`, `raw/`).
- `scripts/`: kịch bản bảo trì và công cụ kiểm kê/lint (`data/`, `quality/`, `examples/`, `documentation/`).
- `infra/`: hướng dẫn triển khai, mẫu cấu hình môi trường (`env.example`) và CI workflow.

Các báo cáo lịch sử có thể mô tả đường dẫn và thiết kế ở thời điểm tạo báo cáo.
Tài liệu này là hướng dẫn cấu trúc hiện hành. Các bản Word/PDF tham khảo vẫn được
giữ trên máy, nhưng không tự động đưa vào Git.

## Kiểm tra thay đổi

Từ thư mục gốc:

```bash
make test
make build
```

`make test` sử dụng Python tại `app/backend/venv/bin/python`; có thể đổi bằng
`make test PYTHON=python`. Chạy riêng bằng `make test-backend` hoặc
`make test-frontend`. Các lệnh `make backend`, `make frontend`, `make inventory`
và `make lint-data` cũng chạy từ thư mục gốc.

Backend có kiểm thử bảo vệ hợp đồng OpenAPI, tài nguyên runtime và việc import
package từ thư mục làm việc khác. Frontend kiểm thử luồng xuất tài liệu, trình chiếu
và sinh nội dung bằng phản hồi API giả lập. Bộ kiểm thử tích hợp đọc lại DOCX/PPTX
và xác minh ZIP, checksum, công thức, ảnh và nội dung bài giảng.


## Chặn tạm trong mốc M0

`core/feature_availability.py` mô tả trạng thái tạm ngắt xử lý biểu thức. Không có cờ bật lại parser cũ. `graph_generator` hiện chỉ render dữ liệu cột/tròn; `latex_to_sympy_expr` trả `None` và audit báo `algebra_unverified`. M1 sẽ thay các điểm này bằng parser giới hạn tài nguyên rồi mới bật lại tính năng.

`core/render_runtime.py` giữ khóa Matplotlib chung cho cả biểu đồ và công thức. Renderer đóng figure của chính job trong `finally`; cleanup chỉ thu gom rác, không đóng figure của request khác. `services/rendering.py` bỏ cache ảnh cũ khi enrich và trả trạng thái đồ thị cho bản nháp.

Copilot đi qua cùng gateway trong test và runtime, chưa phát proposal sửa nội dung. Lỗi xuất trả JSON và giữ nguyên bài yêu cầu. Hợp đồng ID/revision, quyền phiên, proposal và kiểm tra chất lượng nội dung còn thuộc M2/M3.

Hai CLI audit hỗ trợ `--output` và `--mode baseline|acceptance`; frontend CLI đọc bằng chứng backend qua `--input`. Dùng `make test-critical`, `make audit-baseline REVIEW_OUTPUT=/tmp/baseline-001` và `make audit-acceptance REVIEW_OUTPUT=/tmp/m0-001`. Mỗi lần chạy cần prefix mới; acceptance hiện chỉ kiểm tra điều kiện chặn tạm M0.
