"""Comprehensive End-to-End Integration Test Suite for AyurEval (COGNEXA).

Simulates complete user and clinical verification workflows against the live FastAPI backend:
1. Health check & ChromaDB collection verification.
2. Single-claim verification audit (POST /api/v1/verify & POST /api/v1/ask).
3. Biomedical PubMed / curated evidence retrieval (POST /api/v1/biomedical/search).
4. Classical vs. Biomedical dual-evidence cross-audit (POST /api/v1/biomedical/dual-audit).
5. Ayurvedic safety, matra & contraindication check (POST /api/v1/safety/check).
6. Batch claim verification and summary analytics (POST /api/v1/verification/batch).
7. Report formatting and export payload verification (POST /api/v1/export/report).
"""

import sys
import httpx

try:
    import pytest
    FIXTURE_DECORATOR = pytest.fixture(scope="session")
except ImportError:
    # Allow running seamlessly as a standalone script without pytest
    def FIXTURE_DECORATOR(func):
        return func

BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 45.0  # Allow sufficient window for semantic embedding inference


@FIXTURE_DECORATOR
def client():
    """Shared HTTP client with session timeout configuration."""
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


# ==============================================================================
# 1. Health Check & Vector Store Verification
# ==============================================================================
def test_01_health_check(client):
    """Verifies backend service health and operational readiness."""
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed with {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("status") == "healthy"
    assert "service" in data
    print("✓ [Workflow 1A] Health check verified: status=healthy")


def test_01_chromadb_semantic_search(client):
    """Verifies ChromaDB vector store collection and semantic retrieval."""
    payload = {
        "query": "Tila Taila sesame oil for Vata pacification and Abhyanga",
        "top_k": 2,
    }
    res = client.post("/rag/search", json=payload)
    assert res.status_code == 200, f"RAG search failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "passages" in data
    assert len(data["passages"]) > 0
    first_passage = data["passages"][0]
    assert "source_book" in first_passage
    assert "citation" in first_passage
    assert "relevance_score" in first_passage
    print(f"✓ [Workflow 1B] ChromaDB RAG search verified: {len(data['passages'])} passage(s) retrieved")


# ==============================================================================
# 2. Single-Claim Verification Audit
# ==============================================================================
def test_02_verify_existing_answer(client):
    """Simulates auditing an external AI-generated Ayurveda statement."""
    payload = {
        "ai_generated_text": (
            "Sesame oil (Tila Taila) is the foremost sneha for mitigating Vata dosha "
            "and promoting bodily strength during daily Abhyanga."
        ),
        "source_ai_name": "ChatGPT-4o",
    }
    res = client.post("/verify", json=payload)
    assert res.status_code == 200, f"/verify failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "claims" in data
    assert len(data["claims"]) > 0
    first_claim = data["claims"][0]
    assert "claim_text" in first_claim
    assert "category" in first_claim
    assert "overall_summary" in data
    print(f"✓ [Workflow 2A] Verify answer verified: {len(data['claims'])} atomic claim(s) audited")


def test_02_ask_and_verify(client):
    """Simulates end-to-end question answering and source verification."""
    payload = {
        "question": "What are the classical indications and dosage for Ashwagandha in Vata disorders?"
    }
    res = client.post("/ask", json=payload)
    assert res.status_code == 200, f"/ask failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "claims" in data
    assert "overall_summary" in data
    print(f"✓ [Workflow 2B] Ask & verify complete: answer synthesized and cross-audited")


# ==============================================================================
# 3. Biomedical Evidence Retrieval (PubMed / Curated Cache)
# ==============================================================================
def test_03_biomedical_search(client):
    """Queries PubMed and curated evidence database for clinical literature."""
    payload = {
        "query": "Ashwagandha stress reduction cortisol levels",
        "herb": "Ashwagandha",
        "max_results": 3,
    }
    res = client.post("/biomedical/search", json=payload)
    assert res.status_code == 200, f"/biomedical/search failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0
    article = data["results"][0]
    assert "pmid" in article
    assert "title" in article
    assert "study_type" in article
    print(f"✓ [Workflow 3] Biomedical search verified: {len(data['results'])} clinical study/studies found")


# ==============================================================================
# 4. Classical vs. Biomedical Dual-Evidence Cross-Audit
# ==============================================================================
def test_04_dual_evidence_cross_audit(client):
    """Simultaneously cross-audits classical Samhita verses and modern clinical evidence."""
    payload = {
        "text": (
            "Ashwagandha reduces perceived stress and serum cortisol levels. "
            "Sesame oil is the premier sneha for Vata pacification in Abhyanga."
        ),
        "query_context": "E2ETestSuite",
        "max_biomedical_per_claim": 2,
    }
    res = client.post("/biomedical/dual-audit", json=payload)
    assert res.status_code == 200, f"/biomedical/dual-audit failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "claims" in data
    assert "grade_summary" in data
    assert "executive_summary" in data
    first_claim = data["claims"][0]
    assert "dual_grade" in first_claim
    assert "classical_evidence" in first_claim
    assert "biomedical_evidence" in first_claim
    print(f"✓ [Workflow 4] Dual audit verified: {len(data['claims'])} claim(s), grades={list(data['grade_summary'].keys())}")


# ==============================================================================
# 5. Ayurvedic Safety, Matra & Contraindication Checker
# ==============================================================================
def test_05_ayurvedic_safety_check(client):
    """Audits clinical contraindications, matra dosage bounds, and drug interactions."""
    payload = {
        "text": (
            "Patient is a pregnant female taking 10 grams of Ashwagandha root powder daily "
            "along with Turmeric and Warfarin for inflammation."
        )
    }
    res = client.post("/safety/check", json=payload)
    assert res.status_code == 200, f"/safety/check failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "is_safe" in data
    assert "detected_herbs" in data
    assert "Ashwagandha" in data["detected_herbs"]
    assert "alerts" in data
    assert len(data["alerts"]) > 0
    # Expected critical alert: Ashwagandha in pregnancy
    severities = [a["severity"] for a in data["alerts"]]
    assert "CRITICAL" in severities or "WARNING" in severities
    print(f"✓ [Workflow 5] Safety check verified: {len(data['alerts'])} alert(s) detected, is_safe={data['is_safe']}")


# ==============================================================================
# 6. Batch Claim Verification & Summary Analytics
# ==============================================================================
def test_06_batch_claim_verification(client):
    """Executes concurrent verification across multiple claims with aggregate analytics."""
    payload = {
        "claims": [
            "Ashwagandha improves memory and reduces stress.",
            "Turmeric reduces joint inflammation.",
            "Sesame oil is the premier sneha for Vata disorders.",
        ],
        "source_name": "E2E Batch Clinical Test",
    }
    res = client.post("/verification/batch", json=payload)
    assert res.status_code == 200, f"/verification/batch failed with {res.status_code}: {res.text}"
    data = res.json()
    assert "analytics" in data
    assert "results" in data
    analytics = data["analytics"]
    assert analytics["total_claims"] == 3
    assert "supported" in analytics
    assert "insufficient_evidence" in analytics
    assert "total_safety_flags" in analytics
    assert len(data["results"]) == 3
    print(f"✓ [Workflow 6] Batch verification verified: {analytics['total_claims']} claims audited with analytics")


# ==============================================================================
# 7. Report Formatting & Export Payload Verification
# ==============================================================================
def test_07_export_report_markdown(client):
    """Verifies generating and downloading structured academic Markdown reports."""
    payload = {
        "report_type": "verification",
        "format": "markdown",
        "report_data": {
            "query_or_source": "E2E Export Verification Test",
            "claims": [
                {
                    "claim_id": 1,
                    "claim_text": "Sesame oil is the foremost unctuous substance for Vata.",
                    "category": "Supported by source",
                    "classical_reference": "Charaka Samhita Sutrasthana 27/225",
                    "original_passage": "तैलं वातहरं त्वच्यं बल्यं स्निग्धं...",
                    "commentary_note": "Chakrapani emphasizes Tila Taila primacy.",
                    "scientific_evidence": "Sesamin lignans attenuate oxidative stress.",
                    "reasoning": "Direct concordance with canonical Charaka verse.",
                }
            ],
            "overall_summary": "E2E Test overall summary passed.",
            "limitations": ["Research purposes only."],
        },
    }
    res = client.post("/export/report", json=payload)
    assert res.status_code == 200, f"/export/report failed with {res.status_code}: {res.text}"
    assert "text/markdown" in res.headers.get("content-type", "")
    assert "attachment" in res.headers.get("content-disposition", "")
    markdown_content = res.text
    assert "# AyurEval (COGNEXA) Verification Report" in markdown_content
    assert "Sesame oil" in markdown_content
    print("✓ [Workflow 7] Export report verified: Markdown attachment successfully generated")


# ==============================================================================
# Standalone Execution Runner
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  AyurEval (COGNEXA) E2E Integration Test Suite")
    print("=" * 65 + "\n")

    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as test_client:
        tests = [
            ("1. Health Check", test_01_health_check),
            ("2. ChromaDB RAG Search", test_01_chromadb_semantic_search),
            ("3. Single-Claim Verify Answer", test_02_verify_existing_answer),
            ("4. Ask & Verify Pipeline", test_02_ask_and_verify),
            ("5. Biomedical Evidence Retrieval", test_03_biomedical_search),
            ("6. Dual-Evidence Cross-Audit", test_04_dual_evidence_cross_audit),
            ("7. Ayurvedic Safety & Matra Check", test_05_ayurvedic_safety_check),
            ("8. Batch Claim Verification", test_06_batch_claim_verification),
            ("9. Export Academic Report", test_07_export_report_markdown),
        ]

        passed = 0
        failed = 0
        for name, test_fn in tests:
            try:
                test_fn(test_client)
                passed += 1
            except Exception as exc:
                print(f"✗ [{name}] FAILED: {exc}")
                failed += 1

        print("\n" + "=" * 65)
        print(f"  Summary: {passed} PASSED, {failed} FAILED out of {len(tests)} tests")
        print("=" * 65 + "\n")

        if failed > 0:
            sys.exit(1)
        sys.exit(0)
