"""Health check and service status endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Service Health Check")
async def health_check():
    """Verify backend API health and service status."""
    return {"status": "healthy", "service": "AyurEval Backend"}
