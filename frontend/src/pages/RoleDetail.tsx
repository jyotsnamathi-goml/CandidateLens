import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, UserPlus, Filter, ArrowRight, ShieldCheck, CheckCircle2, ChevronRight, Edit3 } from 'lucide-react';
import { api } from '../api/client';
import { Role, CandidateSummary } from '../api/types';
import { BandBadge } from '../components/BandBadge';
import { ConfidenceMeter } from '../components/ConfidenceMeter';

export const RoleDetail: React.FC = () => {
  const { roleId } = useParams<{ roleId: string }>();
  const [filterBand, setFilterBand] = useState<string>('all');

  const { data: role, isLoading: roleLoading } = useQuery<Role>({
    queryKey: ['role', roleId],
    queryFn: () => api.getRole(roleId!),
    enabled: !!roleId,
  });

  const { data: candidates, isLoading: candidatesLoading } = useQuery<CandidateSummary[]>({
    queryKey: ['roleCandidates', roleId],
    queryFn: () => api.getRoleCandidates(roleId!),
    enabled: !!roleId,
    refetchInterval: 5000, // Poll for ingesting candidates
  });

  const filteredCandidates = candidates?.filter((c) => {
    if (filterBand === 'all') return true;
    return c.band === filterBand;
  });

  if (roleLoading) {
    return <div className="max-w-7xl mx-auto p-8 animate-pulse text-slate-500">Loading role details...</div>;
  }

  if (!role) {
    return <div className="max-w-7xl mx-auto p-8 text-rose-400">Role not found.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Link to="/roles" className="hover:text-emerald-400 transition-colors">Roles</Link>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-slate-200">{role.title}</span>
          </div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-heading font-bold text-white tracking-tight">{role.title}</h1>
            <span className="text-xs uppercase font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              {role.role_family}
            </span>
          </div>
        </div>

        <Link
          to={`/roles/${role.role_id}/add-candidate`}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all self-start md:self-auto"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add Candidate</span>
        </Link>
      </div>

      {/* Competencies Section */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-heading font-semibold text-white">Extracted JD Competencies</h2>
            <p className="text-xs text-slate-400">
              Derived from job description via amortized small-model parser. Used for relevance matching and assessment.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {role.competencies?.map((comp, idx) => (
            <div
              key={idx}
              className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/60 flex items-start space-x-3"
            >
              <div className="w-6 h-6 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold font-mono flex-shrink-0 mt-0.5">
                {comp.rank}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-xs font-semibold text-slate-200 truncate">{comp.name}</h4>
                  <span
                    className={`text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.2 rounded border ${
                      comp.importance === 'critical'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-slate-700 text-slate-300 border-slate-600'
                    }`}
                  >
                    {comp.importance}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{comp.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Candidates Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-heading font-semibold text-white">Candidate Readiness Signals</h2>
            <p className="text-xs text-slate-400">
              Objective pre-Round 1 evaluation based on grounded evidence and practical assessment.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={filterBand}
              onChange={(e) => setFilterBand(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Readiness Bands</option>
              <option value="Strong Readiness">Strong Readiness</option>
              <option value="Moderate Readiness">Moderate Readiness</option>
              <option value="Needs Verification">Needs Verification</option>
            </select>
          </div>
        </div>

        {candidatesLoading ? (
          <div className="p-8 text-center text-xs text-slate-500 animate-pulse">Loading candidates...</div>
        ) : filteredCandidates && filteredCandidates.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-900/40 text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  <th className="py-3.5 px-6">Candidate Name</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6">Readiness Band</th>
                  <th className="py-3.5 px-6">Confidence</th>
                  <th className="py-3.5 px-6">Score</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredCandidates.map((c) => (
                  <tr key={c.candidate_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-6 font-semibold text-slate-200">
                      <Link
                        to={`/candidates/${c.candidate_id}`}
                        className="hover:text-emerald-400 transition-colors flex items-center space-x-2"
                      >
                        <span>{c.display_name}</span>
                        {c.sufficiency === 'sparse' && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            Sparse Footprint
                          </span>
                        )}
                      </Link>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] uppercase font-mono font-semibold ${
                          c.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : c.status === 'INGESTING'
                            ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse'
                            : c.status === 'IN_ASSESSMENT'
                            ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      {c.band ? <BandBadge band={c.band} size="sm" /> : <span className="text-slate-500">—</span>}
                    </td>
                    <td className="py-4 px-6">
                      {c.confidence ? (
                        <ConfidenceMeter confidence={c.confidence} showReason={false} />
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      {c.score !== undefined && c.score !== null ? (
                        <span className="font-heading font-bold text-sm text-slate-200">
                          {c.score.toFixed(1)} <span className="text-slate-500 text-[10px]">/ 100</span>
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <Link
                        to={`/candidates/${c.candidate_id}`}
                        className="inline-flex items-center space-x-1 text-emerald-400 hover:text-emerald-300 font-semibold"
                      >
                        <span>View Signal</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-xs text-slate-500 space-y-3">
            <p>No candidates added to this role yet.</p>
            <Link
              to={`/roles/${role.role_id}/add-candidate`}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Add Candidate</span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
