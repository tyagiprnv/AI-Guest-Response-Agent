"""
Analyze LLM calls from LangSmith to understand latency breakdown by parent span.
"""
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

from langsmith import Client


def analyze_llm_calls(project_name: str = None, limit: int = 50):
    """Analyze LLM calls grouped by parent span."""
    client = Client()

    # Use provided project name or default
    if project_name is None:
        project_name = os.getenv("LANGCHAIN_PROJECT", "AIGuestAgent")

    print(f"Analyzing LLM calls from project: {project_name}\n")

    # Get LLM runs
    llm_runs = list(client.list_runs(
        project_name=project_name,
        run_type="llm",
        limit=limit,
    ))

    print(f"Found {len(llm_runs)} LLM runs\n")

    # Group by parent
    parent_stats = defaultdict(lambda: {"count": 0, "total_latency": 0, "total_tokens": 0})

    for run in llm_runs:
        if run.end_time and run.start_time:
            latency = (run.end_time - run.start_time).total_seconds()
            parent_name = "root"

            if run.parent_run_id:
                try:
                    parent = client.read_run(run.parent_run_id)
                    parent_name = parent.name or "unknown"
                except Exception:
                    pass

            parent_stats[parent_name]["count"] += 1
            parent_stats[parent_name]["total_latency"] += latency
            parent_stats[parent_name]["total_tokens"] += (run.total_tokens or 0)

    print("LLM Calls by Parent Span:")
    print("=" * 70)
    print(f"{'Parent':<25} {'Count':<8} {'Total Time':<12} {'Avg Time':<10} {'Tokens':<10}")
    print("=" * 70)

    for parent, stats in sorted(parent_stats.items(), key=lambda x: x[1]["total_latency"], reverse=True):
        avg = stats["total_latency"] / stats["count"] if stats["count"] > 0 else 0
        print(f"{parent:<25} {stats['count']:<8} {stats['total_latency']:<12.1f}s {avg:<10.2f}s {stats['total_tokens']:<10}")

    print("=" * 70)

    # Summary
    total_calls = sum(s["count"] for s in parent_stats.values())
    total_time = sum(s["total_latency"] for s in parent_stats.values())

    if total_calls > 0:
        print(f"\nTotal: {total_calls} LLM calls, {total_time:.1f}s total LLM time")
        print(f"Average LLM latency: {total_time/total_calls:.2f}s per call")

    return dict(parent_stats)


def analyze_child_spans(project_name: str = None, num_runs: int = 15):
    """Analyze all child spans for latency breakdown."""
    client = Client()

    if project_name is None:
        project_name = os.getenv("LANGCHAIN_PROJECT", "AIGuestAgent")

    # Get root runs
    root_runs = list(client.list_runs(
        project_name=project_name,
        limit=num_runs,
        is_root=True,
    ))

    print(f"\nAnalyzing child spans for {len(root_runs)} root runs...\n")

    # Aggregate stats by span name
    span_stats = defaultdict(list)

    for root_run in root_runs:
        # Get all child runs for this root
        child_runs = list(client.list_runs(
            project_name=project_name,
            trace_id=root_run.trace_id,
        ))

        for child in child_runs:
            if child.end_time and child.start_time:
                latency = (child.end_time - child.start_time).total_seconds()
                name = child.name or "unknown"
                span_stats[name].append(latency)

    print("=" * 80)
    print(f"{'Span Name':<40} {'Count':<8} {'Avg(s)':<10} {'Max(s)':<10}")
    print("=" * 80)

    # Sort by total time spent
    sorted_spans = sorted(span_stats.items(), key=lambda x: sum(x[1]), reverse=True)

    for name, latencies in sorted_spans[:20]:
        avg = sum(latencies) / len(latencies)
        max_lat = max(latencies)
        print(f"{name[:38]:<40} {len(latencies):<8} {avg:<10.2f} {max_lat:<10.2f}")

    print("=" * 80)

    return dict(span_stats)


if __name__ == "__main__":
    analyze_llm_calls()
    print("\n" + "=" * 80 + "\n")
    analyze_child_spans()
