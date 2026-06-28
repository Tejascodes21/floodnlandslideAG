import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught EOC interface error:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="glass-panel p-6 rounded-2xl border border-red-500/20 bg-red-950/10 flex flex-col items-center justify-center text-center gap-4 min-h-[220px]">
          <div className="p-3 rounded-full bg-red-500/10 border border-red-500/30 text-red-500 pulse-threat">
            <AlertOctagon className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">Component Rendering Failed</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto leading-relaxed">
              {this.state.error?.message || "An unexpected error occurred in this workspace frame."}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] font-bold text-slate-300 hover:text-white rounded-lg transition-all"
          >
            <RefreshCw className="w-3 h-3" />
            Reload Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
