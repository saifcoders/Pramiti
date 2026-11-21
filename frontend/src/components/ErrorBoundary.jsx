/**
 * ErrorBoundary.jsx - Academic Error Boundary for AyurEval (COGNEXA).
 *
 * Catches unhandled runtime rendering errors in report components or workspace views,
 * preventing full-page white screens and offering self-healing recovery actions.
 */

import React from 'react';
import { AlertOctagon, RotateCcw, RefreshCw, ShieldAlert, Home } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('AyurEval Uncaught Render Exception:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="my-6 p-6 sm:p-8 rounded-3xl bg-rose-50/80 border border-rose-200 text-rose-950 shadow-xs">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-rose-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
              <ShieldAlert className="w-5 h-5" />
            </div>

            <div className="space-y-2 flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-rose-200 text-rose-800">
                  Render Recovery Boundary
                </span>
                <span className="text-xs text-rose-600 font-medium">AyurEval Core UI Guard</span>
              </div>

              <h3 className="text-base font-bold text-rose-950">
                {this.props.title || 'Component Rendering Interrupted'}
              </h3>

              <p className="text-xs text-rose-800 leading-relaxed max-w-2xl">
                An unexpected state or rendering exception occurred in this audit view. Your
                underlying session data and backend services remain safe and healthy.
              </p>

              {this.state.error && (
                <div className="mt-3 p-3 rounded-xl bg-white/80 border border-rose-200 font-mono text-[11px] text-rose-900 overflow-x-auto max-w-full">
                  {this.state.error.toString()}
                </div>
              )}

              <div className="pt-3 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-800 hover:bg-rose-900 active:bg-rose-950 text-white font-semibold text-xs transition-colors shadow-2xs"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reload Audit Component</span>
                </button>

                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-rose-300 bg-white hover:bg-rose-100/50 text-rose-900 font-semibold text-xs transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh Page</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
