# AGENTS.md — AI Agent Working Handbook (`LessonAI-5512`)

> **Baseline:** branch `feat/multi-role-orchestrator`, code baseline `46e4ed2`, updated 2026-11-23.
> Anything marked **[VERIFY]** was carried over without being re-checked against the repo. Verify it before relying on it, and fix this file in the same PR when it is wrong.
> Run `git rev-parse --short HEAD` at the start of every session. The baseline identifies the code reviewed for this handbook. If HEAD differs, check the diff against the baseline, trust the current code, and report the drift.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for `nguyennhan18/lesson-plan-generator`. Before reading or publishing tickets through an engineering skill, consult `docs/agents/issue-tracker.md` if present in the local workspace.

### Triage labels

This repository uses the five canonical triage labels. Before classifying or labeling issues, consult the local `docs/agents/triage-labels.md` if present. Check the live repository labels before applying them.

### Domain docs

Single-context layout with root `GLOSSARY.md` and `docs/adr/`. Before exploring domain terminology or architectural decisions, read `GLOSSARY.md` and the relevant ADR. Consult `docs/agents/domain.md` if present in the local workspace.

## 1. Project Overview
`LessonAI-5512` is a local, single-process teaching studio for Vietnamese high school teachers (Grade 12 Mathematics, GDPT 2018 / Công văn 5512) to author, edit, validate, present, and export lesson plans and slide decks (`DOCX`, `PPTX`, and synchronized dual-package `ZIP`). AI outputs are unverified drafts that need explicit teacher review. The system enforces a **zero-fallback policy**: when AI providers, parsers, or exporters fail, it returns structured errors and preserves the teacher's active draft. It never injects sample lessons, fake images, or placeholder pixels.

## 2. Current Status and Milestones
- Handover is **not yet signed off**: M1–M4 are open, M5 is open. Green automated tests do not replace the human gates below.
- For versioned test evidence and open gates, see Current Status and Blockers in `project-management/PROGRESS.md`.
- Acceptance gate (5 points, local source: `project-management/release-gates/remediation-acceptance-2026-11-03.md`):

| Gate | Evidence required | Who can close it |
|---|---|---|
| Automated tests | Full-suite CI evidence for the release snapshot | Agent can show evidence; owner confirms |
| RAG source | `reviewed_sources.json` non-empty, reviewer record, `hash_version: 2` | **Human reviewer only** |
| Math expertise | Teacher sign-off on `math12_benchmark_suite.json` | **Human teacher only** |
| Device acceptance | Signed record from real projector + real Office | **Human only** |
| Docs/Repo | Clean working tree, `PROGRESS.md` matches HEAD | Agent can do; owner confirms |

- **Agents never mark a human-gated item PASS, never fill reviewer/sign-off fields on their own, and never close M1–M5.** Report it as `MISSING` with the evidence path that would be needed.

## 3. Session Protocol (read this first, every session)
1. One session = one task. Do only what the task prompt names. Record anything else under "Out-of-scope findings" and do not act on it.
2. Before editing: read this file, then the Current Status, Known Issues and Update Log sections of `project-management/PROGRESS.md`. Run `git status --short`, `git log --oneline -5`, `git rev-parse --short HEAD`.
3. State which files you will change and which you will not touch. If the prompt and the repo disagree, stop and ask.
4. If a task says "WAIT FOR CONFIRMATION", present the plan or design and stop until the owner replies.
5. Stop and ask if you need more than 15 files, a new dependency, a design decision, or if a failing test would only pass by changing product behavior.
6. Every "done" claim carries the command you ran and its real result. If you did not run it, say "not run". Never invent numbers.
7. Finish with a report: task and verdict, files changed, commits, evidence per acceptance criterion, tests run (passed/failed/skipped), out-of-scope findings, decisions needed from a human, and which `PROGRESS.md` / `AGENTS.md` lines were updated.
8. One commit per topic. Never `git add -A` or `git add .`; add named files. Do not change branch, rebase, or force-push.

## 4. Tech Stack & Versions
- **Backend (`app/backend/pyproject.toml`, `app/backend/requirements.txt`):** Python `>=3.11` (CI/venv runs `3.13`), `lessonai-backend` `0.2.0`, FastAPI `>=0.100.0`, Uvicorn `>=0.20.0`, Pydantic `>=2.0.0`, SymPy `>=1.13.0`, NumPy `>=2.0.0`, Matplotlib `>=3.10.0`, `python-docx` `>=1.0.0`, `python-pptx` `>=0.6.21`, `latex2mathml` `>=3.80.0`, `mathml2omml` `>=0.0.2`, `openpyxl` `>=3.1.0`, `pillow` `>=13.0.0`, `google-genai` `>=0.1.0`, `openai` `>=1.50.0`, `httpx` `>=0.27.0`, `python-dotenv` `>=1.0.0`, `python-multipart` `>=0.0.9`, `packaging` `>=25.0`, security floors `certifi>=2026.10.18`, `pyasn1>=0.6.5`, `urllib3>=2.8.0`. Exact pins: `app/backend/requirements-lock.txt`.
- **Frontend (`app/frontend/package.json`):** React `^19.0.0`, Vite `^6.0.0`, `@vitejs/plugin-react` `^4.3.4`, Tailwind CSS `^3.4.15`, PostCSS `^8.4.49`, Autoprefixer `^10.4.20`, Three.js `^0.170.0`, MathLive `0.111.4`, KaTeX `^0.18.10`, Lucide React `^0.460.0`. Exact pins: `app/frontend/package-lock.json`.
- **Testing:** `pytest` `>=8.0.0`, Node native test runner (`node --test`), Playwright `1.64.1`.
- **Storage:** browser `IndexedDB` (`lessonai-projects`) holding `schema_version: 2` projects of the old studio and `schema_version: 3` Bài giảng of the Bàn làm việc, plus JSON backup files; server side holds owner session/copilot state **in memory** (see Gotchas) and a local filesystem corpus (`app/backend/data` or `LESSONAI_DATA_DIR`).

## 5. Directory Structure
```text
.
├── GLOSSARY.md                     # Domain terms for multi-role generation
├── .github/workflows/rag-fixture-tests.yml  # RAG triage and fixture CI on Ubuntu
├── app/
│   ├── backend/                    # FastAPI backend (`lessonai-backend`)
│   │   ├── pyproject.toml          # Package metadata + pytest config
│   │   ├── requirements-lock.txt
│   │   ├── data/                   # Runtime curriculum, RAG corpus, reviewed_sources.json
│   │   ├── output/                 # Runtime export workspace
│   │   ├── src/lessonai/
│   │   │   ├── main.py             # App factory, CORS, local origin & error middlewares
│   │   │   ├── core/               # config, ingress (16 MiB limit), jobs (spawn workers), ownership, render_runtime, signing (confirmation key)
│   │   │   ├── api/routes/         # chat, curriculum, exports, geometry, ingest, lesson_plan, math_spec, presentation, quality, slides, system, validation, visuals, web
│   │   │   ├── services/           # business logic, generation/, math_expression, math_worker, geometry_scene, visual_requirements, content_quality, expert_confirmation, copilot, deck_lint
│   │   │   ├── llm/gateway.py      # Multi-provider LLM router (Gemini, Groq, OpenRouter) with fallback
│   │   │   ├── rag/                # CurriculumRegistry, Math12HybridRetriever, content_units, context_builder
│   │   │   ├── parsers/ exporters/ # DOCX/PPTX ingestion; DOCX/PPTX/Dual-ZIP export
│   │   │   ├── schemas/ prompts/   # Pydantic v2 contracts, including math_spec_schema.py, and system prompts
│   │   │   └── templates/          # PowerPoint templates (`template_5512.pptx`, `manifest.json`)
│   │   └── tests/                  # Pytest suite + `fixtures/api_contract.json`
│   └── frontend/
│       ├── src/App.jsx             # Top-level studio state container and screen router
│       ├── src/features/           # dashboard, generation, lesson-plan, slide-editor, presentation, geometry, chat, analytics, exports, workbench (Bàn làm việc, packaged fonts)
│       ├── src/shared/             # api/client.js, storage/projectStore.js (v2 + IndexedDB), storage/lessonProject.js (Bài giảng bản 3), math/, validation/, components/
│       ├── tests/                  # Node unit/contract tests (`*.test.js`)
│       └── e2e/                    # Playwright real-backend tests (`workflows.spec.js`, `ban-lam-viec.spec.js`)
├── docs/                           # adr/ (decisions), agents/, architecture/ (repository.md maps the repo), design/, rag/; requirements/ stays local (ADR 0012)
├── project-management/             # PROGRESS.md and archived update log
├── reports/                        # Immutable evidence; ignored except directories an ADR or issue cites (ADR 0012)
├── data/                           # Datasets, fixtures (`golden_set.json`), raw corpora
├── scripts/quality/                # Benchmark, source review, RAG triage and latency CLIs
└── infra/                          # Deployment docs, `env.example`
```
- The tree includes local-only paths: `app/backend/data/`, `app/backend/output/`, `data/raw/` and `docs/requirements/` stay out of Git (ADR 0012). Use `git ls-files` to verify what a checkout contains. The baseline workflow runs `test_rag_question_triage.py` and `test_retrieval_fixture.py` on Python 3.13.
- On `feat/multi-role-orchestrator`, see `docs/architecture/multi-role-generation-decisions.md` and `docs/adr/0001-verified-chi-do-may-chung-minh.md` before changing the multi-role contracts. Issue #19 records the approved API scope. At the baseline, issue #20 implements only `POST /api/v1/math-spec/verify` in `api/routes/math_spec.py`, backed by `services/math_spec.py`. The evaluate, approve, and orchestrator endpoints remain planned.

## 6. Common Commands
Run from the repository root. For PowerShell, use `app/backend/venv/Scripts/python.exe`, set the three API key variables to empty and point `LESSONAI_CONFIG_DIR` at a new temp dir before running tests.

- **Install**
  ```bash
  python3.13 -m venv app/backend/venv
  app/backend/venv/bin/python -m pip install -r app/backend/requirements-lock.txt
  app/backend/venv/bin/python -m pip install --no-deps -e app/backend
  npm --prefix app/frontend ci
  ```
- **Run** the backend on port 8000 and the frontend on port 5173.
  ```bash
  app/backend/venv/bin/python -m uvicorn lessonai.main:app --app-dir app/backend/src --reload --reload-dir app/backend/src --host 127.0.0.1 --port 8000
  npm --prefix app/frontend run dev
  ```
- **Backend with the portable marker filter** and **frontend build**.
  ```bash
  GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= LESSONAI_CONFIG_DIR="$(mktemp -d)" PYTHONPATH=app/backend/src app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests -m 'not corpus_integration'
  npm --prefix app/frontend run build
  ```
- The four retriever tests in `test_phase3_pedagogical_rag.py` carry the `corpus_integration` marker because they need the local corpus; run them with `LESSONAI_DATA_DIR` pointing at a test copy of it. The **full local backend** suite uses the same pytest command without `-m 'not corpus_integration'` and requires local tests and corpus. For **critical backend** use `-m critical_regressions`. Frontend commands are `npm --prefix app/frontend test`, `npm --prefix app/frontend run test:critical`, and `npm --prefix app/frontend run test:e2e`. Frontend tests and Playwright configuration require the corresponding local files. Prefix the E2E command with `LESSONAI_CONFIG_DIR="$(mktemp -d)"` so its backend signs with a throwaway key, and with `LESSONAI_TEST_PORT=18080` when the port is busy. The E2E backend serves `app/frontend/dist`, so run the frontend build first. `playwright.config.js` launches the local Google Chrome when it is installed; Playwright's own browser (Chromium build 1248 for Playwright 1.64.1) installs with `npm --prefix app/frontend exec -- playwright install chromium`.
- **Math 12 benchmark (15 cases)**. Use a fresh output path for each run.
  ```bash
  GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= LESSONAI_CONFIG_DIR="$(mktemp -d)" PYTHONPATH=app/backend/src app/backend/venv/bin/python scripts/quality/run_benchmark_suite.py --output /tmp/lessonai-math12-UNIQUE.json
  ```
  Replace `UNIQUE` with a run identifier before using the command.
- **Local Makefile** is ignored on this branch. Inspect the file in the active workspace before using targets. The copy inspected for this baseline defines `backend`, `frontend`, `test`, `test-backend`, `test-frontend`, `test-critical`, `test-critical-backend`, `test-critical-frontend`, `build`, `inventory`, `lint-data`, `audit-baseline`, and `audit-acceptance`. Run portable tests, E2E, and the benchmark with the commands above. For source review use `PYTHONPATH=app/backend/src app/backend/venv/bin/python scripts/quality/prepare-source-review.py --output /tmp/lessonai-source-review-UNIQUE.json` with a fresh path and the local corpus.
- **Pre-PR verification** covers the available portable, critical, frontend, build, and E2E checks. Record unavailable suites and their missing inputs.
- **Database migrations:** none server side. Client projects use `IndexedDB` (`schema_version: 2`) with a one-time migration from `sessionStorage` (`lessonai_slide_deck_json_v1`) in `app/frontend/src/shared/storage/projectStore.js`. Bài giảng bản 3 are validated by `normalizeLesson()` in `app/frontend/src/shared/storage/lessonProject.js`; converting v2 projects to v3 is not built yet (#58).

## 7. Code Conventions
- **Imports:** import backend modules as `lessonai.*`. Never mutate `sys.path` in application code or `scripts/`.
- **Layering:** `api/routes -> services -> llm / rag / parsers / exporters -> schemas`. The frontend keeps shared deck/slide/3D/presentation state in `app/frontend/src/App.jsx` and passes state plus updater callbacks into feature actions. Do not create a second state store in `src/features/*`. Splitting state is a pending design decision (see Boundaries, Ask first).
- **Error contract:** errors return `{"detail": {"code": "<snake_case>", "message": "<Vietnamese user message>", "request_id": "<uuid>"}}` plus header `X-Request-ID`. Keep this envelope. Adding fields inside `detail` needs approval because it touches `api_contract.json`.
- **Generation failures:** Routes such as `presentation.py` return HTTP 503 with a classified error code from `classify_generation_error`. Preserve the locked error envelope.
- **Request models:** prefer Pydantic request models in route signatures over `dict`. New endpoints must not accept raw `dict`.
- **Safe math execution:** never use `eval()` or `new Function()` in Python or JS. Parse via `lessonai/services/math_expression.py` (`ExpressionBudget`) and evaluate in bounded `spawn` subprocesses (`lessonai/core/jobs.py` -> `lessonai/services/math_worker.py`).
- **Deterministic tests:** always run pytest with `GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY=` so tests never call live LLM APIs, and with `LESSONAI_CONFIG_DIR` set to a temp dir so they sign with a throwaway key instead of the teacher's.
- **Test hygiene:** do not delete, skip, or weaken tests to get green. A skip or marker (for example `windows_only`, `office_required`) needs a written reason next to it.

## 8. Git Workflow
- Branches: `feature/<name>` or `fix/<name>`.
- Conventional Commits (`feat(scope):`, `fix(scope):`, `refactor(scope):`, `test(scope):`, `docs:`). History is mostly Vietnamese.
- Every PR that fixes a bug or closes a gotcha updates `PROGRESS.md` (Known Issues / Update Log) and, if it changes a rule here, this file.

## 9. Boundaries
- ✅ **Always:**
  - Preserve the teacher's active draft on any error.
  - Use `Depends(require_owner)` on stateful/mutating session endpoints (`/api/v1/chat`, `/api/v1/quality`, `/api/v1/visuals`).
  - Call the API from the frontend through `postJson` in `app/frontend/src/shared/api/client.js` so owner cookies are initialized.
  - Use a new `REVIEW_OUTPUT` path for every probe/review run.
  - Write new evidence to new, uniquely named files (under `reports/` or `/tmp`).
- ⚠️ **Ask first (stop and get approval):**
  - Changing OpenAPI routes/schemas locked in `app/backend/tests/fixtures/api_contract.json`, including adding fields to the error `detail`.
  - Bumping `schema_version` in `projectStore.js`.
  - Adding Python/npm dependencies.
  - Editing or adding GitHub Actions workflows (the task prompt must say it is allowed).
  - Changing upload/worker limits in `ingress.py`, `jobs.py`, `uploads.py`.
  - Changing `.gitignore` tracking rules.
  - Design choices for: persistent owner-session storage, circuit breaker, splitting `App.jsx` state, extending 3D solids beyond the three supported, camera sync rules.
- 🚫 **Never:**
  - Commit `.env`, API keys, signing keys, local DBs, or large corpus files.
  - Bulk-set `"status": "approved"` in `reviewed_sources.json`, or write any reviewer/approval entry without a human decision file attached to the task.
  - Edit reviewer or sign-off fields in `math12_benchmark_suite.json` or acceptance records without a signed document attached.
  - Mark a human-gated acceptance item PASS (see section 2).
  - Re-enable retired `410 Gone` endpoints (`/api/v1/rag/preview`, `/api/v1/geometry/*`, `/api/v1/test-cases`).
  - Inject fallback sample lessons or transparent placeholder pixels when rendering fails.
  - Overwrite existing evidence files in `reports/`.
  - Delete, skip without reason, or loosen tests to make a run green.

## 10. Gotchas
When you resolve an item, update or remove it here.

- **Config and secrets.** Pytest is configured in `[tool.pytest.ini_options]` of `app/backend/pyproject.toml` (`pythonpath = ["src"]`, `testpaths = ["tests"]`); run with `-c app/backend/pyproject.toml`. Runtime secrets/paths come from `app/backend/.env` (loaded by `lessonai/core/config.py`): `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `LESSONAI_DATA_DIR`, `LESSONAI_OUTPUT_DIR`, `LESSONAI_CONFIG_DIR`, `LESSONAI_LOG_LEVEL`, `LESSONAI_LOCAL_ORIGINS`, and the optional Langfuse tracing keys `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_TRACING_ENABLED`. Template: `infra/env.example`.
- **Gemini failover.** `LLMGateway` has a 45 s generation deadline. Provider and model ordering depend on the task and provider preference.
- **Gemini schema cleaning.** `google-genai` rejects `additionalProperties: true` (`ConfigDict(extra="allow")` on `SlideDeckSchema` and `LessonPlanSchema`) with a client-side `ValueError`. The cleaner `_clean_gemini_schema_node` currently strips `additionalProperties`/`discriminator` keys from the whole tree regardless of context and merges `oneOf` into `anyOf` without checking broken or circular `$ref`.
- **Uvicorn reload.** The local Makefile recipe starts from the repository root with `--app-dir app/backend/src` and `--reload`. The command above adds `--reload-dir app/backend/src` to scope file watching to backend source.
- **Port `8000` conflict.** `[Errno 48] Address already in use`: inspect with `lsof -i :8000` or run E2E with `LESSONAI_TEST_PORT=18080`.
- **Ephemeral sessions.** Owner sessions have a 24-hour TTL. Copilot sessions expire after 1 hour and proposals after 15 minutes, subject to their parent session. All live in memory, so restarting the backend clears them.
- **Persistent confirmation key (ADR 0005).** Figure confirmations and Expert Confirmations (deck and lesson-plan review tokens) are signed with `signing.key` in the per-user config dir from `config_dir()` in `lessonai/core/signing.py` (override: `LESSONAI_CONFIG_DIR`). Tokens never expire and survive restarts. A token dies when its fingerprint changes; one signed by a key this machine lacks (key file deleted or replaced, or a token from another machine) fails with `confirmation_key_changed`. A corrupt or unreadable key file returns 503 `signing_key_unavailable` and stays untouched for recovery.
- **Exclusive file creation.** `prepare-source-review.py`, `project-review-probes.py`, `build_packaged_data.py` fail if the output path exists. Pass a fresh `/tmp/` path.
- **Unsaved slide edits lock navigation.** `SlideEditorScreen.jsx` blocks switching slides, changing screens, or exporting while edits are dirty.
- **Manual keyword unpacking in routes.** `lesson_plan.py`, `presentation.py`, `slides.py` unpack request attributes by hand (`topic=req.topic, ...`). Adding a field to `LessonRequest` or `OutlineRequest` means passing it explicitly in the route, in `services/generation/*.py`, and in `app/frontend/src/features/generation/lessonGenerationActions.js`. Some routes still accept raw `dict`; `chat.py` does so even though `ChatInteractRequest` and `ApplyPatchRequest` exist.
- **Slide field fingerprinting and math scanning.** When adding a field to `SlideSchema` or `SlideDeckSchema`: (a) if it is a derived/ephemeral render field, add it to the ignore list in both `content_snapshot()` in `services/content_quality.py` and `mutateDeck()` in `app/frontend/src/shared/storage/projectStore.js`; (b) if it is authored math/problem text, add it to `math_fields()` in `content_quality.py` and `SOURCE_FIELDS` in `services/visual_requirements.py`.
- **3D limits.** `geometry_scene.py` supports only `cube`, `square_pyramid_regular`, `square_pyramid_at_a`; other solids are rejected. PPTX 3D images are static Matplotlib renders at fixed `elev=30`, `azim=-60`, not synchronized with the WebGL view in `ThreeCanvas.jsx`.
- **Frontend storage and build.** `projectStore.js` checks storage revisions during writes. Record evidence for quota exhaustion, concurrent tabs, and migration with real legacy teacher projects before closing M2. Previous builds reported a large `mathlive` chunk.
- **Bàn làm việc behind a switch.** The old studio stays the default until #59. The `Bàn làm việc` switch (per browser, `localStorage` key `lessonai-workbench`) shows `src/features/workbench/`, which opens only Bài giảng bản 3. The old studio refuses v3 with "Phiên bản chưa hỗ trợ" (`assertLegacyProject()`), and `saveProject()` refuses to overwrite a record that has a newer `schema_version`. While the Bàn làm việc is shown, the old keyboard shortcuts are off (`usePresentationControls({ enabled })`). The tag "Đã xác nhận chuyên môn" reflects the stored `deck.review_token`; the browser cannot check the signature, so the server verifies it when it is used.
- **Packaged fonts.** `src/features/workbench/fonts/` holds unmodified WOFF wrappers of the upstream Google Fonts TTFs (provenance and licence in `OFL.txt`). Do not subset or otherwise modify Source Serif 4: its copyright record reserves the font name "Source", so a modified copy could not keep that name.
- **RAG runtime is empty until a human approves sources.** `reviewed_sources.json` has `"sources": []`; `approved_units()` quarantines unapproved units, so `/api/v1/curriculum/math12` and RAG return empty context. This is expected until the reviewer finishes a batch with `hash_version: 2`.

## 11. Keeping This File Honest
- A line here that disagrees with the code is a bug. Fix it in the same PR as the code change.
- Prefer function or symbol names over line numbers; line numbers rot.
- Do not add history ("this file used to exist"). Add only what an agent needs to act correctly now.
- Use verified GitHub issue numbers when linking gotchas to tracked work.
