# AGENTS.md — AI Agent Working Handbook (`LessonAI-5512`)

## 1. Project Overview
`LessonAI-5512` is a local, single-process teaching studio for Vietnamese high school teachers (Grade 12 Mathematics, GDPT 2018 / Công văn 5512) to author, edit, validate, present, and export lesson plans and slide decks (`DOCX`, `PPTX`, and synchronized dual-package `ZIP`). AI outputs are treated strictly as unverified drafts requiring explicit teacher review and confirmation. The system enforces a zero-fallback policy: when AI providers, parsers, or exporters fail, it returns structured errors and preserves the teacher's active draft rather than injecting sample lessons or default visuals.

## 2. Tech Stack & Versions
- **Backend (`app/backend/pyproject.toml`, `app/backend/requirements.txt`):** Python `>=3.11` (CI/venv runs `3.13`), `lessonai-backend` `0.2.0`, FastAPI `>=0.100.0`, Uvicorn `>=0.20.0`, Pydantic `>=2.0.0`, SymPy `>=1.13.0`, NumPy `>=2.0.0`, Matplotlib `>=3.10.0`, `python-docx` `>=1.0.0`, `python-pptx` `>=0.6.21`, `latex2mathml` `>=3.80.0`, `mathml2omml` `>=0.0.2`, `openpyxl` `>=3.1.0`, `pillow` `>=13.0.0`, `google-genai` `>=0.1.0`, `openai` `>=1.50.0`, `httpx` `>=0.27.0`, `python-dotenv` `>=1.0.0`, `python-multipart` `>=0.0.9`, `packaging` `>=25.0`, security floors `certifi>=2026.10.18`, `pyasn1>=0.6.5`, `urllib3>=2.8.0`. *(See `app/backend/requirements-lock.txt` for exact pinned versions).*
- **Frontend (`app/frontend/package.json`):** Node.js `22` (CI), React `^19.0.0`, React DOM `^19.0.0`, Vite `^6.0.0`, `@vitejs/plugin-react` `^4.3.4`, Tailwind CSS `^3.4.15`, PostCSS `^8.4.49`, Autoprefixer `^10.4.20`, Three.js `^0.170.0`, MathLive `0.111.4`, KaTeX `^0.18.10`, Lucide React `^0.460.0`. *(See `app/frontend/package-lock.json` for exact pinned versions).*
- **Testing:** `pytest` `>=8.0.0` (`app/backend/requirements.txt`), Node.js native test runner (`node --test`), Playwright `1.64.1` (`app/frontend/package.json`).
- **Storage:** Client-side browser `IndexedDB` (`lessonai-projects`, `schema_version: 2`) + JSON backup files; server-side in-memory owner session/copilot state + local filesystem corpus (`app/backend/data` or `LESSONAI_DATA_DIR`).

## 3. Directory Structure
```text
.
├── Makefile                        # Root automation commands (dev, test, build, audit, data)
├── .claude/skills/                 # Modular agent skills (<skill-name>/SKILL.md)
├── app/
│   ├── backend/
│   │   ├── pyproject.toml          # Package metadata (`lessonai-backend`) & pytest config
│   │   ├── requirements-lock.txt   # Locked Python dependencies for reproducible installs
│   │   ├── data/                   # Tracked runtime curriculum, RAG corpus, reviewed_sources.json
│   │   ├── src/lessonai/           # Main Python package (`import lessonai.*`)
│   │   │   ├── main.py             # FastAPI app factory, CORS, local origin & error middlewares
│   │   │   ├── core/               # config.py, ingress.py (16 MiB limit), jobs.py (spawn workers), ownership.py, render_runtime.py
│   │   │   ├── api/routes/         # HTTP route handlers (chat, curriculum, exports, geometry, ingest, lesson_plan, presentation, quality, slides, system, validation, visuals, web)
│   │   │   ├── services/           # Business logic, generation/, math_expression.py, math_worker.py, geometry_scene.py, visual_requirements.py, content_quality.py, copilot.py, deck_lint.py
│   │   │   ├── llm/gateway.py      # Multi-provider LLM router (Gemini, Groq, OpenRouter) with auto-fallback
│   │   │   ├── rag/                # CurriculumRegistry, Math12HybridRetriever, content_units.py, context_builder.py
│   │   │   ├── parsers/ & exporters/# DOCX/PPTX ingestion and DOCX/PPTX/Dual-ZIP export pipelines
│   │   │   ├── schemas/ & prompts/ # Pydantic v2 contracts and system prompts
│   │   │   └── templates/          # PowerPoint base templates (`template_5512.pptx`, `manifest.json`)
│   │   └── tests/                  # Pytest suite + `fixtures/api_contract.json`
│   └── frontend/
│       ├── src/App.jsx             # Top-level studio state container and screen router
│       ├── src/features/           # Feature slices: dashboard, generation, lesson-plan, slide-editor, presentation, geometry, chat, analytics, exports
│       ├── src/shared/             # api/client.js, storage/projectStore.js, math/, validation/, components/
│       ├── tests/                  # Node unit/contract tests (`*.test.js`)
│       └── e2e/                    # Playwright real-backend browser tests (`workflows.spec.js`)
├── scripts/                        # `data/` (packaging/inventory) and `quality/` (lint, probes, source review)
├── docs/                           # Architecture (`repository.md`, `decisions.md`), requirements, and remediation plans
└── reports/                        # Audit logs, remediation implementation reports, and test evidence
```

## 4. Common Commands
All commands run from the repository root unless noted (sourced from `Makefile`, `README.md`, `.github/workflows/ci.yml`):
- **Install environment:**
  ```bash
  python3.13 -m venv app/backend/venv
  app/backend/venv/bin/python -m pip install -r app/backend/requirements-lock.txt
  app/backend/venv/bin/python -m pip install --no-deps -e app/backend
  npm --prefix app/frontend ci
  ```
- **Run dev servers:**
  - Backend (`http://127.0.0.1:8000`): `make backend`
  - Frontend (`http://127.0.0.1:5173`, proxies `/api` to `:8000`): `make frontend`
- **Build frontend:** `make build` (`npm --prefix app/frontend run build`)
- **Run tests:**
  - Full unit/integration suite (backend + frontend): `make test` (`make test-backend` + `make test-frontend`)
  - Portable backend suite (no local untracked corpus required): `make test-portable`
  - Release-blocking critical regressions: `make test-critical` (`make test-critical-backend` + `make test-critical-frontend`)
  - Single backend test file/function: `GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_package_contract.py -k "test_name"`
  - Single frontend test file: `node --test app/frontend/tests/critical-regressions.test.js`
  - End-to-end Playwright suite: `make test-e2e` (or if port 8000 is busy: `LESSONAI_TEST_PORT=18080 npm --prefix app/frontend run test:e2e`)
- **Lint, inventory & acceptance probes:**
  - Lint slide deck corpus: `make lint-data`
  - Run data inventory: `make inventory`
  - Prepare RAG review list: `make prepare-source-review REVIEW_OUTPUT=/tmp/lessonai-review-unique`
  - Run baseline / acceptance probes: `make audit-baseline REVIEW_OUTPUT=/tmp/lessonai-base-unique` and `make audit-acceptance REVIEW_OUTPUT=/tmp/lessonai-acceptance-unique`
- **Database migrations:** No server-side SQL database. Client projects use `IndexedDB` (`lessonai-projects`, `schema_version: 2`) with automatic one-time migration from `sessionStorage` (`lessonai_slide_deck_json_v1`) in `app/frontend/src/shared/storage/projectStore.js`.

## 5. Code Conventions
- **Package imports:** Always import backend modules via `lessonai.*` (e.g., `from lessonai.core.config import DATA_DIR`). Never mutate `sys.path` in application code or `scripts/`.
- **Layering:** Backend follows `api/routes -> services -> llm / rag / parsers / exporters -> schemas`. Frontend keeps shared deck/slide/3D/presentation state in `app/frontend/src/App.jsx` and passes state + updater callbacks into feature actions; do not create a second state store inside `src/features/*`.
- **Error contract:** Backend errors return `{"detail": {"code": "<snake_case>", "message": "<Vietnamese user message>", "request_id": "<uuid>"}}` with header `X-Request-ID`.
- **Safe math execution:** Never use `eval()` or `new Function()` in Python or JS. Expressions must be parsed via `lessonai/services/math_expression.py` (`ExpressionBudget`) and evaluated inside bounded `spawn` subprocesses (`lessonai/core/jobs.py` -> `lessonai/services/math_worker.py`).
- **Deterministic tests:** Always clear `GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY=` when running pytest so tests never hit live external LLM APIs.

## 6. Workflow & Git Conventions
- **Branching (`CONTRIBUTING.md`):** Use `feature/<name>` or `fix/<name>`.
- **Commits:** Follow Conventional Commits (`feat(scope): ...`, `fix(scope): ...`, `refactor(scope): ...`, `test(scope): ...`, `docs: ...`). Commit descriptions in history are predominantly written in Vietnamese.
- **Pre-PR verification:** Run `make test-portable`, `make test-critical`, `make test-frontend`, `make build`, and `make test-e2e`.

## 7. Boundaries
- ✅ **Always do:** Preserve the teacher's active draft on any error; require `Depends(require_owner)` on stateful/mutating session endpoints (`/api/v1/chat`, `/api/v1/quality`, `/api/v1/visuals`); pass `postJson` from `app/frontend/src/shared/api/client.js` so owner cookies are initialized; use a new `REVIEW_OUTPUT` path for every probe/review run.
- ⚠️ **Ask first:** Modifying OpenAPI routes/schemas locked in `app/backend/tests/fixtures/api_contract.json`; bumping `schema_version` in `projectStore.js`; adding Python/npm dependencies; editing `.github/workflows/ci.yml`; changing upload/worker resource limits in `ingress.py`, `jobs.py`, or `uploads.py`.
- 🚫 **Never do:** Commit `.env` or API keys; bulk-set `"status": "approved"` in `reviewed_sources.json` without human review; re-enable retired `410 Gone` sample/geometry endpoints (`/api/v1/rag/preview`, `/api/v1/geometry/*`, `/api/v1/test-cases`); inject fallback sample lessons or transparent placeholder pixels when rendering fails; overwrite existing evidence files in `reports/`.

## 8. Gotchas
- **`.env` path:** Backend loads `app/backend/.env` (`BACKEND_DIR / ".env"` in `lessonai/core/config.py`), NOT a root `.env`.
- **Ephemeral signing keys & sessions:** Owner sessions (`ownership.py`), visual confirmation tokens (`visual_requirements.py`), and deck approval tokens (`quality.py`) use in-memory keys with a 24h TTL. Restarting the backend invalidates all active tokens, requiring the teacher to re-confirm visuals/deck quality.
- **Exclusive file creation (`open('x')`):** `prepare-source-review.py`, `project-review-probes.py`, and `build_packaged_data.py` intentionally fail if the output file/folder already exists. Always pass a fresh path in `/tmp/`.
- **Unsaved slide edits lock navigation:** `SlideEditorScreen.jsx` blocks switching slides, changing screens, or exporting while form edits are dirty; changes must be saved first.
- **Explicit keyword unpacking in route handlers:** `lesson_plan.py`, `presentation.py`, and `slides.py` unpack request attributes manually (`topic=req.topic, ...`) rather than passing `req` directly; adding a field to `LessonRequest` or `OutlineRequest` requires passing it explicitly in the route, `services/generation/*.py`, and `app/frontend/src/features/generation/lessonGenerationActions.js`.
- **Slide field fingerprinting & math scanning:** When adding a field to `SlideSchema` or `SlideDeckSchema`: (a) if it is a derived/ephemeral render field, add it to the ignore list in both `lessonai/services/content_quality.py:content_snapshot()` and `app/frontend/src/shared/storage/projectStore.js:mutateDeck()`; (b) if it is authored math/problem text, add it to `math_fields()` in `content_quality.py` and `SOURCE_FIELDS` in `lessonai/services/visual_requirements.py`.
