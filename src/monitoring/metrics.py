"""
Prometheus metrics for monitoring.
"""
from functools import wraps
from time import time

from prometheus_client import Counter, Histogram, Gauge, Info

# Request metrics
request_count = Counter(
    'agent_requests_total',
    'Total number of agent requests',
    ['status', 'response_type']
)

request_duration = Histogram(
    'agent_request_duration_seconds',
    'Request duration in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Response metrics
response_type_count = Counter(
    'agent_response_type_total',
    'Response types generated',
    ['response_type']
)

direct_substitution_count = Counter(
    'agent_direct_substitution_total',
    'Direct substitution attempts',
    ['status']  # 'success', 'fallback_unfilled', 'fallback_low_score'
)

template_match_rate = Gauge(
    'agent_template_match_rate',
    'Rate of template matches'
)

# Cost metrics
tokens_used = Counter(
    'agent_tokens_used_total',
    'Total tokens used',
    ['token_type']
)

cost_usd = Counter(
    'agent_cost_usd_total',
    'Total cost in USD',
    ['response_type', 'model']
)

# Tool metrics
tool_execution_duration = Histogram(
    'agent_tool_execution_seconds',
    'Tool execution duration',
    ['tool_name'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

tool_execution_count = Counter(
    'agent_tool_executions_total',
    'Tool execution count',
    ['tool_name', 'status']
)

# Guardrail metrics
guardrail_triggered = Counter(
    'agent_guardrail_triggered_total',
    'Guardrail triggers',
    ['guardrail_type']
)

topic_filter_path = Counter(
    'agent_topic_filter_path_total',
    'Topic filter path taken',
    ['path']  # 'fast_path' or 'llm'
)

pii_detected = Counter(
    'agent_pii_detected_total',
    'PII detection count'
)

# Cache metrics
cache_hit = Counter(
    'agent_cache_hits_total',
    'Cache hits',
    ['cache_type']
)

cache_miss = Counter(
    'agent_cache_misses_total',
    'Cache misses',
    ['cache_type']
)

# Error metrics
error_count = Counter(
    'agent_errors_total',
    'Error count',
    ['error_type']
)

# System info
system_info = Info(
    'agent_system',
    'System information'
)


def track_request_duration(func):
    """Decorator to track request duration."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time()
        try:
            result = await func(*args, **kwargs)
            duration = time() - start_time
            request_duration.observe(duration)
            return result
        except Exception as e:
            duration = time() - start_time
            request_duration.observe(duration)
            raise
    return wrapper


def track_tool_execution(tool_name: str):
    """Decorator to track tool execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time()
            try:
                result = await func(*args, **kwargs)
                duration = time() - start_time
                tool_execution_duration.labels(tool_name=tool_name).observe(duration)
                tool_execution_count.labels(tool_name=tool_name, status='success').inc()
                return result
            except Exception as e:
                duration = time() - start_time
                tool_execution_duration.labels(tool_name=tool_name).observe(duration)
                tool_execution_count.labels(tool_name=tool_name, status='error').inc()
                raise
        return wrapper
    return decorator
