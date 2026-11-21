"""AyurEval (COGNEXA) - Main FastAPI Application Entry Point.

AI-powered, source-aware verification framework that independently audits the accuracy,
context, classical references (Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya),
and modern scientific evidence behind AI-generated Ayurveda answers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.ayurparam import router as ayurparam_router
from app.api.endpoints.biomedical import router as biomedical_router
from app.api.endpoints.export import router as export_router
from app.api.endpoints.rag import router as rag_router
from app.api.endpoints.safety import router as safety_router
from app.api.endpoints.verification import router as verification_router
from app.core.config import settings

# OpenAPI Tags Metadata configuration for production-grade Swagger & ReDoc
TAGS_METADATA = [
    {
        "name": "Health & Status",
        "description": "Readiness, liveness, and system telemetry endpoints for backend and vector store health.",
    },
    {
        "name": "AyurEval Verification & Inquiry",
        "description": (
            "Primary fact-checking pipeline. Decomposes Ayurvedic assertions into discrete atomic claims "
            "and performs multi-hop verification against canonical Sanskrit passages and modern scientific papers."
        ),
        "externalDocs": {
            "description": "Brihat Trayi Canonical Research Index",
            "url": "http://niimh.nic.in",
        },
    },
    {
        "name": "Dual-Evidence Cross-Auditor",
        "description": (
            "Simultaneously queries classical Samhitas (ChromaDB) and modern biomedical clinical trials "
            "(PubMed / Curated Cache) to grade claims on a unified 6-tier dual-evidence spectrum."
        ),
    },
    {
        "name": "Ayurvedic Safety, Matra & Contraindications",
        "description": (
            "Phytovigilance and pharmacological safety engine. Scans claims and prescriptions for "
            "clinical contraindications, classical Matra (dosage bounds), Anupana (adjuvants), and herb-drug interactions."
        ),
        "externalDocs": {
            "description": "Ayurvedic Pharmacopoeia of India (API)",
            "url": "https://www.ayush.gov.in",
        },
    },
    {
        "name": "Batch Verification & Analytics",
        "description": (
            "High-throughput batch auditor. Concurrently validates up to 10 claims and aggregates summary analytics "
            "(supported, contradicted, safety flags, and category distributions)."
        ),
    },
    {
        "name": "Biomedical Evidence & PubMed",
        "description": (
            "Live E-utilities and curated evidence retrieval over PubMed and biomedical clinical trial registries "
            "for botanical entities, pharmacological mechanisms, and phytochemical constituents."
        ),
        "externalDocs": {
            "description": "NCBI PubMed E-Utilities API",
            "url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/",
        },
    },
    {
        "name": "RAG & Vector Retrieval",
        "description": (
            "ChromaDB dense embedding vector store operations: semantic search over Charaka Samhita, "
            "Sushruta Samhita, and Ashtanga Hridaya, plus e-Samhita (NIIMH) web ingestion."
        ),
    },
    {
        "name": "AyurParam LLM & Claim Extraction",
        "description": (
            "Ayurveda-specialized generative engine: clinical question answering and grammatical "
            "decomposition of clinical answers into verifiable atomic claims."
        ),
    },
    {
        "name": "Report Export & Download",
        "description": (
            "Transforms verification audits, dual-evidence reports, and safety dossiers into formatted "
            "academic Markdown (.md) or raw JSON (.json) downloadable file attachments."
        ),
    },
]

APP_DESCRIPTION = """
## 🌿 AyurEval (COGNEXA) Verification & Phytovigilance Engine

**AyurEval** is an academic-grade, source-aware fact verification framework designed to independently audit,
cross-reference, and validate AI-generated answers regarding Ayurvedic medicine against:

1. **The Classical Brihat Trayi**:
   - *Charaka Samhita* (Agnivesha / Charaka / Dridhabala)
   - *Sushruta Samhita* (Sushruta / Nagarjuna)
   - *Ashtanga Hridaya* (Vagbhata)
2. **Authoritative Traditional Commentaries (Bhashyas)**:
   - *Chakrapani Datta* (*Ayurveda Dipika*)
   - *Dalhana* (*Nibandha Samgraha*)
   - *Arunadatta* (*Sarvangasundara*)
   - *Hemadri* (*Ayurveda Rasayana*)
3. **Contemporary Biomedical Evidence**:
   - NCBI PubMed API (clinical trials, RCTs, systemic reviews)
   - Curated Phytovigilance Database & Ayurvedic Pharmacopoeia of India (API) standards.

---
### 🔬 Key Capabilities
- **Decomposition**: Grammatically partitions complex therapeutic advice into discrete atomic claims.
- **Dual-Evidence Synthesis**: Concurrently checks traditional Samhita shlokas and peer-reviewed biomedical trials.
- **Phytovigilance**: Automatically flags clinical contraindications (pregnancy, bleeding disorders, Pitta aggravation), maximum safe daily dosages (*Matra*), and hazardous herb-drug interactions (e.g. Warfarin, sedatives).
- **Batch Processing**: Concurrently verifies up to 10 claims with statistical summary analytics.
- **Academic Export**: Instant Markdown, PDF, and JSON download for publication or clinical review.
"""

# Initialize FastAPI application with production-grade metadata
app = FastAPI(
    title=f"{settings.app_name} - Canonical Evidence Engine",
    version=settings.version,
    description=APP_DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "AyurEval Research Initiative (COGNEXA)",
        "url": "https://github.com/ayureval/ayureval",
        "email": "research@ayureval.org",
    },
    license_info={
        "name": "Apache 2.0 / Academic Open Science License",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

# Configure CORS Middleware allowing requests from http://localhost:5173
cors_origins = list(
    set(
        ["http://localhost:5173", "http://localhost:3000"]
        + [origin for origin in settings.allowed_origins]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint strictly returning {"status": "healthy", "service": "AyurEval Backend"}
@app.get(
    f"{settings.api_v1_prefix}/health",
    tags=["Health & Status"],
    summary="Service Health Check",
)
async def health_check():
    """Verify backend API health and readiness."""
    return {"status": "healthy", "service": "AyurEval Backend"}


# Root redirection / welcome endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root metadata endpoint with documentation links."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "health_endpoint": f"{settings.api_v1_prefix}/health",
        "docs_url": f"{settings.api_v1_prefix}/docs",
    }


# Register the Verification Router under /api/v1 (providing POST /api/v1/ask & POST /api/v1/verify)
app.include_router(
    verification_router,
    prefix=settings.api_v1_prefix,
    tags=["AyurEval Verification & Inquiry"],
)

# Register the RAG Router under /api/v1/rag (providing POST /api/v1/rag/ingest-sample & POST /api/v1/rag/search)
app.include_router(
    rag_router,
    prefix=f"{settings.api_v1_prefix}/rag",
    tags=["RAG & Vector Retrieval"],
)

# Register the AyurParam Router under /api/v1/ayurparam (providing answer generation & claim decomposition)
app.include_router(
    ayurparam_router,
    prefix=f"{settings.api_v1_prefix}/ayurparam",
    tags=["AyurParam LLM & Claim Extraction"],
)

# Register the Biomedical Evidence Router under /api/v1/biomedical (providing PubMed & clinical trial retrieval)
app.include_router(
    biomedical_router,
    prefix=f"{settings.api_v1_prefix}/biomedical",
    tags=["Biomedical Evidence & PubMed"],
)

# Register the Safety & Contraindications Router under /api/v1/safety
app.include_router(
    safety_router,
    prefix=f"{settings.api_v1_prefix}/safety",
    tags=["Ayurvedic Safety, Matra & Contraindications"],
)

# Register the Report Export Router under /api/v1/export
app.include_router(
    export_router,
    prefix=f"{settings.api_v1_prefix}/export",
    tags=["Report Export & Download"],
)

# Optional alias under /api/v1/verification for backwards-compatibility with /verification/verify
app.include_router(
    verification_router,
    prefix=f"{settings.api_v1_prefix}/verification",
    tags=["AyurEval Verification (Alias)"],
    include_in_schema=False,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
