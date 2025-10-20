"""
Health Router
Health check and collection information endpoints
"""

from fastapi import APIRouter, HTTPException, status

from app.models import HealthResponse, CollectionInfoResponse
from app.qdrant_service import qdrant_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check Qdrant connection and collection status

    Returns health status of the service
    """
    try:
        health = await qdrant_service.check_health()

        return HealthResponse(
            status="healthy" if health["connected"] else "unhealthy",
            qdrant_connected=health["connected"],
            collection_exists=health.get("collection_exists", False),
            message=health.get("error")
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            qdrant_connected=False,
            collection_exists=False,
            message=str(e)
        )


@router.get("/collection/info", response_model=CollectionInfoResponse)
async def get_collection_info():
    """
    Get Qdrant collection information

    Returns collection statistics and configuration
    """
    try:
        info = await qdrant_service.get_collection_info()
        return CollectionInfoResponse(**info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection info: {str(e)}"
        )
