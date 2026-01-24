"""Accuracy evaluator - Is the information correct based on context?"""

from langchain_core.prompts import ChatPromptTemplate
from evaluation.judges.base import BaseEvaluator


class AccuracyEvaluator(BaseEvaluator):
    """Evaluates whether the response provides accurate information based on available context."""

    def get_evaluator_name(self) -> str:
        return "accuracy"

    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing the factual accuracy of AI-generated responses.

Your task is to evaluate whether the information in the response is accurate based on the provided context.

Scoring criteria (1-5):
- 5 (Excellent): All information is completely accurate and consistent with the context. No errors or hallucinations.
- 4 (Good): Information is mostly accurate with only minor inconsistencies that don't affect the core message.
- 3 (Acceptable): Information is generally accurate but contains some errors or unverified claims.
- 2 (Poor): Information contains significant errors or contradicts the provided context.
- 1 (Fail): Information is completely inaccurate, fabricated, or directly contradicts the context.

Consider:
- Does the response match the facts in the context (property details, reservation info, etc.)?
- Are any claims made without supporting evidence in the context?
- Are there any hallucinated details (specific times, prices, policies not in context)?
- If context is unavailable, does the response appropriately indicate uncertainty?

Important:
- If no context was provided but the response makes specific claims, that's a hallucination (low score).
- Generic helpful responses without specific claims should score neutral (3).

{format_instructions}"""),
            ("user", """Evaluate the accuracy of this response:

USER QUERY:
{query}

AGENT RESPONSE:
{response}

AVAILABLE CONTEXT:
{context}

Provide your evaluation:""")
        ])
