import React, { useState } from 'react';
import {
  ShieldCheck,
  BookOpen,
  Sparkles,
  Search,
  Bot,
  Layers,
  Activity,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FileText,
  HelpCircle,
  X,
  RefreshCw,
  Microscope,
  AlertOctagon,
  Scale,
  Pill,
  History,
  ListChecks,
} from 'lucide-react';
import VerificationReportView from './components/VerificationReportView';
import DualAuditReportView from './components/DualAuditReportView';
import SafetyReportView from './components/SafetyReportView';
import BatchReportView from './components/BatchReportView';
import HistoryDrawer from './components/HistoryDrawer';
import ErrorBoundary from './components/ErrorBoundary';
import Toast from './components/Toast';
import {
  askAndVerify,
  verifyExistingAnswer,
  dualAuditText,
  checkAyurvedicSafety,
  batchVerifyClaims,
  getFallbackVerificationReport,
  API_BASE_URL,
} from './services/api';
import {
  getHistory,
  saveReportToHistory,
  deleteHistoryItem,
  clearAllHistory,
} from './utils/historyManager';

/**
 * AyurEval (COGNEXA) Verification Dashboard
 * An academic-grade verification framework that independently audits AI-generated Ayurveda answers
 * against classical Samhitas (Charaka, Sushruta, Ashtanga Hridaya) and modern scientific evidence.
 */
export default function App() {
  // Active Tab state: 'ask', 'verify', 'dual', or 'safety'
  const [activeTab, setActiveTab] = useState('ask');

  // Tab 1 state: Ask a Question
  const [question, setQuestion] = useState(
    'What is the classical rationale and therapeutic efficacy of using sesame oil (Tila Taila) for Abhyanga in Vata disorders?'
  );

  // Tab 2 state: Verify Existing Answer
  const [aiText, setAiText] = useState(
    'Sesame oil (Tila Taila) is regarded in Ayurveda as the premier oil for mitigating Vata dosha. It possesses unctuous, warming, and strengthening properties that penetrate deeply into the dhatus, relieving joint stiffness and nervous tension during daily Abhyanga.'
  );
  const [sourceAiName, setSourceAiName] = useState('ChatGPT-4o');

  // Tab 3 state: Dual Audit
  const [dualText, setDualText] = useState(
    'Ashwagandha (Withania somnifera) reduces cortisol and stress as described in Charaka Samhita\'s Rasayana section. Sesame oil pacifies Vata dosha and is prescribed for daily Abhyanga massage according to classical Ayurvedic texts.'
  );
  const [dualReport, setDualReport] = useState(null);
  const [dualLoading, setDualLoading] = useState(false);
  const [dualError, setDualError] = useState(null);

  // Tab 4 state: Safety & Matra Checker
  const [safetyText, setSafetyText] = useState(
    'Patient is a pregnant female experiencing stress and joint stiffness. She is taking 10 grams of Ashwagandha powder with warm milk, along with Turmeric and Warfarin for inflammation.'
  );
  const [safetyReport, setSafetyReport] = useState(null);
  const [safetyLoading, setSafetyLoading] = useState(false);
  const [safetyError, setSafetyError] = useState(null);

  // Tab 5 state: Batch Claim Audit
  const [batchText, setBatchText] = useState(
    'Ashwagandha improves memory and cognitive function.\nTurmeric reduces joint inflammation via COX-2 inhibition.\nSesame oil is the premier sneha for Vata disorders.\nTriphala promotes gut health and acts as a mild laxative.'
  );
  const [batchReport, setBatchReport] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchError, setBatchError] = useState(null);

  // History & Session Drawer state
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [historyList, setHistoryList] = useState(() => getHistory());

  // Transient Toast Notification state
  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'info') => setToast({ message, type });

  // Shared verification status & report state (tabs 1 & 2)
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Tab 1: Submit question (AyurParam generates -> AyurEval verifies)
  const handleAskSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      showToast('Please enter an Ayurvedic question before generating.', 'warning');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await askAndVerify(question);
      setReport(data);
      const updated = saveReportToHistory('ask', question, data);
      setHistoryList(updated);
      showToast('Verification report generated & archived.', 'success');
    } catch (err) {
      setError(err.message || 'Verification workflow encountered a network error.');
      showToast(err.message || 'Verification workflow encountered a network error.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Tab 2: Verify existing answer (Extract claims -> AyurEval verifies)
  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    if (!aiText.trim()) {
      showToast('Please paste AI-generated text to verify.', 'warning');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await verifyExistingAnswer(aiText, sourceAiName);
      setReport(data);
      const updated = saveReportToHistory('verify', aiText, data);
      setHistoryList(updated);
      showToast('Claims decomposed and verified against Samhitas.', 'success');
    } catch (err) {
      setError(err.message || 'Verification workflow encountered a network error.');
      showToast(err.message || 'Verification workflow encountered a network error.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setReport(null);
    setError(null);
    setDualReport(null);
    setDualError(null);
    setSafetyReport(null);
    setSafetyError(null);
    setBatchReport(null);
    setBatchError(null);
    showToast('Active report workspace cleared.', 'info');
  };

  // Tab 3: Dual Audit (Classical + Biomedical simultaneously)
  const handleDualAuditSubmit = async (e) => {
    e.preventDefault();
    if (!dualText.trim()) {
      showToast('Please enter Ayurvedic claims for dual-evidence audit.', 'warning');
      return;
    }

    setDualLoading(true);
    setDualError(null);
    setDualReport(null);
    try {
      const data = await dualAuditText(dualText, 'DualAuditDashboard', 2);
      setDualReport(data);
      const updated = saveReportToHistory('dual', dualText, data);
      setHistoryList(updated);
      showToast('Dual-evidence cross-audit completed successfully.', 'success');
    } catch (err) {
      setDualError(err.message || 'Dual-evidence audit encountered a network error.');
      showToast(err.message || 'Dual-evidence audit encountered a network error.', 'error');
    } finally {
      setDualLoading(false);
    }
  };

  const handleDualReset = () => {
    setDualReport(null);
    setDualError(null);
    showToast('Dual audit workspace cleared.', 'info');
  };

  // Tab 4: Safety & Matra Check
  const handleSafetySubmit = async (e) => {
    e.preventDefault();
    if (!safetyText.trim()) {
      showToast('Please enter an Ayurvedic prescription or treatment advice.', 'warning');
      return;
    }

    setSafetyLoading(true);
    setSafetyError(null);
    setSafetyReport(null);
    try {
      const data = await checkAyurvedicSafety(safetyText);
      setSafetyReport(data);
      const updated = saveReportToHistory('safety', safetyText, data);
      setHistoryList(updated);
      showToast(
        data.is_safe
          ? 'Safety clearance passed (no critical contraindications).'
          : 'Safety alert: Contraindications or drug interactions flagged.',
        data.is_safe ? 'success' : 'warning'
      );
    } catch (err) {
      setSafetyError(err.message || 'Safety audit encountered a network error.');
      showToast(err.message || 'Safety audit encountered a network error.', 'error');
    } finally {
      setSafetyLoading(false);
    }
  };

  const handleSafetyReset = () => {
    setSafetyReport(null);
    setSafetyError(null);
    showToast('Safety audit workspace cleared.', 'info');
  };

  // Tab 5: Batch Claim Audit
  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    const rawLines = batchText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    if (!rawLines.length) {
      showToast('Please enter at least one claim to run batch audit.', 'warning');
      return;
    }

    if (rawLines.length > 10) {
      showToast('Batch limit is 10 claims. Truncating to first 10 items.', 'info');
    }

    const claims = rawLines.slice(0, 10);

    setBatchLoading(true);
    setBatchError(null);
    setBatchReport(null);
    try {
      const data = await batchVerifyClaims(claims);
      setBatchReport(data);
      const updated = saveReportToHistory('batch', batchText.slice(0, 100), data);
      setHistoryList(updated);
      showToast(`Batch audit complete (${claims.length} claims evaluated).`, 'success');
    } catch (err) {
      setBatchError(err.message || 'Batch audit encountered a network error.');
      showToast(err.message || 'Batch audit encountered a network error.', 'error');
    } finally {
      setBatchLoading(false);
    }
  };

  const handleBatchReset = () => {
    setBatchReport(null);
    setBatchError(null);
    showToast('Batch audit workspace cleared.', 'info');
  };

  // Restore previous session from History Drawer
  const handleSelectSession = (session) => {
    if (!session) return;
    setActiveTab(session.type);

    if (session.type === 'ask') {
      setQuestion(session.queryOrText || '');
      setReport(session.report);
    } else if (session.type === 'verify') {
      setAiText(session.queryOrText || '');
      setReport(session.report);
    } else if (session.type === 'dual') {
      setDualText(session.queryOrText || '');
      setDualReport(session.report);
    } else if (session.type === 'safety') {
      setSafetyText(session.queryOrText || '');
      setSafetyReport(session.report);
    } else if (session.type === 'batch') {
      setBatchText(session.queryOrText || '');
      setBatchReport(session.report);
    }

    setIsHistoryOpen(false);
    showToast(`Restored ${session.badge || 'session'} from archive.`, 'success');
  };

  // Delete individual session from History Drawer
  const handleDeleteSession = (id) => {
    const updated = deleteHistoryItem(id);
    setHistoryList(updated);
    showToast('Session removed from history.', 'info');
  };

  // Clear all saved history
  const handleClearHistory = () => {
    const updated = clearAllHistory();
    setHistoryList(updated);
    showToast('Audit history cleared.', 'info');
  };

  // Allows instant exploration of sample report when testing offline
  const handleLoadDemo = () => {
    setError(null);
    const demoReport = getFallbackVerificationReport(
      activeTab === 'ask' ? question : `Verified from ${sourceAiName || 'External AI'}`,
      activeTab === 'ask'
        ? 'AyurParam Clinical Synthesis: In classical Ayurvedic therapeutics for Vata disorders, sesame oil (Tila Taila) is the primary unctuous agent (sneha dravya). Applied through Abhyanga, it relieves dryness (rukshata), penetrative micro-channel stiffness, and calms aggravated Vata dosha.'
        : aiText
    );
    setReport(demoReport);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-teal-100 selection:text-teal-900">
      {/* ==================================================================== */}
      {/* Academic Top Navigation Bar */}
      {/* ==================================================================== */}
      <header className="bg-white border-b border-slate-200/90 sticky top-0 z-40 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Brand & Tagline */}
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-800 to-emerald-700 flex items-center justify-center text-white shadow-sm ring-1 ring-teal-900/10">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-slate-900">
                  AyurEval
                </span>
                <span className="text-[11px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200/80">
                  COGNEXA
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Don't just generate an answer. Verify its evidence.
              </p>
            </div>
          </div>

          {/* Header Action & Badges */}
          <div className="flex items-center space-x-3">
            {/* Canonical Grounding Badges */}
            <div className="hidden sm:flex items-center space-x-2 text-xs">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 text-slate-700 border border-slate-200 font-medium">
                <BookOpen className="w-3.5 h-3.5 text-amber-600" />
                <span>Charaka</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 text-slate-700 border border-slate-200 font-medium">
                <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                <span>Sushruta</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 text-slate-700 border border-slate-200 font-medium">
                <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
                <span>Ashtanga Hridaya</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 text-slate-700 border border-slate-200 font-medium">
                <Activity className="w-3.5 h-3.5 text-teal-600" />
                <span>PubMed</span>
              </div>
            </div>

            {/* History Drawer Toggle Button */}
            <button
              type="button"
              onClick={() => setIsHistoryOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs shadow-2xs transition-all hover:border-teal-300"
              title="View saved session history"
            >
              <History className="w-3.5 h-3.5 text-teal-700" />
              <span>History</span>
              {historyList.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-teal-100 text-teal-800 font-bold border border-teal-200">
                  {historyList.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ==================================================================== */}
      {/* Main Workspace Container */}
      {/* ==================================================================== */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Academic Context Header Card */}
        <div className="bg-gradient-to-r from-teal-900 via-teal-800 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
          <div className="relative z-10 max-w-3xl space-y-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-700/60 text-teal-100 text-xs font-semibold border border-teal-500/30">
              <ShieldCheck className="w-3.5 h-3.5" />
              Source-Aware Verification Engine
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Academic & Canonical Evidence Verification for Ayurveda
            </h1>
            <p className="text-sm text-teal-100/90 leading-relaxed font-normal pt-1">
              Cross-audit AI-generated Ayurvedic statements against the classical <span className="font-semibold text-white">Brihat Trayi</span> (Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya), authoritative traditional bhashyas, and contemporary peer-reviewed biomedical literature.
            </p>
          </div>
          {/* Subtle decorative background gradient */}
          <div className="absolute right-0 top-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        </div>

        {/* Backend Unreachable / Network Error Alert */}
        {error && (
          <div className="p-5 rounded-3xl bg-rose-50 border border-rose-200/90 text-rose-900 shadow-xs flex flex-col sm:flex-row items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-rose-100 text-rose-700 shrink-0">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-rose-950">
                  Backend Communication Error
                </h4>
                <p className="text-xs text-rose-800 mt-1 leading-relaxed">
                  {error}
                </p>
                <div className="text-[11px] text-rose-700/80 mt-2 font-mono">
                  Target Endpoint: {API_BASE_URL}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
              <button
                type="button"
                onClick={handleLoadDemo}
                className="px-3.5 py-2 rounded-xl bg-rose-200 hover:bg-rose-300 text-rose-900 text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-rose-700" />
                Load Sample Demo Report
              </button>
              <button
                type="button"
                onClick={() => setError(null)}
                className="p-2 rounded-xl text-rose-600 hover:bg-rose-100 transition-colors"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ==================================================================== */}
        {/* Workspace Card with Interactive Tabs */}
        {/* ==================================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
          {/* Tab Selector Header */}
          <div className="flex border-b border-slate-200 bg-slate-50/70 p-1.5 sm:p-2 gap-1.5 sm:gap-2 overflow-x-auto no-scrollbar touch-pan-x">
            {/* Tab 1: Ask a Question */}
            <button
              type="button"
              onClick={() => setActiveTab('ask')}
              className={`flex-1 shrink-0 min-w-[130px] sm:min-w-0 flex items-center justify-center gap-2 py-2.5 sm:py-3 px-3 sm:px-4 rounded-2xl text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'ask'
                  ? 'bg-white text-teal-950 shadow-xs border border-slate-200/80 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <Sparkles
                className={`w-4 h-4 ${
                  activeTab === 'ask' ? 'text-teal-700' : 'text-slate-400'
                }`}
              />
              <span className="hidden md:inline">Tab 1: Ask a Question</span>
              <span className="md:hidden">Ask</span>
            </button>

            {/* Tab 2: Verify Existing Answer */}
            <button
              type="button"
              onClick={() => setActiveTab('verify')}
              className={`flex-1 shrink-0 min-w-[130px] sm:min-w-0 flex items-center justify-center gap-2 py-2.5 sm:py-3 px-3 sm:px-4 rounded-2xl text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'verify'
                  ? 'bg-white text-teal-950 shadow-xs border border-slate-200/80 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <Layers
                className={`w-4 h-4 ${
                  activeTab === 'verify' ? 'text-teal-700' : 'text-slate-400'
                }`}
              />
              <span className="hidden md:inline">Tab 2: Verify Answer</span>
              <span className="md:hidden">Verify</span>
            </button>

            {/* Tab 3: Dual Audit */}
            <button
              type="button"
              onClick={() => setActiveTab('dual')}
              className={`flex-1 shrink-0 min-w-[130px] sm:min-w-0 flex items-center justify-center gap-2 py-2.5 sm:py-3 px-3 sm:px-4 rounded-2xl text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'dual'
                  ? 'bg-white text-teal-950 shadow-xs border border-slate-200/80 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <Microscope
                className={`w-4 h-4 ${
                  activeTab === 'dual' ? 'text-blue-700' : 'text-slate-400'
                }`}
              />
              <span className="hidden md:inline">Tab 3: Dual Audit</span>
              <span className="md:hidden">Dual Audit</span>
            </button>

            {/* Tab 4: Safety & Matra */}
            <button
              type="button"
              onClick={() => setActiveTab('safety')}
              className={`flex-1 shrink-0 min-w-[130px] sm:min-w-0 flex items-center justify-center gap-2 py-2.5 sm:py-3 px-3 sm:px-4 rounded-2xl text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'safety'
                  ? 'bg-white text-rose-950 shadow-xs border border-slate-200/80 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <AlertOctagon
                className={`w-4 h-4 ${
                  activeTab === 'safety' ? 'text-rose-600' : 'text-slate-400'
                }`}
              />
              <span className="hidden md:inline">Tab 4: Safety &amp; Matra</span>
              <span className="md:hidden">Safety</span>
            </button>

            {/* Tab 5: Batch Audit */}
            <button
              type="button"
              onClick={() => setActiveTab('batch')}
              className={`flex-1 shrink-0 min-w-[130px] sm:min-w-0 flex items-center justify-center gap-2 py-2.5 sm:py-3 px-3 sm:px-4 rounded-2xl text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'batch'
                  ? 'bg-white text-purple-950 shadow-xs border border-slate-200/80 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <ListChecks
                className={`w-4 h-4 ${
                  activeTab === 'batch' ? 'text-purple-600' : 'text-slate-400'
                }`}
              />
              <span className="hidden md:inline">Tab 5: Batch Audit</span>
              <span className="md:hidden">Batch</span>
            </button>
          </div>

          {/* Tab Content Area */}
          <div className="p-6 sm:p-8">
            {/* ---------------------------------------------------------------- */}
            {/* Tab 1 Form: Ask a Question */}
            {/* ---------------------------------------------------------------- */}
            {activeTab === 'ask' && (
              <form onSubmit={handleAskSubmit} className="space-y-5">
                {/* Workflow Architecture Explainer */}
                <div className="flex items-center gap-2 text-xs font-medium text-teal-900 bg-teal-50/70 border border-teal-200/70 px-4 py-2.5 rounded-xl">
                  <Bot className="w-4 h-4 text-teal-700 shrink-0" />
                  <span>
                    <strong className="font-semibold">Workflow:</strong> Enter an Ayurveda question &rarr; <span className="font-semibold">AyurParam</span> generates a clinical response &rarr; <span className="font-semibold">AyurEval</span> verifies classical & modern evidence.
                  </span>
                </div>

                {/* Question Input */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Ayurveda Clinical or Lifestyle Question
                    </label>
                    <span className="text-xs text-slate-400">Classical Shloka & Clinical Inquiry</span>
                  </div>
                  <textarea
                    rows={4}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter an Ayurvedic question (e.g., What are the classical indications, contraindications, and dosage of Ashwagandha in Vata-Vyadhi?)..."
                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-700 transition-all text-slate-800 placeholder:text-slate-400 resize-y shadow-2xs"
                    required
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                    <span>Cross-referenced against Brihat Trayi & commentaries</span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    {report && (
                      <button
                        type="button"
                        onClick={handleReset}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !question.trim()}
                      className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-teal-800 hover:bg-teal-900 active:bg-teal-950 text-white font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Generating & Verifying...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-teal-200" />
                          <span>Generate & Verify</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}

            {/* ---------------------------------------------------------------- */}
            {/* Tab 2 Form: Verify Existing Answer */}
            {/* ---------------------------------------------------------------- */}
            {activeTab === 'verify' && (
              <form onSubmit={handleVerifySubmit} className="space-y-5">
                {/* Workflow Architecture Explainer */}
                <div className="flex items-center gap-2 text-xs font-medium text-slate-800 bg-slate-100/80 border border-slate-200 px-4 py-2.5 rounded-xl">
                  <ShieldCheck className="w-4 h-4 text-teal-700 shrink-0" />
                  <span>
                    <strong className="font-semibold">Workflow:</strong> Paste text from an LLM &rarr; <span className="font-semibold">AyurEval</span> extracts claims &rarr; cross-audits Charaka, Sushruta, Ashtanga Hridaya & PubMed.
                  </span>
                </div>

                {/* Optional Model Name Input */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Source AI Model Name <span className="text-slate-400 font-normal lowercase">(optional)</span>
                    </label>
                    <input
                      type="text"
                      value={sourceAiName}
                      onChange={(e) => setSourceAiName(e.target.value)}
                      placeholder="e.g., ChatGPT-4o, Gemini 1.5 Pro, Claude 3.5 Sonnet..."
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-700 transition-all text-slate-800 shadow-2xs"
                    />
                  </div>

                  <div className="space-y-1.5 flex flex-col justify-end">
                    <div className="text-xs text-slate-500 bg-slate-50 border border-slate-100 p-2.5 rounded-xl">
                      AyurEval decomposes the input text into discrete atomic claims and validates each against canonical citations.
                    </div>
                  </div>
                </div>

                {/* Large Textarea for AI-Generated Text */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      AI-Generated Text to Audit
                    </label>
                    <span className="text-xs text-slate-400">Claims Deconstruction & Fact-Audit</span>
                  </div>
                  <textarea
                    rows={6}
                    value={aiText}
                    onChange={(e) => setAiText(e.target.value)}
                    placeholder="Paste the Ayurveda answer generated by ChatGPT, Gemini, or Claude here..."
                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-700 transition-all text-slate-800 placeholder:text-slate-400 resize-y shadow-2xs"
                    required
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Detects hallucinations, misattributions, and contraindications</span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    {report && (
                      <button
                        type="button"
                        onClick={handleReset}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !aiText.trim()}
                      className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-teal-800 hover:bg-teal-900 active:bg-teal-950 text-white font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Extracting & Verifying Claims...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-4 h-4 text-teal-200" />
                          <span>Verify Claims</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}

            {/* ---------------------------------------------------------------- */}
            {/* Tab 3 Form: Dual Audit (Classical + Biomedical simultaneously) */}
            {/* ---------------------------------------------------------------- */}
            {activeTab === 'dual' && (
              <form onSubmit={handleDualAuditSubmit} className="space-y-5">
                {/* Workflow explainer */}
                <div className="flex items-center gap-2 text-xs font-medium text-blue-900 bg-blue-50/80 border border-blue-200/70 px-4 py-2.5 rounded-xl">
                  <Microscope className="w-4 h-4 text-blue-700 shrink-0" />
                  <span>
                    <strong className="font-semibold">Dual Audit Workflow:</strong> Paste any
                    Ayurvedic text &rarr; AyurEval simultaneously queries{' '}
                    <span className="font-semibold">Classical Samhitas</span> (ChromaDB) +{' '}
                    <span className="font-semibold">PubMed Biomedical Evidence</span> &rarr;
                    produces a unified dual-evidence verdict per claim.
                  </span>
                </div>

                {/* Textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Ayurvedic Text or AI-Generated Claims
                    </label>
                    <span className="text-xs text-slate-400">Classical + Biomedical Cross-Audit</span>
                  </div>
                  <textarea
                    rows={5}
                    value={dualText}
                    onChange={(e) => setDualText(e.target.value)}
                    placeholder="Paste Ayurvedic text to simultaneously cross-audit against classical Samhita passages and modern PubMed clinical evidence..."
                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-700 transition-all text-slate-800 placeholder:text-slate-400 resize-y shadow-2xs"
                    required
                  />
                </div>

                {/* Dual error alert */}
                {dualError && (
                  <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                    <div>
                      <strong>Error:</strong> {dualError}
                    </div>
                    <button
                      type="button"
                      onClick={() => setDualError(null)}
                      className="ml-auto shrink-0 text-rose-500 hover:text-rose-700"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-blue-500" />
                    <span>
                      Grades each claim: Dual-supported / Traditional-only / Clinical-backed
                    </span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    {dualReport && (
                      <button
                        type="button"
                        onClick={handleDualReset}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={dualLoading || !dualText.trim()}
                      className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-blue-800 hover:bg-blue-900 active:bg-blue-950 text-white font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {dualLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Running Dual Audit...</span>
                        </>
                      ) : (
                        <>
                          <Microscope className="w-4 h-4 text-blue-200" />
                          <span>Run Dual Audit</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}

            {/* ---------------------------------------------------------------- */}
            {/* Tab 4 Form: Safety, Matra & Contraindications */}
            {/* ---------------------------------------------------------------- */}
            {activeTab === 'safety' && (
              <form onSubmit={handleSafetySubmit} className="space-y-5">
                {/* Workflow explainer */}
                <div className="flex items-center gap-2 text-xs font-medium text-rose-900 bg-rose-50/80 border border-rose-200/70 px-4 py-2.5 rounded-xl">
                  <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>
                    <strong className="font-semibold">Safety & Matra Audit Workflow:</strong> Paste an
                    Ayurvedic prescription, dosage advice, or treatment claim &rarr;{' '}
                    <span className="font-semibold">AyurEval</span> scans for clinical contraindications
                    (pregnancy, gallstones, bleeding), drug interactions (blood thinners, sedatives),
                    maximum dosage limits, and classical <span className="font-semibold">Anupana</span> recommendations.
                  </span>
                </div>

                {/* Textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Ayurvedic Prescription, Dosage Advice, or Clinical Claim
                    </label>
                    <span className="text-xs text-slate-400">Dosage, Anupana & Contraindication Audit</span>
                  </div>
                  <textarea
                    rows={5}
                    value={safetyText}
                    onChange={(e) => setSafetyText(e.target.value)}
                    placeholder="Enter an Ayurvedic formulation, dosage, or patient scenario (e.g., Patient is pregnant and taking 10g of Ashwagandha daily with warm milk)..."
                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-600/20 focus:border-rose-700 transition-all text-slate-800 placeholder:text-slate-400 resize-y shadow-2xs"
                    required
                  />
                </div>

                {/* Safety error alert */}
                {safetyError && (
                  <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                    <div>
                      <strong>Error:</strong> {safetyError}
                    </div>
                    <button
                      type="button"
                      onClick={() => setSafetyError(null)}
                      className="ml-auto shrink-0 text-rose-500 hover:text-rose-700"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5 text-rose-500" />
                    <span>
                      Verifies classical API maximum matra & flags herb-drug interactions
                    </span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    {safetyReport && (
                      <button
                        type="button"
                        onClick={handleSafetyReset}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={safetyLoading || !safetyText.trim()}
                      className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-rose-800 hover:bg-rose-900 active:bg-rose-950 text-white font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {safetyLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Auditing Safety & Matra...</span>
                        </>
                      ) : (
                        <>
                          <AlertOctagon className="w-4 h-4 text-rose-200" />
                          <span>Audit Safety & Matra</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}
            {/* ---------------------------------------------------------------- */}
            {/* Tab 5 Form: Batch Claim Audit */}
            {/* ---------------------------------------------------------------- */}
            {activeTab === 'batch' && (
              <form onSubmit={handleBatchSubmit} className="space-y-5">
                {/* Workflow explainer */}
                <div className="flex items-center gap-2 text-xs font-medium text-purple-900 bg-purple-50/80 border border-purple-200/70 px-4 py-2.5 rounded-xl">
                  <ListChecks className="w-4 h-4 text-purple-600 shrink-0" />
                  <span>
                    <strong className="font-semibold">Batch Audit Workflow:</strong> Paste up to 10
                    newline-separated Ayurvedic claims &rarr;{' '}
                    <span className="font-semibold">AyurEval</span> concurrently verifies classical
                    Brihat Trayi alignment and scans for safety contraindications across all claims &rarr;
                    renders an aggregated analytics dashboard.
                  </span>
                </div>

                {/* Textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Ayurvedic Claims (1 per line, max 10)
                    </label>
                    <span className="text-xs text-slate-400">
                      {batchText.split('\n').filter((s) => s.trim()).length} / 10 Claims
                    </span>
                  </div>
                  <textarea
                    rows={6}
                    value={batchText}
                    onChange={(e) => setBatchText(e.target.value)}
                    placeholder="Enter up to 10 Ayurvedic statements (one per line)...&#10;e.g.&#10;Ashwagandha improves memory and cognitive function.&#10;Turmeric reduces joint inflammation via COX-2 inhibition.&#10;Sesame oil is the premier sneha for Vata disorders."
                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-purple-600/20 focus:border-purple-700 transition-all text-slate-800 placeholder:text-slate-400 resize-y shadow-2xs font-mono"
                    required
                  />
                </div>

                {/* Batch error alert */}
                {batchError && (
                  <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                    <div>
                      <strong>Error:</strong> {batchError}
                    </div>
                    <button
                      type="button"
                      onClick={() => setBatchError(null)}
                      className="ml-auto shrink-0 text-rose-500 hover:text-rose-700"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <ListChecks className="w-3.5 h-3.5 text-purple-500" />
                    <span>Concurrently evaluates classical Samhitas + safety flags</span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    {batchReport && (
                      <button
                        type="button"
                        onClick={handleBatchReset}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={batchLoading || !batchText.trim()}
                      className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-purple-800 hover:bg-purple-900 active:bg-purple-950 text-white font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {batchLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Auditing Batch Claims...</span>
                        </>
                      ) : (
                        <>
                          <ListChecks className="w-4 h-4 text-purple-200" />
                          <span>Run Batch Audit</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* ==================================================================== */}
        {/* Verification Report Container (Tabs 1 & 2) */}
        {/* ==================================================================== */}
        {activeTab !== 'dual' && activeTab !== 'safety' && activeTab !== 'batch' && (
          <section aria-label="Verification Report Section" className="pt-2">
            <ErrorBoundary title="Verification Report Rendering Exception" onReset={handleReset}>
              <VerificationReportView report={report} isLoading={loading} />
            </ErrorBoundary>
          </section>
        )}

        {/* ==================================================================== */}
        {/* Dual Audit Report Container (Tab 3) */}
        {/* ==================================================================== */}
        {activeTab === 'dual' && (
          <section aria-label="Dual Audit Report Section" className="pt-2">
            <ErrorBoundary title="Dual Audit Report Rendering Exception" onReset={handleDualReset}>
              <DualAuditReportView report={dualReport} isLoading={dualLoading} />
            </ErrorBoundary>
          </section>
        )}

        {/* ==================================================================== */}
        {/* Safety & Matra Report Container (Tab 4) */}
        {/* ==================================================================== */}
        {activeTab === 'safety' && (
          <section aria-label="Safety Report Section" className="pt-2">
            <ErrorBoundary title="Safety Report Rendering Exception" onReset={handleSafetyReset}>
              <SafetyReportView report={safetyReport} isLoading={safetyLoading} />
            </ErrorBoundary>
          </section>
        )}

        {/* ==================================================================== */}
        {/* Batch Audit Report Container (Tab 5) */}
        {/* ==================================================================== */}
        {activeTab === 'batch' && (
          <section aria-label="Batch Audit Report Section" className="pt-2">
            <ErrorBoundary title="Batch Audit Report Rendering Exception" onReset={handleBatchReset}>
              <BatchReportView report={batchReport} isLoading={batchLoading} />
            </ErrorBoundary>
          </section>
        )}
      </main>

      {/* ==================================================================== */}
      {/* Academic Footer */}
      {/* ==================================================================== */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-16 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">AyurEval (COGNEXA)</span>
            <span>&bull;</span>
            <span>Canonical Evidence Verification Architecture</span>
          </div>
          <div className="text-slate-400">
            Charaka Samhita &bull; Sushruta Samhita &bull; Ashtanga Hridaya &bull; PubMed
          </div>
        </div>
      </footer>
      {/* ==================================================================== */}
      {/* History & Session Drawer */}
      {/* ==================================================================== */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={historyList}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onClearHistory={handleClearHistory}
      />

      {/* ==================================================================== */}
      {/* Transient Academic Notification Toast */}
      {/* ==================================================================== */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
