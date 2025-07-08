# Development

lint: 
	@echo "🔍 Running ruff linter..."
	uv run ruff check src/

format:
	@echo "🛠️  Running ruff formatter..."
	uv run ruff format src/

typecheck:
	@echo "🔍 Running mypy type checker..."
	uv run mypy src/

fix:
	@echo "🛠️  Running ruff fix..."
	uv run ruff check --fix --unsafe-fixes src/
	uv run ruff format src/

api:
	@echo "🚀 Starting API server..."
	uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: lint format typecheck fix api