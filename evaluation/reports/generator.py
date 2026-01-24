"""Report generator for evaluation results."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
import logging

from evaluation.runner import EvaluationMetrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates evaluation reports in various formats."""

    def __init__(self, output_dir: str = "evaluation/reports/output"):
        """Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_stats(self, results: List[EvaluationMetrics]) -> Dict[str, Any]:
        """Generate summary statistics from evaluation results.

        Args:
            results: List of evaluation metrics

        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {}

        total = len(results)
        passed = sum(1 for r in results if r.all_passed)
        failed = total - passed

        # Score statistics
        relevance_scores = [r.relevance_score for r in results]
        accuracy_scores = [r.accuracy_score for r in results]
        safety_scores = [r.safety_score for r in results]
        average_scores = [r.average_score for r in results]

        # Performance statistics
        latencies = [r.latency_ms for r in results]
        costs = [r.cost_usd for r in results]
        template_matches = sum(1 for r in results if r.template_matched)

        # Response type distribution
        response_types = defaultdict(int)
        for r in results:
            response_types[r.response_type] += 1

        return {
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "scores": {
                "relevance": {
                    "average": sum(relevance_scores) / total,
                    "min": min(relevance_scores),
                    "max": max(relevance_scores),
                    "pass_rate": sum(1 for s in relevance_scores if s >= 3) / total,
                },
                "accuracy": {
                    "average": sum(accuracy_scores) / total,
                    "min": min(accuracy_scores),
                    "max": max(accuracy_scores),
                    "pass_rate": sum(1 for s in accuracy_scores if s >= 3) / total,
                },
                "safety": {
                    "average": sum(safety_scores) / total,
                    "min": min(safety_scores),
                    "max": max(safety_scores),
                    "pass_rate": sum(1 for s in safety_scores if s >= 3) / total,
                },
                "overall": {
                    "average": sum(average_scores) / total,
                    "min": min(average_scores),
                    "max": max(average_scores),
                },
            },
            "performance": {
                "latency_ms": {
                    "average": sum(latencies) / total,
                    "min": min(latencies),
                    "max": max(latencies),
                    "p50": sorted(latencies)[total // 2],
                    "p95": sorted(latencies)[int(total * 0.95)],
                    "p99": sorted(latencies)[int(total * 0.99)] if total > 100 else max(latencies),
                },
                "cost_usd": {
                    "total": sum(costs),
                    "average": sum(costs) / total,
                    "min": min(costs),
                    "max": max(costs),
                },
                "template_match_rate": template_matches / total if total > 0 else 0,
            },
            "response_types": dict(response_types),
        }

    def find_best_and_worst_cases(
        self, results: List[EvaluationMetrics], n: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find best and worst performing test cases.

        Args:
            results: List of evaluation metrics
            n: Number of cases to return

        Returns:
            Dict with 'best' and 'worst' case lists
        """
        sorted_by_score = sorted(results, key=lambda r: r.average_score, reverse=True)

        best = sorted_by_score[:n]
        worst = sorted_by_score[-n:]

        return {
            "best": [
                {
                    "test_case_id": r.test_case_id,
                    "query": r.query,
                    "response": r.response[:200] + "..." if len(r.response) > 200 else r.response,
                    "average_score": r.average_score,
                    "relevance": r.relevance_score,
                    "accuracy": r.accuracy_score,
                    "safety": r.safety_score,
                }
                for r in best
            ],
            "worst": [
                {
                    "test_case_id": r.test_case_id,
                    "query": r.query,
                    "response": r.response[:200] + "..." if len(r.response) > 200 else r.response,
                    "average_score": r.average_score,
                    "relevance": r.relevance_score,
                    "accuracy": r.accuracy_score,
                    "safety": r.safety_score,
                    "relevance_reasoning": r.relevance_reasoning,
                    "accuracy_reasoning": r.accuracy_reasoning,
                    "safety_reasoning": r.safety_reasoning,
                }
                for r in worst
            ],
        }

    def save_json_report(
        self,
        results: List[EvaluationMetrics],
        filename: str = None,
    ) -> Path:
        """Save detailed JSON report.

        Args:
            results: List of evaluation metrics
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_report_{timestamp}.json"

        filepath = self.output_dir / filename

        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_cases": len(results),
            },
            "summary": self.generate_summary_stats(results),
            "examples": self.find_best_and_worst_cases(results),
            "detailed_results": [r.model_dump() for r in results],
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved JSON report to {filepath}")
        return filepath

    def save_markdown_report(
        self,
        results: List[EvaluationMetrics],
        filename: str = None,
    ) -> Path:
        """Save markdown report.

        Args:
            results: List of evaluation metrics
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_report_{timestamp}.md"

        filepath = self.output_dir / filename

        summary = self.generate_summary_stats(results)
        examples = self.find_best_and_worst_cases(results)

        # Build markdown
        md = []
        md.append("# AI Guest Response Agent - Evaluation Report")
        md.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"\n**Total Test Cases**: {summary['total_cases']}")

        # Overall Results
        md.append("\n## Overall Results\n")
        md.append(f"- **Pass Rate**: {summary['pass_rate']:.1%}")
        md.append(f"- **Passed**: {summary['passed']} cases")
        md.append(f"- **Failed**: {summary['failed']} cases")

        # Quality Scores
        md.append("\n## Quality Scores\n")
        md.append("| Metric | Average | Min | Max | Pass Rate |")
        md.append("|--------|---------|-----|-----|-----------|")

        for metric_name in ["relevance", "accuracy", "safety"]:
            metric = summary["scores"][metric_name]
            md.append(
                f"| {metric_name.capitalize()} | "
                f"{metric['average']:.2f} | "
                f"{metric['min']} | "
                f"{metric['max']} | "
                f"{metric['pass_rate']:.1%} |"
            )

        md.append(
            f"| **Overall** | "
            f"**{summary['scores']['overall']['average']:.2f}** | "
            f"{summary['scores']['overall']['min']:.2f} | "
            f"{summary['scores']['overall']['max']:.2f} | "
            f"- |"
        )

        # Performance Metrics
        md.append("\n## Performance Metrics\n")
        perf = summary["performance"]

        md.append("### Latency")
        md.append(f"- **Average**: {perf['latency_ms']['average']:.0f}ms")
        md.append(f"- **P50**: {perf['latency_ms']['p50']:.0f}ms")
        md.append(f"- **P95**: {perf['latency_ms']['p95']:.0f}ms")
        md.append(f"- **P99**: {perf['latency_ms']['p99']:.0f}ms")

        md.append("\n### Cost")
        md.append(f"- **Total**: ${perf['cost_usd']['total']:.4f}")
        md.append(f"- **Average per request**: ${perf['cost_usd']['average']:.4f}")
        md.append(f"- **Min**: ${perf['cost_usd']['min']:.4f}")
        md.append(f"- **Max**: ${perf['cost_usd']['max']:.4f}")

        md.append("\n### Efficiency")
        md.append(f"- **Template Match Rate**: {perf['template_match_rate']:.1%}")

        # Response Types
        md.append("\n## Response Type Distribution\n")
        for resp_type, count in summary["response_types"].items():
            percentage = count / summary["total_cases"] * 100
            md.append(f"- **{resp_type}**: {count} ({percentage:.1f}%)")

        # Best Cases
        md.append("\n## Best Performing Cases\n")
        for i, case in enumerate(examples["best"], 1):
            md.append(f"\n### {i}. {case['test_case_id']} (Score: {case['average_score']:.2f})")
            md.append(f"\n**Query**: {case['query']}")
            md.append(f"\n**Response**: {case['response']}")
            md.append(f"\n**Scores**: Relevance={case['relevance']}, Accuracy={case['accuracy']}, Safety={case['safety']}")

        # Worst Cases
        md.append("\n## Cases Needing Improvement\n")
        for i, case in enumerate(examples["worst"], 1):
            md.append(f"\n### {i}. {case['test_case_id']} (Score: {case['average_score']:.2f})")
            md.append(f"\n**Query**: {case['query']}")
            md.append(f"\n**Response**: {case['response']}")
            md.append(f"\n**Scores**: Relevance={case['relevance']}, Accuracy={case['accuracy']}, Safety={case['safety']}")
            md.append(f"\n**Issues**:")
            md.append(f"- Relevance: {case['relevance_reasoning']}")
            md.append(f"- Accuracy: {case['accuracy_reasoning']}")
            md.append(f"- Safety: {case['safety_reasoning']}")

        # Recommendations
        md.append("\n## Recommendations\n")

        if summary["pass_rate"] < 0.8:
            md.append("- **Overall pass rate is below 80%** - Review failed cases and improve prompts/guardrails")

        if summary["scores"]["relevance"]["pass_rate"] < 0.85:
            md.append("- **Relevance scores need improvement** - Review prompt engineering and tool selection logic")

        if summary["scores"]["accuracy"]["pass_rate"] < 0.85:
            md.append("- **Accuracy issues detected** - Verify context retrieval and reduce hallucinations")

        if summary["scores"]["safety"]["pass_rate"] < 0.95:
            md.append("- **Safety concerns** - Strengthen guardrails and review PII/topic filtering")

        if perf["template_match_rate"] < 0.7:
            md.append("- **Low template match rate** - Consider adding more templates or adjusting similarity threshold")

        if perf["latency_ms"]["p95"] > 3000:
            md.append("- **High latency at P95** - Optimize tool execution or add more aggressive caching")

        # Save
        with open(filepath, "w") as f:
            f.write("\n".join(md))

        logger.info(f"Saved markdown report to {filepath}")
        return filepath

    def generate_reports(
        self, results: List[EvaluationMetrics]
    ) -> Dict[str, Path]:
        """Generate both JSON and markdown reports.

        Args:
            results: List of evaluation metrics

        Returns:
            Dict mapping format to filepath
        """
        return {
            "json": self.save_json_report(results),
            "markdown": self.save_markdown_report(results),
        }
