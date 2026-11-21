"""Classical vs. Biomedical Dual-Evidence Cross-Auditor for AyurEval (COGNEXA).

Simultaneously queries:
  1. Classical Samhita texts via ChromaDB (search_classical_sources_batch)
  2. Modern clinical evidence via BiomedicalEvidenceService (PubMed + curated cache)

Combines both into a unified DualEvidenceReport grading each claim on:
  - Traditional textual alignment (Charaka, Sushruta, Ashtanga Hridaya)
  - Modern scientific backing (RCTs, systematic reviews, clinical trials)

Dual-evidence grades (DualEvidenceGrade):
  ┌─────────────────────────┬─────────────────┬─────────────────┐
  │ Grade                   │ Classical Match │ Biomedical Match│
  ├─────────────────────────┼─────────────────┼─────────────────┤
  │ DUAL_SUPPORTED          │ Strong          │ Strong          │
  │ TRADITIONAL_ONLY        │ Strong          │ Weak / None     │
  │ CLINICAL_BACKED         │ Weak / None     │ Strong          │
  │ PARTIALLY_ALIGNED       │ Moderate either │ Moderate either │
  │ INSUFFICIENT_DUAL       │ Weak / None     │ Weak / None     │
  │ CONTRADICTED            │ Contradicted    │ Any             │
  └─────────────────────────┴─────────────────┴─────────────────┘

Usage:
    from app.services.verification.dual_auditor import dual_auditor
    report = await dual_auditor.audit(text="Ashwagandha reduces cortisol...")
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.ayurparam import ayurparam_service
from app.services.biomedical_service import BiomedicalResult, biomedical_service
from app.services.vector_store import search_classical_sources_batch

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dual-Evidence Grade Enum
# ---------------------------------------------------------------------------
class DualEvidenceGrade(str, Enum):
    """Combined verdict from classical + biomedical evidence streams."""

    DUAL_SUPPORTED = "Dual-supported"            # Strong classical + strong biomedical
    TRADITIONAL_ONLY = "Traditional-only"         # Strong classical, weak/no biomedical
    CLINICAL_BACKED = "Clinical-backed"           # Weak/no classical, strong biomedical
    PARTIALLY_ALIGNED = "Partially aligned"       # Moderate evidence on either side
    INSUFFICIENT_DUAL = "Insufficient dual evidence"  # Both streams weak
    CONTRADICTED = "Contradicted"                 # Classical source contradicts claim


# ---------------------------------------------------------------------------
# Data models for dual-evidence output
# ---------------------------------------------------------------------------
@dataclass
class ClassicalEvidenceSummary:
    """Summary of classical Samhita retrieval for a single claim."""

    matched: bool = False
    top_reference: Optional[str] = None
    original_passage: Optional[str] = None
    commentary_note: Optional[str] = None
    relevance_score: float = 0.0
    is_contradicted: bool = False
    raw_passages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BiomedicalEvidenceSummary:
    """Summary of biomedical retrieval for a single claim."""

    matched: bool = False
    top_pmid: Optional[str] = None
    top_title: Optional[str] = None
    top_journal: Optional[str] = None
    pub_year: Optional[str] = None
    study_type: Optional[str] = None
    abstract_snippet: Optional[str] = None
    relevance_score: float = 0.0
    source: str = "CuratedCache"
    all_results: List[BiomedicalResult] = field(default_factory=list)


@dataclass
class DualClaimAudit:
    """Full dual-evidence audit result for one atomic claim."""

    claim_id: int
    claim_text: str
    dual_grade: DualEvidenceGrade
    classical: ClassicalEvidenceSummary
    biomedical: BiomedicalEvidenceSummary
    unified_reasoning: str
    confidence: float  # 0.0 – 1.0 composite confidence

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "dual_grade": self.dual_grade.value,
            "confidence": round(self.confidence, 3),
            "classical_evidence": {
                "matched": self.classical.matched,
                "reference": self.classical.top_reference,
                "original_passage": self.classical.original_passage,
                "commentary_note": self.classical.commentary_note,
                "relevance_score": round(self.classical.relevance_score, 3),
                "is_contradicted": self.classical.is_contradicted,
            },
            "biomedical_evidence": {
                "matched": self.biomedical.matched,
                "pmid": self.biomedical.top_pmid,
                "title": self.biomedical.top_title,
                "journal": self.biomedical.top_journal,
                "pub_year": self.biomedical.pub_year,
                "study_type": self.biomedical.study_type,
                "abstract_snippet": self.biomedical.abstract_snippet,
                "relevance_score": round(self.biomedical.relevance_score, 3),
                "source": self.biomedical.source,
            },
            "unified_reasoning": self.unified_reasoning,
        }


@dataclass
class DualEvidenceReport:
    """Full dual-evidence report across all extracted claims."""

    query_or_source: str
    input_text: str
    total_claims: int
    claims: List[DualClaimAudit]
    grade_summary: Dict[str, int]
    executive_summary: str
    limitations: List[str]

    def to_dict(self) -> dict:
        return {
            "query_or_source": self.query_or_source,
            "input_text": self.input_text,
            "total_claims": self.total_claims,
            "grade_summary": self.grade_summary,
            "executive_summary": self.executive_summary,
            "limitations": self.limitations,
            "claims": [c.to_dict() for c in self.claims],
        }


# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------
_CLASSICAL_STRONG = 0.55   # ChromaDB relevance ≥ this → strong classical match
_CLASSICAL_MODERATE = 0.30  # ≥ this but < STRONG → moderate
_BIOMEDICAL_STRONG = 0.60  # Curated/PubMed relevance ≥ this → strong biomedical
_BIOMEDICAL_MODERATE = 0.30  # ≥ this but < STRONG → moderate

# Contradiction keywords in classical passages indicating semantic opposition
_CONTRADICTION_SIGNALS = [
    "contraindicated", "avoid", "not advised", "harmful in", "aggravates",
    "viruddha", "apathya", "nindita", "forbidden",
]


# ---------------------------------------------------------------------------
# DualAuditor class
# ---------------------------------------------------------------------------
class DualAuditor:
    """Simultaneously audits claims against classical Samhitas AND modern biomedical literature."""

    def __init__(self) -> None:
        self._ayurparam = ayurparam_service
        self._biomedical = biomedical_service

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    async def audit(
        self,
        text: str,
        query_context: Optional[str] = None,
        max_biomedical_per_claim: int = 2,
    ) -> DualEvidenceReport:
        """Run the full dual-evidence audit on input text.

        Args:
            text:                      Raw text containing Ayurvedic claims.
            query_context:             Optional label (question, source AI name, etc.).
            max_biomedical_per_claim:  Max PubMed/curated results to fetch per claim.

        Returns:
            DualEvidenceReport with per-claim dual grades and unified reasoning.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return self._empty_report(query_context or "AyurEval Dual Audit")

        # Step 1: Extract atomic claims
        raw_claims = self._ayurparam.extract_atomic_claims(cleaned)
        if not raw_claims:
            raw_claims = [
                {
                    "claim_id": 1,
                    "claim_text": cleaned[:220],
                    "claim_type": "medical",
                    "entities_mentioned": [],
                }
            ]

        claim_texts = [c.get("claim_text", "") for c in raw_claims]

        # Step 2: Parallel retrieval — classical (batch sync) + biomedical (async fan-out)
        classical_batch, bio_batch = await asyncio.gather(
            self._retrieve_classical_batch(claim_texts),
            self._retrieve_biomedical_batch(raw_claims, max_biomedical_per_claim),
        )

        # Step 3: Combine into dual-evidence verdicts per claim
        audited: List[DualClaimAudit] = []
        for idx, item in enumerate(raw_claims):
            classical_passages = classical_batch[idx] if idx < len(classical_batch) else []
            bio_results = bio_batch[idx] if idx < len(bio_batch) else []

            classical_summary = self._summarise_classical(classical_passages)
            biomedical_summary = self._summarise_biomedical(bio_results)
            grade = self._assign_dual_grade(classical_summary, biomedical_summary)
            reasoning = self._build_reasoning(
                item.get("claim_text", ""), grade, classical_summary, biomedical_summary
            )
            confidence = self._compute_confidence(classical_summary, biomedical_summary, grade)

            audited.append(
                DualClaimAudit(
                    claim_id=item.get("claim_id", idx + 1),
                    claim_text=item.get("claim_text", ""),
                    dual_grade=grade,
                    classical=classical_summary,
                    biomedical=biomedical_summary,
                    unified_reasoning=reasoning,
                    confidence=confidence,
                )
            )

        # Step 4: Synthesise executive summary
        grade_summary = self._count_grades(audited)
        executive_summary = self._executive_summary(audited, grade_summary)
        limitations = self._standard_limitations()

        return DualEvidenceReport(
            query_or_source=query_context or "AyurEval Dual Cross-Audit",
            input_text=cleaned,
            total_claims=len(audited),
            claims=audited,
            grade_summary=grade_summary,
            executive_summary=executive_summary,
            limitations=limitations,
        )

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------
    async def _retrieve_classical_batch(
        self, claim_texts: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """Retrieve classical passages for all claims in a single ChromaDB batch call."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: search_classical_sources_batch(claim_texts, top_k=2)
        )

    async def _retrieve_biomedical_batch(
        self,
        raw_claims: List[Dict[str, Any]],
        max_results: int,
    ) -> List[List[BiomedicalResult]]:
        """Concurrently fetch biomedical evidence for all claims."""
        tasks = []
        for claim in raw_claims:
            claim_text = claim.get("claim_text", "")
            # Extract the most specific herb entity for the biomedical search
            entities = claim.get("entities_mentioned", [])
            herb = entities[0] if entities else None
            tasks.append(
                self._biomedical.search(
                    query=claim_text,
                    herb=herb,
                    max_results=max_results,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Replace exceptions with empty lists for resilience
        return [r if isinstance(r, list) else [] for r in results]

    # ------------------------------------------------------------------
    # Summarisation helpers
    # ------------------------------------------------------------------
    def _summarise_classical(
        self, passages: List[Dict[str, Any]]
    ) -> ClassicalEvidenceSummary:
        """Compress a list of ChromaDB passages into a ClassicalEvidenceSummary."""
        if not passages:
            return ClassicalEvidenceSummary()

        top = passages[0]
        score = float(top.get("relevance_score", 0.0))
        passage_text = str(top.get("text", "") or top.get("passage", "")).lower()

        # Detect contradiction signals in retrieved passage
        is_contradicted = any(sig in passage_text for sig in _CONTRADICTION_SIGNALS)

        return ClassicalEvidenceSummary(
            matched=score >= _CLASSICAL_MODERATE,
            top_reference=top.get("citation") or top.get("source_book"),
            original_passage=top.get("text") or top.get("passage"),
            commentary_note=top.get("commentary"),
            relevance_score=score,
            is_contradicted=is_contradicted,
            raw_passages=passages,
        )

    def _summarise_biomedical(
        self, results: List[BiomedicalResult]
    ) -> BiomedicalEvidenceSummary:
        """Compress BiomedicalResult list into a BiomedicalEvidenceSummary."""
        if not results:
            return BiomedicalEvidenceSummary()

        top = results[0]
        return BiomedicalEvidenceSummary(
            matched=top.relevance_score >= _BIOMEDICAL_MODERATE,
            top_pmid=top.pmid,
            top_title=top.title,
            top_journal=top.journal,
            pub_year=top.pub_year,
            study_type=top.study_type,
            abstract_snippet=top.abstract_snippet,
            relevance_score=top.relevance_score,
            source=top.source,
            all_results=results,
        )

    # ------------------------------------------------------------------
    # Dual-grade assignment
    # ------------------------------------------------------------------
    def _assign_dual_grade(
        self,
        c: ClassicalEvidenceSummary,
        b: BiomedicalEvidenceSummary,
    ) -> DualEvidenceGrade:
        """Map classical + biomedical strength to a DualEvidenceGrade."""
        if c.is_contradicted:
            return DualEvidenceGrade.CONTRADICTED

        c_strong = c.relevance_score >= _CLASSICAL_STRONG
        c_moderate = c.relevance_score >= _CLASSICAL_MODERATE
        b_strong = b.relevance_score >= _BIOMEDICAL_STRONG
        b_moderate = b.relevance_score >= _BIOMEDICAL_MODERATE

        if c_strong and b_strong:
            return DualEvidenceGrade.DUAL_SUPPORTED
        if c_strong and not b_moderate:
            return DualEvidenceGrade.TRADITIONAL_ONLY
        if not c_moderate and b_strong:
            return DualEvidenceGrade.CLINICAL_BACKED
        if c_moderate or b_moderate:
            return DualEvidenceGrade.PARTIALLY_ALIGNED
        return DualEvidenceGrade.INSUFFICIENT_DUAL

    # ------------------------------------------------------------------
    # Reasoning builder
    # ------------------------------------------------------------------
    def _build_reasoning(
        self,
        claim_text: str,
        grade: DualEvidenceGrade,
        c: ClassicalEvidenceSummary,
        b: BiomedicalEvidenceSummary,
    ) -> str:
        parts: List[str] = []

        # Classical part
        if c.is_contradicted:
            parts.append(
                f"Classical textual evidence ({c.top_reference or 'retrieved passage'}) "
                f"contains a potential contradiction or contraindication signal for this claim."
            )
        elif c.matched:
            parts.append(
                f"Classical alignment: Retrieved passage from {c.top_reference or 'Brihat Trayi'} "
                f"shows relevance score {c.relevance_score:.2f}, supporting the traditional basis."
            )
        else:
            parts.append(
                "Classical alignment: No strong Samhita passage matched this claim "
                f"(best score {c.relevance_score:.2f})."
            )

        # Biomedical part
        if b.matched:
            study_label = f"[{b.study_type}]" if b.study_type else ""
            parts.append(
                f"Biomedical evidence: {study_label} {b.top_title[:70] + '...' if b.top_title else 'Retrieved study'} "
                f"(PMID: {b.top_pmid}, {b.pub_year}) from {b.top_journal or b.source} "
                f"provides modern clinical corroboration (relevance {b.relevance_score:.2f})."
            )
        else:
            parts.append(
                "Biomedical evidence: No peer-reviewed study was matched with sufficient "
                f"relevance (best score {b.relevance_score:.2f})."
            )

        # Grade summary
        grade_descriptions = {
            DualEvidenceGrade.DUAL_SUPPORTED: (
                "Both classical Samhita texts and modern biomedical literature support this claim."
            ),
            DualEvidenceGrade.TRADITIONAL_ONLY: (
                "Supported by classical texts but modern peer-reviewed clinical evidence is currently limited."
            ),
            DualEvidenceGrade.CLINICAL_BACKED: (
                "Supported by modern clinical/biomedical data but lacks direct classical Samhita grounding."
            ),
            DualEvidenceGrade.PARTIALLY_ALIGNED: (
                "Moderate evidence from at least one stream; neither classical nor biomedical evidence is conclusive."
            ),
            DualEvidenceGrade.INSUFFICIENT_DUAL: (
                "Both classical and biomedical evidence streams are insufficient to verify or refute this claim."
            ),
            DualEvidenceGrade.CONTRADICTED: (
                "Retrieved classical evidence signals a potential contradiction or contraindication."
            ),
        }
        parts.append(f"Dual-evidence verdict: {grade_descriptions.get(grade, '')}")

        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------
    def _compute_confidence(
        self,
        c: ClassicalEvidenceSummary,
        b: BiomedicalEvidenceSummary,
        grade: DualEvidenceGrade,
    ) -> float:
        """Composite 0.0–1.0 confidence from both evidence streams."""
        if grade == DualEvidenceGrade.CONTRADICTED:
            return 0.15
        # Weighted average: classical 50%, biomedical 50%
        raw = (c.relevance_score * 0.5) + (b.relevance_score * 0.5)
        # Boost for dual-supported, penalty for insufficient
        if grade == DualEvidenceGrade.DUAL_SUPPORTED:
            raw = min(raw * 1.15, 1.0)
        elif grade == DualEvidenceGrade.INSUFFICIENT_DUAL:
            raw = raw * 0.7
        return round(min(max(raw, 0.0), 1.0), 3)

    # ------------------------------------------------------------------
    # Report synthesis
    # ------------------------------------------------------------------
    def _count_grades(self, audited: List[DualClaimAudit]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for claim in audited:
            key = claim.dual_grade.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _executive_summary(
        self, audited: List[DualClaimAudit], grade_summary: Dict[str, int]
    ) -> str:
        n = len(audited)
        dual = grade_summary.get(DualEvidenceGrade.DUAL_SUPPORTED.value, 0)
        trad = grade_summary.get(DualEvidenceGrade.TRADITIONAL_ONLY.value, 0)
        clinical = grade_summary.get(DualEvidenceGrade.CLINICAL_BACKED.value, 0)
        partial = grade_summary.get(DualEvidenceGrade.PARTIALLY_ALIGNED.value, 0)
        insuff = grade_summary.get(DualEvidenceGrade.INSUFFICIENT_DUAL.value, 0)
        contra = grade_summary.get(DualEvidenceGrade.CONTRADICTED.value, 0)

        parts = [f"AyurEval Dual Cross-Audit completed. {n} claim(s) evaluated."]
        if dual:
            parts.append(f"{dual} claim(s) are Dual-Supported (classical + modern biomedical).")
        if trad:
            parts.append(f"{trad} claim(s) are Traditional-Only (classical support, no modern trial data).")
        if clinical:
            parts.append(f"{clinical} claim(s) are Clinical-Backed (biomedical evidence, weak classical grounding).")
        if partial:
            parts.append(f"{partial} claim(s) show Partial Alignment (moderate evidence in at least one stream).")
        if insuff:
            parts.append(f"{insuff} claim(s) have Insufficient Dual Evidence from either stream.")
        if contra:
            parts.append(f"{contra} claim(s) contain Contradicted evidence from classical sources.")
        return " ".join(parts)

    def _standard_limitations(self) -> List[str]:
        return [
            "Classical textual alignment uses ChromaDB semantic similarity and may not capture all canonical nuances.",
            "Biomedical retrieval is limited to curated entries and live PubMed; absence of a result does not imply absence of evidence.",
            "This dual-evidence grading is a decision-support tool and must be supplemented by expert Ayurvedic and clinical review.",
            "Contradiction detection uses keyword signals in retrieved passages and may produce false positives.",
        ]

    def _empty_report(self, label: str) -> DualEvidenceReport:
        return DualEvidenceReport(
            query_or_source=label,
            input_text="",
            total_claims=0,
            claims=[],
            grade_summary={},
            executive_summary="No input text provided for dual-evidence audit.",
            limitations=self._standard_limitations(),
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
dual_auditor = DualAuditor()
