/**
 * Toast.jsx - Academic Notification Toast Banner for AyurEval.
 *
 * Provides transient, non-intrusive feedback for:
 *  - Form input validations (e.g. empty queries, max claim limits)
 *  - Operation confirmations (e.g. exports, session restores, cache clear)
 *  - Network and API connectivity alerts
 */

import React, { useEffect } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
} from 'lucide-react';

const TOAST_TYPES = {
  success: {
    bg: 'bg-emerald-50 border-emerald-200 text-emerald-950',
    icon: CheckCircle2,
    iconColor: 'text-emerald-600',
    dot: 'bg-emerald-500',
  },
  error: {
    bg: 'bg-rose-50 border-rose-200 text-rose-950',
    icon: AlertCircle,
    iconColor: 'text-rose-600',
    dot: 'bg-rose-500',
  },
  warning: {
    bg: 'bg-amber-50 border-amber-200 text-amber-950',
    icon: AlertTriangle,
    iconColor: 'text-amber-600',
    dot: 'bg-amber-500',
  },
  info: {
    bg: 'bg-slate-50 border-slate-200 text-slate-900',
    icon: Info,
    iconColor: 'text-teal-600',
    dot: 'bg-teal-500',
  },
};

export default function Toast({ message, type = 'info', onClose, duration = 4000 }) {
  useEffect(() => {
    if (!duration || duration <= 0) return;
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const cfg = TOAST_TYPES[type] || TOAST_TYPES.info;
  const Icon = cfg.icon;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-5 right-5 z-50 max-w-sm w-full mx-auto sm:w-auto flex items-start gap-3 p-4 rounded-2xl border ${cfg.bg} shadow-lg backdrop-blur-xs transition-all duration-200 animate-in fade-in slide-in-from-bottom-3`}
    >
      <div className="shrink-0 mt-0.5">
        <Icon className={`w-4 h-4 ${cfg.iconColor}`} />
      </div>

      <div className="flex-1 min-w-0 pr-1">
        <p className="text-xs font-semibold leading-relaxed">{message}</p>
      </div>

      <button
        type="button"
        onClick={onClose}
        className="shrink-0 p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-black/5 transition-colors"
        title="Dismiss notification"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
