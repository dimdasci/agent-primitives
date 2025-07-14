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

# Evaluation
eval_simple:
	@echo "🧪 Running simple evaluation..."
	uv run python -m src.ap.cli evaluate evals/simple_tasks.yaml -d $(driver) -r eval_reports -t eval_threads

eval_multistep:
	@echo "🧪 Running multi step evaluation..."
	uv run python -m src.ap.cli evaluate evals/multistep_tasks.yaml -d $(driver) -r eval_reports -t eval_threads

eval_complex:
	@echo "🧪 Running complex evaluation..."
	uv run python -m src.ap.cli evaluate evals/complex_tasks.yaml -d $(driver) -r eval_reports -t eval_threads


.PHONY: eval_simple eval_multistep eval_complex