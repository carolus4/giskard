# Idiomatic LangChain Router Improvements

## Overview

This document outlines the improvements made to make the LangChain router implementation more idiomatic and follow LangChain best practices.

## Key Improvements Made

### 1. **Consolidated Router Implementation** (`orchestrator/tools/router.py`)

**Before**: Two separate router classes (`StructuredRouter` and `RouterPlanner`) with duplicated functionality.

**After**: Single `Router` class that:
- Uses proper LCEL (LangChain Expression Language) patterns
- Implements structured output with Pydantic models
- Uses `RunnableLambda` for custom logic
- Implements proper error handling and fallbacks
- Uses dependency injection for better testability

### 2. **Configuration Management** (`orchestrator/config/router_config.py`)

**Before**: Hardcoded configuration values scattered throughout the codebase.

**After**: Centralized configuration system with:
- Pydantic-based configuration models
- Environment variable support
- Type-safe configuration access
- Proper validation and defaults

### 3. **Idiomatic Orchestrator** (`orchestrator/idiomatic_orchestrator.py`)

**Before**: Mixed patterns with manual state management and non-idiomatic LangChain usage.

**After**: Proper LangGraph orchestrator that:
- Uses LCEL patterns throughout
- Implements proper state management
- Uses `RunnableLambda` for node functions
- Implements proper error handling and logging
- Uses dependency injection for configuration

### 4. **Enhanced Testing** (`test_idiomatic_router.py`)

**Before**: Basic integration test with limited coverage.

**After**: Comprehensive test suite that:
- Tests configuration management
- Tests router chain functionality
- Tests full orchestrator workflow
- Provides detailed logging and error reporting

## Technical Improvements

### 1. **Proper LCEL Usage**

```python
# Before: Manual chain construction
response = self.llm.invoke(messages)

# After: Proper LCEL chain
self.router_chain = (
    self.prompt
    | self.llm
    | RunnableLambda(self._parse_llm_response)
    | RunnableLambda(self._validate_router_decision)
)
```

### 2. **Structured Output with Pydantic**

```python
# Before: Manual JSON parsing
router_output = json.loads(cleaned_response)

# After: Pydantic validation
decision = RouterDecision(**decision_data)
```

### 3. **Configuration Management**

```python
# Before: Hardcoded values
self.llm = OllamaLLM(model="gemma3:4b", base_url="http://localhost:11434")

# After: Configuration-driven
model_config = self.config_manager.get_model_config()
self.llm = OllamaLLM(**model_config)
```

### 4. **Error Handling and Fallbacks**

```python
# Before: Basic try-catch
try:
    result = self.llm.invoke(messages)
except Exception as e:
    return fallback_response

# After: Proper error handling with LCEL
def handle_router_error(inputs: Dict[str, Any]) -> RouterDecision:
    try:
        return self.router_chain.invoke(inputs)
    except Exception as e:
        logger.error(f"Router chain error: {str(e)}")
        return RouterDecision(
            assistant_text="I'm sorry, I encountered an error...",
            tool_name="no_op",
            tool_args={}
        )
```

## Benefits of the Improvements

### 1. **More Idiomatic LangChain**
- Uses proper LCEL patterns throughout
- Leverages LangChain's built-in capabilities
- Follows LangChain best practices
- Uses structured output properly

### 2. **Better Maintainability**
- Single source of truth for router logic
- Centralized configuration management
- Proper dependency injection
- Comprehensive error handling

### 3. **Enhanced Testability**
- Dependency injection makes testing easier
- Configuration can be mocked
- Individual components can be tested in isolation
- Comprehensive test coverage

### 4. **Improved Reliability**
- Proper error handling and fallbacks
- Structured output validation
- Timeout handling
- Retry mechanisms

### 5. **Better Developer Experience**
- Clear separation of concerns
- Type safety with Pydantic
- Comprehensive logging
- Easy configuration management

## Usage Examples

### Basic Usage

```python
from orchestrator.idiomatic_orchestrator import IdiomaticOrchestrator
from orchestrator.config.router_config import RouterConfigManager

# Initialize with configuration
config_manager = RouterConfigManager.from_env()
orchestrator = IdiomaticOrchestrator(config_manager)

# Run the orchestrator
result = orchestrator.run("Create a task to review the quarterly report")
```

### Custom Configuration

```python
from orchestrator.config.router_config import RouterConfigManager

# Custom configuration
config_dict = {
    "model_name": "llama2:7b",
    "ollama_base_url": "http://localhost:11434",
    "api_base_url": "http://localhost:5001",
    "timeout_seconds": 60
}

config_manager = RouterConfigManager.from_dict(config_dict)
orchestrator = IdiomaticOrchestrator(config_manager)
```

### Direct Router Usage

```python
from orchestrator.tools.router import Router

# Initialize router
router = Router()

# Plan actions
decision = router.plan_actions("What are my current tasks?")

# Execute tool
result = router.execute_tool(decision["tool_name"], decision["tool_args"])
```

## Migration Guide

### 1. **Replace Old Router Usage**

```python
# Before
from orchestrator.tools.structured_router import StructuredRouter
router = StructuredRouter()

# After
from orchestrator.tools.router import Router
router = Router()
```

### 2. **Update Orchestrator Usage**

```python
# Before
from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
orchestrator = LangGraphOrchestrator()

# After
from orchestrator.idiomatic_orchestrator import IdiomaticOrchestrator
from orchestrator.config.router_config import RouterConfigManager

config_manager = RouterConfigManager.from_env()
orchestrator = IdiomaticOrchestrator(config_manager)
```

### 3. **Configuration Management**

```python
# Before: Hardcoded values
# No configuration management

# After: Environment-based configuration
export GISKARD_ROUTER_MODEL_NAME="gemma3:4b"
export GISKARD_ROUTER_OLLAMA_BASE_URL="http://localhost:11434"
export GISKARD_ROUTER_API_BASE_URL="http://localhost:5001"
```

## Testing

Run the comprehensive test suite:

```bash
python test_idiomatic_router.py
```

The test suite includes:
- Configuration system testing
- Router chain functionality testing
- Full orchestrator workflow testing
- Error handling and fallback testing

## Future Improvements

### 1. **Advanced LCEL Patterns**
- Implement `RunnableParallel` for concurrent operations
- Use `RunnablePassthrough` for state management
- Implement custom `Runnable` classes for specific use cases

### 2. **Enhanced Error Handling**
- Implement retry mechanisms with exponential backoff
- Add circuit breaker patterns for external service calls
- Implement proper logging and monitoring

### 3. **Performance Optimizations**
- Implement caching for frequently used prompts
- Add connection pooling for external services
- Implement async operations where appropriate

### 4. **Monitoring and Observability**
- Add metrics collection
- Implement distributed tracing
- Add performance monitoring

## Conclusion

The idiomatic router implementation provides a solid foundation for building robust, maintainable, and testable LangChain applications. The improvements follow LangChain best practices and provide a much better developer experience while maintaining backward compatibility where possible.
