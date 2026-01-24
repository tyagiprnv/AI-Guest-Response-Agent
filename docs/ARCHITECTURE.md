# AI Guest Response Agent - Architecture Deep Dive

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Agent Workflow](#agent-workflow)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Performance Characteristics](#performance-characteristics)

## Overview

The AI Guest Response Agent is a production-quality system that generates contextual responses to guest accommodation inquiries. It demonstrates advanced AI Engineering patterns including agentic workflows, RAG (Retrieval Augmented Generation), safety guardrails, and comprehensive observability.

### Key Features
- **LangGraph Agent**: State machine with conditional routing
- **Multi-Tool Orchestration**: Parallel execution of templates, property, and reservation lookups
- **Safety First**: PII redaction and topic filtering
- **Cost Optimized**: Template-first strategy with multi-layer caching
- **Production Ready**: Monitoring, metrics, error handling, deployment

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Applications                         │
│                  (Web, Mobile, Chat Interfaces)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    API Routes & Middleware                  │ │
│  │  - CORS          - Rate Limiting      - Request Logging    │ │
│  │  - Auth (future) - Error Handling     - Metrics Export     │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐ │
│  │                  LangGraph Agent Workflow                   │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │ 1. Guardrails Node                                    │  │ │
│  │  │    ├─ PII Redaction (Presidio)                        │  │ │
│  │  │    └─ Topic Filter (LLM-based)                        │  │ │
│  │  └──────────────────┬───────────────────────────────────┘  │ │
│  │                     │                                        │ │
│  │            ┌────────▼─────────┐                             │ │
│  │            │  Passed?         │                             │ │
│  │            │  (Conditional)   │                             │ │
│  │            └─┬──────────────┬─┘                             │ │
│  │              │ No           │ Yes                           │ │
│  │              │              │                               │ │
│  │    ┌─────────▼─┐    ┌──────▼───────────────────┐           │ │
│  │    │  Reject   │    │ 2. Execute Tools (Async)  │           │ │
│  │    │  Response │    │    ├─ Template Retrieval  │           │ │
│  │    └───────────┘    │    ├─ Property Details     │           │ │
│  │                     │    └─ Reservation Details │           │ │
│  │                     └──────┬───────────────────┘           │ │
│  │                            │                               │ │
│  │                     ┌──────▼───────────────────┐           │ │
│  │                     │ 3. Generate Response      │           │ │
│  │                     │    - Template match?      │           │ │
│  │                     │    - Custom generation    │           │ │
│  │                     │    - No response          │           │ │
│  │                     └──────────────────────────┘           │ │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌────────────────┐
│  Qdrant Vector  │  │  LLM APIs    │  │  Data Stores   │
│    Database     │  │  - DeepSeek  │  │  - Properties  │
│  - Templates    │  │  - OpenAI    │  │  - Reservations│
│  - Embeddings   │  │              │  │  - Templates   │
└─────────────────┘  └──────────────┘  └────────────────┘

                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌────────────────┐
│   LangSmith     │  │  Prometheus  │  │    Grafana     │
│    Tracing      │  │   Metrics    │  │   Dashboards   │
└─────────────────┘  └──────────────┘  └────────────────┘
```

## Agent Workflow

### State Machine

The agent is implemented as a LangGraph state machine with the following structure:

```python
@dataclass
class AgentState:
    messages: str                    # User query
    property_id: Optional[str]       # Property context
    reservation_id: Optional[str]    # Reservation context
    guardrail_passed: bool           # Guardrail result
    tools_output: Dict               # Tool execution results
    response: str                    # Generated response
    response_type: str               # template/custom/no_response
    metadata: Dict                   # Execution metadata
```

### Execution Flow

1. **Input Reception**
   - Receive user query, property ID, optional reservation ID
   - Initialize agent state

2. **Guardrail Layer**
   - **PII Redaction**: Scan for sensitive information (email, phone, SSN, credit cards)
   - **Topic Filter**: Classify query topic, reject off-topic requests
   - **Decision**: Pass → continue to tools, Fail → return rejection message

3. **Tool Execution** (Parallel)
   - **Template Retrieval**: Semantic search in Qdrant for matching templates
   - **Property Details**: Lookup property information (check-in, amenities, policies)
   - **Reservation Details**: Fetch reservation data (dates, room type, requests)
   - All tools execute asynchronously in parallel for performance

4. **Response Generation**
   - **Strategy Selection**:
     - If template found with high similarity (>0.75): Use template (fast, cheap)
     - Else if tools returned context: Generate custom response (slower, expensive)
     - Else: Return "cannot help" message
   - **LLM Generation**: Use DeepSeek R1 for response generation
   - **Metadata Collection**: Track tokens, cost, latency

5. **Output**
   - Return response with metadata
   - Log to LangSmith for tracing
   - Export metrics to Prometheus

### Conditional Routing

```python
def route_after_guardrails(state: AgentState) -> str:
    """Route based on guardrail results."""
    if state["guardrail_passed"]:
        return "continue"  # → execute_tools
    else:
        return "reject"    # → generate_response (rejection)
```

## Component Details

### 1. Guardrails Layer

#### PII Redaction
- **Library**: Microsoft Presidio
- **Entities Detected**: EMAIL, PHONE, SSN, CREDIT_CARD, IBAN, IP_ADDRESS
- **Strategy**: Block requests containing PII to prevent leakage
- **Performance**: ~50ms per check (spaCy model)

#### Topic Filter
- **Method**: LLM-based classification
- **Model**: GPT-4o-mini (fast, cheap)
- **Restricted Topics**: Legal advice, medical advice, price negotiation, unrelated queries
- **Strategy**: Structured JSON output with reasoning
- **Performance**: ~500ms per check (cached for similar queries)

### 2. Tool System

#### Template Retrieval Tool
```python
class TemplateRetrievalTool:
    """Semantic search for response templates."""

    def __init__(self):
        self.qdrant_client = QdrantClient()
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = 0.75

    async def retrieve(self, query: str) -> List[Template]:
        # 1. Generate embedding (cached)
        embedding = await self.embedding_service.embed(query)

        # 2. Search Qdrant
        results = self.qdrant_client.search(
            collection_name="templates",
            query_vector=embedding,
            limit=3,
            score_threshold=self.similarity_threshold
        )

        # 3. Return templates
        return [Template.from_qdrant(r) for r in results]
```

**Performance**: 100-200ms (50ms embedding + 50-150ms search)

#### Property Details Tool
- **Data Source**: In-memory repository (JSON files)
- **Caching**: 5-minute TTL on lookups
- **Fields**: check_in_time, check_out_time, amenities, policies, parking
- **Performance**: <10ms (cached), ~50ms (cold)

#### Reservation Details Tool
- **Data Source**: In-memory repository
- **Caching**: 5-minute TTL
- **Fields**: guest_name, dates, room_type, special_requests
- **Performance**: <10ms (cached), ~50ms (cold)
- **Graceful**: Optional tool, continues if reservation not found

### 3. Response Generation

#### Template-First Strategy
```python
def select_response_strategy(tools_output):
    templates = tools_output.get("templates", [])

    if templates and templates[0].similarity > 0.75:
        return "template", templates[0].template

    property_details = tools_output.get("property_details")
    if property_details:
        return "custom", generate_custom_response(...)

    return "no_response", DEFAULT_MESSAGE
```

**Cost Impact**:
- Template response: ~$0.002 (retrieval + embedding only)
- Custom response: ~$0.01-0.02 (includes LLM generation)
- **Savings**: 5-10x cost reduction with 70-80% template match rate

#### Custom Response Generation
- **Model**: DeepSeek R1 (cost-effective)
- **Prompt**: Versioned templates with structured output
- **Context**: Property details, reservation info, retrieved templates
- **Max Tokens**: 500 for response
- **Temperature**: 0.7 for natural variation

### 4. Caching System

Three-layer cache architecture:

```python
class CacheManager:
    """Multi-layer caching for cost optimization."""

    # Layer 1: Embedding Cache
    embedding_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)

    # Layer 2: Tool Result Cache
    tool_cache: TTLCache = TTLCache(maxsize=500, ttl=300)

    # Layer 3: Response Cache
    response_cache: TTLCache = TTLCache(maxsize=100, ttl=60)
```

**Cache Hit Rates** (typical):
- Embeddings: 60-80%
- Tool results: 40-60%
- Responses: 20-40%

**Cost Savings**: 40-60% reduction in API costs

### 5. Monitoring & Observability

#### LangSmith Integration
```python
@traceable(name="agent_execution")
async def run_agent(state: AgentState):
    """Traced agent execution."""
    # All tool calls and LLM interactions automatically traced
    result = await agent_graph.ainvoke(state)
    return result
```

**Captures**:
- Full execution trace
- Tool invocations and results
- LLM prompts and completions
- Latency per component
- Token usage and costs

#### Prometheus Metrics
```python
# Request metrics
agent_requests_total = Counter("agent_requests_total", ["status"])
agent_request_duration = Histogram("agent_request_duration_seconds")

# Quality metrics
agent_response_type = Counter("agent_response_type_total", ["response_type"])
agent_guardrail_triggers = Counter("agent_guardrail_triggers_total", ["guardrail_type"])

# Cost metrics
agent_tokens_used = Counter("agent_tokens_total", ["type"])
agent_cost_usd = Counter("agent_cost_usd_total")

# Performance metrics
agent_tool_duration = Histogram("agent_tool_duration_seconds", ["tool_name"])
cache_hits = Counter("cache_hits_total", ["cache_type"])
cache_misses = Counter("cache_misses_total", ["cache_type"])
```

## Data Flow

### Request Processing

```
1. HTTP Request
   ↓
2. FastAPI Middleware
   ├─ CORS validation
   ├─ Rate limiting (60 req/min)
   └─ Request logging
   ↓
3. Pydantic Validation
   ├─ message: str (required)
   ├─ property_id: str (optional)
   └─ reservation_id: str (optional)
   ↓
4. Agent Invocation
   ├─ Initialize state
   └─ Start LangGraph execution
   ↓
5. Guardrails
   ├─ PII check (50ms)
   └─ Topic filter (500ms)
   ↓
6. Tool Execution (Parallel)
   ├─ Template retrieval (150ms)
   ├─ Property lookup (10ms, cached)
   └─ Reservation lookup (10ms, cached)
   ↓
7. Response Generation
   ├─ Strategy selection
   └─ LLM generation if needed (1-2s)
   ↓
8. Response
   ├─ Format JSON
   ├─ Add metadata
   ├─ Export metrics
   └─ Return to client
```

**Total Latency**:
- P50: ~800ms (template response, cached)
- P95: ~2s (custom response, cached)
- P99: ~3s (custom response, cold cache)

## Technology Stack

### Core Technologies
- **Agent Framework**: LangGraph 0.2.x
- **Web Framework**: FastAPI 0.100+
- **Vector Database**: Qdrant 1.7+
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: DeepSeek R1
- **Guardrails**: Microsoft Presidio, LangChain

### Monitoring & Ops
- **Tracing**: LangSmith
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: Structured JSON logs
- **Deployment**: Docker Compose

### Development
- **Language**: Python 3.11+
- **Testing**: pytest, Locust
- **Type Checking**: mypy (future)
- **Formatting**: black, ruff

## Design Decisions

### Why LangGraph?
- **Stateful**: Maintains state across nodes
- **Conditional Routing**: Dynamic execution paths
- **Observability**: Built-in tracing with LangSmith
- **Modularity**: Easy to add/remove nodes
- **Type Safety**: TypedDict for state management

### Why DeepSeek R1?
- **Cost**: ~90% cheaper than GPT-4
- **Quality**: Sufficient for guest response generation
- **Speed**: Fast enough for real-time responses
- **Reliability**: Stable API

### Why Template-First?
- **Speed**: 5-10x faster than generation
- **Cost**: 5-10x cheaper
- **Consistency**: More predictable responses
- **Quality**: Templates can be human-reviewed

### Why Multi-Layer Caching?
- **Embeddings**: Most expensive, longest TTL (1h)
- **Tool Results**: Medium cost, medium TTL (5min)
- **Responses**: Cheapest, shortest TTL (1min)
- **Tradeoff**: Memory vs. API cost

### Why Parallel Tool Execution?
- **Latency**: 60% reduction vs. sequential
- **User Experience**: Faster responses
- **Tradeoff**: Slightly higher cost (3 API calls vs. selective)

## Performance Characteristics

### Latency Profile
```
Guardrails:      ~550ms  (PII: 50ms, Topic: 500ms)
Tool Execution:  ~150ms  (parallel, cached)
LLM Generation:  ~1.5s   (if needed)
Total:           ~700ms  (template) to ~2.2s (custom)
```

### Cost Profile
```
Template Response:
  - Embedding: $0.0001
  - Qdrant search: $0
  - Total: ~$0.002

Custom Response:
  - Embedding: $0.0001
  - Qdrant search: $0
  - LLM generation: $0.01-0.02
  - Total: ~$0.01-0.02

Savings with 70% template rate:
  - Baseline (all custom): $0.015/req
  - Optimized: $0.006/req
  - Savings: 60%
```

### Throughput
- **Single instance**: 10-50 RPS (depends on template match rate)
- **Bottleneck**: LLM API rate limits
- **Scaling**: Horizontal scaling via Docker Compose

### Resource Usage
- **Memory**: ~500MB baseline, ~1GB under load
- **CPU**: Low (I/O bound, not compute bound)
- **Storage**: Minimal (in-memory caching, no persistence)

## Reliability & Resilience

### Error Handling
- **Tool Failures**: Graceful degradation, continue with available data
- **LLM Timeouts**: Retry with backoff
- **Vector DB Errors**: Fall back to generic response
- **Guardrail Failures**: Default to safe (reject)

### Rate Limiting
- **API Level**: 60 requests/minute (configurable)
- **LLM Provider**: Respect API limits
- **Graceful**: Return 429 with Retry-After header

### Health Checks
- **/health**: Basic liveness check
- **/ready**: Readiness check (Qdrant, cache, etc.)
- **Docker**: Health check in compose file

---

**Version**: 1.0
**Last Updated**: 2026-01-24
**Author**: Pranav Tyagi
