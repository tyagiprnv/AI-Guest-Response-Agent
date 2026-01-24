# Deployment & Troubleshooting Guide

## Table of Contents
- [Deployment Options](#deployment-options)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)
- [Monitoring](#monitoring)

## Deployment Options

### 1. Local Development
- **Use Case**: Development, debugging, testing
- **Setup Time**: 5-10 minutes
- **Requirements**: Python 3.11+, Docker
- **Pros**: Fast iteration, full control, easy debugging
- **Cons**: Manual setup, not production-ready

### 2. Docker Compose (Recommended for Testing)
- **Use Case**: Integration testing, staging, demos
- **Setup Time**: 2-3 minutes
- **Requirements**: Docker, Docker Compose
- **Pros**: Easy setup, reproducible, isolated
- **Cons**: Single machine, not highly available

### 3. Kubernetes (Production)
- **Use Case**: Production deployment at scale
- **Setup Time**: 1-2 hours
- **Requirements**: Kubernetes cluster
- **Pros**: Scalable, resilient, production-grade
- **Cons**: Complex setup, higher cost

### 4. Cloud Platforms
- **Options**: AWS ECS, Google Cloud Run, Azure Container Instances
- **Use Case**: Production with managed infrastructure
- **Pros**: Managed, scalable, integrations
- **Cons**: Vendor lock-in, potentially higher cost

## Local Development Setup

### Prerequisites

```bash
# Python 3.11+
python --version

# Docker (for Qdrant, Prometheus, Grafana)
docker --version

# Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Step-by-Step Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd agentic-project
```

#### 2. Install Dependencies
```bash
# Install package in editable mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"

# Download spaCy model for PII detection
python -m spacy download en_core_web_sm
```

#### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or vim, code, etc.
```

**Required Variables**:
```bash
# OpenAI (for embeddings and evaluation)
OPENAI_API_KEY=sk-...

# DeepSeek (for agent LLM)
DEEPSEEK_API_KEY=sk-...

# LangSmith (optional, for tracing)
LANGSMITH_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-guest-response-agent
```

#### 4. Start Infrastructure Services
```bash
# Start Qdrant, Prometheus, Grafana
docker-compose up -d qdrant prometheus grafana

# Wait for services to be ready
sleep 10

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                STATUS    PORTS
qdrant              running   6333->6333, 6334->6334
prometheus          running   9090->9090
grafana             running   3000->3000
```

#### 5. Generate Data and Setup
```bash
# Generate synthetic data
python scripts/generate_synthetic_data.py

# Index templates in Qdrant
python scripts/setup_qdrant.py
```

Expected output:
```
Generated 500 templates
Generated 100 properties
Generated 200 reservations
Generated 50 test cases
✓ Data saved to data/

Connecting to Qdrant...
Creating collection 'templates'...
Indexing 500 templates...
✓ Templates indexed successfully
```

#### 6. Run the Application
```bash
# Development mode
python src/main.py

# Or with uvicorn (auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 7. Verify Setup
```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/v1/generate-response \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is check-in?", "property_id": "prop_001"}'

# Open Swagger docs
open http://localhost:8000/docs
```

## Docker Deployment

### Full Stack with Docker Compose

#### docker-compose.yml

```yaml
version: '3.8'

services:
  # Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # AI Agent API
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./infrastructure/grafana/datasources:/etc/grafana/provisioning/datasources
      - ./infrastructure/grafana/dashboards:/etc/grafana/dashboards
      - ./infrastructure/grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
    depends_on:
      - prometheus

volumes:
  qdrant_data:
  prometheus_data:
  grafana_data:
```

#### Start Full Stack

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Check status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

#### Scale API Service

```bash
# Run 3 instances of the API
docker-compose up -d --scale api=3

# Requires load balancer (nginx, traefik, etc.)
```

## Production Deployment

### Environment Configuration

**Production .env**:
```bash
# Environment
ENVIRONMENT=production

# API Keys (use secrets manager in production)
OPENAI_API_KEY=${OPENAI_API_KEY_SECRET}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY_SECRET}

# Qdrant
QDRANT_HOST=qdrant.internal.example.com
QDRANT_PORT=6333
QDRANT_API_KEY=${QDRANT_API_KEY_SECRET}

# LangSmith
LANGSMITH_API_KEY=${LANGSMITH_API_KEY_SECRET}
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-guest-response-prod

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (restrict in production)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Best Practices

1. **Use Secrets Manager**
   - AWS Secrets Manager, HashiCorp Vault, etc.
   - Never commit API keys to git

2. **Enable HTTPS**
   - Use reverse proxy (nginx, Caddy)
   - Obtain SSL certificates (Let's Encrypt)

3. **Set Resource Limits**
   ```yaml
   api:
     deploy:
       resources:
         limits:
           memory: 2G
           cpus: '1.0'
         reservations:
           memory: 1G
           cpus: '0.5'
   ```

4. **Health Checks & Monitoring**
   - Configure health check endpoints
   - Set up alerts in Grafana
   - Monitor logs aggregation (ELK, Datadog)

5. **Backup & Recovery**
   - Backup Qdrant data regularly
   - Test restore procedures
   - Document recovery steps

6. **Security Hardening**
   - Run as non-root user
   - Scan images for vulnerabilities
   - Enable network policies
   - Use API authentication (JWT, OAuth)

## Troubleshooting

### Common Issues

#### 1. API Key Errors

**Symptom**:
```
AuthenticationError: Invalid API key
```

**Diagnosis**:
```bash
# Check environment variables are set
env | grep API_KEY

# In Docker, check container env
docker exec <container-id> env | grep API_KEY
```

**Solutions**:
- Verify API keys in `.env` file
- Ensure `.env` is loaded (use `python-dotenv`)
- In Docker, check `environment` section in `docker-compose.yml`
- Test API keys directly:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  ```

#### 2. Qdrant Connection Failed

**Symptom**:
```
ConnectionError: Could not connect to Qdrant at localhost:6333
```

**Diagnosis**:
```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Check Qdrant health
curl http://localhost:6333/health

# Check Qdrant collections
curl http://localhost:6333/collections
```

**Solutions**:
- Start Qdrant: `docker-compose up -d qdrant`
- Wait for Qdrant to be ready (can take 10-30s)
- Check port mapping in `docker-compose.yml`
- If using Docker network, use service name: `QDRANT_HOST=qdrant`
- Check firewall rules

#### 3. Templates Not Found

**Symptom**:
```
No templates found in collection
```

**Diagnosis**:
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/templates

# Check points count
curl http://localhost:6333/collections/templates | jq .result.points_count
```

**Solutions**:
- Run indexing script: `python scripts/setup_qdrant.py`
- Verify data files exist: `ls data/templates.json`
- Generate data if missing: `python scripts/generate_synthetic_data.py`
- Check Qdrant logs: `docker logs qdrant`

#### 4. High Latency

**Symptom**: Responses take > 5 seconds

**Diagnosis**:
```bash
# Check Grafana dashboards
open http://localhost:3000

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(agent_request_duration_seconds_bucket[5m]))'

# Check cache hit rate
curl 'http://localhost:9090/api/v1/query?query=rate(cache_hits_total[5m])'
```

**Solutions**:
- **Low cache hit rate** → Increase cache TTL, warm up cache
- **Slow LLM API** → Check DeepSeek/OpenAI status pages
- **Slow Qdrant** → Check Qdrant resource usage, add indexes
- **High load** → Scale API instances, add load balancer
- **Network issues** → Check latency to external APIs

#### 5. Memory Issues

**Symptom**:
```
MemoryError: Out of memory
```

**Diagnosis**:
```bash
# Check memory usage
docker stats

# Check logs for OOM
docker logs api | grep -i memory
```

**Solutions**:
- Increase Docker memory limit
- Reduce cache sizes in `src/data/cache.py`
- Limit concurrent requests
- Enable memory profiling:
  ```python
  import tracemalloc
  tracemalloc.start()
  ```

#### 6. Rate Limiting Issues

**Symptom**:
```
HTTP 429: Too Many Requests
```

**Diagnosis**:
```bash
# Check rate limit settings
grep RATE_LIMIT .env

# Check Prometheus metrics
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])'
```

**Solutions**:
- Increase rate limit: Edit `RATE_LIMIT_PER_MINUTE` in `.env`
- Use exponential backoff in clients
- Implement request queuing
- Scale API instances

#### 7. PII Detection Not Working

**Symptom**: PII not being detected/blocked

**Diagnosis**:
```bash
# Check if spaCy model is installed
python -c "import spacy; spacy.load('en_core_web_sm')"

# Test Presidio directly
python -c "from presidio_analyzer import AnalyzerEngine; print(AnalyzerEngine().analyze(text='test@example.com', language='en'))"
```

**Solutions**:
- Install spaCy model: `python -m spacy download en_core_web_sm`
- Update Presidio: `pip install --upgrade presidio-analyzer presidio-anonymizer`
- Check guardrail is enabled in agent graph

#### 8. LangSmith Traces Not Appearing

**Symptom**: No traces in LangSmith dashboard

**Diagnosis**:
```bash
# Check environment variables
echo $LANGSMITH_API_KEY
echo $LANGCHAIN_TRACING_V2

# Check logs for LangSmith errors
docker logs api | grep -i langsmith
```

**Solutions**:
- Set `LANGCHAIN_TRACING_V2=true` in `.env`
- Verify LangSmith API key: Visit https://smith.langchain.com/settings
- Check internet connectivity to LangSmith servers
- Restart application after changing env vars

## Performance Tuning

### Optimize for Latency

```python
# Increase parallel execution
# In src/agent/graph.py
max_parallel_tools = 5  # Up from 3

# Reduce tool timeouts
tool_timeout = 5  # seconds

# Increase cache sizes
from cachetools import TTLCache
embedding_cache = TTLCache(maxsize=2000, ttl=7200)  # Up from 1000/3600

# Use faster embedding model (trade quality for speed)
EMBEDDING_MODEL = "text-embedding-ada-002"  # Faster than 3-small
```

### Optimize for Cost

```python
# Lower similarity threshold (more template matches)
TEMPLATE_SIMILARITY_THRESHOLD = 0.70  # Down from 0.75

# Increase cache TTLs
tool_cache_ttl = 600  # 10 minutes instead of 5

# Use cheaper models
AGENT_MODEL = "deepseek-chat"  # Already optimal
JUDGE_MODEL = "gpt-4o-mini"    # Instead of gpt-4o
```

### Optimize for Throughput

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 5  # Run 5 instances
  environment:
    - WORKERS=4  # Uvicorn workers per instance
```

```python
# In src/main.py
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # CPU cores
    limit_concurrency=100,  # Max concurrent requests
)
```

## Monitoring

### Key Metrics to Monitor

```yaml
Alerts:
  # High error rate
  - alert: HighErrorRate
    expr: rate(agent_requests_total{status="error"}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "Error rate above 5%"

  # High latency
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(agent_request_duration_seconds_bucket[5m])) > 3
    for: 5m
    annotations:
      summary: "P95 latency above 3s"

  # Low cache hit rate
  - alert: LowCacheHitRate
    expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.3
    for: 10m
    annotations:
      summary: "Cache hit rate below 30%"

  # Service down
  - alert: ServiceDown
    expr: up{job="agent-api"} == 0
    for: 1m
    annotations:
      summary: "Agent API is down"
```

### Grafana Dashboards

Access pre-configured dashboards:
- Agent Performance: http://localhost:3000/d/agent-performance
- Quality Metrics: http://localhost:3000/d/quality-metrics
- Cost Optimization: http://localhost:3000/d/cost-optimization
- System Health: http://localhost:3000/d/system-health

### Log Aggregation

For production, aggregate logs to centralized system:

```yaml
# docker-compose.yml
api:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
      # Or use logging driver for ELK, Datadog, etc.
      # driver: "syslog"
      # options:
      #   syslog-address: "tcp://logstash:5000"
```

---

**Version**: 1.0
**Last Updated**: 2026-01-24
**Author**: Pranav Tyagi
