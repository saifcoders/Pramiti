"""Biomedical evidence endpoints for AyurEval (COGNEXA).

Exposes search functionality over modern clinical literature and PubMed
for Ayurvedic herbs, formulations, and therapeutic claims.

Also exposes the Classical vs. Biomedical Dual-Evidence Cross-Auditor.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.biomedical_service import biomedical_service, BiomedicalResult
from app.services.verification.dual_auditor import dual_auditor

router = APIRouter()


# ==============================================================================
# Schemas
# ==============================================================================


class BiomedicalSearchRequest(BaseModel):
    """Request payload to query biomedical literature."""

    query: str = Field(
        ...,
        description="Search query or claim text (e.g., 'Ashwagandha for stress and insomnia', 'curcumin osteoarthritis')",
        examples=["Ashwagandha stress reduction and sleep quality"],
    )
    herb: Optional[str] = Field(
        default=None,
        description="Optional specific herb or botanical name to focus the search (e.g., 'Withania somnifera')",
        examples=["Ashwagandha"],
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of biomedical evidence articles to return",
    )


class BiomedicalItemResponse(BaseModel):
    """Structured publication item matching clinical criteria."""

    pmid: str = Field(..., description="PubMed identifier or curated catalog reference")
    title: str = Field(..., description="Article title")
    journal: str = Field(..., description="Journal name")
    pub_year: str = Field(..., description="Year of publication")
    study_type: str = Field(..., description="Study classification (RCT, Review, Clinical Trial, etc.)")
    abstract_snippet: str = Field(..., description="Summary or excerpt from the study")
    source: str = Field(default="PubMed", description="Source data provider (PubMed or CuratedCache)")
    relevance_score: float = Field(default=0.0, description="Semantic or keyword relevance score")


class BiomedicalSearchResponse(BaseModel):
    """Response payload containing matching biomedical articles."""

    query: str
    herb: Optional[str] = None
    total_results: int
    results: List[BiomedicalItemResponse]


# ==============================================================================
# Endpoints
# ==============================================================================


@router.post(
    "/search",
    response_model=BiomedicalSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search biomedical clinical evidence for Ayurvedic herbs/claims",
)
async def search_biomedical_evidence(request: BiomedicalSearchRequest) -> BiomedicalSearchResponse:
    """Queries PubMed E-utilities API (with curated offline cache fallback)

    to retrieve peer-reviewed studies, RCTs, and systematic reviews for Ayurvedic herbs
    and therapeutic claims.
    """
    try:
        results: List[BiomedicalResult] = await biomedical_service.search(
            query=request.query,
            herb=request.herb,
            max_results=request.max_results,
        )

        formatted_items = [
            BiomedicalItemResponse(
                pmid=r.pmid,
                title=r.title,
                journal=r.journal,
                pub_year=r.pub_year,
                study_type=r.study_type,
                abstract_snippet=r.abstract_snippet,
                source=r.source,
                relevance_score=r.relevance_score,
            )
            for r in results
        ]

        return BiomedicalSearchResponse(
            query=request.query,
            herb=request.herb,
            total_results=len(formatted_items),
            results=formatted_items,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biomedical evidence search encountered an error: {str(exc)}",
        )


# ==============================================================================
# Dual-Evidence Audit Endpoint
# ==============================================================================


class DualAuditRequest(BaseModel):
    """Request payload for Classical vs. Biomedical dual-evidence cross-audit."""

    text: str = Field(
        ...,
        description="AI-generated Ayurvedic text or claim to audit against both classical and modern evidence.",
        examples=[
            "Ashwagandha reduces cortisol and promotes strength as described in Charaka Samhita's Rasayana section."
        ],
    )
    query_context: Optional[str] = Field(
        default=None,
        description="Optional label for the audit context (source AI name, question, etc.)",
    )
    max_biomedical_per_claim: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Max PubMed/curated results to fetch per claim",
    )


class ClassicalEvidenceResponse(BaseModel):
    matched: bool
    reference: Optional[str] = None
    original_passage: Optional[str] = None
    commentary_note: Optional[str] = None
    relevance_score: float
    is_contradicted: bool


class BiomedicalEvidenceResponse(BaseModel):
    matched: bool
    pmid: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    pub_year: Optional[str] = None
    study_type: Optional[str] = None
    abstract_snippet: Optional[str] = None
    relevance_score: float
    source: str = "CuratedCache"


class DualClaimResponse(BaseModel):
    claim_id: int
    claim_text: str
    dual_grade: str
    confidence: float
    classical_evidence: ClassicalEvidenceResponse
    biomedical_evidence: BiomedicalEvidenceResponse
    unified_reasoning: str


class DualAuditResponse(BaseModel):
    """Full dual-evidence audit report."""

    query_or_source: str
    input_text: str
    total_claims: int
    grade_summary: Dict[str, int]
    executive_summary: str
    limitations: List[str]
    claims: List[DualClaimResponse]


@router.post(
    "/dual-audit",
    response_model=DualAuditResponse,
    status_code=status.HTTP_200_OK,
    tags=["Dual-Evidence Cross-Auditor"],
    summary="Classical vs. Biomedical dual-evidence cross-audit",
    description=(
        "Simultaneously audits AI-generated Ayurvedic claims against "
        "(1) classical Samhita texts via ChromaDB and "
        "(2) modern peer-reviewed biomedical literature via PubMed / curated cache. "
        "Returns a unified dual-evidence verdict per claim."
    ),
)
async def dual_evidence_audit(request: DualAuditRequest) -> DualAuditResponse:
    """Run the Classical vs. Biomedical Dual-Evidence Cross-Auditor."""
    try:
        report = await dual_auditor.audit(
            text=request.text,
            query_context=request.query_context,
            max_biomedical_per_claim=request.max_biomedical_per_claim,
        )

        claims_out = []
        for c in report.claims:
            claims_out.append(
                DualClaimResponse(
                    claim_id=c.claim_id,
                    claim_text=c.claim_text,
                    dual_grade=c.dual_grade.value,
                    confidence=c.confidence,
                    classical_evidence=ClassicalEvidenceResponse(
                        matched=c.classical.matched,
                        reference=c.classical.top_reference,
                        original_passage=c.classical.original_passage,
                        commentary_note=c.classical.commentary_note,
                        relevance_score=c.classical.relevance_score,
                        is_contradicted=c.classical.is_contradicted,
                    ),
                    biomedical_evidence=BiomedicalEvidenceResponse(
                        matched=c.biomedical.matched,
                        pmid=c.biomedical.top_pmid,
                        title=c.biomedical.top_title,
                        journal=c.biomedical.top_journal,
                        pub_year=c.biomedical.pub_year,
                        study_type=c.biomedical.study_type,
                        abstract_snippet=c.biomedical.abstract_snippet,
                        relevance_score=c.biomedical.relevance_score,
                        source=c.biomedical.source,
                    ),
                    unified_reasoning=c.unified_reasoning,
                )
            )

        return DualAuditResponse(
            query_or_source=report.query_or_source,
            input_text=report.input_text,
            total_claims=report.total_claims,
            grade_summary=report.grade_summary,
            executive_summary=report.executive_summary,
            limitations=report.limitations,
            claims=claims_out,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dual-evidence audit failed: {str(exc)}",
        )
