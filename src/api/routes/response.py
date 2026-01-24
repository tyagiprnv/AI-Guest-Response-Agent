"""
Response generation endpoint.
"""
from fastapi import APIRouter, HTTPException, status

from src.agent.graph import run_agent
from src.api.schemas import GenerateResponseRequest, GenerateResponseResponse, ResponseMetadata
from src.data.cache import response_cache
from src.monitoring.logging import get_logger
from src.monitoring.metrics import cache_hit, cache_miss

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/generate-response",
    response_model=GenerateResponseResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_response(request: GenerateResponseRequest):
    """
    Generate a response to a guest message.

    This endpoint:
    1. Applies safety guardrails (PII redaction, topic filtering)
    2. Retrieves relevant response templates
    3. Fetches property and reservation details
    4. Generates an appropriate response

    The response can be:
    - **template**: Based on a pre-written template (fastest, most consistent)
    - **custom**: Custom generated response (when no template matches)
    - **no_response**: Request was blocked by guardrails
    - **error**: An error occurred during processing
    """

    # Check response cache
    cached_response = response_cache.get_response(
        request.message, request.property_id, request.reservation_id
    )

    if cached_response:
        cache_hit.labels(cache_type="response").inc()
        logger.info("Returning cached response")
        return GenerateResponseResponse(**cached_response)

    cache_miss.labels(cache_type="response").inc()

    # Run agent
    try:
        result = await run_agent(
            guest_message=request.message,
            property_id=request.property_id,
            reservation_id=request.reservation_id,
        )

        # Build response
        response = GenerateResponseResponse(
            response_text=result["response_text"],
            response_type=result["response_type"],
            confidence_score=result["confidence_score"],
            metadata=ResponseMetadata(**result["metadata"]),
        )

        # Cache successful responses (not errors)
        if result["response_type"] != "error":
            response_cache.set_response(
                request.message,
                request.property_id,
                request.reservation_id,
                response.model_dump(),
            )

        return response

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )
