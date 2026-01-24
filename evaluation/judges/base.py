"""Base evaluator class for LLM-as-Judge pattern."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Result from an LLM-as-Judge evaluation."""

    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    reasoning: str = Field(..., description="Explanation for the score")
    passed: bool = Field(..., description="Whether evaluation passed threshold")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseEvaluator(ABC):
    """Base class for all LLM-as-Judge evaluators."""

    def __init__(
        self,
        model_name: str = "deepseek-chat",
        temperature: float = 0.0,
        passing_score: int = 3,
        api_key: Optional[str] = None,
    ):
        """Initialize evaluator.

        Args:
            model_name: Model to use for evaluation
            temperature: Temperature for LLM generation
            passing_score: Minimum score to pass (1-5)
            api_key: API key (will use settings if not provided)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.passing_score = passing_score

        # Get API key from settings if not provided
        if api_key is None:
            from src.config.settings import get_settings
            settings = get_settings()
            api_key = settings.deepseek_api_key

        self.llm = ChatDeepSeek(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )

        self.parser = JsonOutputParser(pydantic_object=EvaluationResult)

    @abstractmethod
    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the prompt template for this evaluator."""
        pass

    @abstractmethod
    def get_evaluator_name(self) -> str:
        """Return the name of this evaluator."""
        pass

    def evaluate(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate a response using LLM-as-Judge.

        Args:
            query: User's original query
            response: Agent's response to evaluate
            context: Additional context (property details, templates, etc.)

        Returns:
            EvaluationResult with score and reasoning
        """
        try:
            # Build the prompt
            prompt = self.get_prompt_template()

            # Prepare inputs
            inputs = {
                "query": query,
                "response": response,
                "context": self._format_context(context or {}),
                "format_instructions": self.parser.get_format_instructions(),
            }

            # Run evaluation
            chain = prompt | self.llm | self.parser
            result = chain.invoke(inputs)

            # Convert to EvaluationResult
            eval_result = EvaluationResult(
                score=result["score"],
                reasoning=result["reasoning"],
                passed=result["score"] >= self.passing_score,
                metadata={
                    "evaluator": self.get_evaluator_name(),
                    "model": self.model_name,
                    "passing_score": self.passing_score,
                }
            )

            logger.info(
                f"{self.get_evaluator_name()} evaluation: "
                f"score={eval_result.score}, passed={eval_result.passed}"
            )

            return eval_result

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Return a failed evaluation
            return EvaluationResult(
                score=1,
                reasoning=f"Evaluation failed: {str(e)}",
                passed=False,
                metadata={"error": str(e)}
            )

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string."""
        if not context:
            return "No additional context provided."

        formatted = []
        for key, value in context.items():
            if value is not None:
                formatted.append(f"{key}: {value}")

        return "\n".join(formatted) if formatted else "No additional context provided."
