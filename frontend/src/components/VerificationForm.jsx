import React, { useState } from 'react';
import { Search, Loader2, Sparkles, CheckSquare, Square } from 'lucide-react';

/**
 * VerificationForm allows users to input clinical questions & AI answers to audit.
 */
export default function VerificationForm({ onVerify, isLoading }) {
  const [query, setQuery] = useState(
    'Is sesame oil recommended for daily massage in Vata disorders?'
  );
  const [aiAnswer, setAiAnswer] = useState(
    'Yes, sesame oil (Tila Taila) is the premier oil in Ayurveda for pacifying Vata dosha. It provides unctuousness, relieves dryness, and is suitable for daily Abhyanga (massage).'
  );
  const [checkScience, setCheckScience] = useState(true);
  const [selectedSamhitas, setSelectedSamhitas] = useState([
    'charaka_samhita',
    'sushruta_samhita',
    'ashtanga_hridaya',
  ]);

  const toggleSamhita = (type) => {
    setSelectedSamhitas((prev) =>
      prev.includes(type) ? prev.filter((item) => item !== type) : [...prev, type]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || !aiAnswer.trim()) return;

    onVerify({
      query,
      ai_generated_answer: aiAnswer,
      target_samhitas: selectedSamhitas,
      check_modern_science: checkScience,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5"
    >
      <div className="border-b border-slate-100 pb-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-600" />
          Audit AI-Generated Ayurveda Answer
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Input an AI response to verify its factual adherence against classical Samhitas and scientific trials.
        </p>
      </div>

      {/* Query Input */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
          Clinical or Lifestyle Query
        </label>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., What are the indications of Ashwagandha in Vata disorders?"
          className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all text-slate-800"
          required
        />
      </div>

      {/* AI Answer Input */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
          AI-Generated Answer to Verify
        </label>
        <textarea
          rows={4}
          value={aiAnswer}
          onChange={(e) => setAiAnswer(e.target.value)}
          placeholder="Paste the AI-generated answer here..."
          className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all text-slate-800 resize-y"
          required
        />
      </div>

      {/* Target Corpora Selection */}
      <div className="pt-2">
        <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-2">
          Canonical Corpora & Evidence Sources
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <button
            type="button"
            onClick={() => toggleSamhita('charaka_samhita')}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-colors ${
              selectedSamhitas.includes('charaka_samhita')
                ? 'bg-amber-50 border-amber-300 text-amber-900 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            {selectedSamhitas.includes('charaka_samhita') ? (
              <CheckSquare className="w-4 h-4 text-amber-600" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            Charaka Samhita
          </button>

          <button
            type="button"
            onClick={() => toggleSamhita('sushruta_samhita')}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-colors ${
              selectedSamhitas.includes('sushruta_samhita')
                ? 'bg-blue-50 border-blue-300 text-blue-900 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            {selectedSamhitas.includes('sushruta_samhita') ? (
              <CheckSquare className="w-4 h-4 text-blue-600" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            Sushruta Samhita
          </button>

          <button
            type="button"
            onClick={() => toggleSamhita('ashtanga_hridaya')}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-colors ${
              selectedSamhitas.includes('ashtanga_hridaya')
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            {selectedSamhitas.includes('ashtanga_hridaya') ? (
              <CheckSquare className="w-4 h-4 text-emerald-600" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            Ashtanga Hridaya
          </button>

          <button
            type="button"
            onClick={() => setCheckScience(!checkScience)}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-colors ${
              checkScience
                ? 'bg-purple-50 border-purple-300 text-purple-900 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            {checkScience ? (
              <CheckSquare className="w-4 h-4 text-purple-600" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            Modern Science (PubMed/Trials)
          </button>
        </div>
      </div>

      {/* Submit Button */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Auditing Canonical Shlokas & PubMed...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Run AyurEval Verification
            </>
          )}
        </button>
      </div>
    </form>
  );
}

