PYTHON ?= app/backend/venv/bin/python
REVIEW_OUTPUT ?= /tmp/lessonai-review

.PHONY: backend frontend test test-backend test-frontend test-critical test-critical-backend test-critical-frontend audit-baseline audit-acceptance build inventory lint-data

backend:
	$(PYTHON) -m uvicorn lessonai.main:app --app-dir app/backend/src --reload --host 127.0.0.1 --port 8000

frontend:
	npm --prefix app/frontend run dev

test: test-backend test-frontend

test-backend:
	GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= $(PYTHON) -m pytest -c app/backend/pyproject.toml app/backend/tests

test-frontend:
	npm --prefix app/frontend test

test-critical: test-critical-backend test-critical-frontend

test-critical-backend:
	GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= $(PYTHON) -m pytest -c app/backend/pyproject.toml app/backend/tests -m critical_regressions

test-critical-frontend:
	npm --prefix app/frontend run test:critical

# Evidence is append-only: use a new REVIEW_OUTPUT prefix for each run.
audit-baseline:
	$(PYTHON) scripts/quality/project-review-probes.py --mode baseline --output $(REVIEW_OUTPUT)-backend.json
	node scripts/quality/project-review-frontend-probes.mjs --mode baseline --input $(REVIEW_OUTPUT)-backend.json --output $(REVIEW_OUTPUT).json

audit-acceptance:
	$(PYTHON) scripts/quality/project-review-probes.py --mode acceptance --output $(REVIEW_OUTPUT)-backend.json
	node scripts/quality/project-review-frontend-probes.mjs --mode acceptance --input $(REVIEW_OUTPUT)-backend.json --output $(REVIEW_OUTPUT).json

build:
	npm --prefix app/frontend run build

inventory:
	$(PYTHON) scripts/data/inventory_data.py

lint-data:
	$(PYTHON) scripts/quality/deck_lint.py
