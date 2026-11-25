# LessonAI-5512: chạy từ thư mục gốc repo.
# Ghi đè biến khi cần, ví dụ: make test-backend PYTHON=python PYTEST_ARGS="-m 'not corpus_integration'"
PYTHON ?= app/backend/venv/bin/python
NPM ?= npm
PYTEST_ARGS ?=
# Console script của import-linter. Trên CI, nơi pip cài vào PATH: make lint LINT_IMPORTS=lint-imports
LINT_IMPORTS ?= app/backend/venv/bin/lint-imports

.PHONY: backend frontend lint test test-backend test-frontend build

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

# Luật tầng trong [tool.importlinter] của app/backend/pyproject.toml.
# Cần app/backend/requirements-dev.txt. Đừng gọi bằng `python -m importlinter.cli`:
# cách đó chỉ nạp module rồi thoát 0, tức cổng lint luôn xanh.
lint:
	PYTHONPATH=app/backend/src $(LINT_IMPORTS) app/backend/pyproject.toml

build:
	$(NPM) --prefix app/frontend run build
