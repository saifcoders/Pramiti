"""Lightweight AyurParam test - direct module import, bypassing services/__init__.py chain."""
import sys
import importlib
sys.path.insert(0, 'ayureval/backend')

# ---- Directly import only what we need, bypassing services/__init__.py ----
import importlib.util, os

def load_module_direct(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

base = "ayureval/backend/app"

# Load config first
config = load_module_direct("app.core.config", f"{base}/core/config.py")

# Load schemas
load_module_direct("app.models.schemas", f"{base}/models/schemas.py")

# Now load ayurparam directly (it only needs config + schemas)
ayurparam_mod = load_module_direct("app.services.ayurparam", f"{base}/services/ayurparam.py")

AyurParamService = ayurparam_mod.AyurParamService
CANONICAL_KNOWLEDGE_ARCHETYPES = ayurparam_mod.CANONICAL_KNOWLEDGE_ARCHETYPES

svc = AyurParamService(provider="mock")

# ==== 1. Domain Answer Generation ====
q_sesame = "What is the classical Ayurvedic protocol for sesame oil in Vata dosha?"
ans = svc._generate_domain_answer(q_sesame)
assert len(ans) > 100, f"Expected non-trivial answer, got: {ans[:50]}"
print(f"[PASS] generate_domain_answer → {len(ans)} chars")
print(f"       Preview: {ans[:130]}...\n")

# ==== 2. Canonical archetype claim extraction ====
claims = svc.extract_atomic_claims(ans)
assert len(claims) >= 3, f"Expected >=3 claims, got {len(claims)}"
for c in claims:
    assert 'claim_id' in c, "Missing claim_id"
    assert 'claim_text' in c, "Missing claim_text"
    assert 'claim_type' in c, "Missing claim_type"
    assert isinstance(c['entities_mentioned'], list), "entities_mentioned must be list"
print(f"[PASS] extract_atomic_claims (canonical) → {len(claims)} claims")
for c in claims:
    print(f"       [{c['claim_id']}] ({c['claim_type']}) {c['claim_text'][:85]}...")
print()

# ==== 3. Linguistic decomposition of external AI text ====
external = (
    "Ashwagandha possesses Ushna virya according to Charaka Samhita, Chikitsasthana 1. "
    "Excessive dosage may aggravate acute Pitta disorders and Ama conditions. "
    "It permanently cures all autoimmune diseases within one week without evidence."
)
claims2 = svc.extract_atomic_claims(external)
assert len(claims2) >= 2, f"Expected >=2 claims, got {len(claims2)}"
types_found = {c['claim_type'] for c in claims2}
print(f"[PASS] extract_atomic_claims (external) → {len(claims2)} claims, types={types_found}")
for c in claims2:
    print(f"       [{c['claim_id']}] ({c['claim_type']}) {c['claim_text'][:85]}")
print()

# ==== 4. Entity tagging ====
entities_in_all = [e for c in claims2 for e in c['entities_mentioned']]
assert any("Charaka Samhita" in e for e in entities_in_all), f"Should tag Charaka Samhita, got: {entities_in_all}"
assert any("Ashwagandha" in e for e in entities_in_all), f"Should tag Ashwagandha, got: {entities_in_all}"
print(f"[PASS] Entity tagging → found: {list(set(entities_in_all))}\n")

# ==== 5. Claim type classifier ====
assert svc._classify_claim_type("avoid this in acute Pitta rakta prakopa conditions") == "contraindication"
assert svc._classify_claim_type("Charaka Samhita Sutrasthana verse 27") == "citation"
assert svc._classify_claim_type("daily Abhyanga massage promotes sleep and Nidra") == "lifestyle"
assert svc._classify_claim_type("Tila Taila oil virya rasa dravya botanical") == "botanical"
print("[PASS] _classify_claim_type → 4/4 type classifications correct\n")

# ==== 6. Schema validation ====
schemas = sys.modules["app.models.schemas"]
AtomicClaim = schemas.AtomicClaim
ExtractClaimsRequest = schemas.ExtractClaimsRequest
ExtractClaimsResponse = schemas.ExtractClaimsResponse
AyurParamGenerateRequest = schemas.AyurParamGenerateRequest
AyurParamGenerateResponse = schemas.AyurParamGenerateResponse

ac = AtomicClaim(
    claim_id=1, claim_text="Test claim about Vata",
    claim_type="medical", entities_mentioned=["Vata"], context_snippet="Test"
)
assert ac.claim_id == 1 and ac.claim_type == "medical"
print(f"[PASS] AtomicClaim schema → claim_id={ac.claim_id}, type={ac.claim_type}")

ecr = ExtractClaimsRequest(text="Sesame oil pacifies Vata.", source_ai_name="ChatGPT")
assert ecr.source_ai_name == "ChatGPT"
print(f"[PASS] ExtractClaimsRequest → source_ai_name={ecr.source_ai_name}")

gen_req = AyurParamGenerateRequest(question="Tell me about Ashwagandha", temperature=0.3)
assert gen_req.temperature == 0.3
print(f"[PASS] AyurParamGenerateRequest → temperature={gen_req.temperature}")

gen_resp = AyurParamGenerateResponse(
    question=gen_req.question, answer=ans,
    model_used="AyurParam-Domain-v1", claims_count=len(claims),
    extracted_claims=[AtomicClaim(**c) for c in claims]
)
assert gen_resp.claims_count == len(claims)
print(f"[PASS] AyurParamGenerateResponse → claims_count={gen_resp.claims_count}")

# ==== 7. schema __init__ aliases ====
import app.models.schemas as full_schemas
assert hasattr(full_schemas, 'AtomicClaim'), "AtomicClaim missing from app.models.schemas"
assert hasattr(full_schemas, 'ExtractClaimsRequest'), "ExtractClaimsRequest missing"
assert hasattr(full_schemas, 'AyurParamGenerateRequest'), "AyurParamGenerateRequest missing"
print("[PASS] app.models.schemas exports all AyurParam schemas\n")

print("=" * 60)
print("ALL 7 TEST GROUPS PASSED ✅")
print(f"Provider: {svc.provider} | Model: {svc.model} | Temp: {svc.temperature}")
print(f"Canonical archetypes: {len(CANONICAL_KNOWLEDGE_ARCHETYPES)} topic domains")
print(f"Schemas ready: AtomicClaim, ExtractClaimsRequest/Response, AyurParamGenerateRequest/Response")
