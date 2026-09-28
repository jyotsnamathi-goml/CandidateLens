import React from 'react';
import { Clock, TrendingUp, Users, CheckCircle } from 'lucide-react';
import { TimelineObservation } from '../api/types';

interface Props {
  observations: TimelineObservation[];
}

export const TimelineView: React.FC<Props> = ({ observations }) => {
  const icons = {
    complexity: TrendingUp,
    consistency: CheckCircle,
    recency: Clock,
    collaboration: Users,
  };

  const badgeColors = {
    complexity: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    consistency: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    recency: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    collaboration: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  };

  if (!observations || observations.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-4 italic">
        No dated evidence items available to construct timeline observations.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {observations.map((obs, idx) => {
        const Icon = icons[obs.trend_type] || Clock;
        const color = badgeColors[obs.trend_type] || badgeColors.recency;

        return (
          <div key={idx} className="flex items-start space-x-3.5 group">
            <div className={`p-2 rounded-xl border flex-shrink-0 ${color}`}>
              <Icon className="w-4 h-4" />
            </div>

            <div className="flex-1 bg-slate-800/30 p-3.5 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${color}`}>
                  {obs.trend_type}
                </span>

                {obs.evidence_refs && obs.evidence_refs.length > 0 && (
                  <div className="flex items-center space-x-1">
                    {obs.evidence_refs.map((ref) => (
                      <span
                        key={ref}
                        className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700/60"
                      >
                        {ref}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <p className="text-xs text-slate-200 leading-relaxed">{obs.observation}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
