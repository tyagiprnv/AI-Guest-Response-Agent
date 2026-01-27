"""
Fetch and display relevant Prometheus metrics from the application.
"""
import requests

METRICS_URL = "http://localhost:8000/metrics"


def fetch_metrics():
    response = requests.get(METRICS_URL)
    metrics = response.text

    # Metrics of interest for latency analysis
    metrics_of_interest = [
        "topic_filter_path",
        "direct_substitution",
        "cache_hits",
        "cache_misses",
        "request_duration",
        "guardrail_triggered",
    ]

    print("Prometheus Metrics:\n")
    print("=" * 70)

    for line in metrics.split('\n'):
        if any(m in line for m in metrics_of_interest):
            # Skip comment lines and 'created' timestamp metrics
            if not line.startswith('#') and 'created' not in line:
                print(line)

    print("=" * 70)


if __name__ == "__main__":
    fetch_metrics()
