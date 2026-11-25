# Validator fixture truy hồi — lát cắt đầu

## Phạm vi bằng chứng

CI ở 9980026 bao phủ 18 tests portable trên corpus tổng hợp. Sáu test bổ sung trong test_phase3_pedagogical_rag.py dùng corpus thật và chỉ có bằng chứng local, không được tính vào CI xanh. Đột biến có tổng hợp mutations_by_kind (ba số đếm và correct_detection_rate) cùng invalid_baseline trong JSON runner; phải lưu JSON của lần nghiệm thu, không chỉ viện dẫn pytest xanh.

Đối chiếu manifest với nguồn thật dùng lệnh riêng:

```sh
app/backend/venv/bin/python -m lessonai.services.manifest_corpus_check MANIFEST.json --corpus CORPUS.jsonl --output NEW_REPORT.json
```

Có thể lặp --corpus cho nhiều JSONL. Lệnh chỉ đọc nguồn, xuất file bằng chế độ exclusive, không ghi approval. Báo cáo có commit và hash mã đang thực thi (vì working tree có thể khác commit), hash byte manifest/corpus, số lượng và lỗi. Nội dung mỗi đơn vị được băm bằng source_hash v2. Nguồn thay đổi hoặc biến mất trả FIXTURE_MANIFEST_STALE / exit 2; ID corpus trùng/thiếu bị từ chối; lỗi I/O exit 3. Phạm vi hiện tại là nội dung JSONL, chưa chứng thực asset hoặc lựa chọn nguồn chuyên môn. Logic stale có test synthetic portable; báo cáo kiểm tra corpus thật chỉ xuất khi manifest lô được lập, không coi snapshot tự tạo rồi kiểm ngay là bằng chứng nguồn đã duyệt.

## Bằng chứng Linux CI

Runner mới đã được xác minh success tại commit `99800263b52fb50dbf070c2054111dbac58a792b`: https://github.com/nguyennhan18/lesson-plan-generator/actions/runs/43561006902 . Hai suite portable có 18 test; cũng chạy đạt từ git archive của commit, không dựa vào corpus local. Suite hiệu năng corpus thật chỉ là bằng chứng local (không thuộc workflow này).

Đã kiểm tra trên GitHub Actions ngày 2026-11-14: workflow RAG fixture tests thành công tại commit `63c8086c12af60ba2393d31452d4a315f574e0bc`.
URL: https://github.com/nguyennhan18/lesson-plan-generator/actions/runs/43332629796
Đây là bằng chứng cho hai suite triage/validator ở commit đó, không phải toàn bộ release gate hay thay đổi hash v2 sau này.

Manifest hiện bắt buộc `hash_version: 2`. Source hash v2 chuẩn hóa CRLF/CR thành LF và Unicode NFC đệ quy trong giá trị chuỗi; giữ nguyên khóa object, thứ tự list và nội dung ngoài các phép chuẩn hóa đó. JSON được sắp xếp khóa, UTF-8, không khoảng trắng. Hash byte của asset và kiểm tra approval trước/sau không thay đổi. Approval cũ có nội dung thay đổi hash sẽ bị loại và cần duyệt lại.

Chạy bằng Python đã cài package backend:

```sh
app/backend/venv/bin/python -m lessonai.services.retrieval_fixture fixture.json manifest.json
```

Schema thực thi: `Fixture` và `Manifest` trong `lessonai.services.retrieval_fixture`. Có thể xuất JSON Schema bằng `Fixture.model_json_schema()` và `Manifest.model_json_schema()`. Đây là schema công cụ offline, không đổi OpenAPI.

Manifest gồm `units`, mỗi mục có `unit_id`, `content_hash`. Fixture có `schema_version: "1"`, `config`, và `cases` không rỗng. Mỗi case có `case_id`, `query`, `required_ids`; `optional_relevant_ids` và `forbidden_ids` mặc định rỗng. Các danh sách chứa object với `unit_id`, `content_hash`, `rationale`. Nguồn cấm có thêm `reason` trong `not_approved`, `revoked`, `hash_changed`, `irrelevant_distractor`, cùng `approval_hash` nếu cần. `hash_changed` bắt buộc approval_hash khác content_hash hiện tại.

Config bắt buộc khai báo algorithm, algorithm_version, embedding, embedding_version, index_data_sha256, top_k dương, min_bm25 hữu hạn không âm hoặc null, tie_break = unit_id_ascending. score_threshold cũ bị từ chối vì không phải tham số runtime.

## Runner đã nối cấu hình

`python -m lessonai.services.retrieval_fixture_runner FIXTURE MANIFEST --test-root TEMP_PARENT --mutate` chạy với LESSONAI_DATA_DIR được đặt trước import và phải nằm dưới TEMP_PARENT, khác kho mặc định. CLI trả JSON trên stdout, log loader trên stderr.

Algorithm bắt buộc lessonai-question-bm25-quality, version lấy từ QUESTION_RETRIEVAL_VERSION hiện là 2; embedding và embedding_version đều none. Index hash là SHA-256 của JSON compact chứa danh sách source_hash của câu hỏi theo thứ tự nạp. Runner kiểm tra hash này trước truy hồi; top_k/min_bm25 truyền trực tiếp vào retrieve_questions. Các khóa lạ hoặc thuật toán không hỗ trợ trả exit 2. Manifest vẫn cần bước đối chiếu riêng từng đơn vị corpus trước khi đưa giáo viên.

Đột biến báo detected_correctly/detected_wrong_code/survived; invalid_baseline trả exit 1 và thống kê riêng. Mỗi loại có tập mã lỗi kỳ vọng chính xác (ca rỗng có thể đồng thời EXPECTED_EMPTY và FORBIDDEN_PRESENT/UNEXPECTED_ID), tỷ lệ phát hiện đúng theo loại. Những test này kiểm tra assertion trên output đột biến, không phải chứng minh retriever chống mọi đột biến nội bộ.

CI tại 7129f621ffb0c9f6fc77b399a8aa66f92963b8d6 đã success: https://github.com/nguyennhan18/lesson-plan-generator/actions/runs/43560804185 . Bằng chứng này chưa bao gồm runner mới.

Mã lỗi tĩnh: FIXTURE_SCHEMA, FIXTURE_JSON, FIXTURE_DUPLICATE_ID, FIXTURE_OVERLAP, FIXTURE_UNKNOWN_ID, FIXTURE_HASH_MISMATCH, FIXTURE_APPROVAL_HASH, FIXTURE_CAPACITY. Không đọc được tệp: ENVIRONMENT_IO.

Exit code: 0 đạt validator; 2 fixture sai; 3 lỗi môi trường. Hàm tổng hợp dùng ưu tiên 3 > 2 > 1 > 0. Mã 1 dành cho runner truy hồi/đột biến tương lai, kể cả invalid_baseline; validator này chưa chạy truy hồi hoặc đột biến. Nếu một file lỗi JSON và file kia không đọc được, CLI giữ cả hai lỗi và trả 3.

Hash được so với manifest được cung cấp, chưa tái băm corpus hoặc xác minh index_data_sha256. Manifest phải được dựng từ snapshot nguồn khi triển khai bước kế tiếp. Test dùng ID tổng hợp, không tạo approval trong kho runtime; guard so SHA-256 kho approval thật trước/sau module test.

Đã kiểm chứng CLI subprocess với fixture đúng (0), fixture có ID không tồn tại (2). Bộ test gồm 9 ca, phủ từng mã FIXTURE_* và ưu tiên lỗi môi trường.

## Công việc tiếp theo

Cập nhật truy hồi 2026-11-14: retrieve_questions nhận min_bm25=None (mặc định giữ lọc cũ); khi truyền số hữu hạn không âm, chỉ query có token mới áp dụng cổng BM25 > min_bm25. Không đổi trọng số. Sắp xếp theo -round(score, 9), rồi unit_id/id/question_id tăng dần; hòa điểm có thể đổi top-k so với thứ tự corpus trước đây. Approval thiếu/sai hash_version bị loại, có thể lấy lý do hash_version_mismatch qua approved_units(..., rejection_reasons=list). Test subprocess kiểm tra tham số runtime trực tiếp, từ chối khóa lạ, nguồn nhiễu cùng chất lượng, đảo thứ tự corpus và approval phiên bản cũ. Schema cấu hình fixture tổng quát chưa nối vào runner truy hồi; score_threshold của schema chưa phải alias của min_bm25.

Cập nhật 2026-11-14: local đạt 15 tests trên hai suite. Corpus tổng hợp 24 câu được dựng trong subprocess với DATA_DIR dưới tmp_path; sai đường dẫn dừng exit 3. Test gọi retriever thật và kiểm tra nguồn chưa duyệt/thu hồi/đổi hash không xuất hiện, nguồn hợp lệ xuất hiện, lesson không tồn tại trả []. Guard so nội dung và danh sách tệp reviewed_sources.json* trước/sau. Đây chưa phải bộ kiểm thử phù hợp với nguồn nhiễu đã duyệt. Runtime hiện dùng BM25 thuần Python, chưa có ngưỡng và phá hòa theo unit_id; không tuyên bố đã hoàn thành cấu hình tất định theo hợp đồng mới.

1. Thêm lệnh hoặc cờ đối chiếu corpus riêng: tính lại hash từng đơn vị theo cùng quy tắc định danh/hash của runtime, so với manifest. Sai lệch phải báo `FIXTURE_MANIFEST_STALE` (exit 2); không đọc được corpus báo lỗi môi trường (exit 3). Cần test corpus thay đổi trong khi fixture và manifest cũ vẫn khớp nhau. Mã này mới được dành trước, chưa được triển khai.
2. Cố định cấu hình truy hồi thực tế và truyền đường dẫn approval test tường minh; kiểm tra runtime không nhìn thấy approval test.
3. Chạy ca nguồn vừa được duyệt vừa liên quan xuyên suốt bộ truy hồi thật.
4. Thêm đột biến từng loại với expected_error_code, kiểm tra baseline xanh trước mỗi đột biến.

Test tự dựng fixture/manifest trong mã và ghi các tệp CLI vào thư mục tạm của pytest. Không phụ thuộc fixture mẫu hoặc corpus cục bộ chưa được theo dõi; kiểm tra kho approval thật chỉ thực hiện so hash nếu tệp có mặt. Chạy bằng:

```sh
GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_retrieval_fixture.py
```
