# DECISIONS.md — Architectural Decision Records (`LessonAI-5512`)

## ADR-001: Modular Monolith with Editable `lessonai` Python Package and Feature-Sliced React 19 Frontend
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** Early iterations placed backend scripts and frontend components in flat or loosely coupled directories requiring manual `sys.path` manipulation and making API contract testing across working directories brittle.
- **Decision (Quyết định):** Package the backend as an installable setuptools distribution (`lessonai-backend` under `app/backend/src/lessonai`) imported strictly via `lessonai.*`, and organize the React 19 + Vite frontend into feature slices (`app/frontend/src/features/*`) with centralized top-level state in `app/frontend/src/App.jsx` and shared utilities in `app/frontend/src/shared/*`.
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/pyproject.toml:12-25, app/backend/tests/test_package_contract.py:1 & 13-35, commits 46ec1a8 & fc26ce2]`: Protects public API and resource locations across internal refactors and guarantees `import lessonai` works outside the checkout without `sys.path`.
  - `[TRONG REPO - Loại (b) tài liệu người viết: CONTRIBUTING.md:58-60]`: Instructs contributors to install `./app/backend` in editable mode and import `lessonai` without modifying `sys.path`.
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (docs/architecture/repository.md:31-35)]` -> `TODO(confirm): Confirm whether keeping shared deck/slide/3D state exclusively in App.jsx (without a separate state store inside src/features/*) is a permanent architectural rule.`
- **Alternatives Considered (Phương án thay thế):** Flat `app/backend` scripts with `sys.path.append` (used prior to commits `46ec1a8` and `fc26ce2`); per-feature independent state stores on the frontend (rejected in `docs/architecture/repository.md`).
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Developers and CI must run `pip install --no-deps -e ./app/backend` once when setting up the virtual environment; `App.jsx` remains the single state orchestrator and passes action callbacks down to feature screens.
- **Evidence (Bằng chứng):** Commits `46ec1a8`, `aa738a2`, `fc26ce2`; `app/backend/pyproject.toml`; `docs/architecture/repository.md`; `app/backend/tests/test_package_contract.py`.

---

## ADR-002: Local Single-Process Deployment Model with Cookie Ownership and Browser IndexedDB Storage
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** Teachers need a responsive, low-setup authoring and presentation tool that works offline/locally without requiring external database servers or complex cloud deployment infrastructure.
- **Decision (Quyết định):** Run the backend as a single local FastAPI process bound to `127.0.0.1` (`Makefile`, `main.py`), enforce strict localhost CORS/Origin checks (`local_boundary` middleware), isolate local browser sessions via an `httponly` cookie (`lessonai_owner` in `lessonai/core/ownership.py`), and persist projects (`schema_version: 2`) in browser `IndexedDB` (`lessonai-projects` in `app/frontend/src/shared/storage/projectStore.js`) with JSON file export/import for backup.
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/core/ownership.py:1 & 12-35, app/frontend/src/shared/storage/projectStore.js:1, 22-54 & 80-95, app/backend/src/lessonai/services/copilot.py:1 & 109-138]`: Code comments and implementation enforce durable client-side project envelopes (`schema_version: 2`), preserve legacy `sessionStorage` bytes during migration (`projectStore.js:90`), and scope Copilot proposals to single-process local owner cookies (`ownership.py:1`: `"Single-process local ownership. No claim of multi-user authentication."`).
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (uncommitted README.md:55-58, reports/remediation-implementation-2026-11-03.md:23-26) & thiếu vắng DB server trong requirements.txt]` -> `TODO(confirm): Confirm whether browser IndexedDB + in-memory server session was chosen to keep LessonAI-5512 a zero-DB local single-teacher app permanently, or if server-side persistence and multi-user authentication are planned after M5.`
- **Alternatives Considered (Phương án thay thế):** Legacy `sessionStorage` key `lessonai_slide_deck_json_v1` (superseded by IndexedDB in M2 with automatic one-time migration in `restoreProject()`); full multi-user server authentication and server-side RDBMS.
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Clearing browser site data deletes local IndexedDB projects unless exported to JSON; restarting the backend process clears in-memory owner sessions (`_owners`), Copilot chat history (`copilot.py`), and ephemeral HMAC signing keys (`quality.py`, `visual_requirements.py`).
- **Evidence (Bằng chứng):** `README.md` (lines 54–58); `app/backend/src/lessonai/main.py`; `app/backend/src/lessonai/core/ownership.py`; `app/frontend/src/shared/storage/projectStore.js`.

---

## ADR-003: Multi-Provider LLM Gateway with Auto-Fallback, Dead-Model Blacklisting, and LaTeX JSON Sanitization
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** Relying on a single LLM provider or model leads to single points of failure (HTTP 429 rate limits, 5xx outages, deprecated/404 models), and LLMs frequently emit unescaped LaTeX backslashes (e.g., `\sqrt`, `\frac`) or `<think>...</think>` blocks that break strict `json.loads()` and Pydantic v2 validation.
- **Decision (Quyết định):** Route all AI generation, validation, and Copilot calls through `LLMGateway` (`app/backend/src/lessonai/llm/gateway.py`), supporting Google Gemini (`google-genai`), Groq (`openai` client), and OpenRouter with automatic provider/model fallback, exponential backoff on HTTP 429 (`4s -> 8s`), session-level blacklisting of dead (404) models (`_dead_models`), and pre-parse regex sanitization (`fix_latex_backslashes`, `strip_markdown_json_fence`).
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/llm/gateway.py:1-10, 43-70 & 110-111, commits ddc9766 & 21377d4]`: Eliminates single points of failure (Zero SPOF) across providers, handles HTTP 429 / `RESOURCE_EXHAUSTED` via exponential backoff (`4s -> 8s`), blacklists deprecated/404 models in-session (`_dead_models`), and prevents single-backslash LaTeX commands (`\sqrt`, `\frac`) or `<think>...</think>` blocks from breaking `json.loads()` and Pydantic v2 validation.
- **Alternatives Considered (Phương án thay thế):** Direct single-provider SDK calls inside route handlers (superseded in commits `ddc9766` and `21377d4`).
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Adds gateway routing complexity and retry latency when a primary provider is rate-limited; `_LATEX_CMDS` regex in `gateway.py` must be maintained if new LaTeX macros collide with JSON escape characters (`\b`, `\f`, `\n`, `\r`, `\t`).
- **Evidence (Bằng chứng):** Commits `ddc9766`, `695000`, `cf1b169`, `21377d4`; `app/backend/src/lessonai/llm/gateway.py`; `app/backend/tests/test_gateway_model_routing.py`.

---

## ADR-004: Zero-Fallback Content Policy and Retirement of Sample/Preset Endpoints (`410 Gone`)
- **Status (Trạng thái):** Accepted (Supersedes early Phase 4 / M0 sample fallback behavior)
- **Context (Bối cảnh):** Earlier versions returned pre-built sample lessons, fallback outlines, default parabolas/polyhedra, or mock grade sheets when LLM calls, math parsers, or exports failed. In a real teaching tool, silently substituting sample content misleads teachers and risks presenting unverified or unrelated material in class.
- **Decision (Quyết định):** Treat all AI outputs strictly as drafts requiring verification, never inject sample/fallback lessons or default visuals on error, preserve the teacher's active draft when any operation fails, and retire legacy sample/unverified endpoints (`POST /api/v1/rag/preview` in `curriculum.py`, `/api/v1/geometry/*` in `geometry.py`, and `/api/v1/test-cases`) with HTTP `410 Gone` or removal.
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/main.py:70, app/backend/src/lessonai/api/routes/curriculum.py:48-50, app/backend/src/lessonai/api/routes/geometry.py:1-10, app/backend/tests/test_critical_regressions.py:1-120]`: Code docstrings and error handlers explicitly retire unverified geometry/sample endpoints (`geometry.py:1`: `"Legacy unsourced geometry endpoints retired in favor of confirmed scene specs"`, `curriculum.py:50`: `"The sample browser was removed from the production authoring workflow"`) and preserve the active draft on error (`main.py:70`).
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (uncommitted README.md:3 & 84, reports/remediation-implementation-2026-11-03.md:30-31 & 47-49, docs/plans/remediation-acceptance-2026-11-03.md:9-10)]` -> `TODO(confirm): Confirm that the zero-fallback policy (never returning sample lessons or default visuals even in demo/offline mode) is final for production release.`
- **Alternatives Considered (Phương án thay thế):** Returning static fallback lessons (`services/generation/fallback.py` / sample fixtures) when LLM keys are missing or providers fail (superseded during the November 2026 remediation).
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** AI generation requires a valid `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY` in `app/backend/.env` (though manual authoring, saving, math checking, geometry building, and exporting work completely offline without API keys).
- **Evidence (Bằng chứng):** `README.md` (lines 3, 28, 84); `app/backend/src/lessonai/api/routes/curriculum.py` (line 48); `app/backend/src/lessonai/api/routes/geometry.py`; `app/backend/tests/test_critical_regressions.py`; `reports/remediation-implementation-2026-11-03.md`.

---

## ADR-005: Bounded AST Math Parser and Killable `spawn` Worker Subprocesses
- **Status (Trạng thái):** Accepted (Supersedes direct in-process `eval` / unrestricted `sympy` parsing)
- **Context (Bối cảnh):** Parsing arbitrary user- or LLM-supplied mathematical strings directly in the main FastAPI process via `eval()` or unconstrained symbolic solvers exposes the server to code execution, ReDoS, memory exhaustion, and hung worker threads.
- **Decision (Quyết định):** Parse all mathematical expressions first with a pure-Python bounded AST parser (`lessonai/services/math_expression.py` enforcing `ExpressionBudget`: max length `2048`, max tokens `512`, max nodes `256`, max depth `32`, max integer power `100`, whitelist functions `sin, cos, tan, log, exp, sqrt, Abs`) and execute symbolic/domain analysis and Office ingestion inside isolated `multiprocessing` `spawn` workers (`lessonai/core/jobs.py` -> `lessonai/services/math_worker.py` / `uploads.py`) with hard deadlines and Linux `resource` limits (`RLIMIT_AS=1.5 GiB`, `RLIMIT_CPU=20s`).
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/services/math_expression.py:1-6, app/backend/src/lessonai/core/jobs.py:1 & 15-20, scripts/quality/spike_gates.py:1-10, app/frontend/tests/critical-regressions.test.js:1-20]`: Module docstrings and tests explicitly require producing data-only ASTs (never executable Python/SymPy on import), keeping division/root nodes to preserve excluded domain points (`math_expression.py:3-5`), and bounding worker memory/CPU/wall-time (`jobs.py:15-20`).
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (docs/architecture/decisions.md:56-68, docs/plans/remediation-acceptance-2026-11-03.md:30 & 50)]` -> `TODO(confirm): Confirm whether the current ExpressionBudget ceilings (max_nodes=256, max_integer_power=100, Linux RLIMIT_AS=1.5 GiB, RLIMIT_CPU=20s) are the final production thresholds.`
- **Alternatives Considered (Phương án thay thế):** Temporary M0 feature kill-switch (`lessonai/core/feature_availability.py` returning `None` / `algebra_unverified`), and unrestricted in-process SymPy parsing.
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Expressions outside the supported grammar (`FUNCTIONS = {"sin", "cos", "tan", "log", "exp", "sqrt", "Abs"}`) are rejected with `expression_invalid` or marked unverified; spawning subprocesses adds a small per-job overhead mitigated by bounded concurrency (`concurrency=2, capacity=10`).
- **Evidence (Bằng chứng):** `app/backend/src/lessonai/services/math_expression.py`; `app/backend/src/lessonai/services/math_worker.py`; `app/backend/src/lessonai/core/jobs.py`; `docs/architecture/decisions.md` (Gate G2); `app/backend/tests/test_remediation_runtime.py`.

---

## ADR-006: Hybrid Curriculum Ingestion and Hash-Locked Whole-Unit RAG Approval (`reviewed_sources.json`)
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** The Grade 12 Math (GDPT 2018 - KNTT) corpus (`1,847` slides from 32 `pdf2xml` files and `894` questions) contains OCR/layout fragmentation (`71.36%` of raw slides fail strict structural lint in `docs/architecture/decisions.md`). Feeding unverified or arbitrarily chunked fragments into RAG risks injecting mathematical errors into generated lessons.
- **Decision (Quyết định):**
  1. Use Hybrid Ingestion (Gate G1 in `docs/architecture/decisions.md`): combine `pdf2xml` coordinate-reconstructed KNTT 12 slides, curated theorems, and question banks in `app/backend/data/`.
  2. Keep source units whole (`lessonai/rag/content_units.py`) and gate runtime RAG retrieval (`approved_units()`) behind `app/backend/data/reviewed_sources.json`, requiring an exact `sha256` match (`source_hash`), `status: "approved"`, `reviewer`, and `reviewed_at`.
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/rag/content_units.py:1 & 16-25, scripts/quality/prepare-source-review.py:1-2 & 21, commit 573f6c0]`: `content_units.py:1` explicitly mandates `"Keep source units whole. Only an explicit, hash-matched review enables reuse"`, and `prepare-source-review.py:21` states `"Lint sạch không chứng nhận đúng toán. Cần đối chiếu nguồn và giáo viên duyệt từng hash."`
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (docs/architecture/decisions.md:39-53 Gate G1, reports/remediation-implementation-2026-11-03.md:35)]` -> `TODO(confirm): Confirm the Gate G1 rationale that all 32 KNTT 12 source files on Google Drive only exist as .pdf (requiring pdf2xml reconstruction) and that no native .pptx source exists for CT 2018.`
- **Alternatives Considered (Phương án thay thế):** Unfiltered BM25 retrieval over the entire raw `slides_kntt12_cleaned.jsonl` corpus or fixed-token text chunking that splits problem statements from conditions/solutions.
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Until domain experts review and record approved hashes in `reviewed_sources.json` (currently `0 / 2,741` units approved as of `2026-11-04`), runtime RAG returns zero approved source units rather than leaking unverified content.
- **Evidence (Bằng chứng):** `docs/architecture/decisions.md` (Gate G1); `app/backend/src/lessonai/rag/content_units.py`; `app/backend/src/lessonai/rag/curriculum_registry.py`; `scripts/quality/prepare-source-review.py`.

---

## ADR-007: Hybrid Office Export Pipeline (300 DPI PNG + Alt-Text LaTeX for PPTX, OMML for DOCX, SHA-256 Dual-Package ZIP)
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** Spike Gate G3 (`docs/architecture/decisions.md`) demonstrated that `latex2mathml -> mathml2omml` produces semantic exponent-grouping bugs on parenthesized expressions (e.g., `-(x-1)^2`) and schema incompatibilities (`<a14:m>` vs `<w:rPr>`) across PowerPoint, LibreOffice Impress, and Keynote. Furthermore, teachers need synchronized lesson plans (`.docx`) and slide decks (`.pptx`) with verifiable integrity.
- **Decision (Quyết định):**
  1. In `slide_exporter.py` (`.pptx`), render complex LaTeX formulas via Matplotlib at 300 DPI PNG under a serialized render lock (`@serialized_render` in `lessonai/core/render_runtime.py`) while storing the raw LaTeX string in the shape's `alt-text` (`descr`), and place full step-by-step solutions on slide surfaces with automatic continuation slides instead of hiding them only in speaker notes.
  2. In `docx_exporter.py` (`.docx`), export Công văn 5512 lesson plans with native Word OMML (`latex2mathml` + `mathml2omml`) and explicit draft labeling.
  3. In `dual_package_exporter.py` (`.zip`), bundle synchronized `.docx` and `.pptx` files with a JSON manifest and SHA-256 checksum headers (`X-Dual-Package-SHA256`, `X-Docx-SHA256`, `X-Pptx-SHA256`).
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: scripts/quality/spike_gates.py:10-15, app/backend/src/lessonai/exporters/dual_package_exporter.py:1-40, app/backend/src/lessonai/api/routes/exports.py:93-121, commits f9b5bcc & 693eb29]`: Tracked spike script `spike_gates.py:14` documents that `latex2mathml -> mathml2omml` mis-attaches exponents on parenthesized expressions like `(x-1)^2` to `)` and lacks PowerPoint DrawingML `<a:rPr>` tags; commits `f9b5bcc` and `693eb29` implement SHA-256 dual-package ZIP verification and native/PNG hybrid PowerPoint export.
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (docs/architecture/decisions.md:72-81, reports/remediation-implementation-2026-11-03.md:43-45)]` -> `TODO(confirm): Confirm whether 300 DPI PNG + alt-text LaTeX in PPTX is permanently preferred over fixing PowerPoint DrawingML OMML (<a14:m>) generation.`
- **Alternatives Considered (Phương án thay thế):** Pure native OMML for PowerPoint slides (rejected in Gate G3 due to `<m:d>` parenthesis exponent bugs and Impress incompatibility); inserting 1x1 transparent PNG pixels when formula rendering failed (explicitly banned in M4 remediation).
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** PNG formulas in `.pptx` are not directly text-editable inside PowerPoint without re-exporting or reading the shape alt-text; very long tables/formulas still require layout tuning for M4 sign-off.
- **Evidence (Bằng chứng):** Commits `f9b5bcc`, `693eb29`; `docs/architecture/decisions.md` (Gate G3); `app/backend/src/lessonai/exporters/slide_exporter.py`; `app/backend/src/lessonai/exporters/docx_exporter.py`; `app/backend/src/lessonai/exporters/dual_package_exporter.py`.

---

## ADR-008: HMAC Token Binding for Teacher-Confirmed Visuals and Revision-Bound Quality Approval
- **Status (Trạng thái):** Accepted
- **Context (Bối cảnh):** An LLM or teacher may edit a slide's problem statement after a 2D graph or 3D polyhedron was generated, leaving a stale visual that contradicts the updated text. Similarly, automated math checks only cover a bounded grammar and cannot certify an entire lesson without human sign-off.
- **Decision (Quyết định):**
  1. Restrict 3D geometry to 3 canonical coordinate models (`cube`, `square_pyramid_regular`, `square_pyramid_at_a` in `lessonai/services/geometry_scene.py`) shared between WebGL (`ThreeCanvas.jsx`) and PPTX export.
  2. Require explicit teacher confirmation (`POST /api/v1/visuals/confirm` and `POST /api/v1/quality/approve`) that issues a 24-hour HMAC-SHA256 token (`requirement_token` / `review_token`) bound to the canonical hash of the slide/deck content (`lessonai/services/visual_requirements.py`, `lessonai/api/routes/quality.py`). Any subsequent content edit in `projectStore.js:mutateDeck()` automatically strips these tokens.
- **Rationale (Lý do):**
  - `[TRONG REPO - Loại (a) code/config/commit: app/backend/src/lessonai/services/visual_requirements.py:1 & 36-109, app/backend/src/lessonai/services/content_quality.py:1 & 109-114, app/backend/src/lessonai/services/geometry_scene.py:1 & 45-48, app/frontend/src/shared/storage/projectStore.js:37-52]`: Code comments and assertions explicitly state `"Server-signed confirmation of explicit teacher data, never an LLM boolean"` (`visual_requirements.py:1`), `"Content acceptance is distinct from JSON validity and render success"` (`content_quality.py:1`), `"New confirmation is explicit; ordinary content edits invalidate old tokens"` (`projectStore.js:37`), and verify 3D measurements directly from canonical vertex coordinates (`geometry_scene.py:45`).
  - `[SUY LUẬN - hạ từ nguồn Loại (c) tài liệu AI phiên trước (reports/remediation-implementation-2026-11-03.md:15-17 & 86) & in-memory _KEY = secrets.token_bytes(32) in quality.py:15 / visual_requirements.py:10]` -> `TODO(confirm): Confirm (1) whether restricting 3D geometry to 3 solids is permanent for v1.0, and (2) whether generating a fresh in-memory HMAC key on every backend restart is intentional or should be replaced by a persistent env secret.`
- **Alternatives Considered (Phương án thay thế):** Unverified client-side snapshots (`snapshot_3d_base64` global cache) or LLM self-certification of mathematical correctness.
- **Consequences / Trade-offs (Hệ quả/Đánh đổi):** Editing any slide text invalidates its visual confirmation and deck approval tokens, requiring the teacher to re-confirm before exporting a non-draft deck.
- **Evidence (Bằng chứng):** `app/backend/src/lessonai/services/visual_requirements.py`; `app/backend/src/lessonai/services/geometry_scene.py`; `app/backend/src/lessonai/api/routes/quality.py`; `app/frontend/src/shared/storage/projectStore.js` (lines 28–52).
