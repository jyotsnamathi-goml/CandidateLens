import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';
import { ScoreBreakdownItem } from '../api/types';

interface Props {
  items: ScoreBreakdownItem[];
  totalScore: number;
}

export const ScoreBreakdown: React.FC<Props> = ({ items, totalScore }) => {
  const [expanded, setExpanded] = useState<string | null>(null);

  const chartData = items.map((item) => ({
    name: item.label.split(' ')[0],
    fullName: item.label,
    score: item.score,
    weight: item.weight,
    weighted: item.weighted_score,
  }));

  const toggleExpand = (name: string) => {
    setExpanded(expanded === name ? null : name);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h2 className="text-xl font-heading font-semibold text-white">Score Breakdown</h2>
          <p className="text-sm text-slate-400">7 normalized evaluation components (0 to 100)</p>
        </div>
        <div className="flex items-center space-x-3 bg-slate-800/80 px-4 py-2 rounded-xl border border-slate-700">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Overall Score</span>
          <span className="text-2xl font-heading font-bold text-emerald-400">{totalScore.toFixed(1)}</span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
      </div>

      {/* Recharts Bar Visualization */}
      <div className="h-64 my-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
            <XAxis
              dataKey="name"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis stroke="#64748b" fontSize={12} tickLine={false} domain={[0, 100]} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
                      <p className="font-semibold text-white">{data.fullName}</p>
                      <p className="text-emerald-400 font-medium">Component Score: {data.score} / 100</p>
                      <p className="text-slate-400">Assigned Weight: {data.weight}%</p>
                      <p className="text-slate-400">Weighted Points: {data.weighted}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="score" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.score >= 75 ? '#10b981' : entry.score >= 60 ? '#f59e0b' : '#ef4444'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Expandable List */}
      <div className="space-y-3 pt-2">
        {items.map((item) => {
          const isExp = expanded === item.name;
          return (
            <div
              key={item.name}
              className={`rounded-xl border transition-all ${
                isExp ? 'bg-slate-800/70 border-slate-700' : 'bg-slate-800/30 border-slate-800/80 hover:bg-slate-800/50'
              }`}
            >
              <button
                onClick={() => toggleExpand(item.name)}
                className="w-full px-4 py-3 flex items-center justify-between text-left"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-2.5 h-2.5 rounded-full ${
                      item.score >= 75 ? 'bg-emerald-400' : item.score >= 60 ? 'bg-amber-400' : 'bg-rose-400'
                    }`}
                  />
                  <div>
                    <span className="font-medium text-slate-200 text-sm">{item.label}</span>
                    <span className="text-xs text-slate-500 ml-2">({item.weight}% weight)</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="font-semibold text-slate-200 text-sm">{item.score.toFixed(1)}</span>
                    <span className="text-xs text-slate-500 ml-1">/ 100</span>
                  </div>
                  {isExp ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </div>
              </button>

              {isExp && (
                <div className="px-4 pb-4 pt-2 border-t border-slate-700/60 text-xs space-y-2 text-slate-300">
                  <div className="flex items-start space-x-2 text-slate-400">
                    <Info className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <span>{item.source_description}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/40 mt-2">
                    <div>
                      <span className="text-slate-500 block">Weighted Contribution:</span>
                      <span className="font-semibold text-emerald-400">{item.weighted_score.toFixed(2)} pts</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Assigned Weight:</span>
                      <span className="font-semibold text-slate-300">{item.weight}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
