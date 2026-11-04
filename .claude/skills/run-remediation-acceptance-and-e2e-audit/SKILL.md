---
name: run-remediation-acceptance-and-e2e-audit
description: Execute the complete offline unit, critical regression, acceptance probe, and Playwright browser E2E verification suite. Activate this skill WHENEVER validating backend/frontend changes before a commit/PR, auditing R01-R23 remediation gates, or generating append-only verification evidence.
---
# Run Remediation Acceptance and E2E Audit (`run-remediation-acceptance-and-e2e-audit`)

## When to Use (Khi nào dùng)
Activate this skill after making backend or frontend changes to verify that portable tests, critical regressions, acceptance probes, production build, and real-browser E2E flows all pass without network or LLM API keys.

## Prerequisites (Điều kiện tiên quyết)
- Python 3.13 venv at `app/backend/venv` and Node dependencies installed in `app/frontend/node_modules`.
- Google Chrome installed at `/Applications/Google Chrome.app` on macOS (or Chromium installed via `npx playwright install chromium` in `app/frontend` on Linux).

## Steps (Các bước)
1. **Run critical regression checks (backend + frontend):**
   ```bash
   make test-critical
   ```
2. **Run portable backend tests and frontend unit/contract tests:**
   ```bash
   make test-portable
   make test-frontend
   ```
3. **Run append-only acceptance probes with a unique `/tmp` prefix:**
   ```bash
   make audit-acceptance REVIEW_OUTPUT=/tmp/lessonai-acceptance-$(date +%Y%m%d-%H%M%S)
   ```
4. **Build the production frontend bundle and run Playwright E2E tests:**
   ```bash
   make test-e2e
   ```
   If port `8000` is already in use by another process (such as a dev server), run E2E on an alternate port:
   ```bash
   make build
   LESSONAI_TEST_PORT=18080 npm --prefix app/frontend run test:e2e
   ```

## Reference Examples (Ví dụ mẫu)
- Root build & test targets: `Makefile`.
- CI acceptance workflow: `.github/workflows/ci.yml`.
- Backend & frontend acceptance probes: `scripts/quality/project-review-probes.py` and `scripts/quality/project-review-frontend-probes.mjs`.
- Playwright configuration & E2E specs: `app/frontend/playwright.config.js` and `app/frontend/e2e/workflows.spec.js`.

## Verification (Cách kiểm tra đã làm đúng)
- All commands exit with code `0`.
- `audit-acceptance` generates both `<REVIEW_OUTPUT>-backend.json` and `<REVIEW_OUTPUT>.json` with passing probe results.
- Playwright outputs HTML report to `app/frontend/playwright-report/`.

## Common Pitfalls (Lỗi thường gặp)
- **Port 8000 conflict during `make test-e2e`:** `app/frontend/playwright.config.js` sets `reuseExistingServer: false` and starts a fresh Uvicorn server on `LESSONAI_TEST_PORT` (default `8000`). Stop `make backend` or set `LESSONAI_TEST_PORT=18080`.
- **Reusing `REVIEW_OUTPUT`:** `project-review-probes.py` and `project-review-frontend-probes.mjs` refuse to overwrite existing output files so audit evidence remains append-only.
- **Leaking live API keys into test runs:** Always let `Makefile` pass `GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY=` so tests remain fast, offline, and deterministic.
