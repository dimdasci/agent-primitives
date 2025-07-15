# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses UV for dependency management and make for common tasks:

- **Install dependencies**: `uv sync`
- **Run linting**: `make lint` (uses ruff)
- **Run type checking**: `make typecheck` (uses mypy)
- **Run tests**: `make tests` (pytest)
- **Format code**: `make format` (ruff formatter)
- **Auto-fix issues**: `make fix` (combines ruff fix and format)

## Architecture Overview

This is an agent-based task processing system called "ap2" built with Python 3.13+. The core architecture follows these patterns:

### Core Components

1. **Agent Loop** (`src/ap/agent.py`): Implements the main processing loop that:
   - Determines next action via LLM drivers
   - Executes actions
   - Updates thread history
   - Continues until completion or max iterations

2. **Actions System** (`src/ap/actions.py`): Pydantic-based action classes with:
   - Base `Action` class with result caching
   - Specific action implementations (Add, Done, AskUser, etc.)
   - Execute-once pattern with cached results

3. **LLM Driver System** (`src/ap/drivers/`): Pluggable driver system with:
   - Factory pattern for driver selection (`drivers/factory.py`)
   - Protocol-based interface (`drivers/base.py`)
   - OpenAI integration (`drivers/openai.py`)
   - Anthropic integration (`drivers/anthropic.py`) 
   - Easy extensibility for future drivers (ollama, langchain, etc.)

4. **Configuration System** (`src/ap/config.py`): Driver-aware configuration with:
   - YAML-based config (`config.yaml`)
   - Driver-specific settings with fallback to defaults
   - Runtime driver switching

5. **Thread Management** (`src/ap/thread.py`, `src/ap/inmemory.py`): Conversation state with:
   - Chainable thread updates (add method returns self for method chaining)
   - In-memory storage for thread history
   - Query and action history tracking

6. **Context & Dependencies** (`src/ap/context.py`): Dependency injection container with:
   - LLM clients (OpenAI, etc.)
   - Logging, Langfuse tracing
   - CLI interface, state management

### Key Patterns

- **Either/Result Types** (`src/ap/either.py`): Functional error handling with Left/Right pattern
- **Driver Pluggability**: Easy addition of new LLM providers via factory pattern
- **Chainable APIs**: Thread updates use method chaining pattern (add method returns self)
- **Observability**: Langfuse integration for tracing and session management

## Configuration

The system uses `config.yaml` for driver-specific configuration. Each driver section can override default values. Driver selection happens at runtime via CLI `--driver` flag.

## Testing

Tests are in `tests/` directory covering actions, config, and either utilities. Run with `make tests`.

## Evaluation System

The project includes a comprehensive evaluation framework (`src/ap/eval.py`) for testing agent performance against standardized datasets:

### Evaluation Datasets

Located in `evals/` directory:
- `simple_tasks.yaml`: Basic arithmetic operations
- `multistep_tasks.yaml`: Multi-step problem solving
- `complex_tasks.yaml`: Complex reasoning tasks

### Running Evaluations

Use the evaluation system to test agent performance:
```bash
python -m src.ap.eval --dataset evals/simple_tasks.yaml --driver openai
```

### Evaluation Features

- **Rich UI**: Progress bars, result tables, and summary panels
- **Detailed Reporting**: JSON reports with test results and thread details
- **Multiple Drivers**: Test against different LLM providers
- **Mock User Input**: Automated testing with predefined user responses
- **Result Validation**: Flexible comparison for numeric and string outputs
- **Thread Debugging**: Saves detailed thread information for analysis