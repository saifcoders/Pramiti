import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  HelpCircle,
  FileQuestion,
  BookOpen,
  Activity,
  Layers,
  Sparkles,
  Info,
  ShieldCheck,
  Bot,
  ChevronDown,
  ChevronUp,
  Quote,
  Star,
  Zap,
} from 'lucide-react';
import ExportButton from './ExportButton';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Colour-coding spec (strict 5-category mapping)
// Emerald   → Supported by source
// Amber     → Partially supported
// Rose      → Contradicted by source
// Slate/Gray → Insufficient evidence + Reference not verified
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const BADGE_CONFIG = {
  'Supported by source': {
    badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200 ring-1 ring-emerald-500/20',
    borderAccent: 'border-l-emerald-600',
    headerBg: 'bg-emerald-50/60',
    dotClass: 'bg-emerald-500',
    countClass: 'bg-emerald-100 text-emerald-800 ring-emerald-300/40',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />,
    summaryIcon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
  },
  'Partially supported': {
    badgeClass: 'bg-amber-50 text-amber-800 border-amber-200 ring-1 ring-amber-500/20',
    borderAccent: 'border-l-amber-500',
    headerBg: 'bg-amber-50/40',
    dotClass: 'bg-amber-500',
    countClass: 'bg-amber-100 text-amber-800 ring-amber-300/40',
    icon: <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />,
    summaryIcon: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
  },
  'Contradicted by source': {
    badgeClass: 'bg-rose-50 text-rose-800 border-rose-200 ring-1 ring-rose-500/20',
    borderAccent: 'border-l-rose-500',
    headerBg: 'bg-rose-50/40',
    dotClass: 'bg-rose-500',
    countClass: 'bg-rose-100 text-rose-800 ring-rose-300/40',
    icon: <AlertOctagon className="w-4 h-4 text-rose-700 shrink-0" />,
    summaryIcon: <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />,
  },
  'Insufficient evidence': {
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-300 ring-1 ring-slate-400/20',
    borderAccent: 'border-l-slate-400',
    headerBg: 'bg-slate-50/60',
    dotClass: 'bg-slate-400',
    countClass: 'bg-slate-100 text-slate-700 ring-slate-300/40',
    icon: <HelpCircle className="w-4 h-4 text-slate-600 shrink-0" />,
    summaryIcon: <HelpCircle className="w-3.5 h-3.5 text-slate-500" />,
  },
  'Reference not verified': {
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-300 ring-1 ring-slate-400/20',
    borderAccent: 'border-l-slate-500',
    headerBg: 'bg-slate-50/60',
    dotClass: 'bg-slate-500',
    countClass: 'bg-slate-200 text-slate-700 ring-slate-300/40',
    icon: <FileQuestion className="w-4 h-4 text-slate-600 shrink-0" />,
    summaryIcon: <FileQuestion className="w-3.5 h-3.5 text-slate-500" />,
  },
};

function getConfig(category) {
  return BADGE_CONFIG[category] ?? BADGE_CONFIG['Reference not verified'];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Relevance score bar (0.0–1.0 from ChromaDB distance)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function RelevanceBar({ score }) {
  if (score == null) return null;
  const pct = Math.round(Math.min(Math.max(score, 0), 1) * 100);
  const barColor =
    pct >= 70
      ? 'bg-emerald-500'
      : pct >= 40
      ? 'bg-amber-500'
      : 'bg-slate-400';

  return (
    <div className="flex items-center gap-2 mt-1">
      <span className="text-[11px] text-slate-500 font-medium shrink-0">
        Relevance
      </span>
      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[11px] font-semibold text-slate-600 shrink-0">
        {pct}%
      </span>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Verdict count summary pills
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function VerdictSummaryPills({ claims }) {
  const counts = {
    'Supported by source': 0,
    'Partially supported': 0,
    'Contradicted by source': 0,
    'Insufficient evidence': 0,
    'Reference not verified': 0,
  };
  claims.forEach((c) => {
    if (counts[c.category] !== undefined) counts[c.category]++;
  });

  const categories = Object.entries(counts).filter(([, v]) => v > 0);
  if (categories.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {categories.map(([cat, count]) => {
        const cfg = getConfig(cat);
        return (
          <span
            key={cat}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ring-1 ${cfg.countClass} border-current/20`}
          >
            {cfg.summaryIcon}
            <span>{count}</span>
            <span className="font-normal">{cat}</span>
          </span>
        );
      })}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Step-by-step pipeline loading indicator
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const PIPELINE_STEPS = [
  { label: 'AyurParam generating answer', icon: Bot },
  { label: 'Decomposing atomic claims', icon: Layers },
  { label: 'Querying ChromaDB classical corpora', icon: BookOpen },
  { label: 'Cross-auditing 5-category evidence', icon: ShieldCheck },
  { label: 'Building executive synthesis', icon: Sparkles },
];

function PipelineLoadingIndicator() {
  const [step] = React.useState(() => {
    // Advance a "simulated step" every render cycle purely for visual flair
    return 0;
  });
  const [activeStep, setActiveStep] = React.useState(0);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((s) => (s < PIPELINE_STEPS.length - 1 ? s + 1 : s));
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 p-8 sm:p-12 shadow-xs">
      {/* Spinner */}
      <div className="flex flex-col items-center mb-8">
        <div className="relative w-16 h-16 mb-4">
          <div className="absolute inset-0 rounded-2xl bg-teal-50 flex items-center justify-center">
            <Sparkles
              className="w-8 h-8 text-teal-700 animate-spin"
              style={{ animationDuration: '2.5s' }}
            />
          </div>
          <div className="absolute inset-0 rounded-2xl ring-2 ring-teal-200 animate-ping opacity-30" />
        </div>
        <h3 className="text-base font-bold text-slate-900">
          AyurEval Verification Pipeline Running
        </h3>
        <p className="text-sm text-slate-500 mt-1 text-center max-w-sm">
          Retrieving classical Samhita shlokas and auditing evidence…
        </p>
      </div>

      {/* Pipeline step list */}
      <ol className="space-y-3 max-w-sm mx-auto">
        {PIPELINE_STEPS.map((s, idx) => {
          const Icon = s.icon;
          const isDone = idx < activeStep;
          const isActive = idx === activeStep;
          return (
            <li
              key={idx}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-500 ${
                isActive
                  ? 'bg-teal-50 border border-teal-200 shadow-sm'
                  : isDone
                  ? 'opacity-50'
                  : 'opacity-30'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                  isActive
                    ? 'bg-teal-700 text-white'
                    : isDone
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <Icon
                    className={`w-4 h-4 ${isActive ? 'animate-pulse' : ''}`}
                  />
                )}
              </div>
              <span
                className={`text-xs font-medium ${
                  isActive
                    ? 'text-teal-900 font-semibold'
                    : isDone
                    ? 'text-slate-500'
                    : 'text-slate-400'
                }`}
              >
                {isActive && (
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce mr-1.5 mb-0.5" />
                )}
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>

      <p className="text-center text-xs text-slate-400 mt-6">
        Backend may take 15–30 s on first request (ChromaDB + embedding initialization).
      </p>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Individual claim card
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function ClaimCard({ claim, index }) {
  const [expanded, setExpanded] = useState(true);
  const cfg = getConfig(claim.category);

  return (
    <div
      className={`bg-white rounded-3xl border border-slate-200/90 border-l-4 ${cfg.borderAccent} shadow-xs overflow-hidden`}
    >
      {/* Card Header — always visible */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className={`w-full text-left p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${cfg.headerBg} border-b border-slate-100 transition-colors hover:brightness-95`}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <span className="px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 text-xs font-mono font-bold">
            CLAIM #{claim.claim_id}
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">Atomic Proposition</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Category badge */}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.badgeClass}`}
          >
            {cfg.icon}
            {claim.category}
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expandable body */}
      {expanded && (
        <div className="p-5 sm:p-6 space-y-5">
          {/* Claim text */}
          <div className="space-y-1">
            <span className="block text-xs font-bold uppercase tracking-wider text-slate-400">
              Claim Text
            </span>
            <p className="text-base font-semibold text-slate-900 leading-snug">
              "{claim.claim_text}"
            </p>
          </div>

          {/* Two-column evidence grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* ── Classical Textual Evidence ── */}
            <div className="bg-amber-50/50 rounded-2xl border border-amber-200/70 p-4 sm:p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-950 border-b border-amber-200/50 pb-2">
                <BookOpen className="w-4 h-4 text-amber-700 shrink-0" />
                Classical Textual Evidence
              </div>

              {/* Citation reference */}
              {claim.classical_reference ? (
                <div>
                  <span className="text-xs font-semibold text-amber-900 block mb-1">
                    Canonical Reference:
                  </span>
                  <span className="inline-block px-2.5 py-1 rounded-lg bg-amber-100/70 text-amber-950 text-xs font-medium border border-amber-200 font-mono">
                    {claim.classical_reference}
                  </span>
                </div>
              ) : (
                <p className="text-xs text-amber-800 italic">
                  No classical Samhita reference available.
                </p>
              )}

              {/* Relevance score */}
              {claim.relevance_score != null && (
                <RelevanceBar score={claim.relevance_score} />
              )}

              {/* Original Sanskrit shloka */}
              {claim.original_passage && (
                <div>
                  <span className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider block mb-1">
                    Original Sanskrit Shloka:
                  </span>
                  <blockquote className="text-sm font-serif italic text-amber-950 bg-white/80 p-3 rounded-xl border border-amber-200/70 leading-loose shadow-2xs">
                    {claim.original_passage}
                  </blockquote>
                </div>
              )}

              {/* Commentary note */}
              {claim.commentary_note && (
                <div className="text-xs text-amber-900/95 leading-relaxed bg-amber-100/40 p-3 rounded-xl border border-amber-200/50">
                  <span className="font-bold text-amber-950">Traditional Commentary: </span>
                  {claim.commentary_note}
                </div>
              )}
            </div>

            {/* ── Modern Scientific Evidence ── */}
            <div className="bg-teal-50/40 rounded-2xl border border-teal-200/70 p-4 sm:p-5 flex flex-col space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-950 border-b border-teal-200/50 pb-2">
                <Activity className="w-4 h-4 text-teal-700 shrink-0" />
                Modern Scientific Evidence
              </div>

              {claim.scientific_evidence ? (
                <div className="space-y-2 flex-1">
                  <span className="text-xs font-semibold text-teal-900 block">
                    Biomedical &amp; Clinical Trial Status:
                  </span>
                  <p className="text-xs text-teal-950 leading-relaxed bg-white/80 p-3.5 rounded-xl border border-teal-200/60 shadow-2xs flex-1">
                    {claim.scientific_evidence}
                  </p>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl bg-white/60 border border-teal-100 text-xs text-teal-800 italic flex-1">
                  No empirical clinical data indexed for this specific claim.
                </div>
              )}

              <div className="text-[11px] text-teal-700/80 pt-2 border-t border-teal-100">
                Source: PubMed / AYUSH Research Portal / Phytomedicine Literature
              </div>
            </div>
          </div>

          {/* Verification reasoning */}
          {claim.reasoning && (
            <div className="bg-slate-50 rounded-2xl border border-slate-200/70 p-4 text-xs text-slate-700 leading-relaxed space-y-1">
              <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-slate-500" />
                Verification Reasoning &amp; Methodology:
              </span>
              <p>{claim.reasoning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Main component
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export default function VerificationReportView({ report, isLoading }) {
  // 1. Loading State — step-by-step pipeline indicator
  if (isLoading) {
    return <PipelineLoadingIndicator />;
  }

  // 2. Empty placeholder
  if (!report) {
    return (
      <div className="bg-white rounded-3xl border border-dashed border-slate-300/80 p-10 sm:p-14 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 mb-4">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">
          Verification Report Workspace
        </h3>
        <p className="text-sm text-slate-500 max-w-lg mx-auto mt-2 leading-relaxed">
          Submit an inquiry in{' '}
          <span className="font-medium text-slate-700">"Ask a Question"</span> or
          paste an AI-generated answer in{' '}
          <span className="font-medium text-slate-700">"Verify Existing Answer"</span>{' '}
          above to view the source-grounded audit report.
        </p>

        {/* Feature pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto mt-8 text-left">
          {[
            {
              icon: <BookOpen className="w-4 h-4 text-emerald-700" />,
              title: 'Canonical Brihat Trayi',
              desc: 'Direct shloka attribution with Chakrapani, Dalhana, and Arunadatta bhashyas.',
            },
            {
              icon: <Activity className="w-4 h-4 text-teal-700" />,
              title: 'Empirical Concordance',
              desc: 'PubMed, AYUSH clinical research, and pharmacological correlation checks.',
            },
            {
              icon: <Layers className="w-4 h-4 text-slate-700" />,
              title: 'Claim-Level Rigor',
              desc: 'Flags hallucinations, fabricated citations, and unsupported clinical leaps.',
            },
          ].map((p) => (
            <div
              key={p.title}
              className="p-4 rounded-2xl bg-slate-50 border border-slate-100"
            >
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 mb-1">
                {p.icon}
                {p.title}
              </div>
              <p className="text-xs text-slate-500">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const { query_or_source, generated_answer, claims = [], overall_summary, limitations = [] } =
    report;

  return (
    <div className="space-y-6">
      {/* ═══════════════════════════════════════════════════════
          1. Report Header — query context + verdict summary pills
      ═══════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-7 shadow-xs space-y-5">
        {/* Title row */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-start space-x-3">
            <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-100 text-teal-800 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-teal-700" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                AyurEval Verification Report
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Inquiry Context:{' '}
                <span className="font-semibold text-slate-700">{query_or_source}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              {claims.length} {claims.length === 1 ? 'Claim' : 'Claims'} Evaluated
            </span>
            <ExportButton reportType="verification" report={report} />
          </div>
        </div>

        {/* Verdict count pills */}
        {claims.length > 0 && (
          <div className="space-y-2">
            <span className="block text-xs font-bold uppercase tracking-wider text-slate-500">
              Audit Verdict Summary
            </span>
            <VerdictSummaryPills claims={claims} />
          </div>
        )}

        {/* Generated / submitted answer */}
        {generated_answer && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Bot className="w-4 h-4 text-teal-700" />
                Submitted / Generated Answer
              </span>
              <span className="text-[11px] text-slate-400 font-medium">Text Under Evaluation</span>
            </div>
            <div className="bg-amber-50/50 rounded-2xl border border-amber-200/60 p-4 sm:p-5 relative">
              <p className="text-sm text-slate-800 leading-relaxed font-serif italic pr-4">
                "{generated_answer}"
              </p>
            </div>
          </div>
        )}

        {/* Executive synthesis */}
        <div className="space-y-1.5 pt-1">
          <span className="block text-xs font-bold uppercase tracking-wider text-slate-600">
            Executive Synthesis &amp; Canonical Verdict
          </span>
          <div className="bg-slate-50 rounded-2xl border border-slate-200/70 p-4 sm:p-5 text-sm text-slate-800 leading-relaxed font-medium">
            {overall_summary}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════
          2. Claim-by-claim breakdown (collapsible cards)
      ═══════════════════════════════════════════════════════ */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-teal-700" />
            Claim-Level Evidentiary Breakdown ({claims.length})
          </h4>
          <span className="text-xs text-slate-400">Independent Multi-Source Audit</span>
        </div>

        {claims.length === 0 ? (
          <div className="bg-slate-50 rounded-3xl border border-slate-200 p-8 text-center text-sm text-slate-500">
            No claims were extracted from the submitted text.
          </div>
        ) : (
          claims.map((claim, idx) => (
            <ClaimCard key={claim.claim_id ?? idx} claim={claim} index={idx} />
          ))
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════
          3. System Limitations & Uncertainty Notice
      ═══════════════════════════════════════════════════════ */}
      {limitations.length > 0 && (
        <div className="bg-slate-100/90 rounded-3xl p-6 border border-slate-300/80 text-xs text-slate-700 space-y-3 shadow-2xs">
          <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
            <Info className="w-4 h-4 text-slate-600 shrink-0" />
            <span>System Limitations &amp; Uncertainty Notice</span>
          </div>

          <ul className="list-disc list-inside space-y-1.5 pl-1 text-slate-600 leading-relaxed">
            {limitations.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {item}
              </li>
            ))}
          </ul>

          <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500 leading-normal">
            <strong>Notice:</strong> AyurEval (COGNEXA) is an evidence-auditing research
            framework. It does not provide medical diagnoses or replace personalized clinical
            judgment by registered Ayurvedic physicians (BAMS/MD-Ayurveda).
          </div>
        </div>
      )}
    </div>
  );
}
