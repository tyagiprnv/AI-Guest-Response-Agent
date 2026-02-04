"""
Fetch latency data from LangSmith for recent runs.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from langsmith import Client


def fetch_langsmith_data(project_name: str = None, limit: int = 55):
    """Fetch and analyze recent runs from LangSmith."""
    client = Client()

    # Use provided project name or default
    if project_name is None:
        project_name = os.getenv("LANGCHAIN_PROJECT", "GuestAgent")

    print(f"Fetching runs from project: {project_name}\n")

    # Fetch recent runs
    runs = list(client.list_runs(
        project_name=project_name,
        limit=limit + 5,  # Fetch a few extra in case some are incomplete
        is_root=True,
    ))

    # Get the most recent runs
    recent_runs = sorted(runs, key=lambda r: r.start_time or 0, reverse=True)[:limit]

    print(f"Latest {len(recent_runs)} runs:\n")
    print("=" * 90)
    print(f"{'Input':<50} {'Latency':<10} {'Tokens':<10}")
    print("=" * 90)

    latencies = []
    for run in recent_runs:
        if run.end_time and run.start_time:
            latency = (run.end_time - run.start_time).total_seconds()
            latencies.append(latency)

            inputs = run.inputs or {}
            message = inputs.get("guest_message", str(inputs)[:47])[:47]
            tokens = run.total_tokens or 0

            print(f"{message:<50} {latency:<10.2f} {tokens:<10}")

    if latencies:
        latencies_sorted = sorted(latencies)
        print("=" * 90)
        print(f"\nLatency Stats (n={len(latencies)}):")
        print(f"  Average: {sum(latencies)/len(latencies):.2f}s")
        print(f"  Min: {min(latencies):.2f}s")
        print(f"  Max: {max(latencies):.2f}s")

        p50_idx = int(len(latencies_sorted) * 0.5)
        p95_idx = min(int(len(latencies_sorted) * 0.95), len(latencies_sorted) - 1)
        p99_idx = min(int(len(latencies_sorted) * 0.99), len(latencies_sorted) - 1)
        print(f"  p50: {latencies_sorted[p50_idx]:.2f}s")
        print(f"  p95: {latencies_sorted[p95_idx]:.2f}s")
        print(f"  p99: {latencies_sorted[p99_idx]:.2f}s")

        # Count fast vs slow
        fast = sum(1 for l in latencies if l < 1.0)
        medium = sum(1 for l in latencies if 1.0 <= l < 3.0)
        slow = sum(1 for l in latencies if l >= 3.0)
        print(f"\n  Fast (<1s): {fast}")
        print(f"  Medium (1-3s): {medium}")
        print(f"  Slow (>3s): {slow}")

        return {
            "average": sum(latencies) / len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "p50": latencies_sorted[p50_idx],
            "p95": latencies_sorted[p95_idx],
            "p99": latencies_sorted[p99_idx],
            "fast_count": fast,
            "medium_count": medium,
            "slow_count": slow,
        }

    return None


if __name__ == "__main__":
    fetch_langsmith_data()
