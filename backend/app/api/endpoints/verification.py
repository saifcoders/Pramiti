"""Verification endpoints for AyurEval (COGNEXA).

Provides source-aware, multi-hop fact verification across classical Samhita texts
(Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya) and modern scientific studies
using the real RAG + AyurParam verification pipeline.
"""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.models.schemas import (
    AskRequest,
    ClaimVerificationResult,
    VerificationCategory,
    VerificationReportResponse,
    VerifyRequest,
)
from app.services.ayurparam import ayurparam_service
from app.services.verification.auditor import verification_auditor
from app.services.safety_checker import safety_checker

router = APIRouter()


# ---------------------------------------------------------------------------
# Batch Verification Schemas
# ---------------------------------------------------------------------------

class BatchVerifyRequest(BaseModel):
    claims: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of Ayurvedic claims to audit (1–10 items)",
    )
    source_name: Optional[str] = Field(None, description="Optional label for the source of claims")


class ClaimBatchResult(BaseModel):
    claim_index: int
    claim_text: str
    category: str
    classical_reference: Optional[str] = None
    reasoning: Optional[str] = None
    is_safe: bool
    safety_alerts: List[str] = Field(default_factory=list)


class BatchAnalyticsSummary(BaseModel):
    total_claims: int
    supported: int
    partially_supported: int
    contradicted: int
    insufficient_evidence: int
    reference_not_verified: int
    total_safety_flags: int
    critical_safety_flags: int


class BatchVerifyResponse(BaseModel):
    source_name: Optional[str] = None
    analytics: BatchAnalyticsSummary
    results: List[ClaimBatchResult]


@router.post(
    "/ask",
    response_model=VerificationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit question for AyurParam generation and real AyurEval verification",
)
async def ask_question(request: AskRequest) -> VerificationReportResponse:
    """Accepts an Ayurveda clinical/lifestyle question, synthesizes an authentic answer
    via AyurParam ChromaDB RAG, decomposes it into atomic claims, and cross-audits each claim
    against indexed classical Samhita corpora and modern scientific evidence.
    """
    try:
        # Step 1: Synthesize classical answer via AyurParam RAG
        answer = await ayurparam_service.generate_ayurvedic_answer(request.question)

        # Step 2: Audit text through the real 4-step verification pipeline
        report = await verification_auditor.audit_text(
            text=answer,
            query_context=request.question,
        )
        return report
    except Exception as exc:
        print(f"[VerificationEndpoint] Real pipeline error in /ask: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AyurEval verification pipeline failed during /ask: {str(exc)}",
        )


@router.post(
    "/verify",
    response_model=VerificationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Audit AI-generated Ayurveda answer using real classical evidence cross-referencing",
)
async def verify_answer(request: VerifyRequest) -> VerificationReportResponse:
    """Accepts an AI-generated Ayurveda text, decomposes it into atomic claims,
    queries ChromaDB for closest classical Samhita shlokas, and assigns verified category verdicts.
    """
    source_label = (
        f"Verified from {request.source_ai_name}"
        if request.source_ai_name
        else "External AI Response"
    )
    try:
        # Real verification pipeline: decomposition -> ChromaDB retrieval -> cross-audit
        report = await verification_auditor.audit_text(
            text=request.ai_generated_text,
            query_context=source_label,
        )
        return report
    except Exception as exc:
        print(f"[VerificationEndpoint] Real pipeline error in /verify: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AyurEval verification pipeline failed during /verify: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Batch Verification Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/batch",
    response_model=BatchVerifyResponse,
    status_code=status.HTTP_200_OK,
    tags=["Batch Verification & Analytics"],
    summary="Batch-audit up to 10 Ayurvedic claims with aggregated analytics",
    description=(
        "Concurrently evaluates up to 10 claims against indexed classical Brihat Trayi treatises "
        "and runs phytovigilance safety checks. Returns individual claim outcomes alongside an aggregated "
        "summary (supported, contradicted, insufficient, safety flags)."
    ),
)
async def batch_verify_claims(request: BatchVerifyRequest) -> BatchVerifyResponse:
    """Accepts up to 10 Ayurvedic claims/statements, runs verification and safety checks
    across all items in parallel, and returns aggregated analytics + per-claim results.
    """
    claims_input: List[str] = [c.strip() for c in request.claims if c.strip()]
    if not claims_input:
        raise HTTPException(status_code=400, detail="No non-empty claims provided.")

    async def audit_single_claim(idx: int, claim: str) -> ClaimBatchResult:
        """Audit one claim through the real pipeline with graceful fallback."""
        # --- Classical Verification ---
        category = VerificationCategory.INSUFFICIENT_EVIDENCE.value
        classical_reference: Optional[str] = None
        reasoning: Optional[str] = None
        try:
            report = await verification_auditor.audit_text(text=claim, query_context=claim)
            if report.claims:
                first = report.claims[0]
                category = first.category.value if hasattr(first.category, "value") else str(first.category)
                classical_reference = first.classical_reference
                reasoning = first.reasoning
        except Exception as exc:
            print(f"[BatchVerify] audit_text failed for claim {idx}: {exc}")

        # --- Safety Check ---
        is_safe = True
        safety_alert_msgs: List[str] = []
        try:
            safety_result = safety_checker.scan_text(claim)
            is_safe = safety_result.is_safe
            safety_alert_msgs = [a.message for a in safety_result.alerts]
        except Exception as exc:
            print(f"[BatchVerify] safety_checker failed for claim {idx}: {exc}")

        return ClaimBatchResult(
            claim_index=idx,
            claim_text=claim,
            category=category,
            classical_reference=classical_reference,
            reasoning=reasoning,
            is_safe=is_safe,
            safety_alerts=safety_alert_msgs,
        )

    # Run all claims concurrently
    tasks = [audit_single_claim(i + 1, c) for i, c in enumerate(claims_input)]
    results: List[ClaimBatchResult] = await asyncio.gather(*tasks)

    # --- Aggregate Analytics ---
    cat_counters = {
        VerificationCategory.SUPPORTED_BY_SOURCE.value: 0,
        VerificationCategory.PARTIALLY_SUPPORTED.value: 0,
        VerificationCategory.CONTRADICTED_BY_SOURCE.value: 0,
        VerificationCategory.INSUFFICIENT_EVIDENCE.value: 0,
        VerificationCategory.REFERENCE_NOT_VERIFIED.value: 0,
    }
    total_safety = 0
    critical_safety = 0

    for r in results:
        # Normalize category to match enum values
        cat_key = r.category
        if cat_key in cat_counters:
            cat_counters[cat_key] += 1
        else:
            cat_counters[VerificationCategory.INSUFFICIENT_EVIDENCE.value] += 1
        total_safety += len(r.safety_alerts)
        # Critical: any alert in the safety_alerts list (simple heuristic: flag if not is_safe)
        if not r.is_safe:
            critical_safety += 1

    analytics = BatchAnalyticsSummary(
        total_claims=len(results),
        supported=cat_counters.get(VerificationCategory.SUPPORTED_BY_SOURCE.value, 0),
        partially_supported=cat_counters.get(VerificationCategory.PARTIALLY_SUPPORTED.value, 0),
        contradicted=cat_counters.get(VerificationCategory.CONTRADICTED_BY_SOURCE.value, 0),
        insufficient_evidence=cat_counters.get(VerificationCategory.INSUFFICIENT_EVIDENCE.value, 0),
        reference_not_verified=cat_counters.get(VerificationCategory.REFERENCE_NOT_VERIFIED.value, 0),
        total_safety_flags=total_safety,
        critical_safety_flags=critical_safety,
    )

    return BatchVerifyResponse(
        source_name=request.source_name,
        analytics=analytics,
        results=results,
    )
