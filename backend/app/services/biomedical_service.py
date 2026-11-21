"""Biomedical Evidence Retrieval Service for AyurEval (COGNEXA).

Searches modern peer-reviewed clinical/scientific evidence for Ayurvedic herbs
and formulations using the NCBI PubMed E-utilities API (esearch + esummary).

Falls back gracefully to a curated local dataset when the network is unavailable,
rate-limited, or running in an offline/sandboxed environment.

Architecture:
  BiomedicalEvidenceService
    .search(query, herb, max_results) -> List[BiomedicalResult]
    ._search_pubmed(query, max_results) -> List[BiomedicalResult]
    ._search_local_cache(query, herb)   -> List[BiomedicalResult]
    ._classify_study_type(source_str)   -> str
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NCBI PubMed E-utilities base URLs (no API key required; 3 req/s limit)
# Using an API key lifts the limit to 10 req/s — set NCBI_API_KEY in .env
# ---------------------------------------------------------------------------
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Path to the curated offline fallback dataset
_CURATED_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "scientific" / "curated_evidence.json"

# Study-type classification keywords (highest-specificity first)
_STUDY_TYPE_PATTERNS: List[tuple[str, str]] = [
    (r"\bsystematic review\b|\bmeta.?analysis\b", "Systematic Review / Meta-Analysis"),
    (r"\brandomized\b|\bRCT\b|\bdouble.?blind\b|\bplacebo.?controlled\b", "RCT"),
    (r"\bclinical trial\b|\bphase [iI]+\b", "Clinical Trial"),
    (r"\bcohort\b|\bprospective\b|\bretrospective\b|\bobservational\b", "Observational Study"),
    (r"\bcase.?report\b|\bcase series\b", "Case Report"),
    (r"\bin vitro\b|\bcell line\b|\bin vivo\b|\banimal\b|\bmurine\b|\brat\b|\bmouse\b", "Pre-clinical Study"),
    (r"\breview\b|\boverview\b|\bsummary\b", "Review"),
]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class BiomedicalResult:
    """Structured biomedical evidence item returned by the retrieval service."""

    pmid: str
    title: str
    journal: str
    pub_year: str
    study_type: str
    abstract_snippet: str
    source: str = "PubMed"          # 'PubMed' or 'CuratedCache'
    relevance_score: float = 0.0    # Simple keyword hit score (0.0–1.0)

    def to_dict(self) -> dict:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "journal": self.journal,
            "pub_year": self.pub_year,
            "study_type": self.study_type,
            "abstract_snippet": self.abstract_snippet,
            "source": self.source,
            "relevance_score": round(self.relevance_score, 3),
        }


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------
class BiomedicalEvidenceService:
    """Retrieves peer-reviewed clinical evidence for Ayurvedic substances.

    Priority order:
      1. NCBI PubMed E-utilities (live, async via httpx)
      2. Local curated cache (offline / rate-limited fallback)
    """

    def __init__(self) -> None:
        self._curated: List[dict] = []
        self._load_curated_cache()
        self._ncbi_api_key: str = os.environ.get("NCBI_API_KEY", "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def search(
        self,
        query: str,
        herb: Optional[str] = None,
        max_results: int = 5,
    ) -> List[BiomedicalResult]:
        """Search for biomedical evidence relevant to query/herb.

        Args:
            query:       Free-text query (claim text, herb name, condition).
            herb:        Optional explicit herb name to narrow the PubMed query.
            max_results: Maximum number of results to return.

        Returns:
            List of BiomedicalResult items sorted by relevance / recency.
        """
        effective_query = self._build_pubmed_query(query, herb)
        results: List[BiomedicalResult] = []

        # --- Attempt live PubMed retrieval ---
        try:
            results = await asyncio.wait_for(
                self._search_pubmed(effective_query, max_results),
                timeout=3.0,
            )
            if results:
                logger.info(
                    "[BiomedicalService] PubMed returned %d result(s) for query: %s",
                    len(results), effective_query[:80],
                )
                return results
        except Exception as exc:
            logger.warning(
                "[BiomedicalService] PubMed unavailable (%s). Falling back to curated cache.", exc
            )

        # --- Fallback: local curated cache ---
        results = self._search_local_cache(query, herb, max_results)
        logger.info(
            "[BiomedicalService] Curated cache returned %d result(s) for herb='%s'",
            len(results), herb or query[:40],
        )
        return results

    def search_sync(
        self,
        query: str,
        herb: Optional[str] = None,
        max_results: int = 5,
    ) -> List[BiomedicalResult]:
        """Synchronous wrapper — searches only the local curated cache.

        Use this inside synchronous contexts (e.g., test scripts) or when
        network access is unavailable.
        """
        results = self._search_local_cache(query, herb, max_results)
        if not results:
            logger.info(
                "[BiomedicalService] No curated cache entries found for '%s'.", herb or query
            )
        return results

    # ------------------------------------------------------------------
    # PubMed E-utilities (async)
    # ------------------------------------------------------------------
    async def _search_pubmed(
        self, query: str, max_results: int
    ) -> List[BiomedicalResult]:
        """Run esearch → esummary pipeline against NCBI PubMed."""
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for PubMed retrieval. Install it with: pip install httpx")

        timeout = httpx.Timeout(5.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Step 1: esearch — get PMIDs
            esearch_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            }
            if self._ncbi_api_key:
                esearch_params["api_key"] = self._ncbi_api_key

            esearch_resp = await client.get(PUBMED_ESEARCH_URL, params=esearch_params)
            esearch_resp.raise_for_status()
            esearch_data = esearch_resp.json()

            pmids: List[str] = esearch_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            # Step 2: esummary — get metadata for each PMID
            esummary_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            }
            if self._ncbi_api_key:
                esummary_params["api_key"] = self._ncbi_api_key

            esummary_resp = await client.get(PUBMED_ESUMMARY_URL, params=esummary_params)
            esummary_resp.raise_for_status()
            summary_data = esummary_resp.json()

        results: List[BiomedicalResult] = []
        result_map: dict = summary_data.get("result", {})

        for pmid in pmids:
            article = result_map.get(pmid)
            if not article or not isinstance(article, dict):
                continue

            title = article.get("title", "").rstrip(".")
            journal = article.get("fulljournalname") or article.get("source", "")
            pub_year = self._extract_pub_year(article)
            source_str = " ".join([
                article.get("pubtype", []) if isinstance(article.get("pubtype"), str)
                else " ".join(article.get("pubtype", [])),
                title,
                article.get("sorttitle", ""),
            ])
            study_type = self._classify_study_type(source_str)

            results.append(
                BiomedicalResult(
                    pmid=pmid,
                    title=title,
                    journal=journal,
                    pub_year=pub_year,
                    study_type=study_type,
                    abstract_snippet=self._truncate(title, 300),  # esummary has no abstract; use title
                    source="PubMed",
                    relevance_score=1.0,  # live results always ranked by PubMed relevance
                )
            )

        return results

    # ------------------------------------------------------------------
    # Local curated cache search (offline fallback)
    # ------------------------------------------------------------------
    def _search_local_cache(
        self,
        query: str,
        herb: Optional[str],
        max_results: int = 5,
    ) -> List[BiomedicalResult]:
        """Score curated entries by keyword overlap and return top matches."""
        query_tokens = self._tokenize(query)
        herb_tokens = self._tokenize(herb) if herb else set()
        all_tokens = query_tokens | herb_tokens

        scored: List[tuple[float, dict]] = []
        for entry in self._curated:
            kw_tokens = set(entry.get("keywords", []))
            # Keyword hit score
            kw_hits = len(all_tokens & kw_tokens)
            # Title / abstract token overlap
            text_tokens = self._tokenize(
                entry.get("title", "") + " " + entry.get("abstract_snippet", "")
            )
            text_hits = len(all_tokens & text_tokens)
            score = (kw_hits * 2.0 + text_hits * 0.5) / max(len(all_tokens), 1)
            # Minimum match requirement: at least one keyword hit or multiple text matches with score threshold
            if kw_hits > 0 or (text_hits >= 2 and score >= 0.35):
                scored.append((score, entry))

        # Sort by score descending, then recency
        scored.sort(key=lambda x: (x[0], int(x[1].get("pub_year", "0"))), reverse=True)

        results: List[BiomedicalResult] = []
        for score, entry in scored[:max_results]:
            results.append(
                BiomedicalResult(
                    pmid=entry.get("pmid", ""),
                    title=entry.get("title", ""),
                    journal=entry.get("journal", ""),
                    pub_year=entry.get("pub_year", ""),
                    study_type=entry.get("study_type", "Review"),
                    abstract_snippet=entry.get("abstract_snippet", ""),
                    source="CuratedCache",
                    relevance_score=min(score, 1.0),
                )
            )

        return results

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _load_curated_cache(self) -> None:
        """Load the local curated evidence JSON into memory."""
        try:
            with open(_CURATED_DATA_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self._curated = data.get("entries", [])
            logger.info(
                "[BiomedicalService] Loaded %d curated evidence entries from %s",
                len(self._curated), _CURATED_DATA_PATH,
            )
        except FileNotFoundError:
            logger.warning(
                "[BiomedicalService] Curated evidence file not found at %s. "
                "Only live PubMed retrieval will be available.",
                _CURATED_DATA_PATH,
            )
            self._curated = []
        except json.JSONDecodeError as exc:
            logger.error("[BiomedicalService] Failed to parse curated evidence JSON: %s", exc)
            self._curated = []

    def _build_pubmed_query(self, query: str, herb: Optional[str]) -> str:
        """Build an optimised PubMed search string.

        Combines the herb name (if given) with Ayurveda-specific MeSH terms
        and narrows to human studies.
        """
        parts: List[str] = []

        if herb:
            # Quote multi-word herb names for exact phrase matching
            safe_herb = f'"{herb}"' if " " in herb else herb
            parts.append(f"({safe_herb}[Title/Abstract] OR {safe_herb}[MeSH Terms])")

        # Narrow to Ayurveda / traditional medicine domain
        domain_filter = (
            '("Ayurveda"[Title/Abstract] OR "traditional medicine"[Title/Abstract] '
            'OR "herbal medicine"[Title/Abstract] OR "phytotherapy"[MeSH Terms])'
        )
        parts.append(domain_filter)

        # Add free-text query terms (strip generic stop words)
        query_clean = re.sub(r"\b(the|a|an|and|or|is|for|in|of|as|per)\b", "", query, flags=re.I).strip()
        if query_clean:
            parts.append(f"({query_clean}[Title/Abstract])")

        # Restrict to human studies and exclude animal-only papers at NCBI level
        parts.append('("humans"[MeSH Terms] OR "clinical study"[Publication Type])')

        return " AND ".join(parts)

    @staticmethod
    def _classify_study_type(source_text: str) -> str:
        """Infer study type from title / pubtype string using pattern matching."""
        text_lower = source_text.lower()
        for pattern, label in _STUDY_TYPE_PATTERNS:
            if re.search(pattern, text_lower, re.I):
                return label
        return "Research Article"

    @staticmethod
    def _extract_pub_year(article: dict) -> str:
        """Extract 4-digit publication year from an esummary article dict."""
        # Prefer sortpubdate, then pubdate
        for field in ("sortpubdate", "pubdate", "epubdate"):
            raw = article.get(field, "")
            match = re.search(r"\b(19|20)\d{2}\b", raw)
            if match:
                return match.group()
        return ""

    @staticmethod
    def _tokenize(text: Optional[str]) -> set:
        """Lowercase word-token set, stripping punctuation, ignoring stop words."""
        if not text:
            return set()
        STOP = {
            "the", "a", "an", "and", "or", "in", "of", "for", "to", "is", "are",
            "as", "with", "its", "this", "that", "on", "at", "by", "from", "it",
            "be", "was", "has", "have", "been", "not", "no", "per", "also",
            "herb", "herbs", "plant", "plants", "study", "studies", "effect",
            "effects", "treatment", "review", "clinical",
        }
        tokens = re.findall(r"[a-z]{2,}", text.lower())
        return {t for t in tokens if t not in STOP}

    @staticmethod
    def _truncate(text: str, max_chars: int) -> str:
        """Return text truncated to max_chars with ellipsis if needed."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------
biomedical_service = BiomedicalEvidenceService()
