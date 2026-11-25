# Cấu trúc repo LessonAI-5512

Tài liệu này là bản đồ tra cứu: cần sửa một chỗ thì tìm ở đâu, và sửa xong thì
luật nào ràng buộc. Trạng thái tính năng nằm ở
[`PROGRESS.md`](../../project-management/PROGRESS.md); quy tắc làm việc nằm ở
[`AGENTS.md`](../../AGENTS.md); lý do của từng quyết định nằm ở [`docs/adr/`](../adr).

## Điểm bắt đầu

- Backend: [`lessonai/main.py`](../../app/backend/src/lessonai/main.py) dựng FastAPI, CORS, middleware chặn origin ngoài máy và bọc lỗi. 50 endpoint.
- Frontend: [`src/main.jsx`](../../app/frontend/src/main.jsx) → [`App.jsx`](../../app/frontend/src/App.jsx) giữ trạng thái phiên Bàn làm việc.
- Cấu hình và đường dẫn: [`core/config.py`](../../app/backend/src/lessonai/core/config.py), mẫu biến môi trường ở [`infra/env.example`](../../infra/env.example).
- Học liệu runtime: `app/backend/data/` (không được Git theo dõi, ADR 0012).

## Tìm theo triệu chứng

| Thấy gì | Mở trước tiên |
| --- | --- |
| API trả 4xx/5xx sai | `api/routes/<tên>.py`, rồi `main.py` cho vỏ lỗi dùng chung |
| AI trả nội dung lệch dàn ý | `services/generation/`, đặc biệt `outline_contract.py` |
| AI gọi sai nhà cung cấp, hết thời gian chờ | `llm/gateway.py`; vết chạy ở `llm/tracing.py` |
| Bài bị chặn khi kiểm tra | `services/quality/content_quality.py`, `lesson_quality.py`, `validation.py` |
| Nhãn "Đã xác nhận chuyên môn" mất hoặc không ký được | `services/quality/expert_confirmation.py` + `core/signing.py` |
| Hình không hiện, hoặc báo chưa xác nhận dữ kiện | `services/quality/visual_requirements.py` |
| Đồ thị/BBT/3D vẽ sai | `services/visuals/` (`graph_generator`, `geometry_scene`, `workbench_visuals`) |
| Công thức ra ảnh sai hoặc lỗi render | `services/visuals/latex_render.py` |
| Cổng toán trả `unverified` ngoài mong đợi | `services/math/math_worker.py`, hợp đồng ở `services/math/math_spec.py` |
| Tác vụ toán treo hoặc bị kill | `services/jobs.py` (tiến trình `spawn` có trần tài nguyên) |
| Tải tệp Office lên bị từ chối | `services/uploads.py` + `core/ingress.py` (trần 16 MiB) |
| DOCX/PPTX/ZIP xuất ra sai | `exporters/` |
| Nhập công thức từ DOCX/PPTX bị mất | `parsers/office_math.py` |
| Truy xuất học liệu trả rỗng | `rag/curriculum_registry.py` (nguồn chưa được người duyệt) |
| Giao diện Bàn làm việc | `app/frontend/src/features/workbench/` |

## Backend: tầng và luật import

```text
api | tooling  →  exporters  →  services  →  llm | rag | parsers | prompts  →  schemas  →  core | utils
```

Mũi tên nghĩa là "được phép import". `make lint` cưỡng chế bằng hợp đồng
`[tool.importlinter]` trong [`app/backend/pyproject.toml`](../../app/backend/pyproject.toml);
mọi import đi ngược chiều làm CI đỏ.

Hai điều dễ gây ngạc nhiên, nên ghi rõ:

- `exporters` nằm **trên** `services` vì một bộ xuất phải chạy cổng chất lượng và
  vẽ hình trước khi ghi tệp. Nó dùng `services`, không phải ngược lại.
- `core` chỉ chứa phần không phụ thuộc nghiệp vụ. Vì vậy `jobs.py` nằm ở
  `services/`, không ở `core/`: nó nạp worker của `services`.

Hợp đồng còn **đúng một** dòng `ignore_imports`:
`schemas.schemas -> rag.curriculum_registry`, do validator của `LessonRequest` và
`OutlineRequest` gọi `infer_lesson_id`. Bỏ nó là đổi hành vi phân tích request,
nên để thành việc riêng. Không thêm dòng mới vào đó mà chưa được duyệt.

## Backend: từng thư mục

`app/backend/src/lessonai/`

| Thư mục | Chịu trách nhiệm |
| --- | --- |
| `api/routes/` | 14 router: `chat`, `curriculum`, `exports`, `geometry` (chặn 410), `ingest`, `lesson_plan`, `math_spec`, `presentation`, `quality`, `slides`, `system`, `validation`, `visuals`, `web`. Route chỉ nhận yêu cầu, gọi service, trả JSON hoặc tệp. |
| `services/generation/` | Sinh nội dung: `lesson_plan`, `outline`, `outline_contract`, `slides` và bốn bản `workbench_*` của Bàn làm việc. |
| `services/quality/` | Cổng nhận nội dung: `content_quality`, `lesson_quality`, `validation` (cấu trúc 5512), `visual_requirements`, `expert_confirmation`, `workbench_quality`, `acceptance.check_deck` (lối vào dùng chung cho route và bộ xuất), `artifact_provenance`, `content_blocks`. |
| `services/visuals/` | Dựng hình: `graph_generator`, `latex_render`, `geometry_scene` (khối đa diện + Oxyz), `workbench_visuals`, `rendering`. |
| `services/math/` | Cổng toán: `math_expression` (AST có ngân sách, không bao giờ `eval`), `math_worker` (chứng minh SymPy trong tiến trình con), `math_spec` (hợp đồng `POST /api/v1/math-spec/verify`). |
| `services/assistant/` | Trợ giảng AI: `copilot`, `workbench_assistant`. Chỉ đề xuất, giáo viên quyết định. |
| `services/` (đứng riêng) | `jobs.py` chạy worker `spawn`; `uploads.py` giới hạn tài nguyên khi đọc tệp tải lên; `analytics.py` phân tích bảng điểm. |
| `llm/` | `gateway.py` định tuyến Gemini/Groq/OpenRouter; `tracing.py` phát span Langfuse v5. |
| `rag/` | `curriculum_registry`, `retriever`, `content_units`, `context_builder`. Đang tạm ngừng trong luồng tạo bài. |
| `prompts/` | `lesson_plan`, `roles`, `slides`, `validation`. |
| `parsers/` | `docx_parser`, `pptx_parser`, `common`, `office_math` (trích công thức OMML). |
| `exporters/` | `docx_exporter`, `slide_exporter`, `dual_package_exporter`. |
| `schemas/` | Hợp đồng Pydantic v2: `schemas`, `slide_schema`, `chain_schemas`, `content_blocks`, `lesson_review`, `math_spec_schema`, `provenance`, `workbench_outline`, `workbench_slides`. |
| `core/` | `config`, `ingress`, `ownership`, `render_runtime` (khóa Matplotlib chung), `signing` (khóa xác nhận), `hashing`, `feature_availability`. |
| `utils/` | `temp_file_cleaner`, `xml_text.clean_xml_string` (hai bộ xuất và `latex_render` dùng chung). |
| `tooling/` | Công cụ chạy ngoài tiến trình phục vụ: `deck_lint`, `manifest_corpus_check`, `rag_question_triage`, `retrieval_fixture`, `retrieval_fixture_runner`, `slide_remediation`. Chỉ `scripts/` và bộ kiểm thử dùng; mã lúc chạy không bao giờ import, và luật tầng cưỡng chế điều đó. |

Import nội bộ luôn dùng tên package `lessonai`. Không thêm `sys.path` trong module
hay `scripts/`. Cài editable một lần:

```bash
app/backend/venv/bin/python -m pip install --no-deps -e app/backend
```

`src/main.py` giữ tương thích cho lệnh cũ `uvicorn main:app --app-dir src`.

## Frontend

Từ `#59`, Bàn làm việc là giao diện duy nhất. Đo theo chuỗi import từ `main.jsx`:

| Thư mục trong `src/features/` | Trạng thái |
| --- | --- |
| `workbench/` | Giao diện đang chạy: 3 cột, Canvas `1600 × 900`, Trình chiếu, Đồ thị/BBT/3D, Trợ giảng AI, KHBD 5512, font WOFF đóng gói |
| `lesson-plan/`, `analytics/` | Còn một phần tiếp cận được |
| `chat/`, `exports/`, `generation/`, `geometry/`, `presentation/` | **Mồ côi** từ `#59` — không còn đường import nào từ `main.jsx` |

21 tệp mồ côi (3.187 dòng) chưa xóa: cần chủ dự án xác nhận phần nào sẽ được nối
lại vào Bàn làm việc. Trước khi dựa vào một tệp ở đây, kiểm tra nó có tiếp cận
được không.

`src/shared/` giữ phần nhiều chỗ dùng: `api/client.js` (mọi POST JSON đi qua
`postJson` để cookie chủ phiên được khởi tạo), `storage/projectStore.js` (IndexedDB,
giữ bản ghi bản 2), `storage/lessonProject.js` (Bài giảng bản 3 và
`convertLegacyProjectToV3`), `math/`, `validation/`, `components/`.

Trạng thái bài giảng, slide đang chọn, tham số 3D và chế độ trình chiếu nằm trong
`App.jsx`; action nhận giá trị và hàm cập nhật từ đó. **Không tạo bản trạng thái
thứ hai trong `src/features/*`** — tách trạng thái là quyết định thiết kế còn mở.

## Dữ liệu

| Đường dẫn | Git theo dõi | Nội dung |
| --- | --- | --- |
| `data/fixtures/` | Có | `golden_set.json`, `math12_benchmark_suite.json` |
| `data/raw/`, `data/processed/` | Không | Học liệu nguồn và đầu ra pipeline |
| `app/backend/data/` | Không | Dữ liệu runtime ứng dụng đọc: chương trình, corpus, `reviewed_sources.json` |
| `app/backend/output/` | Không | Vùng làm việc khi xuất tệp |
| `docs/requirements/` | Không | Hồ sơ yêu cầu bản gốc |
| `reports/` | Chỉ thư mục được ADR hoặc issue dẫn chiếu | Bằng chứng bất biến — **không bao giờ ghi đè** |

Chính sách track nằm ở [ADR 0012](../adr/0012-track-mac-dinh-chan-noi-dung-rieng-tu.md).
Dùng `git ls-files` để biết một checkout thật có gì. Ứng dụng không đọc dự phòng từ
`data/raw`. Đường dẫn runtime đổi bằng `LESSONAI_DATA_DIR`, `LESSONAI_OUTPUT_DIR`,
`LESSONAI_CONFIG_DIR`; dùng đường dẫn tuyệt đối.

`scripts/data/build_packaged_data.py` và `scripts/quality/prepare-source-review.py`
từ chối ghi vào đường dẫn đã tồn tại — truyền một đường dẫn `/tmp/` mới mỗi lần.
Kết quả staging không tự ghi đè dữ liệu runtime.

## Phân vùng repo

- `app/` — mã nguồn: backend FastAPI và frontend React 19 + Vite.
- `docs/` — `adr/` (quyết định), `agents/`, `architecture/`, `design/`, `rag/`.
- `project-management/` — `PROGRESS.md`, `decisions/`, `release-gates/`, `phases/` (lịch sử).
- `reports/` — bằng chứng thực nghiệm, bất biến theo thời điểm tạo.
- `data/` — fixtures được theo dõi và kho dữ liệu gốc cục bộ.
- `scripts/` — `data/` (kiểm kê, đóng gói, làm giàu) và `quality/` (benchmark, duyệt nguồn, triage RAG, đo độ trễ).
- `infra/` — hướng dẫn triển khai và `env.example`.
- `GLOSSARY.md` — thuật ngữ miền; đọc trước khi đặt tên mới.

Báo cáo và tài liệu trong `phases/` mô tả đường dẫn ở thời điểm viết. Tài liệu này
là bản hiện hành.

## Kiểm tra thay đổi

Từ thư mục gốc repo:

```bash
make lint            # luật tầng
make test-backend    # pytest, tự làm rỗng 3 API key và ký bằng khóa tạm
make test-frontend   # node --test
make build           # Vite build
```

`make test` chạy cả hai bộ test. Đổi Python bằng `make test-backend PYTHON=python`;
thêm cờ pytest bằng `PYTEST_ARGS`. Bốn ca retriever cần corpus thật mang marker
`corpus_integration`; CI bỏ chúng bằng `-m 'not corpus_integration'`.

E2E và benchmark không có target Makefile — xem mục Common Commands của
[`AGENTS.md`](../../AGENTS.md).

[CI](../../.github/workflows/ci.yml) chạy lint rồi backend trên Python 3.13, và
test frontend rồi build trên Node 26.

## Chặn tạm còn hiệu lực

[`core/feature_availability.py`](../../app/backend/src/lessonai/core/feature_availability.py)
giữ thông điệp và ngoại lệ cho phần xử lý biểu thức bị tạm ngắt. Hai nửa của nó
hiện ở trạng thái khác nhau, nên đọc kỹ:

- Vẽ đồ thị **đã bật lại**: `expression_chart_is_disabled()` trong
  `services/visuals/graph_generator.py` trả `False`, và `services/math/` đã có
  parser giới hạn tài nguyên thay cho đường cũ.
- Kiểm định đại số từ LaTeX **vẫn tắt**: `latex_to_sympy_expr()` trong
  `services/quality/validation.py` trả `None`, nên audit báo `algebra_unverified`.
  Không có cờ bật lại parser cũ; đường đúng là nối qua `services/math/`.

`core/render_runtime.py` giữ một khóa Matplotlib dùng chung cho cả đồ thị và công
thức. Renderer đóng figure của chính job trong `finally`, không đóng figure của
request khác. `services/visuals/rendering.py` bỏ ảnh cache cũ khi enrich.

RAG rỗng tới khi người duyệt xong: `reviewed_sources.json` có `"sources": []`, nên
`/api/v1/curriculum/math12` và truy xuất đều trả ngữ cảnh rỗng. Đây là trạng thái
mong đợi, không phải lỗi.
