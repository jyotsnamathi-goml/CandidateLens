import React, { useState, useEffect } from 'react';
import { Clock, Send, MessageSquare, AlertCircle, ArrowRight } from 'lucide-react';
import { AssessmentSession } from '../../api/types';

interface Props {
  session: AssessmentSession;
  onSubmit: (answer: string, secondsTaken: number) => Promise<void>;
  submitting: boolean;
}

export const AssessQuestionScreen: React.FC<Props> = ({ session, onSubmit, submitting }) => {
  const [answer, setAnswer] = useState('');
  const [seconds, setSeconds] = useState(0);

  const question = session.question;
  const isFollowup = session.is_followup;

  // Question timer
  useEffect(() => {
    setAnswer('');
    setSeconds(0);
    const interval = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [question?.question_id, isFollowup]);

  const wordCount = answer.trim() ? answer.trim().split(/\s+/).length : 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    onSubmit(answer.trim(), seconds);
  };

  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (!question) {
    return null;
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      {/* Top Bar: Progress and Timers */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-200">
            {isFollowup ? 'Follow-up Question' : `Question ${session.current_turn} of ${session.total_planned}`}
          </span>
          <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-400 h-full transition-all duration-300"
              style={{ width: `${(session.current_turn / session.total_planned) * 100}%` }}
            />
          </div>
        </div>

        <div className="flex items-center space-x-4 font-mono">
          <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Time on question: {formatTimer(seconds)}</span>
          </div>
        </div>
      </div>

      {/* Question Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
            {question.competency || question.kind.replace('_', ' ')}
          </span>
          {isFollowup && (
            <span className="text-[11px] uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
              Deepening Follow-up
            </span>
          )}
        </div>

        <h2 className="text-base sm:text-lg font-heading font-semibold text-white leading-relaxed">
          {question.text}
        </h2>

        <p className="text-xs text-slate-400 italic">
          Tip: Explain your practical reasoning, key trade-offs, and failure considerations. Concrete examples from your projects are welcome.
        </p>
      </div>

      {/* Answer Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Your Technical Response:</span>
            <span className={`font-mono ${wordCount < 40 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {wordCount} words {wordCount < 40 && '(Aim for 40+ words for full credit)'}
            </span>
          </div>

          <textarea
            rows={10}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your explanation here. You can paste snippets or reference specific architectural tools..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-2xl p-4 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 leading-relaxed font-sans"
            required
            autoFocus
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <span className="text-[11px] text-slate-500">
            Answers are auto-saved upon submission.
          </span>

          <button
            type="submit"
            disabled={submitting || !answer.trim()}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            <span>{submitting ? 'Recording...' : 'Save & Continue'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
