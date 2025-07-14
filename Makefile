# Development

lint: 
	@echo "🔍 Running ruff linter..."
	uv run ruff check src/

format:
	@echo "🛠️  Running ruff formatter..."
	uv run ruff format src/

typecheck:
	@echo "🔍 Running mypy type checker..."
	uv run mypy src/ --ignore-missing-imports

fix:
	@echo "🛠️  Running ruff fix..."
	uv run ruff check --fix --unsafe-fixes src/
	uv run ruff format src/

.PHONY: lint format typecheck fix api


tests:
	@echo "🧪 Running tests..."
	uv run python -m pytest tests -v

.PHONY: tests