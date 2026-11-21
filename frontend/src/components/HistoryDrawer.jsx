/**
 * HistoryDrawer.jsx - Interactive Slide-Over History & Session Manager.
 *
 * Allows users to:
 *  - Browse past audits, verification inquiries, dual audits, and safety checks
 *  - Filter by session type or search by herb/query
 *  - Instant-reload past sessions directly into the active dashboard workspace
 *  - Delete individual sessions or clear all saved cache
 */

import React, { useState } from 'react';
import {
  X,
  History,
  Trash2,
  Clock,
  RotateCcw,
  Search,
  Sparkles,
  Layers,
  Microscope,
  AlertOctagon,
  ChevronRight,
  ShieldCheck,
  Check,
  ListChecks,
} from 'lucide-react';

const TYPE_CONFIG = {
  ask: {
    label: 'Inquiry',
    color: 'bg-teal-50 text-teal-800 border-teal-200',
    dot: 'bg-teal-600',
    icon: Sparkles,
  },
  verify: {
    label: 'Verify',
    color: 'bg-blue-50 text-blue-800 border-blue-200',
    dot: 'bg-blue-600',
    icon: Layers,
  },
  dual: {
    label: 'Dual Audit',
    color: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    dot: 'bg-indigo-600',
    icon: Microscope,
  },
  safety: {
    label: 'Safety',
    color: 'bg-rose-50 text-rose-800 border-rose-200',
    dot: 'bg-rose-600',
    icon: AlertOctagon,
  },
  batch: {
    label: 'Batch Audit',
    color: 'bg-purple-50 text-purple-800 border-purple-200',
    dot: 'bg-purple-600',
    icon: ListChecks,
  },
};

export default function HistoryDrawer({
  isOpen,
  onClose,
  history = [],
  onSelectSession,
  onDeleteSession,
  onClearHistory,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [copiedId, setCopiedId] = useState(null);

  if (!isOpen) return null;

  // Filter items based on search and type
  const filteredHistory = history.filter((item) => {
    const matchesType = selectedType === 'all' || item.type === selectedType;
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      !term ||
      item.title?.toLowerCase().includes(term) ||
      item.queryOrText?.toLowerCase().includes(term) ||
      item.displaySummary?.toLowerCase().includes(term);
    return matchesType && matchesSearch;
  });

  return (
    <div className="fixed inset-0 z-50 overflow-hidden animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-0 sm:pl-10">
        <div className="w-screen max-w-full sm:max-w-md bg-white shadow-2xl flex flex-col border-l border-slate-200">
          {/* ── Drawer Header ── */}
          <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-teal-800 text-white flex items-center justify-center shadow-xs">
                <History className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900">Audit History</h3>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                    {history.length}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">Stored in browser cache</p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="Close drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* ── Search & Filter Controls ── */}
          <div className="p-3.5 sm:p-4 border-b border-slate-100 bg-white space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search queries, herbs, or summaries..."
                className="w-full pl-9 pr-3.5 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-700 transition-all text-slate-800"
              />
            </div>

            {/* Type Filters */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] no-scrollbar">
              {[
                { id: 'all', label: 'All' },
                { id: 'ask', label: 'Inquiries' },
                { id: 'verify', label: 'Verify' },
                { id: 'dual', label: 'Dual Audit' },
                { id: 'safety', label: 'Safety' },
                { id: 'batch', label: 'Batch Audit' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedType(tab.id)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all shrink-0 ${
                    selectedType === tab.id
                      ? 'bg-teal-800 text-white shadow-2xs font-bold'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Session Cards List ── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
            {filteredHistory.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
                <Clock className="w-8 h-8 text-slate-300 stroke-1" />
                <p className="text-xs font-semibold text-slate-600">
                  {searchTerm ? 'No matching sessions found' : 'No saved sessions yet'}
                </p>
                <p className="text-[11px] text-slate-400 max-w-xs">
                  {searchTerm
                    ? 'Try clearing the search or filter to see all sessions.'
                    : 'Run a verification inquiry, dual audit, or safety check to automatically archive it here.'}
                </p>
              </div>
            ) : (
              filteredHistory.map((item) => {
                const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.ask;
                const TypeIcon = cfg.icon;

                return (
                  <div
                    key={item.id}
                    onClick={() => onSelectSession(item)}
                    className="group relative rounded-2xl border border-slate-200/90 p-3.5 bg-white hover:border-teal-300 hover:shadow-xs transition-all cursor-pointer text-left space-y-2"
                  >
                    {/* Top Row: Type Badge + Date + Delete */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-bold uppercase tracking-wider ${cfg.color}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                          <TypeIcon className="w-2.5 h-2.5" />
                          {cfg.label}
                        </span>
                        <span className="text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5" />
                          {item.displayDate}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(item.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
                        title="Delete this session"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Query Title */}
                    <h4 className="text-xs font-bold text-slate-900 line-clamp-2 leading-snug group-hover:text-teal-900 transition-colors">
                      {item.title}
                    </h4>

                    {/* Summary snippet */}
                    {item.displaySummary && (
                      <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed bg-slate-50 p-2 rounded-xl border border-slate-100">
                        {item.displaySummary}
                      </p>
                    )}

                    {/* Reload Hint */}
                    <div className="flex items-center justify-between pt-1 text-[10px] text-teal-700 font-semibold">
                      <span className="flex items-center gap-1">
                        <RotateCcw className="w-3 h-3 text-teal-600" />
                        Click to restore report
                      </span>
                      <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* ── Drawer Footer ── */}
          {history.length > 0 && (
            <div className="p-4 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <button
                type="button"
                onClick={onClearHistory}
                className="text-xs text-rose-600 hover:text-rose-800 font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-rose-50 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear All History
              </button>

              <button
                type="button"
                onClick={onClose}
                className="text-xs bg-white border border-slate-200 text-slate-700 font-semibold px-4 py-1.5 rounded-xl hover:bg-slate-50 transition-colors"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
