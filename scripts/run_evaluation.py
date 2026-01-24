#!/usr/bin/env python3
"""Script to run comprehensive evaluation of the agent."""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.runner import EvaluationRunner
from evaluation.reports.generator import ReportGenerator
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run evaluation and generate reports."""
    parser = argparse.ArgumentParser(description="Run agent evaluation")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of test cases to evaluate",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter test cases by category",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        help="Model for LLM-as-Judge evaluation",
    )
    parser.add_argument(
        "--passing-score",
        type=int,
        default=3,
        help="Minimum score to pass (1-5)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/reports/output",
        help="Directory to save reports",
    )

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("AI Guest Response Agent - Evaluation")
    logger.info("="*60)
    logger.info(f"Model: {args.model}")
    logger.info(f"Passing score: {args.passing_score}")
    if args.limit:
        logger.info(f"Limit: {args.limit} test cases")
    if args.category:
        logger.info(f"Category filter: {args.category}")
    logger.info("="*60)

    # Initialize runner
    runner = EvaluationRunner(
        model_name=args.model,
        passing_score=args.passing_score,
    )

    # Run evaluation
    logger.info("\nStarting evaluation...")
    results = await runner.run_evaluation(
        limit=args.limit,
        category=args.category,
    )

    # Generate reports
    logger.info("\nGenerating reports...")
    report_gen = ReportGenerator(output_dir=args.output_dir)
    report_paths = report_gen.generate_reports(results)

    # Print summary
    passed = sum(1 for r in results if r.all_passed)
    failed = len(results) - passed

    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)
    print(f"\nTest Cases: {len(results)}")
    print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")

    print("\nAverage Scores:")
    print(f"  Relevance: {sum(r.relevance_score for r in results)/len(results):.2f}/5.0")
    print(f"  Accuracy:  {sum(r.accuracy_score for r in results)/len(results):.2f}/5.0")
    print(f"  Safety:    {sum(r.safety_score for r in results)/len(results):.2f}/5.0")
    print(f"  Overall:   {sum(r.average_score for r in results)/len(results):.2f}/5.0")

    print("\nPerformance:")
    print(f"  Avg latency: {sum(r.latency_ms for r in results)/len(results):.0f}ms")
    print(f"  Total cost:  ${sum(r.cost_usd for r in results):.4f}")
    print(f"  Avg cost:    ${sum(r.cost_usd for r in results)/len(results):.4f}")
    print(f"  Template match rate: {sum(1 for r in results if r.template_matched)/len(results)*100:.1f}%")

    print("\nReports saved:")
    print(f"  JSON:     {report_paths['json']}")
    print(f"  Markdown: {report_paths['markdown']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
