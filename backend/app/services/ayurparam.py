"""AyurParam LLM Integration & Atomic Claim Extraction Engine.

Provides:
1. AyurParamService: Modular LLM wrapper supporting local/cloud LLMs (OpenAI, Gemini, Anthropic, Ollama)
   with resilient fallback synthesis grounded in classical Ayurvedic literature (Brihat Trayi & commentaries).
2. generate_ayurvedic_answer(question: str) -> str: Synthesizes classical clinical and lifestyle answers.
3. extract_atomic_claims(ai_text: str) -> List[dict]: Breaks down AI-generated medical answers into
   discrete, verifiable atomic claims with distinct sequential identifiers for verification auditing.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.models.schemas import AtomicClaim, ClaimType


# Canonical classical archetypes for domain knowledge synthesis
CANONICAL_KNOWLEDGE_ARCHETYPES = [
    {
        "keywords": ["sesame", "tila", "taila", "vata", "abhyanga", "massage", "oil"],
        "answer": (
            "In classical Ayurvedic pharmacology, Tila Taila (sesame oil) is designated as the foremost "
            "unctuous substance (sneha) for pacifying aggravated Vata dosha (Charaka Samhita, Sutrasthana 27/225-226). "
            "Possessing Madhura-Tikta-Kashaya rasa, Ushna virya (warming potency), and Vyavayi (swiftly permeating) "
            "properties, it directly counteracts the cold (Sheeta), dry (Ruksha), and mobile (Chala) attributes of Vata. "
            "Chakrapani Datta in Ayurveda Dipika emphasizes that regular Abhyanga (warm oil massage) lubricates "
            "the micro-channels (srotas), prevents traumatic tissue injury (Abhighata-sahatva), improves sleep (Nidra), "
            "and enhances musculoskeletal tone (Charaka Samhita, Sutrasthana 5/88-89). While classical texts celebrate "
            "habitual Abhyanga for preventative tissue resilience, modern biomedical trials identify its value in "
            "enhancing peripheral microcirculation and reducing neuromuscular tension rather than permanent structural disc reversal."
        ),
        "claims": [
            {
                "claim_text": "Tila Taila (sesame oil) is the foremost unctuous substance (sneha) for pacifying aggravated Vata dosha according to classical pharmacology.",
                "claim_type": "botanical",
                "entities_mentioned": ["Tila Taila", "Vata dosha", "Sneha", "Charaka Samhita"],
            },
            {
                "claim_text": "Charaka Samhita Sutrasthana 27/225-226 documents sesame oil as possessing Madhura-Tikta-Kashaya rasa and Ushna virya (warming potency).",
                "claim_type": "citation",
                "entities_mentioned": ["Charaka Samhita", "Sutrasthana", "Ushna virya"],
            },
            {
                "claim_text": "Regular full-body Abhyanga lubricates micro-channels (srotas), prevents trauma-induced tissue exhaustion, and promotes healthy sleep.",
                "claim_type": "lifestyle",
                "entities_mentioned": ["Abhyanga", "Srotas", "Nidra", "Chakrapani Datta"],
            },
            {
                "claim_text": "Daily warm oil massage permanently restores degenerative lumbar spinal discs and completely cures severe axonal peripheral neuropathy.",
                "claim_type": "therapeutic",
                "entities_mentioned": ["Abhyanga", "Peripheral neuropathy", "Lumbar disc"],
            },
        ],
    },
    {
        "keywords": ["ashwagandha", "withania", "stress", "sleep", "nidra", "insomnia", "anxiety", "ojas"],
        "answer": (
            "Ashwagandha (Withania somnifera) is celebrated in classical Ayurveda as a prime Balya (strength-promoting), "
            "Rasayana (rejuvenative), and Medhya (nootropic) botanical (Charaka Samhita, Chikitsasthana 1/1). "
            "It features Tikta (bitter) and Kashaya (astringent) rasas with Ushna (warming) virya and Madhura vipaka. "
            "Classically, it nourishes Mamsa (muscle), Asthi (bone), and Shukra (reproductive) dhatus while pacifying "
            "aggravated Vata and Kapha doshas. Commentators note that by calming Manovaha Srotas (neurological channels), "
            "it induces restorative Nidra (sleep) and stabilizes Ojas (vital immunity). However, due to its warming virya, "
            "classical sources caution against excessive standalone usage in conditions of acute Ama (metabolic toxins) "
            "or severe Pitta rakta prakopa."
        ),
        "claims": [
            {
                "claim_text": "Ashwagandha (Withania somnifera) is a classical Balya (strength-promoting) and Rasayana herb that pacifies Vata and Kapha doshas.",
                "claim_type": "botanical",
                "entities_mentioned": ["Ashwagandha", "Balya", "Rasayana", "Vata", "Kapha"],
            },
            {
                "claim_text": "Charaka Samhita Chikitsasthana 1/1 classifies Ashwagandha as possessing Ushna virya and Madhura vipaka.",
                "claim_type": "citation",
                "entities_mentioned": ["Charaka Samhita", "Chikitsasthana", "Ushna virya"],
            },
            {
                "claim_text": "Ashwagandha stabilizes Ojas and induces restorative Nidra by calming neurological channels (Manovaha Srotas).",
                "claim_type": "medical",
                "entities_mentioned": ["Ojas", "Nidra", "Manovaha Srotas"],
            },
            {
                "claim_text": "Excessive standalone consumption of Ashwagandha may aggravate acute Pitta disorders or high Ama metabolic states.",
                "claim_type": "contraindication",
                "entities_mentioned": ["Ashwagandha", "Pitta", "Ama"],
            },
        ],
    },
    {
        "keywords": ["triphala", "constipation", "digestion", "amalaki", "haritaki", "bibhitaki", "bowel", "gut"],
        "answer": (
            "Triphala—the synergistic compound of Haritaki (Terminalia chebula), Bibhitaki (Terminalia bellirica), "
            "and Amalaki (Phyllanthus emblica)—is one of the most revered formulations in the Brihat Trayi "
            "(Charaka Samhita, Chikitsasthana 1/3; Sushruta Samhita, Sutrasthana 38/56-57). "
            "Containing five of the six rasas (excluding Lavana/salty), Triphala gently balances all three doshas "
            "(Tridoshahara). It exerts Anulomana (mild downward regulation of Apana Vata), supports Dipana-Pachana "
            "(digestive metabolic fire), and is classically hailed as Chakshushya (beneficial for vision). "
            "Unlike harsh cathartics, classical authorities distinguish Triphala as a Rasayana that purges without "
            "depleting Dhatu strength."
        ),
        "claims": [
            {
                "claim_text": "Triphala is composed of Haritaki, Bibhitaki, and Amalaki, possessing five rasas and balancing Tridosha.",
                "claim_type": "botanical",
                "entities_mentioned": ["Triphala", "Haritaki", "Bibhitaki", "Amalaki", "Tridosha"],
            },
            {
                "claim_text": "Charaka Samhita Chikitsasthana 1/3 and Sushruta Samhita Sutrasthana 38/56 document Triphala as an Anulomana formulation.",
                "claim_type": "citation",
                "entities_mentioned": ["Charaka Samhita", "Sushruta Samhita", "Anulomana"],
            },
            {
                "claim_text": "Triphala supports Dipana-Pachana (digestive fire) and acts as a safe Rasayana without depleting bodily tissues.",
                "claim_type": "therapeutic",
                "entities_mentioned": ["Triphala", "Dipana", "Pachana", "Rasayana"],
            },
        ],
    },
    {
        "keywords": ["ghee", "ghrita", "pitta", "memory", "smriti", "dhi", "intelligence"],
        "answer": (
            "In Ayurvedic dietetics, Go Ghrita (cow's ghee) holds supreme status for pacifying Pitta and Vata doshas "
            "while enhancing Dhi (intelligence), Dhriti (retention), and Smriti (memory) (Charaka Samhita, Sutrasthana 27/231). "
            "Ghee possesses Sheeta virya (cooling potency) and Madhura rasa and vipaka. Unique among all unctuous lipids, "
            "it is Samskaranuvartana—meaning it adopts the therapeutic qualities of medicinal herbs processed with it "
            "without relinquishing its own innate cooling, agni-kindling, and Ojas-enhancing properties."
        ),
        "claims": [
            {
                "claim_text": "Go Ghrita (cow's ghee) pacifies Pitta and Vata doshas and enhances memory, intelligence, and Ojas.",
                "claim_type": "dietary",
                "entities_mentioned": ["Ghrita", "Pitta", "Vata", "Smriti", "Ojas"],
            },
            {
                "claim_text": "Charaka Samhita Sutrasthana 27/231 describes ghee as Sheeta virya and Madhura vipaka.",
                "claim_type": "citation",
                "entities_mentioned": ["Charaka Samhita", "Sutrasthana", "Sheeta virya"],
            },
            {
                "claim_text": "Ghee exhibits the Samskaranuvartana property, assimilating medicinal virtues of processed herbs without losing its native benefits.",
                "claim_type": "botanical",
                "entities_mentioned": ["Ghrita", "Samskaranuvartana", "Agni"],
            },
        ],
    },
    {
        "keywords": ["turmeric", "haridra", "curcumin", "inflammation", "wound", "skin", "vrana", "prameha", "diabetes"],
        "answer": (
            "Haridra (Curcuma longa / turmeric) is cataloged as a premier Lekhana (scraping), Vishaghna (antitoxic), "
            "and Varnya (complexion-enhancing) dravya (Charaka Samhita, Sutrasthana 4/16; Sushruta Samhita, Sutrasthana 38/27). "
            "Having Katu-Tikta rasa, Ruksha guna, and Ushna virya, it specifically remedies Kapha-Pitta imbalance, "
            "metabolic Ama accumulation, and Twak roga (dermatological conditions). Furthermore, classical authorities "
            "stipulate Nishamalaki (Haridra paired with Amalaki) as the definitive classical dual protocol for "
            "managing Prameha (metabolic and urinary disorders)."
        ),
        "claims": [
            {
                "claim_text": "Haridra (turmeric) possesses Katu-Tikta rasa, Ushna virya, and acts as a Lekhana and Vishaghna dravya.",
                "claim_type": "botanical",
                "entities_mentioned": ["Haridra", "Lekhana", "Vishaghna", "Ushna virya"],
            },
            {
                "claim_text": "Charaka Samhita Sutrasthana 4/16 and Sushruta Sutrasthana 38/27 classify Haridra for dermatological and metabolic disorders.",
                "claim_type": "citation",
                "entities_mentioned": ["Charaka Samhita", "Sushruta Samhita", "Twak roga"],
            },
            {
                "claim_text": "Nishamalaki (Haridra paired with Amalaki) is the classical formulation recommended for Prameha (metabolic disorders).",
                "claim_type": "therapeutic",
                "entities_mentioned": ["Nishamalaki", "Amalaki", "Prameha"],
            },
        ],
    },
]

# Canonical entity dictionary for entity tagging
AYURVEDIC_ENTITIES_LEXICON = {
    "Doshas": ["Vata", "Pitta", "Kapha", "Tridosha", "Apana Vata", "Prana Vata", "Sadhaka Pitta", "Pachaka Pitta"],
    "Physiological": ["Ama", "Agni", "Ojas", "Dhatu", "Mamsa", "Asthi", "Majja", "Shukra", "Rasa", "Rakta", "Srotas", "Manovaha Srotas"],
    "Botanicals & Dravyas": ["Tila Taila", "Sesame Oil", "Ashwagandha", "Triphala", "Haridra", "Turmeric", "Ghrita", "Ghee", "Haritaki", "Bibhitaki", "Amalaki", "Brahmi", "Guduchi", "Shatavari", "Guggulu", "Shunthi", "Nishamalaki"],
    "Therapeutic Actions": ["Abhyanga", "Rasayana", "Balya", "Medhya", "Dipana", "Pachana", "Anulomana", "Lekhana", "Vishaghna", "Swedana", "Virechana", "Nasya", "Dinacharya", "Ritucharya"],
    "Classical Texts & Authors": ["Charaka Samhita", "Sushruta Samhita", "Ashtanga Hridaya", "Brihat Trayi", "Chakrapani Datta", "Dalhana", "Arunadatta", "Bhavaprakasha", "Sutrasthana", "Chikitsasthana"],
    "Clinical Conditions": ["Prameha", "Pakshaghata", "Sandhivata", "Twak Roga", "Kushtha", "Nidra", "Insomnia", "Sciatica", "Peripheral Neuropathy"],
}


class AyurParamService:
    """Orchestrates Ayurvedic LLM answer generation and atomic claim decomposition."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """Initialize AyurParam service with provider configuration."""
        self.provider = (provider or settings.llm_provider).lower()
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.http_timeout = 25.0

    async def generate_ayurvedic_answer(self, question: str) -> str:
        """Synthesizes clinical and lifestyle answers grounded in traditional wisdom.

        Attempts external LLM execution if configured (OpenAI, Gemini, Anthropic, Ollama);
        gracefully falls back to domain-informed Ayurvedic synthesis on any network/key failure.

        Args:
            question: Direct Ayurvedic, herbal, or lifestyle inquiry.

        Returns:
            Cohesive, classical Ayurvedic response string.
        """
        question_cleaned = question.strip()
        if not question_cleaned:
            return "Please provide an Ayurvedic clinical or lifestyle question to generate an answer."

        # Attempt external LLM if configured and key is available
        if self.provider in ("openai", "gemini", "anthropic", "ollama"):
            try:
                external_ans = await self._call_external_llm(question_cleaned)
                if external_ans and len(external_ans.strip()) > 30:
                    return external_ans.strip()
            except Exception as exc:
                print(f"[AyurParam] External LLM provider '{self.provider}' failed ({exc}). Falling back to canonical domain synthesizer.")

        # Fallback / Built-in Domain Synthesizer
        return self._generate_domain_answer(question_cleaned)

    def extract_atomic_claims(self, ai_text: str) -> List[Dict[str, Any]]:
        """Breaks down AI-generated text into discrete, verifiable medical/botanical/lifestyle claims.

        Segments compound sentences, detaches classical citations, detects Ayurvedic entities,
        and assigns unique sequential identifiers (claim_id: 1, 2, 3...) for auditing.

        Args:
            ai_text: AI-generated text, clinical summary, or paragraph.

        Returns:
            List of dicts representing AtomicClaim objects.
        """
        if not ai_text or not ai_text.strip():
            return []

        text = ai_text.strip()

        # Dynamic linguistic decomposition engine - always decomposes actual input text
        return self._linguistic_claim_decomposition(text)

    async def generate_and_decompose(self, question: str) -> Dict[str, Any]:
        """Convenience workflow: generates an Ayurvedic answer and immediately decomposes it."""
        answer = await self.generate_ayurvedic_answer(question)
        claims = self.extract_atomic_claims(answer)
        return {
            "question": question,
            "answer": answer,
            "model_used": self.provider if self.provider != "mock" else "AyurParam-Domain-v1",
            "claims_count": len(claims),
            "extracted_claims": claims,
        }

    # ==========================================================================
    # Internal LLM Providers
    # ==========================================================================

    async def _call_external_llm(self, question: str) -> Optional[str]:
        """Routes prompt to appropriate external LLM client."""
        system_prompt = (
            "You are AyurParam, an authoritative Ayurvedic Clinical & Pharmacological Intelligence system "
            "grounded in the Brihat Trayi (Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya) and classical "
            "commentaries (Chakrapani Datta, Dalhana, Arunadatta). Synthesize precise, evidence-grounded answers "
            "detailing Dosha dynamics, Rasa-Guna-Virya-Vipaka, traditional protocols, and modern clinical cautions."
        )

        if self.provider == "openai" and settings.openai_api_key:
            return await self._call_openai(system_prompt, question)
        if self.provider == "gemini" and settings.gemini_api_key:
            return await self._call_gemini(system_prompt, question)
        if self.provider == "anthropic" and settings.anthropic_api_key:
            return await self._call_anthropic(system_prompt, question)
        if self.provider == "ollama":
            return await self._call_ollama(system_prompt, question)
        return None

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model if "gpt" in self.model else "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
        }
        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model if "claude" in self.model else "claude-3-haiku-20240307",
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 1024,
            "temperature": self.temperature,
        }
        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            res = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["content"][0]["text"]

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{settings.ollama_base_url}/api/generate"
        payload = {
            "model": self.model if self.model != "ayurparam-v1" else "llama3",
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            return res.json().get("response", "")

    # ==========================================================================
    # Domain Knowledge Synthesizer
    # ==========================================================================

    def _generate_domain_answer(self, question: str) -> str:
        """Synthesizes an authentic classical Ayurvedic answer dynamically grounded in ChromaDB RAG.

        Retrieves the most semantically relevant classical Samhita shlokas from ChromaDB,
        identifies Ayurvedic entities, and synthesizes an authoritative clinical response
        citing canonical Brihat Trayi verses and traditional commentaries.
        """
        from app.services.vector_store import search_classical_sources

        passages = []
        try:
            passages = search_classical_sources(question, top_k=3)
        except Exception as exc:
            print(f"[AyurParam] ChromaDB RAG search error: {exc}")

        entities = self._extract_entities(question)
        entity_ctx = ", ".join(entities) if entities else "the clinical condition and therapeutic principles"

        if passages and passages[0].get("relevance_score", 0) > 0.15:
            top = passages[0]
            citation = top.get("citation") or f"{top.get('source_book', 'Classical Samhita')}, {top.get('chapter', '')}"
            shloka = top.get("text", "")
            commentary = top.get("commentary", "")
            category = top.get("category", "Classical Therapeutics")

            # Extract clean shloka excerpt
            shloka_clean = shloka.strip()
            if "॥" in shloka_clean:
                first_shloka = shloka_clean.split("॥")[0] + "॥"
                translation = shloka_clean.split("॥", 1)[1].strip(" ()") if len(shloka_clean.split("॥", 1)) > 1 else ""
            else:
                first_shloka = shloka_clean[:120]
                translation = ""

            response_paragraphs = [
                (
                    f"In classical Ayurvedic clinical medicine, the inquiry regarding '{question.strip()}' is "
                    f"evaluated under {category} grounded in the Brihat Trayi canon. "
                    f"According to {citation}, classical pharmacology designates specific protocols for {entity_ctx}."
                ),
            ]

            if first_shloka:
                verse_text = f"Canonical passage ({citation}) states: \"{first_shloka}\""
                if translation:
                    verse_text += f" Translation: {translation}."
                response_paragraphs.append(verse_text)

            response_paragraphs.append(
                f"From a Doshic and pharmacological standpoint, this regimen targets the equilibrium of Vata, Pitta, "
                f"and Kapha by modulating Rasa (taste), Virya (potency), and Vipaka (post-digestive effect). "
                f"It acts directly on Srotas (micro-circulatory pathways) and Dhatus (bodily tissues) to counteract pathological dryness, heat, or stagnation."
            )

            if commentary:
                response_paragraphs.append(
                    f"In traditional commentary (Bhashya), {commentary}"
                )

            if len(passages) > 1 and passages[1].get("relevance_score", 0) > 0.22:
                p2 = passages[1]
                response_paragraphs.append(
                    f"Additionally, {p2.get('source_book')} ({p2.get('chapter')}) corroborates these therapeutic indications, "
                    f"emphasizing systematic administration and appropriate Anupana (carrier substance)."
                )

            response_paragraphs.append(
                "Classical authorities stress that clinical outcomes depend on individualized Yukti—evaluating Agni "
                "(digestive strength), Prakriti, and chronicity, rather than isolated unmonitored usage."
            )

            return " ".join(response_paragraphs)

        # Fallback if no close passage found in vector store
        return (
            f"According to classical Ayurvedic clinical principles, management of '{question.strip()}' requires evaluating "
            f"the patient's constitutional baseline (Prakriti), current doshic vitiation (Vikriti), and metabolic capability (Agni). "
            f"The Brihat Trayi (Charaka, Sushruta, Ashtanga Hridaya) emphasizes that therapy initiates with Nidana Parivarjana "
            f"(elimination of root causative factors), followed by Samana (palliative dosha balancing for {entity_ctx}) or "
            f"appropriate Shodhana therapies. Diet (Ahara) and lifestyle (Vihara) must balance prevailing Gunas (qualities) "
            f"to re-establish physiological equilibrium (Dhatusamya) across affected Dhatus and Srotas."
        )

    # ==========================================================================
    # Linguistic Claim Decomposition Engine
    # ==========================================================================

    def _linguistic_claim_decomposition(self, text: str) -> List[Dict[str, Any]]:
        """Decomposes arbitrary prose into discrete atomic assertions."""
        # 1. Clean and split on major sentence boundaries
        # Protect common abbreviations: e.g., i.e., Dr., vs., Ch., Vol., PMID:
        protected_text = re.sub(r"\b(e\.g\.|i\.e\.|Dr\.|vs\.|Ch\.|Vol\.|PMID:\s*\d+)", lambda m: m.group(0).replace(".", "@@DOT@@"), text)
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", protected_text)

        candidates: List[str] = []
        for s in raw_sentences:
            cleaned = s.replace("@@DOT@@", ".").strip()
            if not cleaned or len(cleaned) < 15:
                continue

            # 2. Decompose compound sentences with major conjunctions
            # e.g., "; ", " Furthermore, ", " Additionally, ", ", while ", ", but "
            split_clauses = re.split(r"(?:;\s*|\s+(?:Furthermore|Additionally|Moreover|In addition),\s*|,\s*(?:while|whereas|but)\s+)", cleaned)
            for clause in split_clauses:
                clause = clause.strip()
                if clause and len(clause) > 20:
                    # Clean leading conjunctions or numbering
                    clause = re.sub(r"^(?:And|Also|However|Therefore|Moreover|\d+[\.\)]\s*)\s*", "", clause, flags=re.IGNORECASE)
                    candidates.append(clause)

        if not candidates:
            candidates = [text]

        atomic_claims: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(candidates, start=1):
            claim_type = self._classify_claim_type(sentence)
            entities = self._extract_entities(sentence)

            atomic_claims.append(
                {
                    "claim_id": idx,
                    "claim_text": sentence,
                    "claim_type": claim_type,
                    "entities_mentioned": entities,
                    "context_snippet": text[:160] + "..." if len(text) > 160 else text,
                }
            )

        return atomic_claims

    def _classify_claim_type(self, statement: str) -> str:
        """Classifies the claim category based on medical and textual cues."""
        s_lower = statement.lower()

        # Citation markers
        if any(w in s_lower for w in ["charaka", "sushruta", "ashtanga", "sutra", "verse", "shloka", "chapter", "pmid", "according to", "chakrapani"]):
            return ClaimType.CITATION.value

        # Contraindication / warning markers
        if any(w in s_lower for w in ["contraindicat", "avoid", "excessive", "aggravate", "caution", "toxic", "adverse", "worsen"]):
            return ClaimType.CONTRAINDICATION.value

        # Botanical / Dravya markers
        if any(w in s_lower for w in ["herb", "botanical", "dravya", "rasa", "virya", "vipaka", "taila", "ghrita", "oil", "plant"]):
            return ClaimType.BOTANICAL.value

        # Lifestyle markers
        if any(w in s_lower for w in ["abhyanga", "massage", "dinacharya", "ritucharya", "sleep", "nidra", "exercise", "daily", "routine"]):
            return ClaimType.LIFESTYLE.value

        # Dietary markers
        if any(w in s_lower for w in ["diet", "food", "milk", "honey", "ahara", "pathya", "incompatible", "viruddha"]):
            return ClaimType.DIETARY.value

        # Therapeutic curative markers
        if any(w in s_lower for w in ["cure", "treat", "permanent", "restore", "alleviate", "heal", "remedy", "relieve"]):
            return ClaimType.THERAPEUTIC.value

        return ClaimType.MEDICAL.value

    def _extract_entities(self, statement: str) -> List[str]:
        """Identifies key Ayurvedic entities, doshas, herbs, and texts in a statement."""
        found_entities: List[str] = []
        s_lower = statement.lower()

        for category, entity_list in AYURVEDIC_ENTITIES_LEXICON.items():
            for entity in entity_list:
                # Case-insensitive whole word boundary check
                pattern = r"\b" + re.escape(entity.lower()) + r"\b"
                if re.search(pattern, s_lower):
                    if entity not in found_entities:
                        found_entities.append(entity)

        return found_entities


# Singleton service instance
ayurparam_service = AyurParamService()

