# Test Suite Documentation

This directory contains comprehensive tests for the Guest Response Agent application.

## Test Structure

The test suite is organized into three main categories:

### 1. Unit Tests (`tests/unit/`)

Tests for individual components in isolation.

- **test_models.py**: Tests for Pydantic data models (Template, Property, Reservation)
  - Model creation and validation
  - Enum types (TemplateCategory, ParkingType, RoomType)
  - Date calculations and field validations

- **test_cache.py**: Tests for the caching layer
  - SimpleCache: Basic TTL-based caching (in-memory)
  - Redis cache: Distributed caching with TTL
  - EmbeddingCache: Text embedding caching with SHA256 hashing
  - ToolResultCache: Caching for tool execution results
  - ResponseCache: Full response caching with composite keys
  - TTL expiration and cache clearing

- **test_tools.py**: Tests for tool functions
  - Property details retrieval (JSON and PostgreSQL backends)
  - Reservation details retrieval (JSON and PostgreSQL backends)
  - Template retrieval from vector database
  - Graceful handling of missing data

- **test_auth.py**: Tests for API key authentication
  - API key validation
  - Rate limiting by tier (standard/premium/enterprise)
  - Protected vs public endpoints
  - Invalid API key handling

- **test_database.py**: Tests for PostgreSQL database layer
  - Connection management
  - Async CRUD operations
  - Database migrations with Alembic
  - Repository pattern

- **test_validation.py**: Tests for enhanced input validation
  - Message validation (length, spam detection, URL limits)
  - ID format validation (property_id, reservation_id)
  - Unicode normalization
  - Spam pattern detection

### 2. Integration Tests (`tests/integration/`)

Tests for component interactions and workflows.

- **test_guardrails.py**: Tests for safety guardrails
  - **PII Redaction**: Email, phone, SSN, credit card detection
  - **Topic Filtering**: Blocks legal advice, medical advice, pricing negotiation, etc.
  - **Guardrail Chaining**: Multiple guardrails working together

- **test_agent_workflow.py**: End-to-end agent workflow tests
  - Template-based responses
  - Custom response generation
  - PII blocking and redaction
  - Topic restriction
  - Parallel query processing
  - Graceful degradation
  - Metadata tracking
  - Different query types (check-in, parking, amenities, policies)

### 3. End-to-End Tests (`tests/e2e/`)

Tests for the complete API.

- **test_api.py**: FastAPI endpoint tests
  - Health endpoints (/health, /ready, /) - public
  - Response generation endpoint (/api/v1/generate-response) - requires API key
  - API key authentication (valid, invalid, missing)
  - Request validation (missing fields, empty messages, max length)
  - Enhanced input validation (spam patterns, ID formats, URL limits)
  - PII handling in requests
  - Confidence score validation
  - Response caching behavior (Redis and in-memory)
  - Rate limiting by tier
  - Error handling (invalid JSON, 404, 405, 401, 403, 422, 429)
  - API documentation (OpenAPI, Swagger UI, ReDoc)
  - CORS configuration
  - Prometheus metrics endpoint (cost tracking metrics)

### 4. Load Tests (`tests/load/`)

Performance and load testing with Locust.

- **locustfile.py**: Load testing scenarios

## Running Tests

### All Tests

```bash
pytest
```

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Specific Test File

```bash
pytest tests/unit/test_models.py -v
```

### Specific Test Class or Function

```bash
pytest tests/unit/test_cache.py::TestEmbeddingCache -v
pytest tests/unit/test_cache.py::TestEmbeddingCache::test_set_and_get_embedding -v
```

## Test Fixtures

Shared fixtures are defined in `tests/conftest.py`:

- **setup_test_environment**: Automatically sets test environment variables
- **mock_openai_embedding**: Mock embedding data for testing
- **mock_property_data**: Sample property data
- **mock_reservation_data**: Sample reservation data
- **mock_template_data**: Sample template data
- **sample_guest_messages**: Common test messages
- **clear_caches**: Clears all caches before each test

## Test Requirements

### External Dependencies

Some tests require external services to be running:

1. **PostgreSQL**: Database for data layer tests
   ```bash
   docker-compose up -d postgres
   alembic upgrade head  # Run migrations
   ```

2. **Redis**: Cache for caching tests
   ```bash
   docker-compose up -d redis
   ```

3. **Qdrant**: Vector database for template retrieval tests
   ```bash
   docker-compose up -d qdrant
   ```

4. **API Keys**: Required for integration tests
   ```bash
   export OPENAI_API_KEY=your-key
   export GROQ_API_KEY=your-key
   # Generate test API keys
   python scripts/generate_api_key.py
   export API_KEYS=test-key-12345
   ```

### Skipped Tests

Tests that require unavailable services will be automatically skipped with informative messages.

## Test Coverage

Current test coverage (as of last update):

- **Unit Tests**: 32 tests covering models, caches, and tools
- **Integration Tests**: Comprehensive coverage of guardrails and agent workflows
- **E2E Tests**: Full API endpoint coverage

Target coverage: >80% for all modules

## Writing New Tests

### Guidelines

1. **Organize by type**: Unit, Integration, or E2E
2. **Use descriptive names**: Test function names should clearly describe what they test
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Use fixtures**: Leverage shared fixtures from conftest.py
5. **Clean up**: Use fixtures to ensure tests don't pollute shared state
6. **Handle async**: Use `@pytest.mark.asyncio` for async tests
7. **Skip gracefully**: Use `pytest.skip()` when dependencies are unavailable

### Example Test

```python
import pytest
from src.data.cache import EmbeddingCache

class TestNewFeature:
    """Test new feature functionality."""

    @pytest.mark.asyncio
    async def test_feature_works(self):
        """Test that feature works as expected."""
        # Arrange
        cache = EmbeddingCache()
        cache.clear()

        # Act
        cache.set_embedding("test", [0.1, 0.2])
        result = cache.get_embedding("test")

        # Assert
        assert result == [0.1, 0.2]
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

- Fast unit tests run on every commit
- Integration tests run on PRs
- E2E tests run before deployment
- Load tests run on-demand

## Troubleshooting

### Common Issues

1. **"Connection refused" errors**: Ensure Qdrant is running
   ```bash
   docker-compose up -d qdrant
   ```

2. **"API key not set" errors**: Set environment variables
   ```bash
   export OPENAI_API_KEY=your-key
   export GROQ_API_KEY=your-key
   ```

3. **Slow tests**: Use `-n auto` for parallel execution
   ```bash
   pytest -n auto
   ```

4. **Cached failures**: Clear pytest cache
   ```bash
   pytest --cache-clear
   ```

## Test Philosophy

- **Fast feedback**: Unit tests should run in seconds
- **Reliable**: Tests should be deterministic and not flaky
- **Maintainable**: Tests should be easy to understand and update
- **Comprehensive**: Cover happy paths, edge cases, and error conditions
- **Realistic**: Use realistic test data and scenarios

## Future Improvements

- [ ] Add property-based testing with Hypothesis
- [ ] Increase coverage to >90%
- [ ] Add mutation testing
- [ ] Add contract tests for API
- [ ] Add visual regression tests for documentation
- [ ] Add security testing (OWASP Top 10)
