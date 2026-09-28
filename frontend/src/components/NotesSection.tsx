import React, { useState } from 'react';
import { Send, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';

interface Props {
  candidateId: string;
  notes: Array<{ author: string; text: string; is_override: boolean; created_at: string }>;
  onNoteAdded: () => void;
}

export const NotesSection: React.FC<Props> = ({ candidateId, notes, onNoteAdded }) => {
  const [text, setText] = useState('');
  const [isOverride, setIsOverride] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    try {
      await api.addNote(candidateId, text.trim(), isOverride);
      setText('');
      setIsOverride(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      onNoteAdded();
    } catch (err: any) {
      alert(err.message || 'Failed to submit note.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {notes && notes.length > 0 && (
        <div className="space-y-3 mb-6">
          {notes.map((n, i) => (
            <div key={i} className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/60 text-xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="font-semibold text-slate-200">
                  {n.author} {n.is_override && <span className="text-amber-400 font-bold ml-1.5">[Override Note]</span>}
                </span>
                <span className="font-mono text-[11px]">{new Date(n.created_at).toLocaleString()}</span>
              </div>
              <p className="text-slate-300 leading-relaxed">{n.text}</p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Add interviewer notes or justification for score/band override..."
          className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          required
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={isOverride}
              onChange={(e) => setIsOverride(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-0"
            />
            <span>Mark as decision override</span>
          </label>

          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors disabled:opacity-50"
          >
            {success ? <CheckCircle2 className="w-4 h-4" /> : <Send className="w-4 h-4" />}
            <span>{success ? 'Saved!' : 'Save Note'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
