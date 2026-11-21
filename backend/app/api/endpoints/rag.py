"""RAG (Retrieval-Augmented Generation) endpoints for AyurEval.

Provides semantic search over canonical Samhitas, sample data ingestion into ChromaDB,
and digital corpus scrapers for online NIIMH/CCRAS repositories and local JSON/TXT files.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.corpus_loader import (
    fetch_and_parse_niimh_page,
    ingest_json_corpus,
)
from app.services.vector_store import (
    AUTHENTIC_SAMHITA_SAMPLES,
    ClassicalAyurvedicText,
    search_classical_sources,
    vector_store,
)

router = APIRouter()


# ==============================================================================
# Request / Response Schemas
# ==============================================================================


class IngestSampleRequest(BaseModel):
    """Optional payload to ingest custom or default authentic Samhita samples."""

    custom_chunks: Optional[List[ClassicalAyurvedicText]] = Field(
        default=None,
        description="Optional list of custom Ayurvedic passages to ingest. If omitted, default authentic Brihat Trayi samples are used.",
    )


class IngestSampleResponse(BaseModel):
    """Response payload acknowledging document ingestion."""

    status: str
    message: str
    chunks_ingested: int
    collection_total: int
    ingested_citations: List[str]


class IngestURLRequest(BaseModel):
    """Request payload to scrape and ingest an e-Samhita / NIIMH web page."""

    url: str = Field(
        ...,
        description="URL of the digital NIIMH or CCRAS e-Samhita chapter page",
        examples=["http://niimh.nic.in/samhita/charaka/sutrasthana/chapter27"],
    )
    source_book: str = Field(
        default="Charaka Samhita",
        description="Canonical book title (e.g. 'Charaka Samhita', 'Sushruta Samhita', 'Ashtanga Hridaya')",
    )
    chapter: str = Field(
        default="Sutrasthana",
        description="Chapter or Adhyaya name (e.g. 'Sutrasthana 27 - Annapanavidhi')",
    )


class IngestURLResponse(BaseModel):
    """Response payload acknowledging web scraping and ingestion."""

    status: str
    message: str
    url: str
    source_book: str
    chapter: str
    chunks_indexed: int
    collection_total: int
    citations: List[str]


class IngestFileRequest(BaseModel):
    """Request payload to ingest a local .json or .txt corpus file."""

    file_path: str = Field(
        ...,
        description="Local path to .json or .txt file containing classical shlokas",
        examples=["./data/samhitas/charaka_sutrasthana_sample.json"],
    )


class IngestFileResponse(BaseModel):
    """Response payload acknowledging file corpus ingestion."""

    status: str
    message: str
    file_path: str
    source_book: str
    chapter: str
    chunks_indexed: int
    collection_total: int
    citations: List[str]


class RAGSearchRequest(BaseModel):
    """Request payload for semantic retrieval of classical passages."""

    query: str = Field(
        ...,
        description="Clinical inquiry, Ayurvedic concept, herb, or disease (e.g. 'sesame oil for vata abhyanga')",
        examples=["What is the classical protocol for sesame oil in vata disorders?"],
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of most relevant classical passages to retrieve",
    )


class PassageItem(BaseModel):
    """Individual retrieved canonical passage."""

    id: str
    source_book: str
    chapter: str
    verse_number: str
    citation: str
    text: str
    commentary: Optional[str] = None
    category: Optional[str] = None
    relevance_score: float
    distance: float


class RAGSearchResponse(BaseModel):
    """Response payload containing ranked retrieved passages."""

    query: str
    total_found: int
    passages: List[PassageItem]


# ==============================================================================
# Endpoint Handlers
# ==============================================================================


@router.post(
    "/ingest-sample",
    response_model=IngestSampleResponse,
    status_code=status.HTTP_200_OK,
    summary="Load initial authentic Samhita sample chunks into ChromaDB",
)
async def ingest_sample_chunks(
    payload: Optional[IngestSampleRequest] = None,
) -> IngestSampleResponse:
    """Ingests authentic canonical passages from Charaka Samhita, Sushruta Samhita,

    and Ashtanga Hridaya into the ChromaDB vector database.
    """
    try:
        if payload and payload.custom_chunks:
            items_to_ingest = payload.custom_chunks
        else:
            items_to_ingest = [
                ClassicalAyurvedicText(**sample)
                for sample in AUTHENTIC_SAMHITA_SAMPLES
            ]

        count = vector_store.ingest_classical_texts(items_to_ingest)
        total = vector_store.collection.count()
        citations = [
            f"{item.source_book}, {item.chapter}, Verse {item.verse_number}"
            for item in items_to_ingest
        ]

        return IngestSampleResponse(
            status="success",
            message=f"Successfully indexed {count} canonical Ayurvedic passages into ChromaDB.",
            chunks_ingested=count,
            collection_total=total,
            ingested_citations=citations,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest canonical texts into vector store: {str(exc)}",
        ) from exc


@router.post(
    "/ingest-url",
    response_model=IngestURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape and ingest an NIIMH e-Samhita web page into ChromaDB",
)
async def ingest_from_niimh_url(payload: IngestURLRequest) -> IngestURLResponse:
    """Dynamically fetches, parses, and indexes Sanskrit shlokas and commentaries

    from NIIMH / CCRAS e-Samhita digital chapter links into ChromaDB.
    """
    try:
        parsed_items = await fetch_and_parse_niimh_page(
            url=payload.url,
            source_book=payload.source_book,
            chapter=payload.chapter,
        )

        indexed_count = vector_store.ingest_classical_texts(parsed_items)
        total = vector_store.collection.count()
        citations = [
            f"{t.source_book}, {t.chapter}, Verse {t.verse_number}"
            for t in parsed_items
        ]

        return IngestURLResponse(
            status="success",
            message=f"Successfully scraped and indexed {indexed_count} verses from digital source into ChromaDB.",
            url=payload.url,
            source_book=payload.source_book,
            chapter=payload.chapter,
            chunks_indexed=indexed_count,
            collection_total=total,
            citations=citations,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest digital corpus URL: {str(exc)}",
        ) from exc


@router.post(
    "/ingest-file",
    response_model=IngestFileResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch ingest local JSON or TXT corpus file into ChromaDB",
)
async def ingest_local_file(payload: IngestFileRequest) -> IngestFileResponse:
    """Reads a local structured .json or .txt file containing classical Ayurvedic verses,

    chunks them cleanly preserving verse boundaries, and indexes them into ChromaDB.
    """
    try:
        res = ingest_json_corpus(payload.file_path)
        total = vector_store.collection.count()

        return IngestFileResponse(
            status=res.status,
            message=res.details or "Successfully indexed file into ChromaDB.",
            file_path=payload.file_path,
            source_book=res.source_book,
            chapter=res.chapter,
            chunks_indexed=res.chunks_indexed,
            collection_total=total,
            citations=res.citations,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch ingest file: {str(exc)}",
        ) from exc


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic retrieval of classical shlokas and bhashyas",
)
async def search_samhitas(request: RAGSearchRequest) -> RAGSearchResponse:
    """Queries the ChromaDB vector database with dense embeddings and returns

    the top-k most relevant classical Sanskrit shlokas, English translations, and
    authoritative traditional commentaries.
    """
    try:
        # If collection is empty, auto-seed with authentic samples
        if vector_store.collection.count() == 0:
            default_samples = [
                ClassicalAyurvedicText(**sample)
                for sample in AUTHENTIC_SAMHITA_SAMPLES
            ]
            vector_store.ingest_classical_texts(default_samples)

        results = search_classical_sources(query=request.query, top_k=request.top_k)

        passages = [
            PassageItem(
                id=item["id"],
                source_book=item["source_book"],
                chapter=item["chapter"],
                verse_number=item["verse_number"],
                citation=item["citation"],
                text=item["text"],
                commentary=item.get("commentary") or None,
                category=item.get("category") or None,
                relevance_score=item["relevance_score"],
                distance=item["distance"],
            )
            for item in results
        ]

        return RAGSearchResponse(
            query=request.query,
            total_found=len(passages),
            passages=passages,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic retrieval failed: {str(exc)}",
        ) from exc
