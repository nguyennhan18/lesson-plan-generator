# Mốc so sánh 15 ca Toán 12 — báo cáo bổ sung chi tiết lỗi (#3)

Báo cáo này dùng lượt đo bổ sung sau rà soát; [báo cáo và dữ liệu lượt đầu](README.md) được giữ nguyên. Đây là bằng chứng kỹ thuật, **không** phải nghiệm thu Toán 12 hoặc gate PASS.

## Phiên bản và trạng thái khi đo

- **HEAD khi đo bổ sung:** `ac9efecbdbd110e7e733320368daa813cac4c67d` (lượt đầu: `9bd7edf70fd8adfca1ff73021f4809735ab0c0b3`).
- **Nhánh:** `feat/multi-role-orchestrator`. Baseline `9980026` trong `AGENTS.md` khác mã hiện hành.
- **Python:** 3.13.7; **LLM:** 0 lượt gọi, 0 provider, ba biến API key được đặt rỗng.
- **Đầu vào:** đúng 15 ca hiện có; 5 valid, 3 faulty, 3 under_specified, 2 contradictory, 2 out_of_scope. Không đổi fixture hay đáp án.
- **SHA-256 runner khi đo:** `1955801949d5de089a4c8a86b0c3bcf688bb4a3736c489fc07bd2143018e5bae`.
- **SHA-256 fixture:** `2b43b722742a3c3e033cfc4e99fe2a0a3e483ed979099614a5fc7ca29d6d40e5`.
- [Manifest nguồn](source-manifest-v2.json) giữ hash 88 tệp Python/config/đầu vào, HEAD, nhánh và toàn bộ `git status --short` tại lúc đo. Có thể đối chiếu hash trước khi chạy lại. Vì workspace có mã ứng dụng chưa commit từ trước, checkout sạch chỉ từ HEAD **không** tái tạo đúng snapshot này; cần chính workspace hoặc bản sao mã khớp manifest.

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
 M scripts/quality/run_benchmark_suite.py
?? app/backend/src/lessonai/services/manifest_corpus_check.py
?? app/backend/src/lessonai/services/slide_remediation.py
?? app/backend/tests/test_day3_parsers.py
?? app/backend/tests/test_office_math.py
?? infra/
?? scripts/quality/prepare-source-review.py
```

Dòng `M scripts/quality/run_benchmark_suite.py` là bổ sung ghi lỗi chi tiết cho phép đo này; các thay đổi khác được giữ nguyên từ trước. [Runner chuẩn](canonical-run-v2.json) và [45 lượt có thời gian/lỗi từng ca](repeated-3x-v2.json) là dữ liệu thô, tạo tệp mới chứ không ghi đè lượt đầu.

## Lệnh đã chạy

```bash
env GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= PYTHONPATH=app/backend/src app/backend/venv/bin/python scripts/quality/run_benchmark_suite.py --output reports/math12-benchmark-baseline-20261122-DDw4sJ/canonical-run-v2.json
env GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= PYTHONPATH=app/backend/src app/backend/venv/bin/python reports/math12-benchmark-baseline-20261122-DDw4sJ/measure_repeats.py --runner scripts/quality/run_benchmark_suite.py --suite data/fixtures/math12_benchmark_suite.json --output reports/math12-benchmark-baseline-20261122-DDw4sJ/repeated-3x-v2.json --rounds 3
```

Để chạy lại, dùng đường dẫn `--output` **mới** vì hai công cụ tạo file riêng và từ chối ghi đè.

## Kết quả kỹ thuật

- Runner chuẩn: **15 đạt / 0 trượt / 0 bỏ qua**, exit code 0, thời gian lệnh 22.907 s.
- Ba vòng: **45/45 khớp kỳ vọng**; thời gian toàn vòng **20.836 s / 11.413 s / 11.316 s**. Đây là thời gian kiểm tra, **không phải** thời gian AI tạo bài.
- `teacher_signoff_complete=false` và `handover_eligible=false`. M1–M5 không đổi.
- Ca `faulty` đạt nghĩa là bị chặn đúng như kỳ vọng; `under_specified`/`out_of_scope` đạt nghĩa là được đánh dấu `unverified` hoặc từ chối đúng. HTTP 200 từ lời gọi `quality/approve` của runner không phải phê duyệt của giáo viên.

| Ca | Khớp kỳ vọng | Trung vị ms (min–max) | Lỗi/cảnh báo quan sát |
|---|---:|---:|---|
| BM-VALID-01 | 3/3 | 3837.753 (3771.416–6492.456) | 0 lỗi chặn; 5 cảnh báo cần xem lại |
| BM-VALID-02 | 3/3 | 1321.014 (1307.329–2654.335) | 0 lỗi chặn; 5 cảnh báo; hai nhánh đồ thị không nối qua gián đoạn |
| BM-VALID-03 | 3/3 | 3.273 (2.850–2594.157) | 0 lỗi chặn; 3 cảnh báo; thể tích lập phương 64 |
| BM-VALID-04 | 3/3 | 2.747 (2.662–4.851) | 0 lỗi chặn; 6 cảnh báo; thể tích chóp 16 |
| BM-VALID-05 | 3/3 | 3.164 (3.148–1396.378) | 0 lỗi chặn; 8 cảnh báo; thể tích chóp 16 |
| BM-FAULTY-01 | 3/3 | 2.574 (2.473–1313.711) | 1 lỗi chặn: đẳng thức số học |
| BM-FAULTY-02 | 3/3 | 2506.746 (2482.827–2621.035) | 1 lỗi chặn: đồng nhất thức đa thức |
| BM-FAULTY-03 | 3/3 | 4.015 (3.784–6.468) | 2 lỗi chặn: lựa chọn/giải thích trắc nghiệm |
| BM-UNDER-01 | 3/3 | 1256.164 (1242.842–1256.560) | `unverified`: hai biểu thức khác miền xác định |
| BM-UNDER-02 | 3/3 | 1232.051 (1231.032–1232.184) | `unverified`: ngoài phạm vi kiểm chứng |
| BM-UNDER-03 | 3/3 | 3.358 (2.923–4.087) | HTTP 422: chưa chọn rõ loại khối |
| BM-CONTRA-01 | 3/3 | 1.075 (1.030–1.103) | HTTP 422: chiều cao lập phương mâu thuẫn cạnh |
| BM-CONTRA-02 | 3/3 | 3.097 (3.054–3.173) | 1 lỗi chặn: đề/giả thiết đổi sau xác nhận hình |
| BM-OOS-01 | 3/3 | 1.036 (0.992–1.052) | HTTP 422: loại khối ngoài phạm vi |
| BM-OOS-02 | 3/3 | 1242.663 (1238.656–1250.235) | `unverified`: bậc đa thức ngoài phạm vi; HTTP 422 với biểu thức plot nguy hiểm |

Mã `issue_id`, mức độ và thông điệp đầy đủ của **từng** lỗi/cảnh báo nằm trong `details.quality_issues` của [repeated-3x-v2.json](repeated-3x-v2.json). Lý do `unverified` nằm trong `details.equality_result`; lỗi xác nhận trực quan/plot nằm trong `error_message` hoặc `unsafe_plot_error_message`. Chi tiết của từng ca ổn định giữa ba vòng. Số `blocking_error_count` là số lỗi phát hiện, **không phải** số chỗ đã sửa.

## Chưa kiểm chứng

| Chỉ số | Trạng thái | Vì sao |
|---|---|---|
| Thời gian AI tạo dàn ý, giáo án, slide | Chưa đo | Runner không gọi LLM hoặc tạo nội dung |
| Lỗi dàn ý | Chưa đo | Bộ 15 ca không sinh/duyệt dàn ý |
| Số chỗ phải sửa | Chưa đo | Runner phát hiện lỗi nhưng không chạy vòng sửa |
| Chất lượng DOCX/PPTX/ZIP | Chưa đo | Runner không xuất hoặc mở tệp |
| Toán và sư phạm được giáo viên ký | MISSING | Fixture còn `pending_teacher_signoff`, reviewer rỗng |
| Nhãn động ba miền của demo D11–D12 | Chưa đo | Không thuộc 15 ca benchmark hiện có |

Đo các mục tạo nội dung cần một phép đo khác có LLM thật và đầu vào/tiêu chí riêng; không suy ra giá trị từ thời gian chạy kỹ thuật. Không tự đánh dấu bất kỳ gate nào PASS.
