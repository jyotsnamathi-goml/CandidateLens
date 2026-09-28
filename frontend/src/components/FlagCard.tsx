import React from 'react';
import { AlertCircle, HelpCircle, ArrowRight } from 'lucide-react';
import { FlagItem } from '../api/types';

interface Props {
  flag: FlagItem;
}

export const FlagCard: React.FC<Props> = ({ flag }) => {
  const typeConfig = {
    potential_mismatch: {
      label: 'Potential Mismatch',
      color: 'text-amber-400',
      badge: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    },
    claim_scope_gap: {
      label: 'Claim-Scope Gap',
      color: 'text-sky-400',
      badge: 'bg-sky-500/10 border-sky-500/30 text-sky-300',
    },
    insufficient_evidence: {
      label: 'Insufficient Evidence',
      color: 'text-slate-400',
      badge: 'bg-slate-500/10 border-slate-500/30 text-slate-300',
    },
  };

  const conf = typeConfig[flag.type] || typeConfig.potential_mismatch;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${conf.badge}`}>
            {conf.label}
          </span>
          <span className="text-xs uppercase font-mono text-slate-500 tracking-wider">
            Severity: {flag.severity}
          </span>
        </div>
        <div className="flex items-center space-x-1 text-slate-500 text-xs font-mono">
          <span>Refs:</span>
          {flag.refs.map((r) => (
            <span key={r} className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
              {r}
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {flag.candidate_statement && (
          <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/50">
            <span className="font-semibold text-slate-400 block mb-1">Candidate Statement / Claim</span>
            <p className="text-slate-200 italic">"{flag.candidate_statement}"</p>
          </div>
        )}

        {flag.public_evidence && (
          <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/50">
            <span className="font-semibold text-slate-400 block mb-1">Public Evidence Artifact</span>
            <p className="text-slate-200">{flag.public_evidence}</p>
          </div>
        )}
      </div>

      <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3 text-xs flex items-start space-x-2.5">
        <ArrowRight className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px] block mb-0.5">
            Recommended Interviewer Action
          </span>
          <p className="text-slate-200">{flag.action_text}</p>
        </div>
      </div>
    </div>
  );
};
