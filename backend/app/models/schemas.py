"""Pydantic schemas strictly aligned with the AyurEval verification architecture.

Defines verification categories, claim-level verification results, query/verify requests,
and structured verification audit reports.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Verification Architecture Core Schemas (Requested Specifications)
# ==============================================================================


class VerificationCategory(str, Enum):
    """Categorization of claim alignment against canonical sources."""

    SUPPORTED_BY_SOURCE = "Supported by source"
    PARTIALLY_SUPPORTED = "Partially supported"
    CONTRADICTED_BY_SOURCE = "Contradicted by source"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence"
    REFERENCE_NOT_VERIFIED = "Reference not verified"


class ClaimVerificationResult(BaseModel):
    """Granular verification verdict for an individual clinical or theoretical claim."""

    claim_id: int = Field(
        ..., description="Sequential identifier for the decomposed claim"
    )
    claim_text: str = Field(
        ..., description="The specific atomic claim extracted from the AI response"
    )
    category: VerificationCategory = Field(
        ..., description="Verification classification category"
    )
    classical_reference: Optional[str] = Field(
        default=None,
        description="Classical Samhita citation, e.g. 'Charaka Samhita, Sutrasthana, 1/42'",
    )
    original_passage: Optional[str] = Field(
        default=None,
        description="Original Sanskrit shloka or direct canonical excerpt",
    )
    commentary_note: Optional[str] = Field(
        default=None,
        description="Authoritative commentary note (Chakrapani Datta, Dalhana, Arunadatta)",
    )
    scientific_evidence: Optional[str] = Field(
        default=None,
        description="Modern biomedical or pharmacological evidence (PubMed/trials)",
    )
    reasoning: str = Field(
        ..., description="Detailed clinical and textual reasoning justifying the category"
    )


class AskRequest(BaseModel):
    """Request payload to query the system with a direct clinical or lifestyle question."""

    question: str = Field(
        ..., description="Ayurvedic clinical, herbal, or lifestyle question"
    )


class VerifyRequest(BaseModel):
    """Request payload to audit an AI-generated Ayurvedic answer."""

    ai_generated_text: str = Field(
        ..., description="The AI-generated text or answer to be independently verified"
    )
    source_ai_name: Optional[str] = Field(
        default=None,
        description="Name of the model or system that generated the text (e.g. 'GPT-4', 'Claude 3', 'Llama 3')",
    )


class VerificationReportResponse(BaseModel):
    """Complete verification report containing decomposed claims, verdicts, and source citations."""

    query_or_source: str = Field(
        ..., description="Original user prompt or source identifier"
    )
    generated_answer: Optional[str] = Field(
        default=None, description="The original AI-generated answer being audited"
    )
    claims: List[ClaimVerificationResult] = Field(
        default_factory=list,
        description="Itemized claim-level verification results with canonical citations",
    )
    overall_summary: str = Field(
        ..., description="Synthesized executive summary of the verification findings"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Known methodological, textual, or empirical limitations of this audit",
    )


# ==============================================================================
# Supporting Corpora & RAG Schemas
# ==============================================================================


class CorpusType(str, Enum):
    """Categorization of canonical knowledge sources."""

    CHARAKA_SAMHITA = "charaka_samhita"
    SUSHRUTA_SAMHITA = "sushruta_samhita"
    ASHTANGA_HRIDAYA = "ashtanga_hridaya"
    COMMENTARY = "commentary"
    SCIENTIFIC_EVIDENCE = "scientific_evidence"


class AlignmentStatus(str, Enum):
    """Alignment between claim and source passage."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PARTIALLY_SUPPORTS = "partially_supports"
    UNSUBSTANTIATED = "unsubstantiated"


class EvidenceItem(BaseModel):
    """Evidence snippet retrieved during RAG search."""

    id: str = Field(..., description="Unique reference ID")
    corpus_type: CorpusType = Field(..., description="Corpus source category")
    source_title: str = Field(..., description="Title of text, e.g. 'Charaka Samhita'")
    reference_location: str = Field(
        ..., description="Specific location, e.g. 'Sutra Sthana Ch. 27, Verse 45'"
    )
    sanskrit_excerpt: Optional[str] = Field(
        None, description="Original Sanskrit shloka if available"
    )
    text_content: str = Field(..., description="English translation or study abstract")
    alignment: AlignmentStatus = Field(
        default=AlignmentStatus.SUPPORTS, description="Alignment with claim"
    )
    relevance_score: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Relevance score"
    )


class RAGQueryRequest(BaseModel):
    """Request payload for direct knowledge base retrieval."""

    query: str = Field(..., description="Search query or clinical concept")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    corpus_filter: Optional[List[CorpusType]] = Field(
        default=None, description="Optional corpus filter"
    )


class RAGQueryResponse(BaseModel):
    """Response payload for knowledge base retrieval."""

    query: str = Field(..., description="Original query")
    retrieved_items: List[EvidenceItem] = Field(
        default_factory=list, description="Retrieved evidence chunks"
    )
    total_found: int = Field(..., description="Count of matched items")


# ==============================================================================
# AyurParam LLM & Atomic Claim Decomposition Schemas
# ==============================================================================


class ClaimType(str, Enum):
    """Classification of an extracted atomic statement."""

    MEDICAL = "medical"
    BOTANICAL = "botanical"
    THERAPEUTIC = "therapeutic"
    CITATION = "citation"
    DIETARY = "dietary"
    LIFESTYLE = "lifestyle"
    CONTRAINDICATION = "contraindication"


class AtomicClaim(BaseModel):
    """A single discrete, verifiable medical/botanical/lifestyle assertion."""

    claim_id: int = Field(
        ..., description="Distinct sequential identifier for auditing"
    )
    claim_text: str = Field(
        ..., description="The discrete verifiable assertion extracted from the response"
    )
    claim_type: str = Field(
        default="medical",
        description="Categorization: medical, botanical, therapeutic, citation, dietary, lifestyle, contraindication",
    )
    entities_mentioned: List[str] = Field(
        default_factory=list,
        description="Key Ayurvedic entities, herbs, doshas, or physiological terms mentioned",
    )
    context_snippet: Optional[str] = Field(
        default=None,
        description="The source sentence or clause context from which the claim was extracted",
    )


class ExtractClaimsRequest(BaseModel):
    """Request payload to decompose text into atomic claims."""

    text: str = Field(
        ...,
        description="The AI-generated text, clinical summary, or paragraph to decompose",
        examples=[
            "Tila Taila (sesame oil) is the foremost oil for pacifying Vata dosha according to Charaka Samhita. Daily Abhyanga permanently cures all forms of sciatica and disc herniation."
        ],
    )
    source_ai_name: Optional[str] = Field(
        default=None,
        description="Name of the model or system that produced the text (e.g. 'ChatGPT', 'Gemini', 'AyurParam')",
    )


class ExtractClaimsResponse(BaseModel):
    """Response payload containing itemized atomic claims with distinct identifiers."""

    source_ai_name: Optional[str] = Field(
        default=None, description="Source model or system identifier"
    )
    total_claims: int = Field(
        ..., description="Total count of atomic claims extracted"
    )
    claims: List[AtomicClaim] = Field(
        default_factory=list,
        description="List of discrete atomic claims ready for verification",
    )


class AyurParamGenerateRequest(BaseModel):
    """Request payload for generative Ayurvedic reasoning."""

    question: str = Field(
        ...,
        description="Clinical or lifestyle inquiry grounded in Ayurvedic wisdom",
        examples=["What is the classical Ayurvedic protocol for pacifying Vata dosha using sesame oil?"],
    )
    temperature: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Generation temperature (lower for canonical faithfulness)",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional model override (defaults to configured system LLM)",
    )


class AyurParamGenerateResponse(BaseModel):
    """Response payload containing synthesized answer and decomposed claims."""

    question: str = Field(..., description="The original clinical/lifestyle question")
    answer: str = Field(..., description="Synthesized Ayurvedic answer")
    model_used: str = Field(..., description="LLM provider or model name used")
    claims_count: int = Field(..., description="Number of atomic claims extracted")
    extracted_claims: List[AtomicClaim] = Field(
        default_factory=list,
        description="Atomic claims extracted from the generated answer",
    )
