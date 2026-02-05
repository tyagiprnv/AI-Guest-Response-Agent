# AI Guest Response Agent

A production-quality AI agent that generates responses to guest accommodation inquiries.

## Features

- **Agentic Workflow**: LangGraph-based agent with conditional routing and parallel tool execution
- **Multi-Tool System**: Template retrieval (RAG), property details, and reservation lookups
- **Safety Guardrails**: PII redaction and topic filtering with fast-path optimization (71% hit rate)
- **Production Monitoring**: LangSmith tracing, Prometheus metrics, Grafana dashboards
- **Cost Optimization**: Template-first strategy, direct template substitution (58% skip LLM), multi-layer caching
- **Cost Tracking**: Real-time LLM usage cost monitoring via Prometheus metrics
- **High Performance**:
  - **p50 latency**: 0.07s (median, warm cache)
  - **p95 latency**: 0.61s warm / 0.83s cold (95th percentile)
  - **p99 latency**: 0.66s warm / 1.89s cold (99th percentile)
  - **Average latency**: 0.21s warm / 0.27s cold
  - **Fast queries**: 100% warm cache, 98% cold cache complete in <1s
  - **Parallel execution**: Topic filter + response generation run concurrently
  - **Optimized caching**: Async Redis with 1-hour embedding cache, 5-min response cache
  - **LLM optimization**: Cached instances, filtered context, concise prompts (max_tokens: 150)
- **PostgreSQL Database**: Production-grade database with async operations and migrations
- **Redis Cache**: Fully async distributed caching with proper await handling
- **API Key Authentication**: Secure endpoints with multi-tier API key validation
- **Enhanced Input Validation**: Spam detection, ID format validation, multi-tier rate limiting
- **Comprehensive Testing**: Unit, integration, and E2E tests (100% pass rate)
- **Docker Deployment**: Full stack deployment with Docker Compose

## Architecture

### Agent Workflow

![Agent Workflow](data/img/arch_diag.png)


## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangGraph |
| LLM | Groq (LLaMA 3.1 8B Instant) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant |
| Database | PostgreSQL |
| Cache | Redis |
| API | FastAPI |
| Monitoring | LangSmith + Prometheus + Grafana |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Groq API key
- LangSmith API key (optional)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agentic-project

# Sync dependencies (creates .venv automatically)
uv sync

# For development tools
uv sync --extra dev

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required:
#   - OPENAI_API_KEY
#   - GROQ_API_KEY
#   - DATABASE_PASSWORD (for PostgreSQL)
# Optional:
#   - LANGSMITH_API_KEY

# Generate API keys for authentication
python scripts/generate_api_key.py

# Add generated keys to .env
# API_KEYS=dev-xxx,test-xxx
# AUTH_ENABLED=true
```

### 3. Start Infrastructure Services

```bash
# Start all infrastructure services
docker-compose up -d postgres redis qdrant prometheus grafana

# Wait for services to be ready
sleep 10
```

### 4. Setup Database and Generate Data

```bash
# Run database migrations
alembic upgrade head

# Generate synthetic data (500 templates, 100 properties, 200 reservations)
python scripts/generate_synthetic_data.py

# Migrate data to PostgreSQL
python scripts/migrate_json_to_postgres.py

# Index templates in Qdrant
python scripts/setup_qdrant.py

# Verify setup
python scripts/verify_implementation.py
```

### 5. Run the Application

```bash
# Development mode
python src/main.py

# Or with Docker Compose (full stack)
docker-compose up
```

### 6. Test the API

```bash
# Health check (public endpoint)
curl http://localhost:8000/health

# Generate a response (requires API key)
curl -X POST http://localhost:8000/api/v1/generate-response \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "message": "What time is check-in?",
    "property_id": "prop_001"
  }'

# View Swagger docs
open http://localhost:8000/docs
```

## Access Monitoring

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Qdrant**: http://localhost:6333/dashboard
- **PostgreSQL**: localhost:5432 (agent_user/guest_response_agent)
- **Redis**: localhost:6379
- **LangSmith**: https://smith.langchain.com

## Project Structure

```
agentic-project/
├── src/
│   ├── agent/              # LangGraph agent
│   │   ├── graph.py        # Workflow definition
│   │   ├── state.py        # State schema
│   │   ├── nodes.py        # Graph nodes
│   │   └── prompts.py      # Versioned prompts
│   ├── tools/              # Agent tools (incl. template_substitution)
│   ├── guardrails/         # Safety mechanisms (PII, topic filter with fast-path)
│   ├── api/                # FastAPI application
│   ├── retrieval/          # Vector DB operations
│   ├── monitoring/         # Observability
│   ├── data/               # Data layer (incl. cache warming)
│   └── config/             # Configuration
├── data/                   # Synthetic dataset
├── evaluation/             # Eval framework
├── tests/                  # Tests
├── infrastructure/         # Prometheus/Grafana config
└── scripts/                # Setup scripts
```

## Response Generation Strategy

The agent uses a three-tier response strategy to optimize for both quality and cost:

| Response Type | Condition | LLM Call | Description |
|---------------|-----------|----------|-------------|
| **Direct Template** | Score ≥ 0.75 + all placeholders fillable | No | High-confidence matches skip LLM entirely. Placeholders are substituted with live property/reservation data. |
| **Template Response** | Score ≥ 0.70 + missing placeholders | Yes | Good matches use templates as context for LLM generation. |
| **Custom Response** | Score < 0.70 | Yes | Low matches generate fully custom responses. |

### Trigger-Query Embeddings

Templates are indexed using **trigger queries** rather than response text, enabling query-to-query semantic matching. This produces high similarity scores (0.85-1.00) for common accommodation queries, making the direct template path highly effective.

### Direct Template Substitution

For high-confidence template matches, the system performs runtime placeholder substitution:

- Templates contain placeholders like `{check_in_time}`, `{guest_name}`, `{property_name}`
- The system builds context from property and reservation data
- If all placeholders can be filled, the response is returned directly without an LLM call
- This eliminates LLM latency for the majority of common queries

Configure via environment variables:
```bash
DIRECT_SUBSTITUTION_THRESHOLD=0.75   # Score threshold for direct substitution
RETRIEVAL_SIMILARITY_THRESHOLD=0.70  # Score threshold for template matching
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Performance

### Measured Latency (n=55 queries)

**Warm Cache (typical production):**

| Metric | Value |
|--------|-------|
| **Average** | 0.21s |
| **p50** | 0.07s |
| **p95** | 0.61s |
| **p99** | 0.66s |
| **Min** | 0.02s |
| **Max** | 0.66s |

| Speed Tier | Count | Percentage |
|------------|-------|------------|
| Fast (<1s) | 55 | 100% |
| Medium (1-3s) | 0 | 0% |
| Slow (>3s) | 0 | 0% |

**Cold Start (empty cache):**

| Metric | Value |
|--------|-------|
| **Average** | 0.27s |
| **p50** | 0.07s |
| **p95** | 0.83s |
| **p99** | 1.89s |
| **Min** | 0.03s |
| **Max** | 1.89s |

| Speed Tier | Count | Percentage |
|------------|-------|------------|
| Fast (<1s) | 54 | 98% |
| Medium (1-3s) | 1 | 2% |
| Slow (>3s) | 0 | 0% |

### Latency by Component

**Warm cache:**

| Component | Avg Latency | Max Latency |
|-----------|-------------|-------------|
| Full Request (LangGraph) | 0.21s | 0.66s |
| Topic Filter (fast-path) | 0.09s | 0.12s |
| Topic Filter (LLM, when needed) | 0.25s | 0.35s |
| Response Generation (LLM) | 0.35s | 0.60s |
| Tool Execution (parallel) | 0.15s | 0.30s |
| Direct Template (no LLM) | 0.05s | 0.15s |

**Cold cache:**

| Component | Avg Latency | Max Latency |
|-----------|-------------|-------------|
| Full Request (LangGraph) | 0.27s | 1.89s |
| Embedding Generation | +0.10s | +0.20s |
| Qdrant Search | +0.05s | +0.10s |

### Optimizations

The agent includes several optimizations for low-latency responses:

**Topic Filter Fast-Path**: For common safe queries (check-in times, amenities, parking, etc.), the topic filter uses regex pattern matching (~90ms) instead of an LLM call, reducing guardrails latency significantly.

**Embedding Cache Warming**: At startup, embeddings for 54 common queries are pre-generated in a single batch API call. Cached queries skip the embedding API call entirely.

**Trigger-Query Embeddings**: Templates are indexed by trigger queries, enabling high-confidence semantic matches (0.85-1.00 similarity scores) that qualify for direct template substitution.

### Latency by Path

**Warm cache (typical production):**

| Query Path | Typical Latency |
|------------|-----------------|
| Fast-path + direct template + cache hit | 50-150ms |
| Fast-path + LLM response + cache hit | 200-400ms |
| LLM topic check + LLM response (parallel, cached) | 300-600ms |
| Blocked queries (topic filter only, cached) | 400-600ms |

**Cold cache (worst case):**

| Query Path | Typical Latency |
|------------|-----------------|
| Fast-path + direct template (no cache) | 100-300ms |
| Fast-path + LLM response (no cache) | 400-800ms |
| LLM topic check + LLM response (parallel, no cache) | 600-1,200ms |
| Blocked queries (topic filter only, no cache) | 800-1,500ms |

## Metrics

The agent tracks the following via Prometheus:

| Category | Metrics |
|----------|---------|
| **Quality** | Relevance score, accuracy score, safety score |
| **Performance** | P50/P95/P99 latency, tokens per request |
| **Cost** | Cost per response (by response type and model), template match rate, direct substitution rate, total USD cost |
| **Operational** | Error rate, cache hit rate, guardrail triggers, topic filter path (fast_path/llm), direct substitution status (success/fallback) |
| **Authentication** | Auth failures, requests by API key tier |
| **Validation** | Validation errors, spam detection, rate limit hits by tier |

## Development

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Production Deployment

```bash
# Build and deploy full stack
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale the API
docker-compose up -d --scale api=3
```

## License

MIT

## Author

Pranav Tyagi
