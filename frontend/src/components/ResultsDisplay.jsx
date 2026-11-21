import React from 'react';
import {
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  HelpCircle,
  FileQuestion,
  BookOpen,
  Activity,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';

/**
 * Maps VerificationCategory enum strings to UI styling and icons.
 */
const getCategoryBadge = (category) => {
  switch (category) {
    case 'Supported by source':
      return {
        icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
        label: 'Supported by Source',
        badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      };
    case 'Partially supported':
      return {
        icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
        label: 'Partially Supported',
        badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
      };
    case 'Contradicted by source':
      return {
        icon: <AlertOctagon className="w-4 h-4 text-rose-600" />,
        label: 'Contradicted by Source',
        badgeClass: 'bg-rose-50 text-rose-800 border-rose-200',
      };
    case 'Insufficient evidence':
      return {
        icon: <HelpCircle className="w-4 h-4 text-slate-600" />,
        label: 'Insufficient Evidence',
        badgeClass: 'bg-slate-50 text-slate-700 border-slate-200',
      };
    case 'Reference not verified':
    default:
      return {
        icon: <FileQuestion className="w-4 h-4 text-purple-600" />,
        label: 'Reference Not Verified',
        badgeClass: 'bg-purple-50 text-purple-800 border-purple-200',
      };
  }
};

/**
 * Displays the comprehensive verification audit report based on VerificationReportResponse.
 */
export default function ResultsDisplay({ result }) {
  if (!result) return null;

  const {
    query_or_source,
    generated_answer,
    claims = [],
    overall_summary,
    limitations = [],
  } = result;

  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-3">
          <div className="p-2 rounded-xl bg-emerald-100 text-emerald-800">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Verification Synthesis</h3>
            <p className="text-xs text-slate-500">{query_or_source}</p>
          </div>
        </div>

        <p className="text-sm text-slate-700 leading-relaxed font-medium bg-slate-50 p-4 rounded-xl border border-slate-100">
          {overall_summary}
        </p>

        {generated_answer && (
          <div className="mt-4 pt-3 border-t border-slate-100">
            <span className="block text-xs font-semibold uppercase text-slate-500 mb-1">
              Audited AI Answer
            </span>
            <p className="text-xs text-slate-600 italic bg-amber-50/50 p-3 rounded-lg border border-amber-100">
              "{generated_answer}"
            </p>
          </div>
        )}
      </div>

      {/* Decomposed Claims Audit */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" />
            Claim-Level Verification ({claims.length})
          </h3>
          <span className="text-xs text-slate-400">Strict Canonical Alignment</span>
        </div>

        {claims.map((claim) => {
          const badge = getCategoryBadge(claim.category);

          return (
            <div
              key={claim.claim_id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3"
            >
              {/* Claim Header & Category Badge */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <span className="text-xs font-bold text-slate-400 font-mono">
                  CLAIM #{claim.claim_id}
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${badge.badgeClass}`}
                >
                  {badge.icon}
                  {claim.category}
                </span>
              </div>

              {/* Claim Statement */}
              <p className="text-sm font-semibold text-slate-900">
                {claim.claim_text}
              </p>

              {/* Classical Reference & Shloka */}
              {claim.classical_reference && (
                <div className="bg-amber-50/70 border-l-4 border-amber-500 p-3 rounded-r-xl space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                    <BookOpen className="w-3.5 h-3.5 text-amber-700" />
                    <span>{claim.classical_reference}</span>
                  </div>
                  {claim.original_passage && (
                    <p className="text-xs font-serif italic text-amber-950">
                      {claim.original_passage}
                    </p>
                  )}
                  {claim.commentary_note && (
                    <p className="text-xs text-amber-900 mt-1">
                      <span className="font-semibold">Commentary: </span>
                      {claim.commentary_note}
                    </p>
                  )}
                </div>
              )}

              {/* Modern Scientific Evidence */}
              {claim.scientific_evidence && (
                <div className="bg-purple-50/70 border-l-4 border-purple-500 p-3 rounded-r-xl">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-purple-900 mb-0.5">
                    <Activity className="w-3.5 h-3.5 text-purple-700" />
                    <span>Modern Scientific Evidence</span>
                  </div>
                  <p className="text-xs text-purple-900">
                    {claim.scientific_evidence}
                  </p>
                </div>
              )}

              {/* Reasoning */}
              <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="font-semibold text-slate-700">Verification Reasoning: </span>
                {claim.reasoning}
              </div>
            </div>
          );
        })}
      </div>

      {/* Audit Limitations */}
      {limitations && limitations.length > 0 && (
        <div className="bg-slate-100/80 rounded-xl p-4 border border-slate-200 text-xs text-slate-600 space-y-1.5">
          <div className="flex items-center gap-1.5 font-bold text-slate-700">
            <Info className="w-4 h-4 text-slate-500" />
            <span>Verification Limitations & Boundaries:</span>
          </div>
          <ul className="list-disc list-inside space-y-1 pl-1">
            {limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
