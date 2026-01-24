"""Relevance evaluator - Does the response address the user's query?"""

from langchain_core.prompts import ChatPromptTemplate
from evaluation.judges.base import BaseEvaluator


class RelevanceEvaluator(BaseEvaluator):
    """Evaluates whether the response is relevant to the user's query."""

    def get_evaluator_name(self) -> str:
        return "relevance"

    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing the relevance of AI-generated responses to guest accommodation inquiries.

Your task is to evaluate whether the response directly addresses the user's query.

Scoring criteria (1-5):
- 5 (Excellent): Response directly and completely addresses the query. All aspects of the question are covered.
- 4 (Good): Response addresses the query well but may miss minor details or include slight tangents.
- 3 (Acceptable): Response addresses the main point but misses important aspects or includes unnecessary information.
- 2 (Poor): Response is only tangentially related to the query or addresses it incompletely.
- 1 (Fail): Response is completely irrelevant or does not address the query at all.

Consider:
- Does the response answer what was asked?
- Are all parts of multi-part questions addressed?
- Is the information provided relevant to the query?
- Does the response stay focused on the user's needs?

{format_instructions}"""),
            ("user", """Evaluate the relevance of this response:

USER QUERY:
{query}

AGENT RESPONSE:
{response}

ADDITIONAL CONTEXT:
{context}

Provide your evaluation:""")
        ])
