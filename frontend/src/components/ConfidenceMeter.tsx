import React from 'react';
import { HelpCircle } from 'lucide-react';
import { ConfidenceLevel } from '../api/types';

interface Props {
  confidence: ConfidenceLevel;
  reason?: string;
  showReason?: boolean;
}

export const ConfidenceMeter: React.FC<Props> = ({ confidence, reason, showReason = true }) => {
  const levels: Record<ConfidenceLevel, { count: number; color: string; label: string }> = {
    Low: { count: 1, color: 'bg-rose-400', label: 'Low Confidence' },
    Medium: { count: 2, color: 'bg-amber-400', label: 'Medium Confidence' },
    High: { count: 3, color: 'bg-emerald-400', label: 'High Confidence' },
  };

  const current = levels[confidence] || levels.Medium;

  return (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-2">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Confidence</span>
        <div className="flex items-center space-x-1">
          {[1, 2, 3].map((dot) => (
            <div
              key={dot}
              className={`w-2.5 h-2.5 rounded-full transition-all ${
                dot <= current.count ? `${current.color} shadow-sm` : 'bg-slate-700'
              }`}
            />
          ))}
        </div>
        <span className="text-xs font-medium text-slate-300">({confidence})</span>
      </div>

      {showReason && reason && (
        <p className="text-xs text-slate-400 leading-relaxed bg-slate-800/40 p-2 rounded border border-slate-700/50">
          {reason}
        </p>
      )}
    </div>
  );
};
