# LessonAI-5512: chạy từ thư mục gốc repo.
# Ghi đè biến khi cần, ví dụ: make test-backend PYTHON=python PYTEST_ARGS="-m 'not corpus_integration'"
PYTHON ?= app/backend/venv/bin/python
NPM ?= npm
PYTEST_ARGS ?=

.PHONY: backend frontend test test-backend test-frontend build

# Backend ở cổng 8000, tự nạp lại khi sửa app/backend/src.
backend:
	$(PYTHON) -m uvicorn lessonai.main:app --app-dir app/backend/src --reload --reload-dir app/backend/src --host 127.0.0.1 --port 8000

# Frontend (Vite) ở cổng 5173.
frontend:
	$(NPM) --prefix app/frontend run dev

# Không gọi API LLM thật và ký bằng khoá tạm (AGENTS.md, Code Conventions).
test-backend:
	GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= LESSONAI_CONFIG_DIR="$$(mktemp -d)" PYTHONPATH=app/backend/src $(PYTHON) -m pytest -c app/backend/pyproject.toml app/backend/tests $(PYTEST_ARGS)

test-frontend:
	$(NPM) --prefix app/frontend test

test: test-backend test-frontend

build:
	$(NPM) --prefix app/frontend run build
