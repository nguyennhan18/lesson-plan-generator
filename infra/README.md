# Infrastructure & Deployment (`LessonAI-5512`)

This directory documents the deployment model, environment configuration, and continuous integration pipeline for LessonAI-5512.

---

## 1. Local Single-Process Execution Model

LessonAI-5512 is designed as a **local single-process teaching studio** (ADR-002).
- **Backend Host & Port:** Defaults to `127.0.0.1:8000`. Managed via `make backend`.
- **Frontend Dev Host & Port:** Defaults to `127.0.0.1:5173`. Managed via `make frontend`.
- **Production Build:** Frontend builds into static assets at `app/frontend/dist/` via `make build`.
- **Security Boundary:** Bound to localhost (`127.0.0.1`), enforces strict local origin checks (`LESSONAI_LOCAL_ORIGINS`), and uses in-memory cookie sessions (`lessonai_owner`) with a 24-hour TTL. It is not designed for public multi-tenant cloud hosting without adding an external authentication and durable persistence layer.

---

## 2. Configuration (`app/backend/.env`)

Runtime configuration is loaded from `app/backend/.env` using `python-dotenv` in `lessonai/core/config.py`. A documented template is provided at [`infra/env.example`](env.example).

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for structured generation & chat | *(empty)* |
| `GROQ_API_KEY` | Groq API key for low-latency Llama fallback | *(empty)* |
| `OPENROUTER_API_KEY` | OpenRouter API key for multi-provider routing | *(empty)* |
| `LESSONAI_DATA_DIR` | Absolute path to the canonical runtime data directory | `app/backend/data` |
| `LESSONAI_OUTPUT_DIR` | Absolute path to generated output directory | `app/backend/output` |
| `LESSONAI_LOG_LEVEL` | Python standard logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `LESSONAI_LOCAL_ORIGINS`| Comma-separated list of allowed HTTP origins for CORS | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000` |

---

## 3. Continuous Integration (`.github/workflows/ci.yml`)

The repository includes a GitHub Actions workflow configured at [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) targeting Ubuntu runners:
- Python 3.13 (`requirements-lock.txt`) and Node.js 22 (`package-lock.json`).
- Executes:
  - `make test-portable`
  - `make test-critical-backend`
  - `make test-frontend`
  - `make audit-acceptance`
  - `make test-e2e` (Playwright Chromium)
  - `npm audit --audit-level=high`
- Archives the `acceptance-evidence` artifact containing acceptance JSON probes, test results, and Playwright HTML reports.
