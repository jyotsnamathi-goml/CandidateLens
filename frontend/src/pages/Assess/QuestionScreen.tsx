import React, { useState, useEffect, useRef } from 'react';
import { Clock, Send, MessageSquare, AlertCircle, ArrowRight, Shield, ShieldAlert, AlertTriangle } from 'lucide-react';
import { AssessmentSession } from '../../api/types';

interface Props {
  session: AssessmentSession;
  onSubmit: (answer: string, secondsTaken: number, tabSwitches: number) => Promise<void>;
  submitting: boolean;
}

export const AssessQuestionScreen: React.FC<Props> = ({ session, onSubmit, submitting }) => {
  const [answer, setAnswer] = useState('');
  const [seconds, setSeconds] = useState(0);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [proctorWarning, setProctorWarning] = useState<string | null>(null);
  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const question = session.question;
  const isFollowup = session.is_followup;
  const questionIndex = session.question_index || 1;
  const totalPlanned = session.total_planned || 6;

  const proctoring = session.proctoring || {
    enabled: true,
    disable_copy_paste: true,
    track_tab_switch: true,
    max_tab_warnings: 3,
  };

  const showWarning = (msg: string) => {
    setProctorWarning(msg);
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
    }
    warningTimerRef.current = setTimeout(() => {
      setProctorWarning(null);
    }, 4500);
  };

  // Question timer
  useEffect(() => {
    setAnswer('');
    setSeconds(0);
    const interval = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [question?.question_id, isFollowup]);

  // Tab switch & visibility change proctoring listener
  useEffect(() => {
    if (!proctoring.enabled || !proctoring.track_tab_switch) {
      return;
    }

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitches((prev) => {
          const next = prev + 1;
          showWarning(`⚠️ Tab switch or focus loss detected (${next}). Please remain on this assessment window.`);
          return next;
        });
      }
    };

    const handleBlur = () => {
      setTabSwitches((prev) => {
        const next = prev + 1;
        showWarning(`⚠️ Window focus lost (${next}). Please stay focused on the assessment tab.`);
        return next;
      });
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
    };
  }, [proctoring.enabled, proctoring.track_tab_switch]);

  const wordCount = answer.trim() ? answer.trim().split(/\s+/).length : 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    onSubmit(answer.trim(), seconds, tabSwitches);
  };

  const handleCopyPasteBlock = (e: React.SyntheticEvent, action: string) => {
    if (proctoring.enabled && proctoring.disable_copy_paste) {
      e.preventDefault();
      showWarning(`⚠️ ${action} is disabled during this proctored assessment. Please type your answer directly.`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (proctoring.enabled && proctoring.disable_copy_paste) {
      const isCtrlOrCmd = e.ctrlKey || e.metaKey;
      if (isCtrlOrCmd && ['c', 'v', 'x', 'a', 'insert'].includes(e.key.toLowerCase())) {
        if (['c', 'v', 'x'].includes(e.key.toLowerCase())) {
          e.preventDefault();
          showWarning(`⚠️ Keyboard shortcut (Ctrl/Cmd+${e.key.toUpperCase()}) is disabled for integrity.`);
        }
      }
    }
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
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6 select-none">
      {/* Top Bar: Progress, Proctoring Badge, and Timers */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-200">
            {isFollowup ? (
              <span className="text-amber-400">Follow-up on Question {questionIndex} of {totalPlanned}</span>
            ) : (
              <span>Question {questionIndex} of {totalPlanned}</span>
            )}
          </span>
          <div className="w-28 bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${isFollowup ? 'bg-amber-400' : 'bg-emerald-400'}`}
              style={{ width: `${Math.min(100, (questionIndex / totalPlanned) * 100)}%` }}
            />
          </div>
        </div>

        <div className="flex items-center space-x-3 font-mono text-[11px]">
          {proctoring.enabled && (
            <div className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg border ${tabSwitches > 0 ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' : 'bg-slate-800/80 border-slate-700/60 text-slate-300'}`}>
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Proctored</span>
              {tabSwitches > 0 && <span className="text-amber-400 font-bold ml-1">({tabSwitches} switches)</span>}
            </div>
          )}

          <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Time: {formatTimer(seconds)}</span>
          </div>
        </div>
      </div>

      {/* Proctoring Floating / Inline Banner */}
      {proctorWarning && (
        <div className="p-3.5 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs flex items-center space-x-2.5 shadow-lg animate-pulse">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span className="font-medium">{proctorWarning}</span>
        </div>
      )}

      {/* Question Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-4 shadow-xl select-text">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
            {question.competency || question.kind.replace('_', ' ')}
          </span>
          {isFollowup && (
            <span className="text-[11px] uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
              Deepening Follow-up (No extra question count)
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
            onCopy={(e) => handleCopyPasteBlock(e, 'Copying')}
            onCut={(e) => handleCopyPasteBlock(e, 'Cut')}
            onPaste={(e) => handleCopyPasteBlock(e, 'Pasting')}
            onContextMenu={(e) => {
              if (proctoring.enabled && proctoring.disable_copy_paste) {
                e.preventDefault();
                showWarning('⚠️ Context menu is disabled during assessment.');
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={proctoring.enabled && proctoring.disable_copy_paste
              ? "Type your explanation directly here (Copy/Paste is disabled for integrity)..."
              : "Type your explanation here. You can paste snippets or reference specific architectural tools..."}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-2xl p-4 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 leading-relaxed font-sans select-text"
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
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 cursor-pointer"
          >
            <span>{submitting ? 'Recording...' : 'Save & Continue'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
