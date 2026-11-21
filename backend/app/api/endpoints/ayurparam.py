"""AyurParam API Endpoints for generative Ayurvedic reasoning and atomic claim extraction.

Exposes:
- POST /api/v1/ayurparam/generate: Synthesize answers grounded in classical Samhitas.
- POST /api/v1/ayurparam/extract-claims: Decompose arbitrary AI text into atomic verifiable claims.
- POST /api/v1/ayurparam/generate-and-extract: One-shot answer synthesis and claim decomposition.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AtomicClaim,
    AyurParamGenerateRequest,
    AyurParamGenerateResponse,
    ExtractClaimsRequest,
    ExtractClaimsResponse,
)
from app.services.ayurparam import ayurparam_service

router = APIRouter()


@router.post(
    "/generate",
    response_model=AyurParamGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an authoritative Ayurvedic answer using AyurParam",
)
async def generate_answer(payload: AyurParamGenerateRequest) -> AyurParamGenerateResponse:
    """Synthesizes clinical and lifestyle answers grounded in the Brihat Trayi

    (Charaka, Sushruta, Ashtanga Hridaya) and traditional commentaries.
    """
    try:
        answer = await ayurparam_service.generate_ayurvedic_answer(payload.question)
        claims_raw = ayurparam_service.extract_atomic_claims(answer)
        claims = [AtomicClaim(**c) for c in claims_raw]

        model_name = payload.model_name or ayurparam_service.model or "AyurParam-Canonical-v1"

        return AyurParamGenerateResponse(
            question=payload.question,
            answer=answer,
            model_used=model_name,
            claims_count=len(claims),
            extracted_claims=claims,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AyurParam generation failed: {str(exc)}",
        ) from exc


@router.post(
    "/extract-claims",
    response_model=ExtractClaimsResponse,
    status_code=status.HTTP_200_OK,
    summary="Decompose AI-generated medical/lifestyle text into atomic verifiable claims",
)
async def extract_claims(payload: ExtractClaimsRequest) -> ExtractClaimsResponse:
    """Breaks down an AI-generated paragraph into discrete, verifiable medical/botanical/lifestyle

    claims with distinct sequential identifiers (claim_id: 1, 2, 3...) for auditing.
    """
    try:
        claims_raw = ayurparam_service.extract_atomic_claims(payload.text)
        claims = [AtomicClaim(**c) for c in claims_raw]

        return ExtractClaimsResponse(
            source_ai_name=payload.source_ai_name or "External AI Model",
            total_claims=len(claims),
            claims=claims,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Claim extraction failed: {str(exc)}",
        ) from exc


@router.post(
    "/generate-and-extract",
    response_model=AyurParamGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="One-step answer generation and atomic claim decomposition",
)
async def generate_and_extract(payload: AyurParamGenerateRequest) -> AyurParamGenerateResponse:
    """Convenience endpoint that synthesizes an answer and decomposes it in a single request."""
    return await generate_answer(payload)

