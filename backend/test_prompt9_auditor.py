"""Unit and integration test for Prompt 9: VerificationAuditor and real /ask & /verify endpoints."""
import sys
import asyncio
sys.path.insert(0, 'ayureval/backend')

from app.services.verification.auditor import verification_auditor
from app.models.schemas import VerificationCategory

async def run_tests():
    print("=" * 70)
    print("STEP 1: Direct VerificationAuditor.audit_text() testing")
    print("=" * 70)

    # Test Case 1: Sesame oil & Abhyanga with exaggerated claim
    input_text_1 = (
        "In classical Ayurvedic pharmacology, Tila Taila (sesame oil) is the foremost unctuous substance for pacifying Vata dosha. "
        "Daily full-body Abhyanga permanently cures severe peripheral neuropathy and completely restores degenerate lumbar intervertebral discs. "
        "According to Charaka Samhita, Sutrasthana 12/99, consuming raw sesame seeds directly cures acute hemiplegia within three days."
    )

    report1 = await verification_auditor.audit_text(input_text_1, query_context="Vata Sneha Clinical Inquiry")
    print(f"Report 1: Total claims audited: {len(report1.claims)}")
    print(f"Summary: {report1.overall_summary}")

    for idx, c in enumerate(report1.claims, 1):
        print(f"\n--- Claim {c.claim_id} [{c.category.value}] ---")
        print(f"  Claim Text: {c.claim_text}")
        print(f"  Reference: {c.classical_reference}")
        if c.original_passage:
            print(f"  Shloka Snippet: {c.original_passage[:80]}...")
        if c.commentary_note:
            print(f"  Commentary: {c.commentary_note[:100]}...")
        if c.scientific_evidence:
            print(f"  Biomedical Evidence: {c.scientific_evidence[:100]}...")
        print(f"  Reasoning: {c.reasoning[:120]}...")

    categories = [c.category for c in report1.claims]
    assert VerificationCategory.SUPPORTED_BY_SOURCE in categories, "Must contain Supported by source"
    assert VerificationCategory.PARTIALLY_SUPPORTED in categories, "Must contain Partially supported"
    assert VerificationCategory.REFERENCE_NOT_VERIFIED in categories, "Must contain Reference not verified"
    print("\n✅ Test Case 1 Passed: Generated Supported, Partially Supported, and Reference Not Verified.")

    # Test Case 2: Dietary Contradiction (Viruddha Ahara)
    input_text_2 = "Consuming fish together with milk is safe and highly beneficial for health."
    report2 = await verification_auditor.audit_text(input_text_2, query_context="Viruddha Ahara Inquiry")
    print("\n" + "=" * 70)
    print("Test Case 2: Dietary Contradiction")
    print("=" * 70)
    print(f"Claim 1 Category: {report2.claims[0].category.value}")
    print(f"Reference: {report2.claims[0].classical_reference}")
    print(f"Reasoning: {report2.claims[0].reasoning}")
    assert report2.claims[0].category == VerificationCategory.CONTRADICTED_BY_SOURCE
    print("✅ Test Case 2 Passed: Correctly classified Contradicted by source.")

    # Test Case 3: TestClient for POST /api/v1/ask and POST /api/v1/verify
    print("\n" + "=" * 70)
    print("STEP 2: FastAPI Endpoints TestClient (/api/v1/ask & /api/v1/verify)")
    print("=" * 70)
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    # Test /ask
    res_ask = client.post("/api/v1/ask", json={"question": "What is the classical Ayurvedic protocol for pacifying Vata dosha using sesame oil?"})
    print(f"POST /api/v1/ask -> HTTP {res_ask.status_code}")
    assert res_ask.status_code == 200
    data_ask = res_ask.json()
    print(f"  Generated Answer Length: {len(data_ask.get('generated_answer', ''))}")
    print(f"  Audited Claims Count: {len(data_ask.get('claims', []))}")
    print(f"  Overall Summary: {data_ask.get('overall_summary')}")
    assert len(data_ask.get("claims", [])) > 0

    # Test /verify
    res_verify = client.post("/api/v1/verify", json={
        "ai_generated_text": input_text_1,
        "source_ai_name": "GPT-4-Ayurveda"
    })
    print(f"\nPOST /api/v1/verify -> HTTP {res_verify.status_code}")
    assert res_verify.status_code == 200
    data_verify = res_verify.json()
    print(f"  Source Label: {data_verify.get('query_or_source')}")
    print(f"  Audited Claims Count: {len(data_verify.get('claims', []))}")
    print(f"  Summary: {data_verify.get('overall_summary')}")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! Real verification pipeline operational.")

if __name__ == "__main__":
    asyncio.run(run_tests())
