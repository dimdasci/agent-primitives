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
	uv run ruff check --fix --unsafe-fix src/
	uv run ruff format src/

.PHONY: lint format typecheck fix