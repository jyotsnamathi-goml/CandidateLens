import React from 'react';
import { CheckCircle2, ShieldCheck } from 'lucide-react';

export const AssessCompleted: React.FC = () => {
  return (
    <div className="max-w-md mx-auto py-20 px-4 text-center space-y-6">
      <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/10">
        <CheckCircle2 className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Assessment Completed!</h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          Thank you for completing the practical assessment. Your responses have been securely submitted
          for single-pass readiness evaluation.
        </p>
      </div>

      <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-xs text-slate-400 space-y-2 text-left">
        <span className="font-semibold text-slate-300 block">Next Steps:</span>
        <p>
          The hiring team will review your explainable readiness report ahead of Round 1 technical interviews.
          You may now close this window.
        </p>
      </div>
    </div>
  );
};
