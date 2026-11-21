"""API routes and routers package for AyurEval."""

from fastapi import APIRouter
from app.api.endpoints import health, rag, verification

api_router = APIRouter()

# Register core endpoint routers with prefixes
api_router.include_router(health.router, prefix="/health", tags=["Health & Status"])
api_router.include_router(
    verification.router, prefix="/verification", tags=["Answer Verification"]
)
api_router.include_router(
    rag.router, prefix="/rag", tags=["Corpus Retrieval & RAG"]
)

__all__ = ["api_router"]

