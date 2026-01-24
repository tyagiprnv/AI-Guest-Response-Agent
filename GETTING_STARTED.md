# Getting Started with AI Guest Response Agent

This guide will walk you through setting up and running the AI Guest Response Agent.

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.11 or higher** installed
2. **Docker and Docker Compose** installed
3. **API Keys**:
   - OpenAI API key (required)
   - DeepSeek API key (required)
   - LangSmith API key (optional, for tracing)

## Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
# Install the package and dependencies
pip install -e .

# Download spaCy model for PII detection
python -m spacy download en_core_web_sm

# (Optional) Install development tools
pip install -e ".[dev]"
```

This will install all required packages including:
- LangChain and LangGraph for agent orchestration
- FastAPI for the API server
- Qdrant client for vector database
- Presidio for PII detection
- Prometheus client for metrics
- And more...

### Step 2: Configure API Keys

Edit the `.env` file and add your API keys:

```bash
# Open .env in your editor
nano .env  # or vim, code, etc.
```

Update these lines with your actual keys:
```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
DEEPSEEK_API_KEY=your-actual-deepseek-key-here
LANGSMITH_API_KEY=your-actual-langsmith-key-here  # Optional
```

**Where to get keys:**
- OpenAI: https://platform.openai.com/api-keys
- DeepSeek: https://platform.deepseek.com/api_keys
- LangSmith: https://smith.langchain.com/settings

### Step 3: Start Docker Services

Start Qdrant (vector database) and monitoring services:

```bash
docker-compose up -d qdrant prometheus grafana
```

Verify services are running:
```bash
docker-compose ps
```

You should see all services with status "Up".

### Step 4: Generate Synthetic Data

Generate the training data (templates, properties, reservations):

```bash
python scripts/generate_synthetic_data.py
```

This creates:
- 500 response templates across different categories
- 100 properties with varied attributes
- 200 reservations
- 50 test cases

### Step 5: Index Templates in Qdrant

Index the templates into the vector database:

```bash
python scripts/setup_qdrant.py
```

This will:
1. Create a Qdrant collection
2. Generate embeddings for all templates
3. Index them for semantic search

### Step 6: Verify Setup

Run the verification script:

```bash
python scripts/verify_setup.py
```

This checks that all necessary files and data are in place.

### Step 7: Start the Application

Run the FastAPI application:

```bash
python src/main.py
```

Or use uvicorn directly:
```bash
uvicorn src.main:app --reload
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 8: Test the API

#### Via Swagger UI (Interactive)

Open your browser to: http://localhost:8000/docs

You'll see the interactive API documentation where you can:
1. Click on the `/api/v1/generate-response` endpoint
2. Click "Try it out"
3. Enter a test request
4. Click "Execute"

#### Via cURL (Command Line)

```bash
curl -X POST http://localhost:8000/api/v1/generate-response \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What time is check-in?",
    "property_id": "prop_001"
  }'
```

Expected response:
```json
{
  "response_text": "Check-in is available from 3:00 PM onwards...",
  "response_type": "template",
  "confidence_score": 0.92,
  "metadata": {
    "execution_time_ms": 450.5,
    "pii_detected": false,
    "templates_found": 3
  }
}
```

#### Via Python

```python
import httpx
import asyncio

async def test_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/generate-response",
            json={
                "message": "What time is check-in?",
                "property_id": "prop_001"
            }
        )
        print(response.json())

asyncio.run(test_agent())
```

## Accessing Monitoring Tools

### Swagger API Documentation
- URL: http://localhost:8000/docs
- Interactive API documentation
- Try out endpoints directly in the browser

### Prometheus Metrics
- URL: http://localhost:9090
- View raw metrics
- Query metrics with PromQL
- Example query: `agent_request_duration_seconds`

### Grafana Dashboards
- URL: http://localhost:3000
- Default credentials: admin/admin
- Visualize metrics in real-time
- Create custom dashboards

### Qdrant Dashboard
- URL: http://localhost:6333/dashboard
- View collections
- Inspect indexed vectors
- Search interface

### LangSmith (if configured)
- URL: https://smith.langchain.com
- View execution traces
- Debug agent workflow
- Track costs and performance

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Example Queries to Try

### Simple queries (should use templates):
- "What time is check-in?"
- "Do you have parking?"
- "Is WiFi available?"
- "What's your cancellation policy?"

### Complex queries (may use custom generation):
- "I'm arriving late tonight, what should I do?"
- "Can I bring my dog and also need parking?"
- "What amenities do you have for families with young children?"

### Queries that trigger guardrails:
- "Can you give me legal advice about my booking?"
- "My credit card number is 1234-5678-9012-3456" (PII)
- "Can you lower the price for me?" (pricing negotiation)

## Troubleshooting

### Issue: "Collection not found" error

**Solution**: Run the setup script again:
```bash
python scripts/setup_qdrant.py
```

### Issue: "ModuleNotFoundError"

**Solution**: Install dependencies:
```bash
pip install -e .
python -m spacy download en_core_web_sm
```

### Issue: Qdrant connection refused

**Solution**: Ensure Docker services are running:
```bash
docker-compose up -d qdrant
# Wait a few seconds
curl http://localhost:6333/healthz
```

### Issue: API returns 500 errors

**Solution**: Check the logs for details:
```bash
# If running via docker-compose
docker-compose logs api

# If running locally
# Check the terminal output where you ran python src/main.py
```

### Issue: Slow response times

**Solutions**:
1. Check if caching is working (should see cache hits in metrics)
2. Verify Qdrant is running smoothly
3. Check your internet connection (API calls to OpenAI/DeepSeek)

## Next Steps

Now that your system is running:

1. **Explore the code**:
   - Start with `src/agent/graph.py` to see the agent workflow
   - Look at `src/agent/nodes.py` for the core logic
   - Review `src/tools/` for tool implementations

2. **Customize**:
   - Add your own templates to `data/templates/`
   - Modify prompts in `src/agent/prompts.py`
   - Adjust settings in `.env`

3. **Monitor**:
   - Watch metrics in Grafana
   - View traces in LangSmith
   - Check logs for insights

4. **Extend**:
   - Add new tools (weather, local attractions, etc.)
   - Implement additional guardrails
   - Create custom evaluation metrics

## Need Help?

- Check `PROJECT_STATUS.md` for implementation details
- Review `README.md` for architecture overview
- Look at test files for usage examples
- Check Docker logs: `docker-compose logs -f`

## Production Deployment

To run the full stack in production:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale the API
docker-compose up -d --scale api=3

# Stop all services
docker-compose down
```

Congratulations! You now have a fully functional AI Guest Response Agent running locally. 🎉
