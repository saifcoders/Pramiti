import React, { useState } from 'react';
import Header from '../components/Header';
import VerificationForm from '../components/VerificationForm';
import ResultsDisplay from '../components/ResultsDisplay';
import { verificationApi } from '../services/api';
import { ShieldCheck, Info } from 'lucide-react';

/**
 * Main AyurEval Verification Dashboard page.
 */
export default function Dashboard() {
  const [verificationResult, setVerificationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleVerify = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await verificationApi.verifyAnswer(payload);
      setVerificationResult(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during verification.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Intro banner */}
        <div className="mb-8 bg-gradient-to-r from-emerald-800 to-teal-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
          <div className="relative z-10 max-w-3xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-700/60 text-emerald-100 text-xs font-semibold mb-3 border border-emerald-500/30">
              <ShieldCheck className="w-3.5 h-3.5" />
              Source-Aware Verification Engine
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Cross-Audit AI Ayurvedic Claims Against Classical & Empirical Ground Truth
            </h2>
            <p className="mt-2 text-sm text-emerald-100/90 leading-relaxed">
              AyurEval (COGNEXA) prevents AI hallucinations by systematically indexing and checking claims against
              Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya, and contemporary biomedical literature.
            </p>
          </div>
          <div className="absolute right-0 bottom-0 translate-x-10 translate-y-10 w-72 h-72 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Verification Form */}
          <div className="lg:col-span-5">
            <VerificationForm onVerify={handleVerify} isLoading={loading} />
          </div>

          {/* Right Column: Verification Results */}
          <div className="lg:col-span-7">
            {verificationResult ? (
              <ResultsDisplay result={verificationResult} />
            ) : (
              <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center text-slate-500">
                <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-slate-700">No Verification Run Yet</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                  Submit a query and an AI-generated Ayurveda response on the left to inspect its classical Samhita references and scientific alignment.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
        AyurEval / COGNEXA &copy; {new Date().getFullYear()} — Classical Ayurveda & Modern Science AI Verification Framework
      </footer>
    </div>
  );
}

