import React from 'react';
import { Target, HelpCircle } from 'lucide-react';

interface Props {
  probes: string[];
}

export const InterviewProbes: React.FC<Props> = ({ probes }) => {
  if (!probes || probes.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {probes.map((probe, idx) => (
        <div
          key={idx}
          className="flex items-start space-x-3 p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-emerald-500/30 transition-all"
        >
          <div className="w-6 h-6 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-xs font-bold">{idx + 1}</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">{probe}</p>
        </div>
      ))}
    </div>
  );
};
