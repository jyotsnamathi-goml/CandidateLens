import React from 'react';
import { AlertCircle } from 'lucide-react';

export const AssessExpired: React.FC = () => {
  return (
    <div className="max-w-md mx-auto py-20 px-4 text-center space-y-6">
      <div className="w-16 h-16 rounded-3xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
        <AlertCircle className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Assessment Link Expired</h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          This assessment link has expired or has already been submitted.
        </p>
      </div>

      <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-xs text-slate-400 text-left">
        Please contact your recruiter or the technical hiring team if you need a new assessment link generated.
      </div>
    </div>
  );
};
