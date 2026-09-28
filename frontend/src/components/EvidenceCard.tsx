import React from 'react';
import { ExternalLink, GitBranch, Calendar, ShieldAlert, Cpu } from 'lucide-react';
import { EvidenceItem } from '../api/types';

interface Props {
  item: EvidenceItem;
}

export const EvidenceCard: React.FC<Props> = ({ item }) => {
  const provenanceBadges = {
    public_evidence: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    candidate_provided: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    model_inference: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500 block mb-1">
              ID: {item.evidence_id}
            </span>
            <h3 className="font-heading font-semibold text-white text-base leading-snug">{item.title}</h3>
          </div>
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full border font-medium uppercase tracking-wider text-[10px] flex-shrink-0 ${
              provenanceBadges[item.provenance] || provenanceBadges.candidate_provided
            }`}
          >
            {item.provenance.replace('_', ' ')}
          </span>
        </div>

        {item.role && <p className="text-xs text-emerald-400 font-medium mb-3">{item.role}</p>}

        {/* Technologies */}
        {item.technologies && item.technologies.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {item.technologies.map((t) => (
              <span
                key={t}
                className="text-[11px] bg-slate-800/80 text-slate-300 px-2 py-0.5 rounded border border-slate-700/60 font-mono"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Responsibilities / Details */}
        {item.responsibilities && item.responsibilities.length > 0 && (
          <ul className="text-xs text-slate-400 space-y-1 mb-4 list-disc list-inside">
            {item.responsibilities.slice(0, 3).map((r, i) => (
              <li key={i} className="line-clamp-2">{r}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          {item.date_start && (
            <span className="flex items-center space-x-1 font-mono text-[11px]">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>{item.date_start} — {item.date_end || 'present'}</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1" title="Technical Depth">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold text-slate-300">{(item.attributes.technical_depth * 100).toFixed(0)}%</span>
          </div>

          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 p-1"
              title="Open Source Artifact"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
