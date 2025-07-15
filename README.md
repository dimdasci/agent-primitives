# Agent Primitives (ap2)

A research project exploring how general software engineering design patterns can be applied to agentic system design.

## Purpose

This project demonstrates that many challenges in agentic systems can be elegantly solved using well-established software engineering patterns, without requiring specialized frameworks. While tools like LangChain and others have made significant contributions to the field, this project explores an alternative approach that leverages fundamental design patterns.

**Core Exploration Areas:**
- **Action Pattern**: How structured actions with result caching can simplify agent behavior
- **Driver Pattern**: Clean abstraction for different LLM providers
- **Functional Error Handling**: Either/Result types for robust error management
- **Dependency Injection**: Clean separation of concerns in agent systems
- **Evaluation Systems**: Comprehensive testing approaches for agent behavior

## Key Demonstrations

### Action System
- **Pydantic-based Actions**: Type-safe action definitions with validation
- **Execute-once Pattern**: Automatic result caching to prevent redundant computation
- **Chain of Thought**: Built-in reasoning trace for each action

### Multi-LLM Support
- **OpenAI**: GPT-4 and other OpenAI models
- **Anthropic**: Claude models
- **Ollama**: Local model support
- **Extensible**: Easy to add new providers

### Evaluation Framework
- **Rich UI**: Progress bars, result tables, and summary panels
- **Multiple Test Suites**: Simple, multistep, and complex task evaluation
- **Automated Testing**: Mock user inputs for consistent evaluation
- **Detailed Reporting**: JSON reports with thread debugging information

### Architecture Patterns
- **Dependency Injection**: Clean separation of concerns
- **Factory Pattern**: Driver selection and initialization
- **Either/Result Types**: Functional error handling
- **Chainable APIs**: Fluent interface for thread operations

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-primitives

# Install dependencies
uv sync
```

### Basic Usage

```python
from src.ap.actions import Add, Done
from src.ap.agent import go
from src.ap.context import Context
from src.ap.thread import Thread
from src.ap.inmemory import ThreadInMemoryStore

# Create an action
action = Add(a=10, b=20)
result = action.execute()
print(result)  # Output: 30

# Run the agent loop
async def example():
    # Initialize context and thread
    context = Context(...)
    thread = Thread(query="Calculate 15 + 25")
    
    # Run the agent
    result = await go(context, thread.id)
    print(result)
```

### CLI Usage

```bash
# Run evaluation on a dataset
uv run python -m src.ap.eval --dataset evals/simple_tasks.yaml --driver openai

# Run with different drivers
uv run python -m src.ap.eval --dataset evals/complex_tasks.yaml --driver anthropic
```

## Architecture

### Core Components

```
src/ap/
├── actions.py         # Action definitions and base classes
├── agent.py           # Main agent loop implementation
├── config.py          # Configuration management
├── context.py         # Dependency injection container
├── thread.py          # Conversation state management
├── inmemory.py        # In-memory storage backend
├── either.py          # Functional error handling
├── eval.py            # Evaluation framework
└── drivers/           # LLM driver implementations
    ├── factory.py     # Driver factory
    ├── base.py        # Driver protocol
    ├── openai.py      # OpenAI integration
    ├── anthropic.py   # Anthropic integration
    └── ollama.py      # Ollama integration
```

### Agent Loop

The core agent follows a simple but powerful loop:

1. **Determine Action**: LLM driver selects the next action
2. **Execute Action**: Action is executed with result caching
3. **Update Thread**: Thread history is updated
4. **Continue or Terminate**: Loop continues until completion

```python
async def go(ctx: Context, thread_id: str) -> Either[Actions, str]:
    """Process a task through the agent loop."""
    # 1. Get thread from storage
    # 2. Initialize driver
    # 3. Loop until terminal action or max iterations
    # 4. Return final result or error
```

## Design Patterns Explored

### Action Pattern
```python
class MyAction(Action):
    param1: str = Field(..., description="Required parameter")
    param2: int = Field(default=0, description="Optional parameter")
    
    def _compute_result(self, **kwargs: Any) -> Result:
        # Implement your action logic
        return f"Result: {self.param1} * {self.param2}"
```

### Driver Pattern
```python
class MyDriver(Driver):
    async def next_action(self, thread: Thread) -> Either[Actions, str]:
        # Implement LLM interaction
        # Return parsed action or error
```

### Either/Result Pattern
```python
from src.ap.either import Either, Left, Right

def safe_operation() -> Either[str, int]:
    try:
        result = compute_something()
        return Right(result)
    except Exception as e:
        return Left(str(e))

# Usage
result = safe_operation()
if isinstance(result, Right):
    print(f"Success: {result.value}")
else:
    print(f"Error: {result.error}")
```

## Configuration

Configure drivers in `config.yaml`:

```yaml
default:
  max_actions: 10

openai:
  model: gpt-4-turbo
  temperature: 0.0
  max_tokens: 1000

anthropic:
  model: claude-3-haiku-20240307
  temperature: 0.0
  max_tokens: 1000
```

## Evaluation System

### Test Datasets

Located in `evals/` directory:
- `simple_tasks.yaml`: Basic arithmetic operations
- `multistep_tasks.yaml`: Multi-step problem solving  
- `complex_tasks.yaml`: Complex reasoning tasks

### Example Test Case

```yaml
- id: simple_001
  prompt: "Calculate 1000487.07 + 58753.24"
  expected_answer: 1059240.31
  expected_steps:
    - "Add(a=1000487.07, b=58753.24)"
    - "Done(output=1059240.31)"
```

### Running Evaluations

```bash
# Run specific dataset
uv run python -m src.ap.eval --dataset evals/simple_tasks.yaml --driver openai

# The system will show:
# - Progress bars during execution
# - Results table with pass/fail status
# - Summary statistics
# - Detailed JSON reports
```

## Development

### Commands

```bash
# Install dependencies
uv sync

# Run tests
make tests

# Run linting
make lint

# Run type checking
make typecheck

# Format code
make format

# Auto-fix issues
make fix
```

## Extending the Implementation

### Adding New Actions

```python
class SearchWeb(Action):
    query: str = Field(..., description="Search query")
    
    def _compute_result(self, **kwargs: Any) -> Result:
        # Implement web search logic
        return {"results": [...]}
```

### Adding New Drivers

```python
class MyLLMDriver(Driver):
    async def next_action(self, thread: Thread) -> Either[Actions, str]:
        # Implement your LLM integration
        pass
```

### Adding New Evaluation Datasets

```yaml
- id: custom_001
  prompt: "Your test prompt"
  expected_answer: "Expected result"
  expected_steps:
    - "Action1(param=value)"
    - "Done(output=result)"
  user_input: "Optional user input"  # For interactive tests
```

## Research Goals

This project aims to demonstrate that:

1. **Standard patterns work**: Many agentic system challenges can be solved with well-known software engineering patterns
2. **Simplicity over complexity**: Simple, focused implementations can be more maintainable and understandable
3. **Evaluation is crucial**: Comprehensive testing is essential for reliable agent behavior
4. **Abstraction helps**: Clean interfaces make systems more flexible and testable

## Contributing

This is a research project exploring design patterns in agentic systems. Contributions that demonstrate new patterns or improve existing implementations are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting: `make tests && make lint`
5. Submit a pull request

## Related Work

- [12-Factor Agents](https://github.com/humanlayer/12-factor-agents/tree/main) - Inspiration for this project's design principles
- [Instructor](https://python.useinstructor.com) - Structured outputs from LLMs using Pydantic
- [LangChain](https://langchain.com/) - Comprehensive framework for LLM applications
- [Langfuse](https://langfuse.com/) - Observability and tracing
- [Pydantic](https://pydantic.dev/) - Data validation and settings management
- [Rich](https://rich.readthedocs.io/) - Rich text and beautiful formatting

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

*This project explores alternative approaches to agentic system design while respecting the valuable contributions of existing frameworks and tools in the field.*