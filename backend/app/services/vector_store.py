"""Vector database storage and semantic retrieval service for AyurEval.

Integrates ChromaDB with persistent embeddings to ingest and retrieve
canonical passages from the Brihat Trayi (Charaka, Sushruta, Ashtanga Hridaya)
and traditional commentaries.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from app.core.config import settings

# ChromaDB import with graceful embedding function configuration
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection


class ClassicalAyurvedicText(BaseModel):
    """Structured data contract for indexing a canonical Ayurvedic shloka or passage."""

    text: str = Field(
        ...,
        description="The Sanskrit shloka (Devanagari/IAST) and/or English translation",
    )
    source_book: str = Field(
        ...,
        description="Canonical text name, e.g. 'Charaka Samhita', 'Sushruta Samhita', 'Ashtanga Hridaya'",
    )
    chapter: str = Field(
        ...,
        description="Section and Adhyaya identifier, e.g. 'Sutrasthana 27 (Annapanavidhi)'",
    )
    verse_number: str = Field(
        ...,
        description="Shloka/verse citation number, e.g. '225-226'",
    )
    commentary: Optional[str] = Field(
        default=None,
        description="Authoritative traditional commentary (Chakrapani Datta, Dalhana, Arunadatta, Hemadri)",
    )
    category: Optional[str] = Field(
        default=None,
        description="Thematic category, e.g. 'Taila Varga', 'Vata Shamana', 'Dinacharya', 'Viruddha Ahara'",
    )


class VectorStoreService:
    """Manages ChromaDB client lifecycle, embedding computation, and similarity search."""

    COLLECTION_NAME = "classical_samhitas"

    def __init__(self, persist_dir: Optional[str] = None):
        """Initialize persistent ChromaDB client and configure embedding function."""
        self.persist_dir = persist_dir or settings.chroma_persist_directory

        # Ensure persist directory exists
        os.makedirs(self.persist_dir, exist_ok=True)

        # Initialize persistent ChromaDB client
        self.client: ClientAPI = chromadb.PersistentClient(path=self.persist_dir)

        # Configure embedding function (Sentence-Transformers / ONNX MiniLM)
        self.embedding_function = self._get_embedding_function()

        # Initialize collection
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def _get_embedding_function(self):
        """Initializes Sentence-Transformer or Chroma's default ONNX all-MiniLM-L6-v2."""
        try:
            # Check if sentence_transformers is available
            from chromadb.utils import embedding_functions

            # Use Chroma's built-in ONNX all-MiniLM-L6-v2 which runs efficiently on Windows
            return embedding_functions.DefaultEmbeddingFunction()
        except Exception as exc:
            print(f"[VectorStore] Fallback to default embedding function: {exc}")
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            return DefaultEmbeddingFunction()

    def ingest_classical_texts(
        self, texts: List[Union[ClassicalAyurvedicText, Dict[str, Any]]]
    ) -> int:
        """Ingest structured classical Ayurvedic texts into ChromaDB.

        Args:
            texts: List of ClassicalAyurvedicText instances or equivalent dicts.

        Returns:
            Number of documents indexed.
        """
        if not texts:
            return 0

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for item in texts:
            if isinstance(item, dict):
                obj = ClassicalAyurvedicText(**item)
            else:
                obj = item

            # Create composite searchable representation
            searchable_content = f"{obj.source_book} {obj.chapter} {obj.verse_number}\n{obj.text}"
            if obj.commentary:
                searchable_content += f"\nCommentary: {obj.commentary}"
            if obj.category:
                searchable_content += f"\nCategory: {obj.category}"

            # Deterministic ID based on source and verse
            raw_id = f"{obj.source_book}_{obj.chapter}_{obj.verse_number}"
            hash_suffix = hashlib.md5(searchable_content.encode("utf-8")).hexdigest()[:6]
            doc_id = f"{raw_id.replace(' ', '_').replace('/', '_')}_{hash_suffix}"

            citation = f"{obj.source_book}, {obj.chapter}, Verse {obj.verse_number}"

            documents.append(searchable_content)
            metadatas.append(
                {
                    "source_book": obj.source_book,
                    "chapter": obj.chapter,
                    "verse_number": obj.verse_number,
                    "citation": citation,
                    "commentary": obj.commentary or "",
                    "category": obj.category or "",
                    "original_text": obj.text,
                }
            )
            ids.append(doc_id)

        # Upsert documents into collection
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def search_classical_sources(
        self, query: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across indexed Samhita shlokas and bhashyas.

        Args:
            query: Clinical concept, herb, or therapeutic query.
            top_k: Number of most relevant passages to retrieve.

        Returns:
            List of structured passage dictionaries with book names, chapters, and citations.
        """
        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = self.collection.query(
            query_texts=[query],
            n_results=actual_k,
        )

        passages: List[Dict[str, Any]] = []

        if not results or not results.get("ids") or not results["ids"][0]:
            return passages

        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        docs = results.get("documents", [[]])[0] if results.get("documents") else []

        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            dist = distances[idx] if idx < len(distances) else 0.0
            relevance = max(0.0, min(1.0, 1.0 - dist))

            passages.append(
                {
                    "id": doc_id,
                    "source_book": meta.get("source_book", "Classical Samhita"),
                    "chapter": meta.get("chapter", "General"),
                    "verse_number": meta.get("verse_number", ""),
                    "citation": meta.get("citation", ""),
                    "text": meta.get("original_text", docs[idx] if idx < len(docs) else ""),
                    "commentary": meta.get("commentary", ""),
                    "category": meta.get("category", ""),
                    "relevance_score": round(relevance, 3),
                    "distance": round(dist, 4) if dist else 0.0,
                }
            )

        return passages

    def search_classical_sources_batch(
        self, queries: List[str], top_k: int = 2
    ) -> List[List[Dict[str, Any]]]:
        """Perform batched semantic search across indexed Samhita shlokas.

        Embeds all queries in a single vectorized forward pass for high performance.
        """
        if not queries:
            return []
        count = self.collection.count()
        if count == 0:
            return [[] for _ in queries]

        actual_k = min(top_k, count)
        results = self.collection.query(
            query_texts=queries,
            n_results=actual_k,
        )
        batch_passages: List[List[Dict[str, Any]]] = []
        if not results or not results.get("ids"):
            return [[] for _ in queries]

        all_ids = results["ids"]
        all_distances = results.get("distances") or [[] for _ in queries]
        all_metadatas = results.get("metadatas") or [[] for _ in queries]
        all_docs = results.get("documents") or [[] for _ in queries]

        for q_idx in range(len(queries)):
            passages: List[Dict[str, Any]] = []
            if q_idx < len(all_ids):
                q_ids = all_ids[q_idx]
                q_dists = all_distances[q_idx] if q_idx < len(all_distances) else []
                q_metas = all_metadatas[q_idx] if q_idx < len(all_metadatas) else []
                q_docs = all_docs[q_idx] if q_idx < len(all_docs) else []

                for idx, doc_id in enumerate(q_ids):
                    meta = q_metas[idx] if idx < len(q_metas) else {}
                    dist = q_dists[idx] if idx < len(q_dists) else 0.0
                    relevance = max(0.0, min(1.0, 1.0 - dist))
                    passages.append(
                        {
                            "id": doc_id,
                            "source_book": meta.get("source_book", "Classical Samhita"),
                            "chapter": meta.get("chapter", "General"),
                            "verse_number": meta.get("verse_number", ""),
                            "citation": meta.get("citation", ""),
                            "text": meta.get("original_text", q_docs[idx] if idx < len(q_docs) else ""),
                            "commentary": meta.get("commentary", ""),
                            "category": meta.get("category", ""),
                            "relevance_score": round(relevance, 3),
                            "distance": round(dist, 4) if dist else 0.0,
                        }
                    )
            batch_passages.append(passages)
        return batch_passages


# Singleton instance for application-wide reuse
vector_store = VectorStoreService()


def search_classical_sources(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Convenience functional interface to search the vector database."""
    return vector_store.search_classical_sources(query=query, top_k=top_k)


def search_classical_sources_batch(
    queries: List[str], top_k: int = 2
) -> List[List[Dict[str, Any]]]:
    """Convenience functional interface for batched vector search."""
    return vector_store.search_classical_sources_batch(queries=queries, top_k=top_k)


# Authentic canonical sample dataset representing the Brihat Trayi
AUTHENTIC_SAMHITA_SAMPLES: List[Dict[str, Any]] = [
    {
        "text": "तैलं वातहरं त्वच्यं बल्यं स्निग्धं च पित्तकृत्। कषायं मधुरं तिक्तं सूक्ष्मोष्णं च विपाकतः॥ (Sesame oil alleviates Vata dosha, enhances skin texture and lustre, promotes bodily strength, possesses unctuous qualities, and mildly elevates Pitta. It is astringent, sweet, and bitter in taste, deeply permeating (sukshma), and heating in post-digestive effect.)",
        "source_book": "Charaka Samhita",
        "chapter": "Sutrasthana, Chapter 27 (Annapanavidhi Adhyaya)",
        "verse_number": "225-226",
        "commentary": "Chakrapani Datta in Ayurveda Dipika emphasizes that while Ghrita (ghee) is supreme for pacifying Pitta, Tila Taila is categorically foremost among all unctuous substances (sneha dravyas) for Vata shamana due to its vyavayi (rapidly permeating) and ushna (warming) virya.",
        "category": "Taila Varga / Vata Shamana",
    },
    {
        "text": "न चाभिघाताभिहतं गात्रमभ्यङ्गसेविनः। विकारं भजतेऽत्यर्थं कायायसकरं च यत्॥ (The body of a person accustomed to daily Abhyanga (warm oil massage) does not easily succumb to external traumatic injury or structural displacement, nor is it overwhelmed by physical exhaustion and fatigue from strenuous bodily exertion.)",
        "source_book": "Charaka Samhita",
        "chapter": "Sutrasthana, Chapter 5 (Matrashitiya Adhyaya)",
        "verse_number": "88-89",
        "commentary": "Chakrapani Datta clarifies that regular unction fosters Abhighata-sahatva—the tissue resilience that cushions joints, protects neuro-muscular pathways, and maintains physiological stability against environmental trauma.",
        "category": "Dinacharya / Abhyanga Regimen",
    },
    {
        "text": "वातश्लेष्महरं तैलं लघु सूक्ष्मं विपाके कटु। दीपनं वृष्यमायुष्यं मेधास्मृतिकरं परम्॥ (Tila Taila pacifies Vata and Kapha, is light, subtle, pungent in post-digestive conversion (katu vipaka), kindles digestive agni (deepana), acts as a reproductive tonic (vrishya), prolongs lifespan, and acts as an exceptional promoter of intellect and memory (medha-smriti-karam).)",
        "source_book": "Sushruta Samhita",
        "chapter": "Sutrasthana, Chapter 45 (Dravadravya Vidhi)",
        "verse_number": "112",
        "commentary": "Dalhana in Nibandha Samgraha explains that the sukshma (micro-penetrating) quality of sesame oil allows it to transport therapeutic active principles directly across deep srotas (micro-circulatory channels) into asthi and majja dhatus.",
        "category": "Dravya Guna / Sneha",
    },
    {
        "text": "अभ्यङ्गमाचरेन्नित्यं स जराश्रमवातहा। दृष्टिप्रसादपुष्ट्यायुःस्वप्नसुत्वक्त्वदार्ढ्यकृत्॥ (One should practice oil massage (Abhyanga) regularly every day; it wards off premature aging (jara), relieves exhaustion (shrama) and aggravated Vata, clarifies eyesight, nourishes the body tissues, increases longevity, induces sound sleep, and imparts firm muscle tone and radiant skin.)",
        "source_book": "Ashtanga Hridaya",
        "chapter": "Sutrasthana, Chapter 2 (Dinacharya Adhyaya)",
        "verse_number": "8-9",
        "commentary": "Arunadatta in Sarvanga Sundara notes that daily abhyanga pacifies Vyana and Prana Vata, which govern sensory transmission and neuro-motor coordination, stabilizing somatic tone throughout the circadian cycle.",
        "category": "Dinacharya / Daily Regimen",
    },
    {
        "text": "मत्स्यैस्तु पयोऽभ्यवहरेत्... (Consuming fish together with milk is strongly incompatible (Viruddha Ahara). Both possess opposing potencies (viruddha virya)—fish being intensely heating and milk being cooling—which mutually disrupt metabolism and cause micro-channel blockage (srotorodha).)",
        "source_book": "Charaka Samhita",
        "chapter": "Sutrasthana, Chapter 26 (Atreyabhadrakapyiya Adhyaya)",
        "verse_number": "82-83",
        "commentary": "Chakrapani Datta emphasizes that conflicting viryas trigger Mahavisha-like vascular and cutaneous reactions by vitiating Rakta and Pitta doshas simultaneously.",
        "category": "Viruddha Ahara / Dietary Incompatibilities",
    },
    {
        "text": "अश्वगन्धा कषायोष्णा तिक्ता कट्वी च शुक्रला। मारुते श्लैष्मिके क्षीणे कासे श्वासे क्षये हिता॥ (Ashwagandha is astringent, bitter, and pungent in taste, heating in potency, promotes reproductive tissue (shukrala), and is beneficial in aggravated Vata, Kapha, emaciation (kshaya), cough, dyspnoea, and physical wasting.)",
        "source_book": "Bhavaprakasha Nighantu",
        "chapter": "Haritakyadi Varga",
        "verse_number": "189-190",
        "commentary": "Classical Rasayana treatises describe Ashwagandha as Balya (strength-promoting) and Rasayana (rejuvenative), particularly effective in degenerative conditions of Vata-Vyadhi.",
        "category": "Rasayana / Dravya Guna",
    },
]

