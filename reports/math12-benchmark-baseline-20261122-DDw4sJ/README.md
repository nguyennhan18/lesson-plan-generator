# Mốc so sánh kỹ thuật: 15 ca Toán 12 — ticket #3

- **Trạng thái:** bằng chứng kỹ thuật, chưa phải nghiệm thu chuyên môn hay bàn giao.
- **Thời điểm đo:** 2026-11-22 (UTC được ghi chính xác trong `repeated-3x.json`).
- **HEAD khi đo:** `9bd7edf70fd8adfca1ff73021f4809735ab0c0b3` (`9bd7edf`).
- **Nhánh:** `feat/multi-role-orchestrator`. Baseline `9980026` trong `AGENTS.md` đã cũ so với HEAD này; dùng mã hiện hành để đo.
- **Python:** 3.13.7.
- **LLM:** 0 lượt gọi; không dùng provider hoặc khóa API.

## Working tree khi đo

Kết quả `git status --short` trước và sau phép đo giống nhau; các thay đổi này đã có sẵn và không thuộc ticket #3:

```text
 M README.md
 M app/backend/src/lessonai/api/routes/system.py
 M app/backend/src/lessonai/exporters/slide_exporter.py
 M app/backend/src/lessonai/parsers/docx_parser.py
 M app/backend/src/lessonai/parsers/pptx_parser.py
 M app/backend/src/lessonai/rag/retriever.py
 M app/backend/src/lessonai/services/office_math.py
 M app/backend/tests/test_retrieval_fixture.py
 M docs/retrieval-fixture-validator.md
?? app/backend/src/lessonai/services/manifest_corpus_check.py
?? app/backend/src/lessonai/services/slide_remediation.py
?? app/backend/tests/test_day3_parsers.py
?? app/backend/tests/test_office_math.py
?? infra/
?? scripts/quality/prepare-source-review.py
```

## Đầu vào và cách chạy lại

- Dùng đúng bộ 15 ca hiện có: 5 `valid`, 3 `faulty`, 3 `under_specified`, 2 `contradictory`, 2 `out_of_scope`; không đổi kỳ vọng hoặc tạo bộ ca mới.
- SHA-256 runner `scripts/quality/run_benchmark_suite.py`: `3d5569f6be10336a480e761c8748ab5602fd999e9fee45b3bdc01826bd4181d8`.
- SHA-256 fixture `data/fixtures/math12_benchmark_suite.json`: `2b43b722742a3c3e033cfc4e99fe2a0a3e483ed979099614a5fc7ca29d6d40e5`.
- Lệnh runner chuẩn:

```bash
env GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= PYTHONPATH=app/backend/src app/backend/venv/bin/python scripts/quality/run_benchmark_suite.py --output reports/math12-benchmark-baseline-20261122-DDw4sJ/canonical-run.json
```

- Lệnh đã chạy để lặp ba vòng dùng `evaluate_benchmark_case` của cùng runner, với `TestClient` mới ở mỗi vòng. Công cụ đo chỉ bọc runner để đo thời gian, không sửa sản phẩm, fixture hoặc runner:

```bash
env GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= PYTHONPATH=app/backend/src app/backend/venv/bin/python /tmp/lessonai_benchmark_repeat_20261122.py --runner scripts/quality/run_benchmark_suite.py --suite data/fixtures/math12_benchmark_suite.json --output reports/math12-benchmark-baseline-20261122-DDw4sJ/repeated-3x.json --rounds 3
```

Kết quả thô: [runner chuẩn](canonical-run.json) và [45 lượt đánh giá, thời gian từng ca](repeated-3x.json). Công cụ đo được lưu lại tại [measure_repeats.py](measure_repeats.py); bản lưu thêm kiểm tra đúng 15 ID riêng biệt trước khi chạy, còn logic đánh giá/thời gian giống công cụ tạm đã dùng. Để chạy lại, thay đường dẫn `/tmp/lessonai_benchmark_repeat_20261122.py` trong lệnh trên bằng đường dẫn bản lưu và dùng `--output` mới. Cả hai công cụ tạo file theo chế độ không ghi đè.

## Kết quả

- Runner chuẩn: **15 đạt / 0 trượt / 0 bỏ qua** theo kỳ vọng kỹ thuật; exit code `0`, `technical_pass=true`; thời gian thực thi quan sát từ lệnh là **22.580 s**.
- Ba vòng lặp: **45/45 lượt khớp kỳ vọng** (mỗi ca 3/3). Thời gian toàn vòng lần lượt **20.641 s, 11.672 s, 11.600 s**. Chênh lệch vòng đầu gồm chi phí khởi động và không được diễn giải là thời gian AI tạo bài.
- `teacher_signoff_complete=false`, `handover_eligible=false`. M1–M5 không đổi; mọi cổng ký bởi giáo viên/thiết bị vẫn **MISSING**.

| Ca | Nhóm | Kết quả 3 vòng | Trung vị ms (min–max) | Quan sát kỹ thuật |
|---|---|---:|---:|---|
| BM-VALID-01 | valid | 3/3 | 3928.979 (3919.358–6557.125) | Đồ thị tính được; quality `needs_review`, 0 lỗi chặn |
| BM-VALID-02 | valid | 3/3 | 1363.476 (1334.538–2596.556) | Hai nhánh đồ thị; không nối qua gián đoạn |
| BM-VALID-03 | valid | 3/3 | 3.694 (2.876–2531.125) | Hình lập phương, thể tích 64 |
| BM-VALID-04 | valid | 3/3 | 3.986 (3.412–4.060) | Chóp đều, thể tích 16, cạnh bên bằng nhau |
| BM-VALID-05 | valid | 3/3 | 3.367 (3.124–1268.525) | Chóp tại A, thể tích 16, cạnh bên không đồng nhất |
| BM-FAULTY-01 | faulty | 3/3 | 2.872 (2.409–1296.641) | Quality `blocked`, 1 lỗi chặn |
| BM-FAULTY-02 | faulty | 3/3 | 2542.069 (2534.264–2558.598) | Quality `blocked`, 1 lỗi chặn |
| BM-FAULTY-03 | faulty | 3/3 | 3.670 (3.607–6.265) | Quality `blocked`, 2 lỗi chặn |
| BM-UNDER-01 | under_specified | 3/3 | 1281.602 (1263.158–1291.093) | Đẳng thức `unverified`: khác miền xác định |
| BM-UNDER-02 | under_specified | 3/3 | 1251.966 (1224.685–1262.768) | Đẳng thức `unverified`: ngoài phạm vi kiểm chứng |
| BM-UNDER-03 | under_specified | 3/3 | 3.488 (2.786–3.672) | Xác nhận hình/đồ thị bị từ chối HTTP 422 |
| BM-CONTRA-01 | contradictory | 3/3 | 1.255 (1.117–1.365) | Dữ kiện chiều cao lập phương mâu thuẫn, HTTP 422 |
| BM-CONTRA-02 | contradictory | 3/3 | 3.584 (3.531–3.972) | Quality `blocked`, 1 lỗi chặn |
| BM-OOS-01 | out_of_scope | 3/3 | 1.149 (0.993–1.399) | Loại hình ngoài phạm vi, HTTP 422 |
| BM-OOS-02 | out_of_scope | 3/3 | 1274.019 (1268.289–1274.976) | Đẳng thức `unverified` vì bậc đa thức; biểu thức plot nguy hiểm HTTP 422 |

**Cách đọc:** `passed` nghĩa là hành vi của từng ca khớp kỳ vọng, kể cả ca được kỳ vọng phải bị từ chối. HTTP 200 ở `quality/approve` của ca hợp lệ chỉ là lời gọi kỹ thuật của runner, không phải chữ ký hoặc quyết định của giáo viên. Các số `blocking_error_count` là lỗi phát hiện, **không phải** số chỗ đã được sửa.

## Chỉ số chưa kiểm chứng

| Chỉ số được yêu cầu | Trạng thái | Lý do |
|---|---|---|
| Thời gian AI tạo dàn ý, giáo án, slide | Chưa đo | Runner không gọi LLM hoặc luồng tạo bài; thời gian ở trên là thời gian đánh giá kỹ thuật |
| Lỗi dàn ý | Chưa đo | Bộ 15 ca không sinh hoặc duyệt dàn ý |
| Số chỗ giáo viên/AI phải sửa | Chưa đo | Runner phát hiện lỗi nhưng không thực hiện chu trình sửa |
| Chất lượng DOCX/PPTX/ZIP | Chưa đo | Runner không xuất hay mở tệp |
| Chất lượng toán/sư phạm do giáo viên xác nhận | MISSING | Fixture còn `pending_teacher_signoff`; không có biên bản ký |
| Đồ thị tham số ba miền của D11–D12 | Chưa đo | Đây là mốc bộ 15 ca hiện có, không phải bộ phép kiểm của demo nhiều vai trò |

Đo các chỉ số tạo nội dung bằng LLM thật sẽ là phép đo khác, cần thống nhất trước số lượt gọi và provider; phép đo này đã thực hiện **0** lượt gọi. Không suy ra trạng thái PASS của bất kỳ release gate nào từ báo cáo này.
