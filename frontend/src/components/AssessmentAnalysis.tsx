import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Quote } from 'lucide-react';
import { QuestionEvaluation } from '../api/types';

interface Props {
  evaluations: QuestionEvaluation[];
}

export const AssessmentAnalysis: React.FC<Props> = ({ evaluations }) => {
  const [openQ, setOpenQ] = useState<string>(evaluations[0]?.question_id || 'q1');

  const dimensions = [
    { key: 'technical_correctness', label: 'Technical Correctness' },
    { key: 'technical_depth', label: 'Technical Depth' },
    { key: 'mechanism', label: 'Mechanism & Execution' },
    { key: 'trade_offs', label: 'Trade-offs Reasoning' },
    { key: 'problem_solving', label: 'Problem Solving' },
    { key: 'communication', label: 'Communication' },
    { key: 'specificity', label: 'Specificity' },
  ];

  const getScoreBadge = (score: number) => {
    if (score >= 4) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (score === 3) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  };

  return (
    <div className="space-y-4">
      {evaluations.map((q) => {
        const isOpen = openQ === q.question_id;

        return (
          <div
            key={q.question_id}
            className={`rounded-xl border transition-all ${
              isOpen ? 'bg-slate-800/60 border-slate-700' : 'bg-slate-800/20 border-slate-800 hover:bg-slate-800/40'
            }`}
          >
            <button
              onClick={() => setOpenQ(isOpen ? '' : q.question_id)}
              className="w-full px-5 py-4 flex items-center justify-between text-left"
            >
              <div className="flex items-center space-x-3">
                <span className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 font-mono font-bold text-xs text-slate-300 flex items-center justify-center">
                  {q.question_id.toUpperCase()}
                </span>
                <div>
                  <h4 className="font-heading font-semibold text-white text-sm">
                    {q.competency || `Assessment Question ${q.question_id}`}
                  </h4>
                  <p className="text-xs text-slate-400">7-dimension anchored evaluation with verbatim quotes</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </button>

            {isOpen && (
              <div className="px-5 pb-5 pt-2 border-t border-slate-700/60 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {dimensions.map((d) => {
                    const dimData = (q as any)[d.key];
                    if (!dimData) return null;

                    return (
                      <div key={d.key} className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-slate-300">{d.label}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold border ${getScoreBadge(
                              dimData.score
                            )}`}
                          >
                            Level {dimData.score} / 5
                          </span>
                        </div>

                        {dimData.quote && dimData.quote.trim() && (
                          <div className="flex items-start space-x-2 text-[11px] text-slate-400 bg-slate-800/40 p-2 rounded border border-slate-800">
                            <Quote className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            <p className="italic text-slate-300">"{dimData.quote}"</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
