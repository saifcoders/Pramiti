import axios from 'axios';

/**
 * AyurEval Axios HTTP Client Configuration.
 * Communicates with the FastAPI verification backend at VITE_API_BASE_URL.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s — allows ChromaDB + ONNX embedding init on first request
});

/**
 * Fallback realistic Ayurvedic mock report used for offline previews or demo testing.
 */
export const getFallbackVerificationReport = (sourceLabel, answerText) => ({
  query_or_source: sourceLabel || 'AyurParam Clinical Inquiry',
  generated_answer:
    answerText ||
    'In classical Ayurvedic pharmacology, Tila Taila (sesame oil) is the foremost sneha dravya for pacifying Vata dosha. Applied via daily Abhyanga, it penetrates micro-channels, relieves musculoskeletal tension, and imparts bodily firmness. While traditional sources indicate long-term preventative resilience, modern clinical trials emphasize symptomatic relief.',
  claims: [
    {
      claim_id: 1,
      claim_text:
        'Tila Taila (sesame oil) is the foremost unctuous substance (sneha) for pacifying aggravated Vata dosha and promoting bodily strength.',
      category: 'Supported by source',
      classical_reference: 'Charaka Samhita, Sutrasthana, 27/225-226',
      original_passage:
        'तैलं वातहरं त्वच्यं बल्यं स्निग्धं च पित्तकृत्। कषायं मधुरं तिक्तं सूक्ष्मोष्णं च विपाकतः॥',
      commentary_note:
        'Chakrapani Datta in Ayurveda Dipika emphasizes that while Ghrita (ghee) excels in pacifying Pitta, Tila Taila is categorically supreme for Vata shamana due to its vyavayi (permeating) and ushna (warming) virya, distinguishing its lipid dynamics from animal fats.',
      scientific_evidence:
        'Peer-reviewed pharmacological trials corroborate that sesamin and sesamolin lignans possess significant anti-inflammatory, antioxidant, and chondroprotective properties that attenuate oxidative stress in chronic musculoskeletal degeneration (PMID: 31201844, Journal of Ethnopharmacology).',
      reasoning:
        'The claim precisely matches canonical doctrine in Charaka Samhita Sutrasthana 27/225, corroborated by Sushruta Samhita (Sutra 45/112) and Ashtanga Hridaya (Sutra 5/55). The classical distinction made by Chakrapani Datta regarding sneha hierarchy is preserved.',
    },
    {
      claim_id: 2,
      claim_text:
        'Daily full-body Abhyanga (warm oil massage) permanently cures severe peripheral neuropathy and completely restores degenerate lumbar intervertebral discs.',
      category: 'Partially supported',
      classical_reference: 'Charaka Samhita, Sutrasthana, 5/88-89',
      original_passage:
        'न चाभिघाताभिहतं गात्रमभ्यङ्गसेविनः। विकारं भजतेऽत्यर्थं कायायसकरं च यत्॥',
      commentary_note:
        'Chakrapani Datta clarifies that habitual Abhyanga imparts resistance against trauma (Abhighata-sahatva) and mitigates muscular exhaustion. However, classical commentators frame this as swasthavritta (preventative maintenance) and functional palliative care rather than an absolute anatomical cure for structural disc herniation.',
      scientific_evidence:
        'Insufficient modern clinical evidence. While topical warm-oil oleation enhances cutaneous microcirculation, reduces peripheral cortisol levels, and relieves subjective muscle stiffness, high-quality double-blind RCTs demonstrating structural anatomical regeneration of extruded lumbar discs or reversal of chronic axonal neuropathy are lacking.',
      reasoning:
        'Classical passages support the neuro-protective, vata-palliating qualities of regular Abhyanga (supported classically), but the claim of permanent anatomical cure for structural spinal displacement is medically exaggerated and unproven in clinical trials.',
    },
    {
      claim_id: 3,
      claim_text:
        'According to Charaka Samhita, Sutrasthana 12/99, consuming raw sesame seeds directly cures acute hemiplegia (Pakshaghata) within three days without supplementary therapy.',
      category: 'Reference not verified',
      classical_reference: 'Fabricated Citation: "Charaka Samhita, Sutrasthana 12/99"',
      original_passage: null,
      commentary_note:
        'Fabricated reference. Charaka Samhita Sutrasthana Chapter 12 (Vatakalakaliya Adhyaya) contains only 28 verses in total. No verse 99 exists in this chapter. Furthermore, classical management of Pakshaghata is detailed in Chikitsa Sthana Chapter 28 using Virechana, Snehana, and Svedana, never through isolated raw sesame ingestion.',
      scientific_evidence:
        'No modern pharmacological or clinical literature supports the resolution of acute stroke-induced hemiplegia via solitary raw sesame seed administration.',
      reasoning:
        'Hallucinated citation detected. The referenced chapter terminates at verse 28. The AI generated a non-existent verse number and combined generic Vata dietary knowledge with an impossible therapeutic timeline.',
    },
  ],
  overall_summary:
    'AyurEval audit complete: Found 1 fully verified canonical claim supported by Charaka Samhita with authoritative Chakrapani Datta commentary; 1 partially supported claim lacking sufficient modern clinical trial evidence; and 1 critical hallucination with a fabricated citation ("Sutrasthana 12/99") referencing a non-existent verse.',
  limitations: [
    'Classical textual support in the Brihat Trayi (Charaka, Sushruta, Ashtanga Hridaya) does not equate to modern clinical efficacy or regulatory approval.',
    'Modern biomedical evidence correlates phytochemical analogs and clinical trials where available; empirical gaps remain for multi-herb classical formulations.',
    'Automated shloka verification analyzes digitized Sanskrit corpora; textual validation should complement, not replace, clinical evaluation by a registered Ayurvedic physician.',
  ],
});

/**
 * Helper to build clear, descriptive error messages for API failures.
 */
function handleApiError(error, endpoint) {
  if (error.response?.data?.detail) {
    throw new Error(`API Error (${error.response.status}): ${error.response.data.detail}`);
  }
  if (error.code === 'ECONNABORTED') {
    throw new Error('Connection timed out while waiting for AyurEval backend response.');
  }
  if (!error.response && error.request) {
    throw new Error(
      `Unable to connect to AyurEval backend at ${API_BASE_URL}${endpoint}. Please verify that the FastAPI server is running (e.g. uvicorn app.main:app --port 8000).`
    );
  }
  throw new Error(error.message || 'An unexpected communication error occurred.');
}

/**
 * Submit an Ayurveda clinical/lifestyle question.
 * Workflow: AyurParam generates an answer -> AyurEval verifies it.
 * Hits POST /api/v1/ask
 * @param {string} question
 * @returns {Promise<Object>} VerificationReportResponse
 */
export async function askAndVerify(question) {
  try {
    const response = await apiClient.post('/ask', { question });
    return response.data;
  } catch (error) {
    handleApiError(error, '/ask');
  }
}

/**
 * Audit an AI-generated Ayurveda text from an external LLM.
 * Hits POST /api/v1/verify
 * @param {string} text - AI-generated answer to audit
 * @param {string} [sourceAiName] - Optional source model name
 * @returns {Promise<Object>} VerificationReportResponse
 */
export async function verifyExistingAnswer(text, sourceAiName) {
  try {
    const payload = {
      ai_generated_text: text,
      source_ai_name: sourceAiName || undefined,
    };
    const response = await apiClient.post('/verify', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, '/verify');
  }
}

/**
 * Perform semantic search across indexed Samhita passages.
 * Hits POST /api/v1/rag/search
 * @param {string} query
 * @param {number} [topK=3]
 */
export async function searchRAG(query, topK = 3) {
  try {
    const response = await apiClient.post('/rag/search', {
      query,
      top_k: topK,
    });
    return response.data;
  } catch (error) {
    handleApiError(error, '/rag/search');
  }
}

/**
 * Ingest authentic canonical Samhita sample chunks into ChromaDB.
 * Hits POST /api/v1/rag/ingest-sample
 */
export async function ingestSampleRAG(customChunks = null) {
  try {
    const payload = customChunks ? { custom_chunks: customChunks } : {};
    const response = await apiClient.post('/rag/ingest-sample', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, '/rag/ingest-sample');
  }
}

/**
 * Scrape and ingest an online e-Samhita (NIIMH/CCRAS) chapter URL into ChromaDB.
 * Hits POST /api/v1/rag/ingest-url
 * @param {string} url
 * @param {string} [sourceBook="Charaka Samhita"]
 * @param {string} [chapter="Sutrasthana"]
 */
export async function ingestURL(url, sourceBook = 'Charaka Samhita', chapter = 'Sutrasthana') {
  try {
    const response = await apiClient.post('/rag/ingest-url', {
      url,
      source_book: sourceBook,
      chapter,
    });
    return response.data;
  } catch (error) {
    handleApiError(error, '/rag/ingest-url');
  }
}

/**
 * Ingest a structured local .json or .txt corpus file into ChromaDB.
 * Hits POST /api/v1/rag/ingest-file
 * @param {string} filePath
 */
export async function ingestFile(filePath) {
  try {
    const response = await apiClient.post('/rag/ingest-file', {
      file_path: filePath,
    });
    return response.data;
  } catch (error) {
    handleApiError(error, '/rag/ingest-file');
  }
}

/**
 * Run the Classical vs. Biomedical Dual-Evidence Cross-Audit.
 * Simultaneously queries ChromaDB (classical Samhitas) + PubMed/curated cache.
 * Hits POST /api/v1/biomedical/dual-audit
 * @param {string} text - AI-generated Ayurvedic text to audit
 * @param {string|null} [queryContext] - Optional label (source AI, question, etc.)
 * @param {number} [maxBiomedicalPerClaim=2] - Max PubMed results per claim
 * @returns {Promise<Object>} DualAuditResponse
 */
export async function dualAuditText(text, queryContext = null, maxBiomedicalPerClaim = 2) {
  try {
    const response = await apiClient.post('/biomedical/dual-audit', {
      text,
      query_context: queryContext,
      max_biomedical_per_claim: maxBiomedicalPerClaim,
    });
    return response.data;
  } catch (error) {
    handleApiError(error, '/biomedical/dual-audit');
  }
}

/**
 * Audit Ayurvedic text for safety, dosage (matra), contraindications, and drug interactions.
 * Hits POST /api/v1/safety/check
 * @param {string} text - Ayurvedic recommendation or claim
 * @param {Array<string>|null} [claims=null] - Optional atomic claims list
 * @returns {Promise<Object>} SafetyCheckResponse
 */
export async function checkAyurvedicSafety(text, claims = null) {
  try {
    const payload = { text };
    if (claims && Array.isArray(claims) && claims.length > 0) {
      payload.claims = claims;
    }
    const response = await apiClient.post('/safety/check', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, '/safety/check');
  }
}

/**
 * Run a Batch Claim Verification across up to 10 Ayurvedic claims.
 * Hits POST /api/v1/verification/batch
 * @param {string[]} claims - Array of claim strings (1–10)
 * @param {string|null} [sourceName] - Optional label for the source
 * @returns {Promise<Object>} BatchVerifyResponse
 */
export async function batchVerifyClaims(claims, sourceName = null) {
  try {
    const payload = { claims };
    if (sourceName) payload.source_name = sourceName;
    const response = await apiClient.post('/verification/batch', payload);
    return response.data;
  } catch (error) {
    handleApiError(error, '/verification/batch');
  }
}

/**
 * Export a report (all types including batch) as a Markdown file via backend.
 * Hits POST /api/v1/export/report
 * @param {string} reportType
 * @param {Object} report
 */
export async function exportReportMarkdownApi(reportType, report) {
  try {
    const response = await apiClient.post(
      '/export/report',
      { report_type: reportType, report },
      { responseType: 'blob' }
    );
    return response.data;
  } catch (error) {
    handleApiError(error, '/export/report');
  }
}

/**
 * Convenience service object export for backward-compatibility.
 */
export const verificationApi = {
  askAndVerify,
  verifyExistingAnswer,
  searchRAG,
  ingestSampleRAG,
  ingestURL,
  ingestFile,
  askQuestion: ({ question }) => askAndVerify(question),
  verifyText: ({ ai_generated_text, source_ai_name }) =>
    verifyExistingAnswer(ai_generated_text, source_ai_name),
  verifyAnswer: ({ ai_generated_text, source_ai_name }) =>
    verifyExistingAnswer(ai_generated_text, source_ai_name),
  dualAuditText,
  checkAyurvedicSafety,
  batchVerifyClaims,
  async checkHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;
