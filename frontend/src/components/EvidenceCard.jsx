import React from 'react';
import { BookOpen, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';

/**
 * EvidenceCard component to render an excerpt from a Samhita or Scientific paper.
 */
export default function EvidenceCard({ evidence }) {
  const isSamhita = evidence.corpus_type !== 'scientific_evidence';

  // Badge styling according to alignment
  const getAlignmentBadge = (status) => {
    switch (status) {
      case 'supports':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5" />
            Corroborated
          </span>
        );
      case 'partially_supports':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            Partially Aligned
          </span>
        );
      case 'contradicts':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" />
            Contradiction
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-200">
            <Info className="w-3.5 h-3.5" />
            Neutral
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center space-x-2">
          <span
            className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
              isSamhita ? 'bg-amber-100 text-amber-800' : 'bg-purple-100 text-purple-800'
            }`}
          >
            <BookOpen className="w-4 h-4" />
          </span>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">{evidence.source_title}</h4>
            <p className="text-xs text-slate-500">{evidence.reference_location}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getAlignmentBadge(evidence.alignment)}
          <span className="text-xs text-slate-400 font-mono">
            {Math.round(evidence.relevance_score * 100)}% match
          </span>
        </div>
      </div>

      {/* Sanskrit Shloka Quote if available */}
      {evidence.sanskrit_excerpt && (
        <blockquote className="my-2 p-2.5 rounded-lg bg-amber-50/60 border-l-4 border-amber-400 text-amber-950 font-serif text-sm italic">
          {evidence.sanskrit_excerpt}
        </blockquote>
      )}

      {/* English translation / scientific finding */}
      <p className="text-sm text-slate-700 leading-relaxed mt-2">
        {evidence.text_content}
      </p>
    </div>
  );
}

