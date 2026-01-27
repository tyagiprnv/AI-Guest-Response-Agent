# Load Testing with Locust

This directory contains load testing scenarios for the AI Guest Response Agent API.

## Prerequisites

```bash
uv add locust
```

## Running Load Tests

### Basic Load Test

Test with 10 concurrent users, ramping up 1 user per second:

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 1 --run-time 5m
```

### Web UI Mode

For interactive testing with graphs and real-time stats:

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

### Headless Mode

For automated testing without the web UI:

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless \
  --html=reports/load_test_report.html
```

## Test Scenarios

### GuestResponseUser (Normal Load)
- Simulates typical user behavior
- 1-5 second wait between requests
- Mix of simple queries (10x) and reservation queries (3x)
- Occasional health checks

### HighLoadUser (Stress Test)
- Simulates high load scenarios
- 0.1-0.5 second wait between requests
- Rapid fire requests to test rate limiting and system limits

## Example Commands

### Light Load (Development)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 5 \
  --spawn-rate 1 \
  --run-time 2m \
  --headless
```

### Medium Load (Staging)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless \
  --html=reports/medium_load.html
```

### High Load (Stress Test)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 10 \
  --run-time 15m \
  --headless \
  --html=reports/stress_test.html
```

### Spike Test (Sudden Traffic)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 50 \
  --run-time 5m \
  --headless
```

## Monitoring During Tests

While running load tests, monitor:

1. **Grafana Dashboards**: http://localhost:3000
   - Agent Performance dashboard
   - System Health dashboard
   - Cost & Efficiency dashboard

2. **Prometheus**: http://localhost:9090
   - Query metrics directly

3. **Application Logs**:
   ```bash
   docker-compose logs -f api
   ```

4. **Locust Web UI**: http://localhost:8089 (if not headless)

## Key Metrics to Watch

- **Response Time**: P50, P95, P99 should stay under 3s
- **Error Rate**: Should be < 1%
- **RPS**: Requests per second sustained
- **Cache Hit Rate**: Should be 40-60%
- **Template Match Rate**: Should be 70-80%
- **Cost per Request**: Should stay under $0.02

## Expected Performance

Based on the agent's design:

| Metric | Target | Notes |
|--------|--------|-------|
| P50 Latency | < 1s | With caching |
| P95 Latency | < 2s | Typical |
| P99 Latency | < 3s | Max acceptable |
| Error Rate | < 1% | Excluding rate limits |
| Throughput | 10-50 RPS | Single instance |
| Template Match | 70-80% | Cost optimization |
| Cache Hit Rate | 40-60% | Typical usage |

## Troubleshooting

### High Error Rates
- Check application logs for errors
- Verify Qdrant is running: `docker-compose ps qdrant`
- Check API keys are set in `.env`

### High Latency
- Check if LLM API (Groq/OpenAI) is slow
- Monitor cache hit rates (low = more API calls)
- Check Qdrant response times

### Rate Limiting (429 errors)
- This is expected under high load
- Adjust rate limits in `src/api/middleware.py`
- Or reduce spawn rate in load test

### Out of Memory
- Monitor with: `docker stats`
- Reduce concurrent users
- Check for memory leaks in application logs

## Generating Reports

After a test run:

1. **HTML Report**: Generated with `--html` flag
2. **CSV Stats**: Use `--csv` flag
   ```bash
   locust ... --csv=reports/stats
   ```

3. **Custom Analysis**: Parse Locust stats
   ```python
   import pandas as pd
   df = pd.read_csv('reports/stats_stats.csv')
   print(df.describe())
   ```

## CI/CD Integration

Run automated load tests in CI:

```bash
#!/bin/bash
# ci/load_test.sh

# Start services
docker-compose up -d

# Wait for health
sleep 30

# Run load test
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 20 \
  --spawn-rate 2 \
  --run-time 5m \
  --headless \
  --html=reports/ci_load_test.html

# Check exit code
if [ $? -eq 0 ]; then
  echo "Load test passed"
  exit 0
else
  echo "Load test failed"
  exit 1
fi
```

## Best Practices

1. **Warm Up**: Let the system warm up before measuring
2. **Realistic Data**: Use production-like queries and property IDs
3. **Monitor Everything**: Watch Grafana, Prometheus, logs simultaneously
4. **Gradual Ramp**: Use appropriate spawn rates
5. **Document Results**: Save reports and note observations
6. **Compare Baselines**: Track performance over time
