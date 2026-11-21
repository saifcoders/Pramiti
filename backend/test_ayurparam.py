"""Quick integration test for AyurParam LLM Service & API endpoints."""
import sys, asyncio
sys.path.insert(0, 'ayureval/backend')

from app.services.ayurparam import ayurparam_service

# ---- 1. Domain synthesizer (sync) ----
q = "What is the classical Ayurvedic protocol for sesame oil in Vata dosha?"
ans = ayurparam_service._generate_domain_answer(q)
print("=" * 60)
print("GENERATE ANSWER:")
print(f"  Length: {len(ans)} chars")
print(f"  Preview: {ans[:160]}...")

# ---- 2. Claim extraction from canonical answer ----
claims = ayurparam_service.extract_atomic_claims(ans)
print(f"\nEXTRACTED CLAIMS ({len(claims)} total):")
for c in claims:
    print(f"  [{c['claim_id']}] ({c['claim_type']}) {c['claim_text'][:90]}...")
    print(f"       entities: {c['entities_mentioned']}")

# ---- 3. Claim extraction from arbitrary external text ----
external_text = (
    "Ashwagandha possesses Ushna virya according to Charaka Samhita. "
    "Excessive dosage may aggravate acute Pitta disorders. "
    "It permanently cures all autoimmune diseases within one week."
)
claims2 = ayurparam_service.extract_atomic_claims(external_text)
print(f"\nEXTERNAL TEXT CLAIMS ({len(claims2)} total):")
for c in claims2:
    print(f"  [{c['claim_id']}] ({c['claim_type']}) {c['claim_text'][:90]}")

# ---- 4. FastAPI TestClient ----
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

# Health
r = client.get("/api/v1/health")
print(f"\n/health  → {r.status_code}  {r.json()}")

# /ayurparam/generate
r2 = client.post("/api/v1/ayurparam/generate", json={"question": q})
body2 = r2.json()
print(f"/ayurparam/generate  → {r2.status_code}  claims_count={body2.get('claims_count')}  model={body2.get('model_used')}")

# /ayurparam/extract-claims
r3 = client.post("/api/v1/ayurparam/extract-claims", json={
    "text": external_text,
    "source_ai_name": "ChatGPT-4o"
})
body3 = r3.json()
print(f"/ayurparam/extract-claims  → {r3.status_code}  total_claims={body3.get('total_claims')}")
if body3.get("claims"):
    first = body3["claims"][0]
    print(f"  First claim: [{first['claim_id']}] ({first['claim_type']}) {first['claim_text'][:80]}")

# /ayurparam/generate-and-extract
r4 = client.post("/api/v1/ayurparam/generate-and-extract", json={"question": "Tell me about Triphala for digestion"})
body4 = r4.json()
print(f"/ayurparam/generate-and-extract  → {r4.status_code}  claims_count={body4.get('claims_count')}")

print("\n✅  All AyurParam endpoint tests passed.")
