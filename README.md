# Agent Primitives Exploration

The project is based on [Building the 12-factor agent template from scratch](https://github.com/humanlayer/12-factor-agents/blob/main/workshops/2025-05/walkthrough.md) Workshop.

The key concepts are stated as [12 principles]((https://github.com/humanlayer/12-factor-agents/tree/main)) of building reliable agents, following the 12-factor app methodology:
- Use declarative formats for setup automation, to minimize time and cost for new developers joining the project;
- Have a clean contract with the underlying operating system, offering maximum portability between execution environments;
- Are suitable for deployment on modern cloud platforms, obviating the need for servers and systems administration;
- Minimize divergence between development and production, enabling continuous deployment for maximum agility;
- And can scale up without significant changes to tooling, architecture, or development practices.

## Implementation Overview

This project implements a simple calculator agent using [BAML](https://docs.boundaryml.com/home) as the core LLM interface. The implementation demonstrates key 12-factor agent principles through a modular architecture.

### Core Components

#### 1. BAML Configuration (`baml_src/`)
- **Function Definition**: `DetermineNextStep` function in `agent.baml:21-45` that processes conversation threads and determines next actions
- **Type System**: Structured types for calculator operations (`CalculatorTools`) and human interactions (`HumanTools`)
- **Client Configuration**: Multiple LLM clients with fallback and retry policies (`clients.baml`)
- **Code Generation**: Python client automatically generated from BAML definitions (`generators.baml`)

#### 2. Agent Core (`src/agent_primitives/`)
- **Agent Loop**: `agent.py:13-40` implements the main agent execution loop
- **Event System**: `model.py:28-42` defines event-driven architecture with `Thread` and `Event` classes
- **Intent Mapping**: `agent.py:5-10` maps BAML intents to Python functions for calculator operations

#### 3. Interface Layer
- **FastAPI Server**: `src/api/main.py` provides RESTful API with thread management
- **CLI Interface**: `src/cli/main.py` offers interactive command-line experience
- **State Management**: `src/state/` implements thread persistence with protocol-based design

#### 4. Testing Strategy
BAML enables test-driven development through declarative test definitions in `agent.baml:47-151`:
- Unit tests for specific intents (`HelloWorld`, `MathOperation`)
- Integration tests for multi-step workflows (`LongMath`)
- Error handling tests (`MathOperationWithClarification`)

### Architecture Benefits

The implementation demonstrates several 12-factor principles:
- **Declarative Configuration**: BAML provides declarative LLM function definitions
- **Explicit Dependencies**: Clear separation between BAML config and Python implementation
- **Stateless Processes**: Agent functions are stateless with external thread management
- **Port Binding**: API and CLI provide different interface bindings
- **Concurrency**: Async/await pattern throughout for scalable execution

## BAML Evaluation

### Pros
- **Prompts as Functions**: BAML treats prompts as first-class functions with type safety, enabling test-driven development of LLM interactions
- **Multi-Model Support**: Built-in support for OpenAI, Anthropic, Google AI with fallback/retry policies
- **Type Safety**: Strong typing system prevents runtime errors and improves developer experience
- **Testing Framework**: Declarative test syntax with assertions makes prompt engineering more reliable
- **Code Generation**: Automatic client generation eliminates boilerplate and ensures consistency

### Cons
- **Vendor Lock-in**: Proprietary Boundary Studio required for advanced observability and monitoring
- **Black Box Clients**: Generated clients (`src/baml_client/`) are not easily customizable or extensible
- **Limited Ecosystem**: No integration with popular open-source tools like Langfuse, Weights & Biases
- **12-Factor Violations**: Contradicts principles of explicit dependencies and maximum portability
- **Learning Curve**: Domain-specific language requires additional learning investment

### Conclusion

While BAML provides excellent developer experience and type safety for LLM interactions, it introduces vendor dependencies that conflict with 12-factor principles. The trade-off between convenience and portability should be carefully considered for production deployments.

