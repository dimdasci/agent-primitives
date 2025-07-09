# BAML to Instructor Migration Plan

## Overview

This document outlines the detailed plan for migrating from BAML to Instructor library, maintaining the same functionality while improving 12-factor compliance and removing vendor lock-in.

## Migration Goals

- **Primary**: Replace BAML with Instructor while maintaining exact same functionality
- **Secondary**: Improve 12-factor compliance (explicit dependencies, portability)
- **Tertiary**: Enable better ecosystem integration (Langfuse, W&B, etc.)

## Current BAML Implementation Analysis

### Key Components to Replace

1. **BAML Function**: `DetermineNextStep` in `baml_src/agent.baml:21-45`
2. **Type System**: Union types and structured classes in `baml_src/`
3. **Client Configuration**: Multi-provider setup in `baml_src/clients.baml`
4. **Generated Code**: Auto-generated client in `src/baml_client/`
5. **Testing Framework**: Declarative tests with assertions in `baml_src/agent.baml:47-151`

### Current Usage Pattern

```python
# Current agent implementation
next_step = await b.DetermineNextStep(thread=thread.serialize())
intent = Intents(next_step.intent)
```

## Detailed Migration Steps

### Phase 1: Dependencies and Structure

#### 1.1 Update Dependencies
**File**: `pyproject.toml`

**Remove:**
```toml
"baml-py>=0.201.0",
```

**Add:**
```toml
"instructor>=1.0.0",
"openai>=1.0.0",
"anthropic>=0.25.0",
```

#### 1.2 Create New Directory Structure
```
src/
├── llm_client/
│   ├── __init__.py
│   ├── manager.py      # Client management and configuration
│   ├── models.py       # Pydantic models and LLM functions
│   └── providers.py    # Provider-specific configurations
├── agent_primitives/   # Existing - will be updated
└── tests/              # New - structured tests
    ├── test_llm_client.py
    └── test_agent_integration.py
```

### Phase 2: Type System Migration

#### 2.1 Create Pydantic Models
**File**: `src/llm_client/models.py`

**Convert BAML types to Pydantic:**

```python
from pydantic import BaseModel, Field
from typing import Union, Literal

# Human interaction tools
class ClarificationRequest(BaseModel):
    """Request for clarification from user"""
    reasoning: str = Field(description="Why the task needs clarification")
    intent: Literal["request_more_information"] = "request_more_information"
    message: str

class DoneForNow(BaseModel):
    """Task completion notification"""
    reasoning: str = Field(description="Why the task is done")
    intent: Literal["done_for_now"] = "done_for_now"
    message: str = Field(description="Message to send to user about completed work")

# Calculator tools
class AddTool(BaseModel):
    """Addition operation"""
    intent: Literal["add"] = "add"
    a: Union[int, float]
    b: Union[int, float]

class SubtractTool(BaseModel):
    """Subtraction operation"""
    intent: Literal["subtract"] = "subtract"
    a: Union[int, float]
    b: Union[int, float]

class MultiplyTool(BaseModel):
    """Multiplication operation"""
    intent: Literal["multiply"] = "multiply"
    a: Union[int, float]
    b: Union[int, float]

class DivideTool(BaseModel):
    """Division operation"""
    intent: Literal["divide"] = "divide"
    a: Union[int, float]
    b: Union[int, float]

# Union types for response models
HumanTools = Union[ClarificationRequest, DoneForNow]
CalculatorTools = Union[AddTool, SubtractTool, MultiplyTool, DivideTool]
AllTools = Union[HumanTools, CalculatorTools]
```

#### 2.2 Update Intents Enum
**File**: `src/agent_primitives/model.py`

**Ensure enum values match Pydantic literal types:**
```python
class Intents(Enum):
    REQUEST_INFO = "request_more_information"  # Matches ClarificationRequest
    DONE = "done_for_now"                      # Matches DoneForNow
    ADD = "add"                                # Matches AddTool
    SUBTRACT = "subtract"                      # Matches SubtractTool
    MULTIPLY = "multiply"                      # Matches MultiplyTool
    DIVIDE = "divide"                          # Matches DivideTool
```

### Phase 3: Client Management System

#### 3.1 Provider Configuration
**File**: `src/llm_client/providers.py`

```python
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ProviderConfig:
    """Configuration for LLM provider"""
    provider: str
    model: str
    api_key: str
    additional_options: Dict[str, Any] = None

class ProviderManager:
    """Manages different LLM provider configurations"""
    
    def __init__(self):
        self.providers = {
            "openai-gpt4o": ProviderConfig(
                provider="openai",
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                additional_options={"temperature": 0.1}
            ),
            "openai-gpt4o-mini": ProviderConfig(
                provider="openai", 
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
                additional_options={"temperature": 0.1}
            ),
            "anthropic-sonnet": ProviderConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022", 
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ),
            "anthropic-haiku": ProviderConfig(
                provider="anthropic",
                model="claude-3-haiku-20240307",
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        }
    
    def get_config(self, provider_name: str) -> ProviderConfig:
        """Get configuration for specified provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]
```

#### 3.2 Client Manager
**File**: `src/llm_client/manager.py`

```python
import instructor
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from typing import Dict, Any
from .providers import ProviderManager, ProviderConfig

class LLMClientManager:
    """Manages LLM clients with fallback and retry logic"""
    
    def __init__(self):
        self.provider_manager = ProviderManager()
        self._clients: Dict[str, Any] = {}
        self._default_provider = "openai-gpt4o-mini"
    
    async def get_client(self, provider_name: str = None) -> instructor.AsyncInstructor:
        """Get or create instructor client for specified provider"""
        provider_name = provider_name or self._default_provider
        
        if provider_name not in self._clients:
            config = self.provider_manager.get_config(provider_name)
            self._clients[provider_name] = self._create_client(config)
        
        return self._clients[provider_name]
    
    def _create_client(self, config: ProviderConfig) -> instructor.AsyncInstructor:
        """Create instructor client from provider config"""
        if config.provider == "openai":
            openai_client = AsyncOpenAI(api_key=config.api_key)
            return instructor.from_openai(openai_client)
        elif config.provider == "anthropic":
            anthropic_client = AsyncAnthropic(api_key=config.api_key)
            return instructor.from_anthropic(anthropic_client)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def call_with_fallback(self, providers: list[str], **kwargs):
        """Call with fallback to multiple providers"""
        last_exception = None
        
        for provider_name in providers:
            try:
                client = await self.get_client(provider_name)
                return await client.chat.completions.create(**kwargs)
            except Exception as e:
                last_exception = e
                continue
        
        raise last_exception or RuntimeError("All providers failed")
```

### Phase 4: LLM Function Implementation

#### 4.1 Core LLM Function
**File**: `src/llm_client/models.py` (add to existing file)

```python
import instructor
from typing import Union
from .manager import LLMClientManager

async def determine_next_step(
    thread: str, 
    client_manager: LLMClientManager = None,
    provider: str = None
) -> AllTools:
    """
    Determine the next step in agent conversation.
    
    Replaces BAML's DetermineNextStep function with equivalent Instructor implementation.
    
    Args:
        thread: Serialized conversation thread
        client_manager: LLM client manager instance
        provider: Specific provider to use (optional)
        
    Returns:
        Union of all possible tool types (HumanTools | CalculatorTools)
    """
    if client_manager is None:
        client_manager = LLMClientManager()
    
    client = await client_manager.get_client(provider)
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",  # Will be made configurable
        response_model=AllTools,
        messages=[
            {
                "role": "system", 
                "content": "You are a helpful assistant that can help solve a given task."
            },
            {
                "role": "user",
                "content": f"You are working on the following thread:\n\n{thread}"
            },
            {
                "role": "assistant", 
                "content": "What should the next step be?\n\nFirst, think about the task at hand, what do you have to solve it, and plan out what to do next."
            }
        ]
    )
    
    return response
```

### Phase 5: Agent Integration

#### 5.1 Update Agent Implementation
**File**: `src/agent_primitives/agent.py`

**Replace BAML imports and calls:**

```python
# Remove BAML import
# from src.baml_client.async_client import b

# Add Instructor imports
from src.llm_client.models import determine_next_step
from src.llm_client.manager import LLMClientManager

# Update agent run function
async def run(thread: Thread) -> Thread:
    """Run the agent with the given question."""
    client_manager = LLMClientManager()
    
    while True:
        # Replace BAML function call with Instructor equivalent
        next_step = await determine_next_step(
            thread=thread.serialize(),
            client_manager=client_manager
        )
        
        # Rest of the logic remains the same
        intent = Intents(next_step.intent)
        if intent in (Intents.DONE, Intents.REQUEST_INFO):
            thread.events.append(Event(type=et.SYSTEM_RESPONSE, data=next_step))
            return thread
        elif intent in (Intents.ADD, Intents.SUBTRACT, Intents.MULTIPLY, Intents.DIVIDE):
            thread.events.append(Event(type=et.TOOL_CALL, data=next_step))
            try:
                result = ACTIONS[intent](next_step.a, next_step.b)
                result_type = et.TOOL_RESPONSE
            except Exception as e:
                result = str(e)
                result_type = et.ERROR
            thread.events.append(Event(type=result_type, data=result))
        else:
            raise ValueError(f"Unknown intent: {intent}")
```

### Phase 6: Testing Framework

#### 6.1 Create Test Infrastructure
**File**: `src/tests/test_llm_client.py`

```python
import pytest
from src.llm_client.models import determine_next_step
from src.llm_client.manager import LLMClientManager
from src.agent_primitives.model import Intents

class TestLLMClient:
    """Test suite for LLM client functionality"""
    
    @pytest.fixture
    async def client_manager(self):
        """Create client manager for testing"""
        return LLMClientManager()
    
    @pytest.mark.asyncio
    async def test_hello_world(self, client_manager):
        """Test basic greeting response"""
        thread = '{"type": "user_input", "data": "How are you doing?"}'
        result = await determine_next_step(thread, client_manager)
        
        assert result.intent == "done_for_now"
        assert "doing" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_math_operation(self, client_manager):
        """Test math operation detection"""
        thread = '{"type": "user_input", "data": "can you multiply 3 and 4?"}'
        result = await determine_next_step(thread, client_manager)
        
        assert result.intent == "multiply"
        assert result.a == 3
        assert result.b == 4
    
    @pytest.mark.asyncio
    async def test_long_math_sequence(self, client_manager):
        """Test multi-step math operation"""
        thread = '''[
            {"type": "user_input", "data": "can you multiply 3 and 4, then divide the result by 2 and then add 12 to that result?"},
            {"type": "tool_call", "data": {"intent": "multiply", "a": 3, "b": 4}},
            {"type": "tool_response", "data": 12},
            {"type": "tool_call", "data": {"intent": "divide", "a": 12, "b": 2}},
            {"type": "tool_response", "data": 6},
            {"type": "tool_call", "data": {"intent": "add", "a": 6, "b": 12}},
            {"type": "tool_response", "data": 18}
        ]'''
        
        result = await determine_next_step(thread, client_manager)
        
        assert result.intent == "done_for_now"
        assert "18" in result.message
    
    @pytest.mark.asyncio
    async def test_clarification_request(self, client_manager):
        """Test clarification request for invalid input"""
        thread = '{"type": "user_input", "data": "can you multiply 3 and feee9ff10"}'
        result = await determine_next_step(thread, client_manager)
        
        assert result.intent == "request_more_information"
        assert "clarify" in result.message.lower() or "correct" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_post_clarification(self, client_manager):
        """Test response after clarification"""
        thread = '''[
            {"type": "user_input", "data": "can you multiply 3 and FD*(#F&&?"},
            {"type": "tool_call", "data": {"intent": "request_more_information", "message": "Could you please clarify the second number?"}},
            {"type": "human_response", "data": "lets try 12 instead"}
        ]'''
        
        result = await determine_next_step(thread, client_manager)
        
        assert result.intent == "multiply"
        assert result.a == 3
        assert result.b == 12
```

#### 6.2 Integration Tests
**File**: `src/tests/test_agent_integration.py`

```python
import pytest
from src.agent_primitives.agent import run
from src.agent_primitives.model import Thread, Event, EventType as ET

class TestAgentIntegration:
    """Integration tests for full agent workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_math_workflow(self):
        """Test complete math calculation workflow"""
        thread = Thread(events=[
            Event(type=ET.USER_INPUT, data="What is 5 plus 3?")
        ])
        
        result_thread = await run(thread)
        
        # Check that we have the expected sequence of events
        assert len(result_thread.events) >= 3  # Input, tool call, tool response, system response
        
        # Check final response
        last_event = result_thread.events[-1]
        assert last_event.type == ET.SYSTEM_RESPONSE
        assert last_event.data.intent == "done_for_now"
        assert "8" in last_event.data.message
    
    @pytest.mark.asyncio
    async def test_clarification_workflow(self):
        """Test clarification request workflow"""
        thread = Thread(events=[
            Event(type=ET.USER_INPUT, data="Calculate xyz plus abc")
        ])
        
        result_thread = await run(thread)
        
        # Should end with clarification request
        last_event = result_thread.events[-1]
        assert last_event.type == ET.SYSTEM_RESPONSE
        assert last_event.data.intent == "request_more_information"
```

### Phase 7: Cleanup

#### 7.1 Remove BAML Files
**Files to delete:**
- `baml_src/` (entire directory)
- `src/baml_client/` (entire directory)

#### 7.2 Update Configuration
**File**: `pyproject.toml`

Remove BAML-related configuration and add test configuration:

```toml
[dependency-groups]
dev = [
    "mypy>=1.16.1",
    "pytest>=8.4.1",
    "pytest-asyncio>=0.24.0",  # Add for async testing
    "pytest-mock>=3.14.1",
    "ruff>=0.12.2",
]
```

### Phase 8: Documentation Updates

#### 8.1 Update README.md
Update the BAML evaluation section to reflect the migration:

```markdown
## Migration to Instructor

This project has been migrated from BAML to Instructor to improve 12-factor compliance:

### Benefits Achieved:
- ✅ **Explicit Dependencies**: No vendor lock-in, standard Python packages
- ✅ **Maximum Portability**: Works across environments without proprietary tools
- ✅ **Open Source Ecosystem**: Integrates with Langfuse, Weights & Biases
- ✅ **Standard Development**: Native Python development experience

### Implementation:
- **Type System**: Pydantic models with discriminated unions
- **LLM Integration**: Instructor library with multi-provider support
- **Testing**: Standard pytest framework with async support
- **Client Management**: Configurable provider system with fallback logic
```

## Risk Mitigation

### Testing Strategy
1. **Unit Tests**: Test each component in isolation
2. **Integration Tests**: Test complete workflows
3. **Compatibility Tests**: Ensure exact same behavior as BAML version
4. **Performance Tests**: Verify no significant performance degradation

### Rollback Plan
- Keep BAML branch available for quick rollback
- Maintain feature parity checklist
- Test both implementations side-by-side during transition

### Validation Checklist
- [ ] All existing tests pass with new implementation
- [ ] Performance is comparable to BAML version
- [ ] Error handling works correctly
- [ ] Multi-provider support functions properly
- [ ] CLI and API interfaces unchanged
- [ ] Documentation updated and accurate

## Implementation Timeline

**Phase 1-2**: Dependencies and types (4 hours)
**Phase 3-4**: Client management and LLM functions (8 hours)
**Phase 5-6**: Agent integration and testing (8 hours)
**Phase 7-8**: Cleanup and documentation (4 hours)

**Total Estimated Time**: 24 hours (3 working days)

## Success Criteria

1. **Functional Parity**: All existing features work identically
2. **Test Coverage**: 100% of BAML tests have Instructor equivalents
3. **12-Factor Compliance**: No vendor dependencies, full portability
4. **Documentation**: Complete migration guide and updated README
5. **Performance**: No significant performance degradation

This migration will transform the project from a BAML-dependent system to a fully portable, 12-factor compliant agent implementation while maintaining all existing functionality.