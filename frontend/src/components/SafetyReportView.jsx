/**
 * SafetyReportView.jsx
 *
 * Renders the Ayurvedic Safety, Matra (Dosage) & Contraindication Audit Report
 * returned by POST /api/v1/safety/check.
 *
 * Features:
 *  - Primary is_safe status banner (SAFE vs CAUTION vs CRITICAL HAZARD)
 *  - Detected herb identification tags
 *  - Color-coded safety alerts (CRITICAL in rose, WARNING in amber, ADVISORY in teal)
 *  - Classical Matra & Anupana pharmacology cards per herb
 *  - Canonical source citations & phytovigilance references
 */

import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Info,
  BookOpen,
  Pill,
  Scale,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileText,
  Activity,
  HeartPulse,
  Sparkles,
} from 'lucide-react';
import ExportButton from './ExportButton';

// ---------------------------------------------------------------------------
// Severity configuration
// ---------------------------------------------------------------------------
const SEVERITY_CONFIG = {
  CRITICAL: {
    bg: 'bg-rose-50',
    border: 'border-rose-300',
    headerBg: 'bg-rose-100/70',
    text: 'text-rose-900',
    pill: 'bg-rose-100 text-rose-800 border-rose-300',
    icon: AlertOctagon,
    label: 'Critical Contraindication',
    badge: 'bg-rose-600 text-white',
  },
  WARNING: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    headerBg: 'bg-amber-100/70',
    text: 'text-amber-900',
    pill: 'bg-amber-100 text-amber-800 border-amber-300',
    icon: AlertTriangle,
    label: 'Precaution / Drug Interaction',
    badge: 'bg-amber-600 text-white',
  },
  ADVISORY: {
    bg: 'bg-teal-50/70',
    border: 'border-teal-200',
    headerBg: 'bg-teal-100/60',
    text: 'text-teal-900',
    pill: 'bg-teal-100 text-teal-800 border-teal-200',
    icon: Info,
    label: 'Classical Matra & Anupana',
    badge: 'bg-teal-700 text-white',
  },
};

const ALERT_TYPE_LABELS = {
  CONTRAINDICATION: 'Clinical Contraindication',
  DRUG_INTERACTION: 'Herb-Drug Interaction',
  DOSAGE_WARNING: 'Dosage Threshold Exceeded',
  VIRUDDHA_AHARA: 'Viruddha Ahara (Incompatibility)',
  PRECAUTION: 'Special Precaution',
  ADVISORY: 'Matra & Anupana Advisory',
};

// ---------------------------------------------------------------------------
// Single Alert Card Component
// ---------------------------------------------------------------------------
function SafetyAlertCard({ alert }) {
  const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.ADVISORY;
  const AlertIcon = cfg.icon;
  const typeLabel = ALERT_TYPE_LABELS[alert.alert_type] || alert.alert_type;

  return (
    <div className={`rounded-2xl border ${cfg.border} ${cfg.bg} overflow-hidden shadow-2xs`}>
      <div className={`p-4 flex items-start gap-3.5`}>
        <div className={`p-2 rounded-xl ${cfg.headerBg} ${cfg.text} shrink-0 mt-0.5`}>
          <AlertIcon className="w-5 h-5" />
        </div>

        <div className="space-y-1.5 min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md ${cfg.badge}`}>
              {alert.severity}
            </span>
            <span className="text-xs font-semibold text-slate-700 bg-white/80 border border-slate-200 px-2 py-0.5 rounded-md">
              {alert.herb}
            </span>
            <span className="text-xs font-medium text-slate-500">
              {typeLabel}
            </span>
          </div>

          <p className={`text-sm font-semibold ${cfg.text} leading-snug`}>
            {alert.message}
          </p>

          <div className="pt-1 text-xs text-slate-700 bg-white/70 rounded-xl p-3 border border-slate-200/60 space-y-1">
            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
              <span>Guidance & Action:</span>
            </div>
            <p className="leading-relaxed">{alert.recommendation}</p>
          </div>

          {alert.classical_reference && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 pt-0.5 font-mono">
              <BookOpen className="w-3.5 h-3.5 text-slate-400" />
              <span>Source: {alert.classical_reference}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Herb Pharmacology & Matra Profile Card
// ---------------------------------------------------------------------------
function HerbProfileCard({ profile, index }) {
  const [expanded, setExpanded] = useState(index === 0);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-2xs overflow-hidden transition-all">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-slate-50/80 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shrink-0 font-bold text-sm">
            {profile.herb_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-900">{profile.herb_name}</h4>
              <span className="text-xs italic text-slate-500">({profile.botanical_name})</span>
            </div>
            <p className="text-xs text-slate-500 line-clamp-1">
              Matra: {profile.classical_matra} &bull; Max: {profile.max_daily_matra}
            </p>
          </div>
        </div>

        <div className="text-slate-400">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="p-4 sm:p-5 border-t border-slate-100 bg-slate-50/40 space-y-4 text-xs">
          {/* Matra & Anupana Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="font-bold text-teal-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <Scale className="w-3.5 h-3.5" /> Classical Matra (Dosage)
              </span>
              <p className="text-slate-700 leading-relaxed">{profile.classical_matra}</p>
              <p className="text-[11px] text-slate-500 font-medium pt-1">
                Max Daily Bound: <strong className="text-slate-800">{profile.max_daily_matra}</strong>
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="font-bold text-blue-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <Pill className="w-3.5 h-3.5" /> Classical Anupana (Adjuvants)
              </span>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {profile.anupana.map((anu, i) => (
                  <span
                    key={i}
                    className="inline-block px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 font-medium text-[11px]"
                  >
                    {anu}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Contraindications */}
          {profile.contraindications?.length > 0 && (
            <div className="bg-white p-3.5 rounded-xl border border-rose-200 space-y-1.5">
              <span className="font-bold text-rose-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5 text-rose-600" /> Known Contraindications
              </span>
              <ul className="space-y-1 pl-4 list-disc text-slate-700">
                {profile.contraindications.map((contra, i) => (
                  <li key={i} className="leading-relaxed">{contra}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Herb-Drug Interactions */}
          {profile.herb_drug_interactions?.length > 0 && (
            <div className="bg-white p-3.5 rounded-xl border border-amber-200 space-y-1.5">
              <span className="font-bold text-amber-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <HeartPulse className="w-3.5 h-3.5 text-amber-600" /> Herb-Drug Interactions
              </span>
              <ul className="space-y-1 pl-4 list-disc text-slate-700">
                {profile.herb_drug_interactions.map((inter, i) => (
                  <li key={i} className="leading-relaxed">{inter}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Special Precautions & Source */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-1 text-slate-500">
            {profile.special_precautions && (
              <span className="text-[11px] italic">
                <strong>Precaution:</strong> {profile.special_precautions}
              </span>
            )}
            <span className="text-[11px] font-mono text-slate-400 shrink-0">
              Citation: {profile.classical_source}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Exported Component
// ---------------------------------------------------------------------------
export default function SafetyReportView({ report, isLoading }) {
  // Loading State
  if (isLoading) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 space-y-4">
        {[
          { icon: Pill, label: 'Scanning text for Ayurvedic herbs and formulations…', delay: '0ms' },
          { icon: Scale, label: 'Checking classical Matra (dosage) against API thresholds…', delay: '300ms' },
          { icon: AlertTriangle, label: 'Cross-auditing clinical contraindications & drug interactions…', delay: '600ms' },
          { icon: ShieldCheck, label: 'Compiling safety clearance and Anupana recommendations…', delay: '900ms' },
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
        <div className="flex items-center gap-2 text-xs text-teal-700 font-medium pt-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          Running Ayurvedic safety and contraindication audit…
        </div>
      </div>
    );
  }

  // Empty State
  if (!report) {
    return (
      <div className="bg-white rounded-3xl border border-slate-100 p-8 text-center text-slate-400 space-y-3">
        <div className="mx-auto w-14 h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center">
          <ShieldAlert className="w-7 h-7 text-slate-300" />
        </div>
        <p className="text-sm font-medium">Ayurvedic safety audit results will appear here.</p>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Enter an Ayurvedic prescription, treatment advice, or herb inquiry above to audit
          clinical contraindications, maximum dosages, and herb-drug interactions.
        </p>
      </div>
    );
  }

  const { is_safe, detected_herbs = [], alerts = [], profiles = {}, summary } = report;

  // Classify overall banner status
  const hasCritical = alerts.some((a) => a.severity === 'CRITICAL') || !is_safe;
  const hasWarning = alerts.some((a) => a.severity === 'WARNING');

  return (
    <div className="space-y-6">
      {/* ── Status Banner Card ── */}
      <div
        className={`rounded-3xl border p-6 sm:p-7 shadow-xs relative overflow-hidden ${
          hasCritical
            ? 'bg-rose-50 border-rose-300 text-rose-950'
            : hasWarning
            ? 'bg-amber-50 border-amber-300 text-amber-950'
            : 'bg-emerald-50 border-emerald-300 text-emerald-950'
        }`}
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div
              className={`p-3 rounded-2xl shrink-0 ${
                hasCritical
                  ? 'bg-rose-600 text-white shadow-xs'
                  : hasWarning
                  ? 'bg-amber-500 text-white shadow-xs'
                  : 'bg-emerald-600 text-white shadow-xs'
              }`}
            >
              {hasCritical ? (
                <AlertOctagon className="w-7 h-7" />
              ) : hasWarning ? (
                <AlertTriangle className="w-7 h-7" />
              ) : (
                <ShieldCheck className="w-7 h-7" />
              )}
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-white/70 border border-current">
                  {hasCritical ? 'CRITICAL HAZARD' : hasWarning ? 'CAUTION ADVISED' : 'SAFE FOR ADMINISTRATION'}
                </span>
                <span className="text-xs text-slate-500">
                  {detected_herbs.length} herb{detected_herbs.length !== 1 ? 's' : ''} evaluated
                </span>
              </div>
              <h3 className="text-lg font-extrabold tracking-tight">
                {hasCritical
                  ? 'Contraindication or Toxicity Hazard Detected'
                  : hasWarning
                  ? 'Safety Clearance with Cautions & Drug Interactions'
                  : 'Classical Safety Clearance Passed'}
              </h3>
              <p className="text-xs leading-relaxed opacity-90 max-w-3xl">
                {summary}
              </p>
            </div>
          </div>

          <div className="self-end sm:self-center shrink-0">
            <ExportButton reportType="safety" report={report} />
          </div>
        </div>

        {/* Detected Herbs Tags */}
        {detected_herbs.length > 0 && (
          <div className="mt-5 pt-4 border-t border-current/15 flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 mr-1">
              Detected Herbs:
            </span>
            {detected_herbs.map((herb) => (
              <span
                key={herb}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-slate-200/90 text-xs font-bold text-slate-800 shadow-2xs"
              >
                <Pill className="w-3.5 h-3.5 text-teal-700" />
                {herb}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Active Alerts List ── */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-teal-700" />
              Safety Alerts & Guidelines ({alerts.length})
            </h4>
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 text-rose-700 font-semibold">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                Critical: {alerts.filter((a) => a.severity === 'CRITICAL').length}
              </span>
              <span className="inline-flex items-center gap-1 text-amber-700 font-semibold">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Warnings: {alerts.filter((a) => a.severity === 'WARNING').length}
              </span>
            </div>
          </div>

          <div className="space-y-2.5">
            {alerts.map((alert, i) => (
              <SafetyAlertCard key={i} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {/* ── Classical Matra & Pharmacology Profiles ── */}
      {Object.keys(profiles).length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-slate-800 px-1 flex items-center gap-2">
            <Scale className="w-4 h-4 text-teal-700" />
            Classical Matra (Dosage) & Anupana Pharmacology Profiles
          </h4>
          <div className="space-y-2.5">
            {Object.values(profiles).map((profile, i) => (
              <HerbProfileCard key={profile.herb_name} profile={profile} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
