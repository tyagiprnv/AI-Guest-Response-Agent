"""Evaluation runner for testing agent performance on test cases."""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from evaluation.judges import (
    RelevanceEvaluator,
    AccuracyEvaluator,
    SafetyEvaluator,
    EvaluationResult,
)
from src.agent.graph import create_agent_graph
from src.data.models import Property, Reservation

logger = logging.getLogger(__name__)


class TestCase(BaseModel):
    """A test case for evaluation."""

    id: str
    category: str
    query: str
    property_id: Optional[str] = None
    reservation_id: Optional[str] = None
    expected_behavior: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationMetrics(BaseModel):
    """Metrics for a single test case evaluation."""

    test_case_id: str
    query: str
    response: str
    response_type: str

    # Evaluation scores
    relevance_score: int
    relevance_reasoning: str
    relevance_passed: bool

    accuracy_score: int
    accuracy_reasoning: str
    accuracy_passed: bool

    safety_score: int
    safety_reasoning: str
    safety_passed: bool

    # Performance metrics
    latency_ms: float
    tokens_used: int
    cost_usd: float
    template_matched: bool

    # Overall
    all_passed: bool
    average_score: float

    # Context used
    context: Dict[str, Any] = Field(default_factory=dict)


class EvaluationRunner:
    """Runs evaluation on test cases."""

    def __init__(
        self,
        test_cases_path: str = "data/test_cases.json",
        model_name: str = "deepseek-chat",
        passing_score: int = 3,
    ):
        """Initialize evaluation runner.

        Args:
            test_cases_path: Path to test cases JSON file
            model_name: Model for LLM-as-Judge (deepseek-chat recommended)
            passing_score: Minimum score to pass (1-5)
        """
        self.test_cases_path = Path(test_cases_path)
        self.model_name = model_name
        self.passing_score = passing_score

        # Initialize evaluators
        self.relevance_evaluator = RelevanceEvaluator(
            model_name=model_name,
            passing_score=passing_score,
        )
        self.accuracy_evaluator = AccuracyEvaluator(
            model_name=model_name,
            passing_score=passing_score,
        )
        self.safety_evaluator = SafetyEvaluator(
            model_name=model_name,
            passing_score=passing_score,
        )

        # Initialize agent graph
        self.agent = create_agent_graph()

    def load_test_cases(self) -> List[TestCase]:
        """Load test cases from JSON file."""
        try:
            with open(self.test_cases_path) as f:
                data = json.load(f)

            test_cases = [TestCase(**tc) for tc in data]
            logger.info(f"Loaded {len(test_cases)} test cases from {self.test_cases_path}")
            return test_cases

        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            raise

    async def run_agent(
        self,
        query: str,
        property_id: Optional[str] = None,
        reservation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the agent on a single query.

        Returns:
            Dict with response, response_type, latency, tokens, cost, etc.
        """
        try:
            start_time = time.time()

            # Prepare input
            from src.agent.state import AgentState
            initial_state: AgentState = {
                "messages": query,
                "property_id": property_id,
                "reservation_id": reservation_id,
                "guardrail_passed": True,
                "tools_output": {},
                "response": "",
                "response_type": "no_response",
                "metadata": {},
            }

            # Run agent
            result = await self.agent.ainvoke(initial_state)

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": result.get("response", ""),
                "response_type": result.get("response_type", "no_response"),
                "latency_ms": latency_ms,
                "tokens_used": result.get("metadata", {}).get("total_tokens", 0),
                "cost_usd": result.get("metadata", {}).get("total_cost", 0.0),
                "template_matched": result.get("response_type") == "template",
                "tools_output": result.get("tools_output", {}),
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "response": f"Error: {str(e)}",
                "response_type": "error",
                "latency_ms": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "template_matched": False,
                "tools_output": {},
                "metadata": {"error": str(e)},
            }

    def evaluate_response(
        self,
        query: str,
        response: str,
        context: Dict[str, Any],
    ) -> Dict[str, EvaluationResult]:
        """Run all evaluators on a response.

        Args:
            query: User's query
            response: Agent's response
            context: Context used (property details, templates, etc.)

        Returns:
            Dict mapping evaluator name to EvaluationResult
        """
        evaluations = {}

        # Relevance
        try:
            evaluations["relevance"] = self.relevance_evaluator.evaluate(
                query=query,
                response=response,
                context=context,
            )
        except Exception as e:
            logger.error(f"Relevance evaluation failed: {e}")

        # Accuracy
        try:
            evaluations["accuracy"] = self.accuracy_evaluator.evaluate(
                query=query,
                response=response,
                context=context,
            )
        except Exception as e:
            logger.error(f"Accuracy evaluation failed: {e}")

        # Safety
        try:
            evaluations["safety"] = self.safety_evaluator.evaluate(
                query=query,
                response=response,
                context=context,
            )
        except Exception as e:
            logger.error(f"Safety evaluation failed: {e}")

        return evaluations

    async def evaluate_test_case(self, test_case: TestCase) -> EvaluationMetrics:
        """Evaluate a single test case.

        Args:
            test_case: Test case to evaluate

        Returns:
            EvaluationMetrics with all scores and metrics
        """
        logger.info(f"Evaluating test case: {test_case.id} - {test_case.category}")

        # Run agent
        agent_result = await self.run_agent(
            query=test_case.query,
            property_id=test_case.property_id,
            reservation_id=test_case.reservation_id,
        )

        # Prepare context for evaluators
        context = {
            "property_details": agent_result["tools_output"].get("property_details"),
            "reservation_details": agent_result["tools_output"].get("reservation_details"),
            "templates": agent_result["tools_output"].get("templates"),
            "response_type": agent_result["response_type"],
            "expected_behavior": test_case.expected_behavior,
        }

        # Run evaluations
        evaluations = self.evaluate_response(
            query=test_case.query,
            response=agent_result["response"],
            context=context,
        )

        # Compile metrics
        relevance = evaluations.get("relevance")
        accuracy = evaluations.get("accuracy")
        safety = evaluations.get("safety")

        scores = [
            relevance.score if relevance else 1,
            accuracy.score if accuracy else 1,
            safety.score if safety else 1,
        ]
        average_score = sum(scores) / len(scores)

        all_passed = all([
            relevance.passed if relevance else False,
            accuracy.passed if accuracy else False,
            safety.passed if safety else False,
        ])

        metrics = EvaluationMetrics(
            test_case_id=test_case.id,
            query=test_case.query,
            response=agent_result["response"],
            response_type=agent_result["response_type"],
            relevance_score=relevance.score if relevance else 1,
            relevance_reasoning=relevance.reasoning if relevance else "Evaluation failed",
            relevance_passed=relevance.passed if relevance else False,
            accuracy_score=accuracy.score if accuracy else 1,
            accuracy_reasoning=accuracy.reasoning if accuracy else "Evaluation failed",
            accuracy_passed=accuracy.passed if accuracy else False,
            safety_score=safety.score if safety else 1,
            safety_reasoning=safety.reasoning if safety else "Evaluation failed",
            safety_passed=safety.passed if safety else False,
            latency_ms=agent_result["latency_ms"],
            tokens_used=agent_result["tokens_used"],
            cost_usd=agent_result["cost_usd"],
            template_matched=agent_result["template_matched"],
            all_passed=all_passed,
            average_score=average_score,
            context=context,
        )

        return metrics

    async def run_evaluation(
        self,
        limit: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[EvaluationMetrics]:
        """Run evaluation on all test cases.

        Args:
            limit: Maximum number of test cases to evaluate
            category: Filter by category (optional)

        Returns:
            List of EvaluationMetrics
        """
        test_cases = self.load_test_cases()

        # Filter by category
        if category:
            test_cases = [tc for tc in test_cases if tc.category == category]

        # Limit
        if limit:
            test_cases = test_cases[:limit]

        logger.info(f"Running evaluation on {len(test_cases)} test cases")

        # Run evaluations
        results = []
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Progress: {i}/{len(test_cases)}")
            metrics = await self.evaluate_test_case(test_case)
            results.append(metrics)

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

        logger.info(f"Evaluation complete: {len(results)} test cases evaluated")
        return results


async def main():
    """Run evaluation and print summary."""
    runner = EvaluationRunner()

    # Run evaluation
    results = await runner.run_evaluation(limit=10)  # Start with 10 for testing

    # Print summary
    print(f"\n{'='*60}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total test cases: {len(results)}")
    print(f"Passed: {sum(1 for r in results if r.all_passed)}")
    print(f"Failed: {sum(1 for r in results if not r.all_passed)}")
    print(f"\nAverage scores:")
    print(f"  Relevance: {sum(r.relevance_score for r in results) / len(results):.2f}")
    print(f"  Accuracy:  {sum(r.accuracy_score for r in results) / len(results):.2f}")
    print(f"  Safety:    {sum(r.safety_score for r in results) / len(results):.2f}")
    print(f"  Overall:   {sum(r.average_score for r in results) / len(results):.2f}")
    print(f"\nPerformance:")
    print(f"  Avg latency: {sum(r.latency_ms for r in results) / len(results):.0f}ms")
    print(f"  Avg cost:    ${sum(r.cost_usd for r in results) / len(results):.4f}")
    print(f"  Template match rate: {sum(1 for r in results if r.template_matched) / len(results) * 100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
