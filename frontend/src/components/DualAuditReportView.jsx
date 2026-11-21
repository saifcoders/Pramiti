/**
 * DualAuditReportView.jsx
 *
 * Renders the Classical vs. Biomedical Dual-Evidence Cross-Audit report
 * returned by POST /api/v1/biomedical/dual-audit.
 *
 * Shows:
 *  - Grade summary pills (Dual-supported, Traditional-only, Clinical-backed, etc.)
 *  - Per-claim collapsible cards with side-by-side Classical + Biomedical evidence
 *  - Unified reasoning text and confidence score
 *  - Audit limitations footnote
 */

import React, { useState } from 'react';
import {
  BookOpen,
  FlaskConical,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Microscope,
  ScrollText,
  RefreshCw,
  Info,
  FileText,
} from 'lucide-react';
import ExportButton from './ExportButton';

// ---------------------------------------------------------------------------
// Grade config: colour palette & icon per DualEvidenceGrade value
// ---------------------------------------------------------------------------
const GRADE_CONFIG = {
  'Dual-supported': {
    bg: 'bg-emerald-50',
    border: 'border-emerald-300',
    text: 'text-emerald-800',
    pill: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    dot: 'bg-emerald-500',
    icon: CheckCircle2,
    emoji: '🟢',
    label: 'Dual-Supported',
    description: 'Strong classical Samhita text + strong modern biomedical backing.',
  },
  'Traditional-only': {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    text: 'text-amber-800',
    pill: 'bg-amber-100 text-amber-800 border-amber-300',
    dot: 'bg-amber-500',
    icon: BookOpen,
    emoji: '🟡',
    label: 'Traditional-Only',
    description: 'Supported by classical Samhitas; modern clinical trial data limited.',
  },
  'Clinical-backed': {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    text: 'text-blue-800',
    pill: 'bg-blue-100 text-blue-800 border-blue-300',
    dot: 'bg-blue-500',
    icon: Microscope,
    emoji: '🔵',
    label: 'Clinical-Backed',
    description: 'Supported by modern biomedical evidence; classical textual grounding is weak.',
  },
  'Partially aligned': {
    bg: 'bg-slate-50',
    border: 'border-slate-300',
    text: 'text-slate-700',
    pill: 'bg-slate-100 text-slate-700 border-slate-300',
    dot: 'bg-slate-400',
    icon: HelpCircle,
    emoji: '⚪',
    label: 'Partially Aligned',
    description: 'Moderate evidence in at least one stream; neither is conclusive.',
  },
  'Insufficient dual evidence': {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-600',
    pill: 'bg-gray-100 text-gray-600 border-gray-200',
    dot: 'bg-gray-400',
    icon: HelpCircle,
    emoji: '⚫',
    label: 'Insufficient Evidence',
    description: 'Both classical and biomedical evidence streams are weak for this claim.',
  },
  Contradicted: {
    bg: 'bg-rose-50',
    border: 'border-rose-300',
    text: 'text-rose-800',
    pill: 'bg-rose-100 text-rose-800 border-rose-300',
    dot: 'bg-rose-500',
    icon: XCircle,
    emoji: '🔴',
    label: 'Contradicted',
    description: 'Retrieved classical passage signals a potential contradiction or contraindication.',
  },
};

const DEFAULT_GRADE_CFG = {
  bg: 'bg-slate-50',
  border: 'border-slate-200',
  text: 'text-slate-600',
  pill: 'bg-slate-100 text-slate-600 border-slate-200',
  dot: 'bg-slate-400',
  icon: HelpCircle,
  emoji: '❓',
  label: 'Unknown',
  description: '',
};

function getGradeCfg(grade) {
  return GRADE_CONFIG[grade] || DEFAULT_GRADE_CFG;
}

// ---------------------------------------------------------------------------
// Confidence bar helper
// ---------------------------------------------------------------------------
function ConfidenceBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color =
    pct >= 70
      ? 'bg-emerald-500'
      : pct >= 45
      ? 'bg-amber-400'
      : pct >= 25
      ? 'bg-blue-400'
      : 'bg-gray-300';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-1.5 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Individual claim card
// ---------------------------------------------------------------------------
function DualClaimCard({ claim, index }) {
  const [expanded, setExpanded] = useState(index === 0);
  const cfg = getGradeCfg(claim.dual_grade);
  const GradeIcon = cfg.icon;

  const classical = claim.classical_evidence || {};
  const bio = claim.biomedical_evidence || {};

  return (
    <div className={`rounded-2xl border ${cfg.border} overflow-hidden shadow-xs`}>
      {/* Card header — always visible */}
      <button
        type="button"
        onClick={() => setExpanded((p) => !p)}
        className={`w-full flex items-start justify-between gap-3 p-4 sm:p-5 ${cfg.bg} hover:brightness-[0.98] transition-all text-left`}
      >
        <div className="flex items-start gap-3 min-w-0">
          {/* Claim number badge */}
          <span className="shrink-0 mt-0.5 w-6 h-6 rounded-lg bg-white/70 border border-current flex items-center justify-center text-xs font-bold text-slate-600">
            {claim.claim_id}
          </span>

          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-800 leading-snug line-clamp-2">
              {claim.claim_text}
            </p>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {/* Grade pill */}
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${cfg.pill}`}
              >
                <GradeIcon className="w-3 h-3" />
                {cfg.emoji} {cfg.label}
              </span>
              {/* Confidence */}
              <span className="text-xs text-slate-500">
                Confidence:{' '}
                <span className="font-semibold text-slate-700">
                  {Math.round((claim.confidence || 0) * 100)}%
                </span>
              </span>
            </div>
          </div>
        </div>

        <div className="shrink-0 mt-1 text-slate-400">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expandable body */}
      {expanded && (
        <div className="bg-white border-t border-slate-100 p-4 sm:p-5 space-y-5">
          {/* Confidence bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Composite Confidence Score</span>
              <span className={`font-semibold ${cfg.text}`}>{cfg.label}</span>
            </div>
            <ConfidenceBar score={claim.confidence} />
          </div>

          {/* Two-column evidence grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* ── Classical Evidence ── */}
            <div className="rounded-xl bg-amber-50 border border-amber-200/80 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-amber-700 shrink-0" />
                <span className="text-xs font-bold uppercase tracking-wider text-amber-800">
                  Classical (Samhita)
                </span>
                {classical.matched ? (
                  <span className="ml-auto text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full">
                    Matched
                  </span>
                ) : (
                  <span className="ml-auto text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded-full">
                    No match
                  </span>
                )}
              </div>

              {classical.reference && (
                <p className="text-xs font-semibold text-amber-900">
                  📖 {classical.reference}
                </p>
              )}

              {classical.original_passage && (
                <blockquote className="border-l-2 border-amber-400 pl-3 text-xs font-mono text-amber-900 leading-relaxed bg-amber-100/50 py-1 rounded-r-lg">
                  {classical.original_passage}
                </blockquote>
              )}

              {classical.commentary_note && (
                <p className="text-xs text-amber-800/90 italic leading-relaxed">
                  <span className="font-semibold not-italic">Commentary:</span>{' '}
                  {classical.commentary_note}
                </p>
              )}

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-amber-700">Relevance Score</span>
                <ConfidenceBar score={classical.relevance_score} />
              </div>

              {classical.is_contradicted && (
                <div className="flex items-center gap-1.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-2.5 py-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  Contradiction signal detected in retrieved passage.
                </div>
              )}

              {!classical.matched && (
                <p className="text-xs text-slate-500 italic">
                  No classical Samhita passage matched with sufficient relevance.
                </p>
              )}
            </div>

            {/* ── Biomedical Evidence ── */}
            <div className="rounded-xl bg-blue-50 border border-blue-200/80 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-blue-700 shrink-0" />
                <span className="text-xs font-bold uppercase tracking-wider text-blue-800">
                  Biomedical (PubMed)
                </span>
                {bio.matched ? (
                  <span className="ml-auto text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full">
                    Matched
                  </span>
                ) : (
                  <span className="ml-auto text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded-full">
                    No match
                  </span>
                )}
              </div>

              {bio.pmid && (
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    {bio.study_type && (
                      <span className="text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-blue-200/70 text-blue-800 border border-blue-300">
                        {bio.study_type}
                      </span>
                    )}
                    {bio.pub_year && (
                      <span className="text-xs text-blue-700 font-medium">{bio.pub_year}</span>
                    )}
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${bio.pmid}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-auto text-[10px] text-blue-600 hover:text-blue-900 font-mono border border-blue-200 px-1.5 py-0.5 rounded-full hover:bg-blue-100 transition-colors"
                      onClick={(e) => e.stopPropagation()}
                    >
                      PMID: {bio.pmid} ↗
                    </a>
                  </div>

                  {bio.title && (
                    <p className="text-xs font-semibold text-blue-900 leading-snug">{bio.title}</p>
                  )}

                  {bio.journal && (
                    <p className="text-[11px] text-blue-700 italic">{bio.journal}</p>
                  )}
                </div>
              )}

              {bio.abstract_snippet && (
                <p className="text-xs text-blue-800/90 leading-relaxed border-l-2 border-blue-300 pl-2.5 italic">
                  {bio.abstract_snippet}
                </p>
              )}

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-blue-700">Relevance Score</span>
                <ConfidenceBar score={bio.relevance_score} />
              </div>

              {bio.source && (
                <p className="text-[10px] text-blue-500 font-mono">Source: {bio.source}</p>
              )}

              {!bio.matched && (
                <p className="text-xs text-slate-500 italic">
                  No peer-reviewed study matched with sufficient relevance.
                </p>
              )}
            </div>
          </div>

          {/* Unified Reasoning */}
          {claim.unified_reasoning && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-wider">
                <ScrollText className="w-3.5 h-3.5" />
                Unified Reasoning
              </div>
              <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
                {claim.unified_reasoning.split(' | ').join('\n\n')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Grade summary pills bar
// ---------------------------------------------------------------------------
function GradeSummaryBar({ gradeSummary }) {
  const entries = Object.entries(gradeSummary || {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([grade, count]) => {
        const cfg = getGradeCfg(grade);
        const GradeIcon = cfg.icon;
        return (
          <div
            key={grade}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold ${cfg.pill} shadow-xs`}
          >
            <GradeIcon className="w-3.5 h-3.5" />
            <span>
              {cfg.emoji} {count} × {cfg.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main exported component
// ---------------------------------------------------------------------------
export default function DualAuditReportView({ report, isLoading }) {
  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 sm:p-10 space-y-5">
        {/* Pipeline steps loader */}
        {[
          { icon: FileText, label: 'Extracting atomic claims from text…', delay: '0ms' },
          { icon: BookOpen, label: 'Querying classical Samhita corpus (ChromaDB)…', delay: '350ms' },
          { icon: FlaskConical, label: 'Fetching PubMed biomedical evidence (live)…', delay: '700ms' },
          { icon: CheckCircle2, label: 'Synthesising dual-evidence verdicts…', delay: '1050ms' },
        ].map(({ icon: Icon, label, delay }) => (
          <div
            key={label}
            className="flex items-center gap-3 text-sm text-slate-500 animate-pulse"
            style={{ animationDelay: delay }}
          >
            <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
              <Icon className="w-4 h-4 text-slate-400" />
            </div>
            <span>{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-2 text-xs text-teal-700 font-medium mt-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          Dual-evidence cross-audit running (may take 15–30s on first request)…
        </div>
      </div>
    );
  }

  // Empty state
  if (!report) {
    return (
      <div className="bg-white rounded-3xl border border-slate-100 p-8 text-center text-slate-400 space-y-3">
        <div className="mx-auto w-14 h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center">
          <Microscope className="w-7 h-7 text-slate-300" />
        </div>
        <p className="text-sm font-medium">Dual-evidence audit results will appear here.</p>
        <p className="text-xs text-slate-400">
          Paste Ayurvedic text above and click <strong>Run Dual Audit</strong> to cross-audit
          classical Samhita passages against PubMed biomedical evidence simultaneously.
        </p>
      </div>
    );
  }

  const { grade_summary, executive_summary, claims = [], limitations = [] } = report;
  const totalClaims = report.total_claims || claims.length;

  return (
    <div className="space-y-6">
      {/* ── Report header card ── */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-5 sm:p-6 space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-800 to-teal-700 flex items-center justify-center">
                <Microscope className="w-4 h-4 text-white" />
              </div>
              <h2 className="text-base font-bold text-slate-900">
                Dual-Evidence Cross-Audit Report
              </h2>
            </div>
            <p className="text-xs text-slate-500 pl-10">
              {report.query_or_source} &bull; {totalClaims} claim
              {totalClaims !== 1 ? 's' : ''} evaluated
            </p>
          </div>

          <ExportButton reportType="dual-audit" report={report} />
        </div>

        {/* Executive summary */}
        {executive_summary && (
          <div className="bg-teal-50 border border-teal-200/80 rounded-xl px-4 py-3 text-sm text-teal-900 leading-relaxed font-medium">
            {executive_summary}
          </div>
        )}

        {/* Grade summary pills */}
        <GradeSummaryBar gradeSummary={grade_summary} />

        {/* Grade legend */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
          {Object.entries(GRADE_CONFIG).map(([grade, cfg]) => (
            <div key={grade} className="flex items-start gap-2 text-[11px] text-slate-500">
              <span
                className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${cfg.dot}`}
              />
              <span>
                <span className="font-semibold text-slate-700">{cfg.emoji} {cfg.label}:</span>{' '}
                {cfg.description}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Claim-by-claim cards ── */}
      {claims.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-700 px-1 flex items-center gap-2">
            <ScrollText className="w-4 h-4 text-teal-700" />
            Claim-by-Claim Dual Evidence
          </h3>
          {claims.map((claim, i) => (
            <DualClaimCard key={claim.claim_id} claim={claim} index={i} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400 text-sm">
          No individual claims were extracted from the input text.
        </div>
      )}

      {/* ── Limitations footnote ── */}
      {limitations.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-wider">
            <Info className="w-3.5 h-3.5 text-slate-400" />
            Audit Limitations
          </div>
          <ul className="space-y-1">
            {limitations.map((lim, i) => (
              <li key={i} className="text-xs text-slate-500 flex items-start gap-2 leading-relaxed">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-slate-300 shrink-0" />
                {lim}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
