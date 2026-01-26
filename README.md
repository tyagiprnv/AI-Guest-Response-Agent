# AI Guest Response Agent

A production-quality AI agent that generates responses to guest accommodation inquiries. This project demonstrates AI Engineering and MLOps expertise through LangGraph orchestration, multi-tool agentic workflows, comprehensive evaluation, and production monitoring.

## Features

- **Agentic Workflow**: LangGraph-based agent with conditional routing and parallel tool execution
- **Multi-Tool System**: Template retrieval (RAG), property details, and reservation lookups
- **Safety Guardrails**: PII redaction and topic filtering with fast-path optimization
- **Production Monitoring**: LangSmith tracing, Prometheus metrics, Grafana dashboards
- **Cost Optimization**: Template-first strategy, direct template substitution (skips LLM), multi-layer caching
- **Latency Optimization**: Topic filter fast-path (~90ms vs ~3.5s), embedding cache warming at startup
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Docker Deployment**: Full stack deployment with Docker Compose

## Architecture

### Agent Workflow

```mermaid
graph LR
    Start([Guest Message]) --> Guardrails[Apply Guardrails<br/>Detect & Redact PII<br/>Topic Filter ⚡]

    Guardrails -->|Topic Allowed?| Decision{Guardrail Check}

    Decision -->|Rejected| NoResponse[No Response<br/>Polite Decline]
    Decision -->|Approved| Tools[Execute Tools]

    Tools --> T1[Template Retrieval<br/>Qdrant ⚡]
    Tools --> T2[Property Details]
    Tools --> T3[Reservation Details]

    T1 --> Merge[Merge Results]
    T2 --> Merge
    T3 --> Merge

    Merge --> ResponseDecision{Template<br/>Score ≥ 0.65?}

    ResponseDecision -->|Yes| DirectCheck{All Placeholders<br/>Fillable?}
    ResponseDecision -->|No| CustomResponse[Custom Response<br/>Deepseek-V3.2]

    DirectCheck -->|Yes| DirectTemplate[Direct Template<br/>No LLM Call]
    DirectCheck -->|No| TemplateResponse[Template Response<br/>Deepseek-V3.2]

    NoResponse --> End([Return Response])
    DirectTemplate --> End
    TemplateResponse --> End
    CustomResponse --> End

    %% Entry / Exit
    style Start fill:#E5E7EB,stroke:#374151,stroke-width:1.5px,color:#111827
    style End fill:#E5E7EB,stroke:#374151,stroke-width:1.5px,color:#111827

    %% Guardrails / Safety
    style Guardrails fill:#FFEDD5,stroke:#C2410C,stroke-width:1.5px,color:#111827
    style NoResponse fill:#FECACA,stroke:#B91C1C,stroke-width:1.5px,color:#111827

    %% Decisions
    style Decision fill:#DBEAFE,stroke:#1D4ED8,stroke-width:1.5px,color:#111827
    style ResponseDecision fill:#DBEAFE,stroke:#1D4ED8,stroke-width:1.5px,color:#111827
    style DirectCheck fill:#DBEAFE,stroke:#1D4ED8,stroke-width:1.5px,color:#111827

    %% Tool execution
    style Tools fill:#EDE9FE,stroke:#6D28D9,stroke-width:1.5px,color:#111827
    style T1 fill:#EDE9FE,stroke:#6D28D9,stroke-width:1.2px,color:#111827
    style T2 fill:#EDE9FE,stroke:#6D28D9,stroke-width:1.2px,color:#111827
    style T3 fill:#EDE9FE,stroke:#6D28D9,stroke-width:1.2px,color:#111827
    style Merge fill:#DDD6FE,stroke:#6D28D9,stroke-width:1.5px,color:#111827

    %% Successful responses
    style DirectTemplate fill:#A7F3D0,stroke:#047857,stroke-width:1.5px,color:#111827
    style TemplateResponse fill:#D1FAE5,stroke:#047857,stroke-width:1.5px,color:#111827
    style CustomResponse fill:#D1FAE5,stroke:#047857,stroke-width:1.5px,color:#111827


```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangGraph |
| LLM | DeepSeek-V3.2 |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant |
| API | FastAPI |
| Monitoring | LangSmith + Prometheus + Grafana |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- DeepSeek API key
- LangSmith API key (optional)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agentic-project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# For development tools
uv pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required:
#   - OPENAI_API_KEY
#   - DEEPSEEK_API_KEY
# Optional:
#   - LANGSMITH_API_KEY
```

### 3. Start Services

```bash
# Start Qdrant and monitoring stack
docker-compose up -d qdrant prometheus grafana

# Wait for services to be ready
sleep 10
```

### 4. Generate Data and Setup

```bash
# Generate synthetic data (500 templates, 100 properties, 200 reservations)
python scripts/generate_synthetic_data.py

# Index templates in Qdrant
python scripts/setup_qdrant.py
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
# Health check
curl http://localhost:8000/health

# Generate a response
curl -X POST http://localhost:8000/api/v1/generate-response \
  -H "Content-Type: application/json" \
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
| **Direct Template** | Score ≥ 0.65 + all placeholders fillable | No | High-confidence matches skip LLM entirely. Placeholders are substituted with live property/reservation data. |
| **Template Response** | Score ≥ 0.65 + missing placeholders | Yes | Good matches use templates as context for LLM generation. |
| **Custom Response** | Score < 0.65 | Yes | Low matches generate fully custom responses. |

### Direct Template Substitution

For high-confidence template matches, the system performs runtime placeholder substitution:

- Templates contain placeholders like `{check_in_time}`, `{guest_name}`, `{property_name}`
- The system builds context from property and reservation data
- If all placeholders can be filled, the response is returned directly without an LLM call
- This significantly reduces latency and API costs for common queries

Configure via environment variables:
```bash
DIRECT_SUBSTITUTION_THRESHOLD=0.55  # Score threshold for direct substitution
RETRIEVAL_SIMILARITY_THRESHOLD=0.65  # Score threshold for template matching
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

## Performance Optimizations

The agent includes several optimizations for low-latency responses:

### Topic Filter Fast-Path
For common safe queries (check-in times, amenities, parking, etc.), the topic filter uses pattern matching instead of an LLM call:
- **Before**: ~3,500ms (DeepSeek API call)
- **After**: ~90ms (regex pattern matching)

### Embedding Cache Warming
At startup, embeddings for 54 common queries are pre-generated:
- **Cache hit**: ~50ms (no OpenAI API call)
- **Cache miss**: ~500ms (requires OpenAI API call)

### End-to-End Latency

| Query Type | Latency | Path |
|------------|---------|------|
| Common query + template match | **~130ms** | Fast-path + cache hit + direct template |
| New query + template match | **~700ms** | Fast-path + cache miss + direct template |
| Query requiring LLM response | **~3,000ms** | Fast-path + custom/template response |

## Key Metrics

The agent tracks:
- **Quality**: Relevance, accuracy, safety scores
- **Performance**: P50/P95/P99 latency, tokens/request
- **Cost**: Cost per response, template match rate, direct substitution rate
- **Operational**: Error rate, cache hit rate, guardrail triggers, topic filter path (fast_path/llm), direct substitution success/fallback

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

Pranav Tyagi - AI Engineer Portfolio Project
