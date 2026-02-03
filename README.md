# AI Guest Response Agent

A production-quality AI agent that generates responses to guest accommodation inquiries.

## Features

- **Agentic Workflow**: LangGraph-based agent with conditional routing and parallel tool execution
- **Multi-Tool System**: Template retrieval (RAG), property details, and reservation lookups
- **Safety Guardrails**: PII redaction and topic filtering with fast-path optimization
- **Production Monitoring**: LangSmith tracing, Prometheus metrics, Grafana dashboards
- **Cost Optimization**: Template-first strategy, direct template substitution (skips LLM), multi-layer caching
- **Cost Tracking**: Real-time LLM usage cost monitoring via Prometheus metrics
- **Latency Optimization**: Topic filter fast-path, embedding cache warming, trigger-query embeddings
- **PostgreSQL Database**: Production-grade database with async operations and migrations
- **Redis Cache**: Distributed caching for improved performance and scalability
- **API Key Authentication**: Secure endpoints with multi-tier API key validation
- **Enhanced Input Validation**: Spam detection, ID format validation, multi-tier rate limiting
- **Comprehensive Testing**: Unit, integration, and E2E tests
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
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
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
| **Direct Template** | Score ≥ 0.80 + all placeholders fillable | No | High-confidence matches skip LLM entirely. Placeholders are substituted with live property/reservation data. |
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
DIRECT_SUBSTITUTION_THRESHOLD=0.80   # Score threshold for direct substitution
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

### Measured Latency (n=35 queries)

| Metric | Value |
|--------|-------|
| **Average** | 1.07s |
| **p50** | 0.09s |
| **p99** | 5.03s |
| **Min** | 0.01s |
| **Max** | 5.03s |

| Speed Tier | Count | Percentage |
|------------|-------|------------|
| Fast (<1s) | 21 | 60% |
| Medium (1-3s) | 9 | 26% |
| Slow (>3s) | 5 | 14% |

### Latency by Component

| Component | Avg Latency | Max Latency |
|-----------|-------------|-------------|
| Full Request (LangGraph) | 2.22s | 5.03s |
| LLM Call (Groq) | 1.45s | 4.48s |
| Response Generation | 1.05s | 4.50s |
| Guardrails | 0.73s | 3.45s |
| Tool Execution | 0.59s | 1.16s |

### Optimizations

The agent includes several optimizations for low-latency responses:

**Topic Filter Fast-Path**: For common safe queries (check-in times, amenities, parking, etc.), the topic filter uses regex pattern matching (~90ms) instead of an LLM call, reducing guardrails latency significantly.

**Embedding Cache Warming**: At startup, embeddings for 54 common queries are pre-generated in a single batch API call. Cached queries skip the embedding API call entirely.

**Trigger-Query Embeddings**: Templates are indexed by trigger queries, enabling high-confidence semantic matches (0.85-1.00 similarity scores) that qualify for direct template substitution.

### Latency by Path

| Query Path | Typical Latency |
|------------|-----------------|
| Cache hit + fast-path + direct template | ~90ms (p50) |
| Cache miss + fast-path + direct template | ~500ms |
| Fast-path + LLM response | ~2-3s |
| LLM guardrails + LLM response | ~5s |

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
