import React from 'react';
import { Shield, Clock, FileText, CheckCircle2, ArrowRight } from 'lucide-react';
import { AssessmentSession } from '../../api/types';

interface Props {
  session: AssessmentSession;
  onStart: () => void;
}

export const AssessWelcome: React.FC<Props> = ({ session, onStart }) => {
  return (
    <div className="max-w-2xl mx-auto py-12 px-4 space-y-8">
      <div className="text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 mx-auto">
          <Shield className="w-8 h-8 text-slate-950 stroke-[2.5]" />
        </div>
        <h1 className="text-3xl font-heading font-bold text-white tracking-tight">
          Welcome, {session.candidate_name}
        </h1>
        <p className="text-slate-400 text-sm">
          Technical Readiness Assessment for <span className="text-emerald-400 font-semibold">{session.role_title}</span>
        </p>
      </div>

      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-6">
        <h2 className="text-base font-heading font-semibold text-white">What to Expect</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
              <Clock className="w-4 h-4" />
              <span>~30 Minutes Total</span>
            </div>
            <p className="text-slate-400">
              6 practical scenario questions (4 role scenarios + 2 tailored to your projects).
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
              <FileText className="w-4 h-4" />
              <span>Text-Based Scenarios</span>
            </div>
            <p className="text-slate-400">
              No live camera, no audio, no aggressive surveillance. Explain your design thinking naturally.
            </p>
          </div>
        </div>

        <div className="space-y-2 text-xs text-slate-400 border-t border-slate-800/80 pt-4">
          <h3 className="font-semibold text-slate-200">How Answers Are Evaluated:</h3>
          <ul className="space-y-1.5 list-disc list-inside">
            <li>We evaluate practical mechanism, trade-offs, and concrete technical specificity.</li>
            <li>Generic textbook answers score lower than real-world engineering experiences.</li>
            <li>Take your time to structure your thoughts clearly.</li>
          </ul>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
          <span className="font-semibold text-slate-300 block">Privacy & Data Retention:</span>
          Your responses and assessment data are retained for 90 days for this hiring process and can be deleted
          at any time upon request.
        </div>

        <button
          onClick={onStart}
          className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-emerald-500/20 transition-all"
        >
          <span>Begin Practical Assessment</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
