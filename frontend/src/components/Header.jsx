import React from 'react';
import { ShieldCheck, BookOpen, Sparkles, Activity } from 'lucide-react';

/**
 * Header component featuring branding and canonical reference badges.
 */
export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo and Brand Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">AyurEval</h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                COGNEXA
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Source-Aware AI Verification Framework for Classical & Modern Ayurveda
            </p>
          </div>
        </div>

        {/* Canonical Reference Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-amber-600" />
            Charaka Samhita
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-900 border border-blue-200 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            Sushruta Samhita
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-900 border border-emerald-200 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            Ashtanga Hridaya
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 text-purple-900 border border-purple-200 font-medium">
            <Activity className="w-3.5 h-3.5 text-purple-600" />
            PubMed / Science
          </span>
        </div>
      </div>
    </header>
  );
}

