/**
 * ExportButton.jsx - Reusable Academic Report Export Dropdown for AyurEval.
 *
 * Allows one-click export into:
 *  - Formatted Markdown (.md)
 *  - High-Resolution Print / Save as PDF
 *  - Raw Report Data (.json)
 */

import React, { useState, useRef, useEffect } from 'react';
import { Download, FileText, Printer, FileCode, ChevronDown } from 'lucide-react';
import { exportReportMarkdown, exportReportJSON, printReportToPDF } from '../utils/exportReport';

export default function ExportButton({ reportType, report, label = 'Export Report', onExported }) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!report) return null;

  const handleAction = (fn, formatName) => {
    try {
      fn(reportType, report);
      if (onExported) {
        onExported(`Report exported successfully as ${formatName}.`);
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
    setOpen(false);
  };

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 px-3.5 py-2 sm:py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 font-semibold text-xs shadow-2xs transition-colors focus:outline-none focus:ring-2 focus:ring-teal-600/20"
        title="Export this report"
      >
        <Download className="w-3.5 h-3.5 text-teal-700" />
        <span>{label}</span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {open && (
        <div className="absolute right-0 mt-1.5 w-56 max-w-[calc(100vw-2rem)] rounded-2xl bg-white border border-slate-200/90 shadow-xl z-50 py-1.5 text-xs animate-in fade-in-50 slide-in-from-top-1 duration-100">
          <div className="px-3.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 mb-1">
            Export Options
          </div>

          {/* Option 1: Markdown */}
          <button
            type="button"
            onClick={() => handleAction(exportReportMarkdown, 'Markdown (.md)')}
            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-slate-700 hover:bg-teal-50 hover:text-teal-900 active:bg-teal-100 transition-colors text-left"
          >
            <FileText className="w-4 h-4 text-teal-600 shrink-0" />
            <div>
              <div className="font-semibold">Markdown Document</div>
              <div className="text-[10px] text-slate-400">Formatted (.md) file</div>
            </div>
          </button>

          {/* Option 2: Print to PDF */}
          <button
            type="button"
            onClick={() => handleAction(printReportToPDF, 'PDF')}
            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-slate-700 hover:bg-blue-50 hover:text-blue-900 active:bg-blue-100 transition-colors text-left"
          >
            <Printer className="w-4 h-4 text-blue-600 shrink-0" />
            <div>
              <div className="font-semibold">Save as PDF / Print</div>
              <div className="text-[10px] text-slate-400">Print-styled academic view</div>
            </div>
          </button>

          {/* Option 3: JSON */}
          <button
            type="button"
            onClick={() => handleAction(exportReportJSON, 'JSON Data')}
            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-slate-700 hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100 transition-colors text-left"
          >
            <FileCode className="w-4 h-4 text-slate-500 shrink-0" />
            <div>
              <div className="font-semibold">Raw Data (JSON)</div>
              <div className="text-[10px] text-slate-400">Full audit schema (.json)</div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
}
