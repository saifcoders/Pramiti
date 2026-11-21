/**
 * BatchReportView.jsx - Batch Claim Verification Analytics & Results View.
 *
 * Displays:
 *  1. Analytics Summary Bar — colored stat cards for all verdict categories + safety flags
 *  2. Per-Claim Results Table — verdict badge, classical ref, safety status, reasoning
 *  3. ExportButton (Markdown / PDF / JSON)
 *  4. Loading state spinner and empty state invitation
 */

import React from 'react';
import {
  BarChart3,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  FileSearch,
  MinusCircle,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  ListChecks,
  ChevronRight,
} from 'lucide-react';
import ExportButton from './ExportButton';

// ---------------------------------------------------------------------------
// Category display config
// ---------------------------------------------------------------------------
const CATEGORY_CONFIG = {
  'Supported by source': {
    label: 'Supported',
    shortLabel: '✅ Supported',
    pill: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    icon: CheckCircle2,
    iconColor: 'text-emerald-600',
  },
  'Partially supported': {
    label: 'Partial',
    shortLabel: '🟡 Partial',
    pill: 'bg-amber-100 text-amber-800 border-amber-200',
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
  },
  'Contradicted by source': {
    label: 'Contradicted',
    shortLabel: '🔴 Contradicted',
    pill: 'bg-rose-100 text-rose-800 border-rose-200',
    icon: XCircle,
    iconColor: 'text-rose-600',
  },
  'Insufficient evidence': {
    label: 'Insufficient',
    shortLabel: '⚫ Insufficient',
    pill: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: MinusCircle,
    iconColor: 'text-slate-500',
  },
  'Reference not verified': {
    label: 'Not Verified',
    shortLabel: '❓ Not Verified',
    pill: 'bg-purple-100 text-purple-800 border-purple-200',
    icon: FileSearch,
    iconColor: 'text-purple-600',
  },
};

function getCategoryConfig(cat) {
  return CATEGORY_CONFIG[cat] || {
    label: cat || 'Unknown',
    shortLabel: cat || 'Unknown',
    pill: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: HelpCircle,
    iconColor: 'text-slate-500',
  };
}

// ---------------------------------------------------------------------------
// Analytics Summary Bar
// ---------------------------------------------------------------------------
function AnalyticsSummaryBar({ analytics }) {
  if (!analytics) return null;

  const statCards = [
    {
      label: 'Total Claims',
      value: analytics.total_claims,
      bg: 'bg-slate-50 border-slate-200',
      text: 'text-slate-800',
      icon: ListChecks,
      iconColor: 'text-slate-600',
    },
    {
      label: 'Supported',
      value: analytics.supported,
      bg: 'bg-emerald-50 border-emerald-200',
      text: 'text-emerald-900',
      icon: CheckCircle2,
      iconColor: 'text-emerald-600',
    },
    {
      label: 'Partial',
      value: analytics.partially_supported,
      bg: 'bg-amber-50 border-amber-200',
      text: 'text-amber-900',
      icon: AlertTriangle,
      iconColor: 'text-amber-500',
    },
    {
      label: 'Contradicted',
      value: analytics.contradicted,
      bg: 'bg-rose-50 border-rose-200',
      text: 'text-rose-900',
      icon: XCircle,
      iconColor: 'text-rose-600',
    },
    {
      label: 'Insufficient',
      value: analytics.insufficient_evidence,
      bg: 'bg-slate-50 border-slate-200',
      text: 'text-slate-700',
      icon: MinusCircle,
      iconColor: 'text-slate-500',
    },
    {
      label: 'Not Verified',
      value: analytics.reference_not_verified,
      bg: 'bg-purple-50 border-purple-200',
      text: 'text-purple-900',
      icon: FileSearch,
      iconColor: 'text-purple-600',
    },
    {
      label: 'Safety Flags',
      value: analytics.total_safety_flags,
      bg: 'bg-orange-50 border-orange-200',
      text: 'text-orange-900',
      icon: ShieldAlert,
      iconColor: 'text-orange-500',
    },
    {
      label: 'Critical Safety',
      value: analytics.critical_safety_flags,
      bg: analytics.critical_safety_flags > 0 ? 'bg-rose-100 border-rose-300' : 'bg-slate-50 border-slate-200',
      text: analytics.critical_safety_flags > 0 ? 'text-rose-900 font-bold' : 'text-slate-600',
      icon: analytics.critical_safety_flags > 0 ? ShieldAlert : ShieldCheck,
      iconColor: analytics.critical_safety_flags > 0 ? 'text-rose-600' : 'text-emerald-600',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
      {statCards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`flex flex-col items-center justify-center p-3 rounded-2xl border ${card.bg} text-center`}
          >
            <Icon className={`w-4 h-4 mb-1 ${card.iconColor}`} />
            <span className={`text-xl font-extrabold ${card.text}`}>{card.value}</span>
            <span className="text-[10px] font-semibold text-slate-500 mt-0.5 uppercase tracking-wide">
              {card.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results Table
// ---------------------------------------------------------------------------
function ResultsTable({ results }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-xs">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th className="text-left px-4 py-3 font-bold text-slate-700 uppercase tracking-wider w-10">#</th>
            <th className="text-left px-4 py-3 font-bold text-slate-700 uppercase tracking-wider">Claim</th>
            <th className="text-left px-4 py-3 font-bold text-slate-700 uppercase tracking-wider w-36">Verdict</th>
            <th className="text-left px-4 py-3 font-bold text-slate-700 uppercase tracking-wider hidden md:table-cell">
              Classical Reference
            </th>
            <th className="text-center px-4 py-3 font-bold text-slate-700 uppercase tracking-wider w-20">Safety</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {results.map((r) => {
            const cfg = getCategoryConfig(r.category);
            const Icon = cfg.icon;
            return (
              <tr key={r.claim_index} className="hover:bg-slate-50/70 transition-colors group">
                {/* Index */}
                <td className="px-4 py-3 text-slate-500 font-mono font-bold">{r.claim_index}</td>

                {/* Claim text + reasoning */}
                <td className="px-4 py-3">
                  <p className="text-slate-800 font-medium leading-snug line-clamp-2">
                    {r.claim_text}
                  </p>
                  {r.reasoning && (
                    <p className="text-slate-500 mt-1 text-[11px] leading-snug line-clamp-2 italic">
                      <ChevronRight className="inline w-3 h-3 text-slate-400 mr-0.5" />
                      {r.reasoning}
                    </p>
                  )}
                </td>

                {/* Verdict badge */}
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${cfg.pill}`}
                  >
                    <Icon className={`w-3 h-3 ${cfg.iconColor}`} />
                    {cfg.label}
                  </span>
                </td>

                {/* Classical reference */}
                <td className="px-4 py-3 hidden md:table-cell text-slate-600 font-mono text-[11px]">
                  {r.classical_reference || <span className="text-slate-300">—</span>}
                </td>

                {/* Safety */}
                <td className="px-4 py-3 text-center">
                  {r.is_safe ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                      <ShieldCheck className="w-3 h-3" /> Safe
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200">
                      <ShieldAlert className="w-3 h-3" /> Alert
                    </span>
                  )}
                  {r.safety_alerts && r.safety_alerts.length > 0 && (
                    <div className="mt-1 space-y-0.5">
                      {r.safety_alerts.map((msg, i) => (
                        <p key={i} className="text-[10px] text-rose-600 leading-tight text-left">
                          • {msg.length > 60 ? msg.slice(0, 57) + '…' : msg}
                        </p>
                      ))}
                    </div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main BatchReportView
// ---------------------------------------------------------------------------
export default function BatchReportView({ report, isLoading }) {
  // Loading state with polished skeleton
  if (isLoading) {
    return (
      <div className="mt-6 space-y-6 animate-pulse">
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div className="space-y-1.5">
            <div className="h-5 w-48 bg-purple-100 rounded-lg" />
            <div className="h-3 w-64 bg-slate-100 rounded-lg" />
          </div>
          <div className="h-8 w-28 bg-slate-100 rounded-xl" />
        </div>

        {/* Pipeline status indicator */}
        <div className="p-4 rounded-2xl bg-purple-50/70 border border-purple-200/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-purple-200 text-purple-800 flex items-center justify-center shrink-0">
              <RefreshCw className="w-4 h-4 animate-spin" />
            </div>
            <div>
              <p className="text-xs font-bold text-purple-950">
                Executing Concurrent Batch Verification
              </p>
              <p className="text-[11px] text-purple-800/80">
                Retrieving classical Samhita citations via ChromaDB and cross-auditing phytovigilance rules...
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wide px-2.5 py-1 rounded-full bg-purple-100 text-purple-800">
            Processing Claims
          </span>
        </div>

        {/* 8-Card Stat Summary Skeleton */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="p-3 rounded-2xl border border-slate-100 bg-slate-50 flex flex-col items-center gap-1.5">
              <div className="w-4 h-4 bg-slate-200 rounded-full" />
              <div className="w-8 h-6 bg-slate-200 rounded-md" />
              <div className="w-12 h-2.5 bg-slate-200 rounded-full" />
            </div>
          ))}
        </div>

        {/* Table Skeleton */}
        <div className="rounded-2xl border border-slate-200 p-4 space-y-3 bg-white">
          <div className="h-4 w-32 bg-slate-200 rounded-md mb-2" />
          {[1, 2, 3].map((row) => (
            <div key={row} className="flex items-center gap-4 py-2 border-b border-slate-100">
              <div className="w-6 h-4 bg-slate-200 rounded-md" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-4/5 bg-slate-200 rounded" />
                <div className="h-2.5 w-1/2 bg-slate-100 rounded" />
              </div>
              <div className="w-20 h-6 bg-slate-200 rounded-full" />
              <div className="w-16 h-6 bg-slate-200 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!report) {
    return (
      <div className="mt-6 flex flex-col items-center justify-center py-20 gap-4 text-slate-400">
        <BarChart3 className="w-10 h-10 text-slate-300" />
        <p className="text-sm font-semibold text-slate-500">Batch Audit Results will appear here</p>
        <p className="text-xs text-slate-400 text-center max-w-sm">
          Paste up to 10 newline-separated Ayurvedic claims above and click <strong>Run Batch Audit</strong>.
          Results include individual verdicts, classical references, safety flags, and aggregated analytics.
        </p>
      </div>
    );
  }

  const { analytics, results, source_name } = report;

  return (
    <div className="mt-6 space-y-6">
      {/* Header row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
            <h2 className="text-base font-extrabold text-slate-900">Batch Audit Analytics</h2>
          </div>
          {source_name && (
            <p className="text-xs text-slate-500 mt-0.5">
              Source: <span className="font-semibold text-slate-700">{source_name}</span>
            </p>
          )}
        </div>
        <ExportButton reportType="batch" report={report} />
      </div>

      {/* Analytics Summary Bar */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2.5">
          Summary Analytics
        </h3>
        <AnalyticsSummaryBar analytics={analytics} />
      </div>

      {/* Verdict Distribution visual bar */}
      {analytics && analytics.total_claims > 0 && (
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">
            Verdict Distribution
          </h3>
          <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
            {analytics.supported > 0 && (
              <div
                className="bg-emerald-500 transition-all"
                style={{ width: `${(analytics.supported / analytics.total_claims) * 100}%` }}
                title={`Supported: ${analytics.supported}`}
              />
            )}
            {analytics.partially_supported > 0 && (
              <div
                className="bg-amber-400 transition-all"
                style={{ width: `${(analytics.partially_supported / analytics.total_claims) * 100}%` }}
                title={`Partially supported: ${analytics.partially_supported}`}
              />
            )}
            {analytics.contradicted > 0 && (
              <div
                className="bg-rose-500 transition-all"
                style={{ width: `${(analytics.contradicted / analytics.total_claims) * 100}%` }}
                title={`Contradicted: ${analytics.contradicted}`}
              />
            )}
            {analytics.insufficient_evidence > 0 && (
              <div
                className="bg-slate-400 transition-all"
                style={{ width: `${(analytics.insufficient_evidence / analytics.total_claims) * 100}%` }}
                title={`Insufficient: ${analytics.insufficient_evidence}`}
              />
            )}
            {analytics.reference_not_verified > 0 && (
              <div
                className="bg-purple-400 transition-all"
                style={{ width: `${(analytics.reference_not_verified / analytics.total_claims) * 100}%` }}
                title={`Not Verified: ${analytics.reference_not_verified}`}
              />
            )}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-medium text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Supported</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" /> Partial</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500 inline-block" /> Contradicted</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-400 inline-block" /> Insufficient</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-400 inline-block" /> Not Verified</span>
          </div>
        </div>
      )}

      {/* Results Table */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2.5">
          Per-Claim Results ({results?.length || 0})
        </h3>
        <ResultsTable results={results} />
      </div>

      {/* Disclaimer */}
      <p className="text-[11px] text-slate-400 italic border-t border-slate-100 pt-4">
        Batch audit cross-references each claim against indexed Brihat Trayi corpora (ChromaDB) and the
        AyurEval safety database. Results are for research and informational purposes only. Consult a
        registered Ayurvedic physician for clinical decisions.
      </p>
    </div>
  );
}
