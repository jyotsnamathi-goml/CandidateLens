import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DollarSign, Cpu, Layers, Activity, TrendingUp, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';
import { CostSummary } from '../api/types';

export const Costs: React.FC = () => {
  const { data: costs, isLoading } = useQuery<CostSummary>({
    queryKey: ['costs'],
    queryFn: api.getCosts,
  });

  if (isLoading) {
    return <div className="max-w-7xl mx-auto p-8 animate-pulse text-slate-500">Loading cost telemetry...</div>;
  }

  const c = costs || {
    total_cost_usd: 0,
    total_calls: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
    avg_cost_per_candidate_usd: 0.035,
    projected_100_candidates_usd: 3.50,
    calls_by_stage: {},
    cost_by_model: {},
    recent_calls: [],
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-heading font-bold text-white tracking-tight">API Cost & Telemetry</h1>
        <p className="text-sm text-slate-400 mt-1">
          Live monitoring of OpenAI token consumption, per-candidate costs, and architectural budget limits.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-2">
          <div className="flex items-center justify-between text-emerald-400">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">Total Spend Till Now</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-heading font-bold text-white">
            ${c.total_cost_usd.toFixed(4)}
          </div>
          <span className="text-[11px] text-emerald-400 font-medium">Actual OpenAI spend to date</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">Avg Cost / Candidate</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-heading font-bold text-white">
            ${c.avg_cost_per_candidate_usd.toFixed(4)}
          </div>
          <span className="text-[11px] text-emerald-400 font-medium">3 to 5 calls per candidate</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">Projected 100 Cand/Mo</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-heading font-bold text-emerald-400">
            ${c.projected_100_candidates_usd.toFixed(2)}
          </div>
          <span className="text-[11px] text-slate-400">Estimated enterprise cost</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">Total Tokens Logged</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-heading font-bold text-white">
            {(c.total_input_tokens + c.total_output_tokens).toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {c.total_input_tokens.toLocaleString()} in / {c.total_output_tokens.toLocaleString()} out
          </span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">Total Recorded Calls</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-heading font-bold text-white">{c.total_calls}</div>
          <span className="text-[11px] text-slate-400">Total API calls executed</span>
        </div>
      </div>

      {/* Stage Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h2 className="text-base font-heading font-semibold text-white">Calls by Pipeline Stage</h2>
          <div className="space-y-2.5">
            {Object.entries(c.calls_by_stage).length > 0 ? (
              Object.entries(c.calls_by_stage).map(([stage, count]) => (
                <div key={stage} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs">
                  <span className="font-mono text-slate-300">{stage}</span>
                  <span className="font-bold text-emerald-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {count} calls
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic">No stage data recorded yet.</p>
            )}
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h2 className="text-base font-heading font-semibold text-white">Cost by Model Tier</h2>
          <div className="space-y-2.5">
            {Object.entries(c.cost_by_model).length > 0 ? (
              Object.entries(c.cost_by_model).map(([model, cost]) => (
                <div key={model} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs">
                  <span className="font-mono text-slate-300">{model}</span>
                  <span className="font-bold text-white">${cost.toFixed(5)}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic">No model cost data recorded yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent LLM Calls Log */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <h2 className="text-base font-heading font-semibold text-white">Recent LLM Executions</h2>
          <p className="text-xs text-slate-400">
            Structured cost logs. Prompts, resumes, and answers are never stored in telemetry logs.
          </p>
        </div>

        {c.recent_calls && c.recent_calls.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  <th className="py-3 px-6">Call ID</th>
                  <th className="py-3 px-6">Stage</th>
                  <th className="py-3 px-6">Model</th>
                  <th className="py-3 px-6">Tokens (In / Out)</th>
                  <th className="py-3 px-6">Latency</th>
                  <th className="py-3 px-6">Est. Cost</th>
                  <th className="py-3 px-6">Mode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {c.recent_calls.map((call) => (
                  <tr key={call.call_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-6 text-slate-400">{call.call_id}</td>
                    <td className="py-3 px-6 text-slate-200">{call.stage}</td>
                    <td className="py-3 px-6 text-slate-400">{call.model}</td>
                    <td className="py-3 px-6 text-slate-300">
                      {call.input_tokens} / {call.output_tokens}
                    </td>
                    <td className="py-3 px-6 text-slate-400">{call.latency_ms} ms</td>
                    <td className="py-3 px-6 text-emerald-400 font-semibold">${call.est_cost_usd.toFixed(5)}</td>
                    <td className="py-3 px-6">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${call.mock ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                        {call.mock ? 'MOCK' : 'LIVE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-500">No calls recorded yet.</div>
        )}
      </div>
    </div>
  );
};
