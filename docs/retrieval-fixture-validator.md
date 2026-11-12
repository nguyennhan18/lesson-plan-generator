# Validator fixture truy hồi — lát cắt đầu

Chạy bằng Python đã cài package backend:

```sh
app/backend/venv/bin/python -m lessonai.services.retrieval_fixture fixture.json manifest.json
```

Schema thực thi: `Fixture` và `Manifest` trong `lessonai.services.retrieval_fixture`. Có thể xuất JSON Schema bằng `Fixture.model_json_schema()` và `Manifest.model_json_schema()`. Đây là schema công cụ offline, không đổi OpenAPI.

Manifest gồm `units`, mỗi mục có `unit_id`, `content_hash`. Fixture có `schema_version: "1"`, `config`, và `cases` không rỗng. Mỗi case có `case_id`, `query`, `required_ids`; `optional_relevant_ids` và `forbidden_ids` mặc định rỗng. Các danh sách chứa object với `unit_id`, `content_hash`, `rationale`. Nguồn cấm có thêm `reason` trong `not_approved`, `revoked`, `hash_changed`, `irrelevant_distractor`, cùng `approval_hash` nếu cần. `hash_changed` bắt buộc approval_hash khác content_hash hiện tại.

Config bắt buộc khai báo algorithm, algorithm_version, embedding, embedding_version, index_data_sha256, top_k dương, score_threshold hữu hạn, tie_break = unit_id_ascending. Các trường phiên bản là khai báo; lát cắt này chưa thực thi hoặc kiểm tra phiên bản thuật toán truy hồi.

Mã lỗi tĩnh: FIXTURE_SCHEMA, FIXTURE_JSON, FIXTURE_DUPLICATE_ID, FIXTURE_OVERLAP, FIXTURE_UNKNOWN_ID, FIXTURE_HASH_MISMATCH, FIXTURE_APPROVAL_HASH, FIXTURE_CAPACITY. Không đọc được tệp: ENVIRONMENT_IO.

Exit code: 0 đạt validator; 2 fixture sai; 3 lỗi môi trường. Hàm tổng hợp dùng ưu tiên 3 > 2 > 1 > 0. Mã 1 dành cho runner truy hồi/đột biến tương lai, kể cả invalid_baseline; validator này chưa chạy truy hồi hoặc đột biến. Nếu một file lỗi JSON và file kia không đọc được, CLI giữ cả hai lỗi và trả 3.

Hash được so với manifest được cung cấp, chưa tái băm corpus hoặc xác minh index_data_sha256. Manifest phải được dựng từ snapshot nguồn khi triển khai bước kế tiếp. Test dùng ID tổng hợp, không tạo approval trong kho runtime; guard so SHA-256 kho approval thật trước/sau module test.

Đã kiểm chứng CLI subprocess với fixture đúng (0), fixture có ID không tồn tại (2). Bộ test gồm 9 ca, phủ từng mã FIXTURE_* và ưu tiên lỗi môi trường.

## Công việc tiếp theo

1. Thêm lệnh hoặc cờ đối chiếu corpus riêng: tính lại hash từng đơn vị theo cùng quy tắc định danh/hash của runtime, so với manifest. Sai lệch phải báo `FIXTURE_MANIFEST_STALE` (exit 2); không đọc được corpus báo lỗi môi trường (exit 3). Cần test corpus thay đổi trong khi fixture và manifest cũ vẫn khớp nhau. Mã này mới được dành trước, chưa được triển khai.
2. Cố định cấu hình truy hồi thực tế và truyền đường dẫn approval test tường minh; kiểm tra runtime không nhìn thấy approval test.
3. Chạy ca nguồn vừa được duyệt vừa liên quan xuyên suốt bộ truy hồi thật.
4. Thêm đột biến từng loại với expected_error_code, kiểm tra baseline xanh trước mỗi đột biến.

Test tự dựng fixture/manifest trong mã và ghi các tệp CLI vào thư mục tạm của pytest. Không phụ thuộc fixture mẫu hoặc corpus cục bộ chưa được theo dõi; kiểm tra kho approval thật chỉ thực hiện so hash nếu tệp có mặt. Chạy bằng:

```sh
GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_retrieval_fixture.py
```
