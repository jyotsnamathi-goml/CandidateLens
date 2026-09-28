import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Upload, Github, Globe, Shield, ArrowRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { IngestionStep } from '../api/types';

export const AddCandidate: React.FC = () => {
  const { roleId } = useParams<{ roleId: string }>();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState('');
  const [githubUsername, setGithubUsername] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Ingestion polling state
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [ingestionStatus, setIngestionStatus] = useState<string | null>(null);
  const [ingestionSteps, setIngestionSteps] = useState<IngestionStep[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeFile) {
      setError('Please select a resume file (PDF, DOCX, or TXT).');
      return;
    }
    if (!consent) {
      setError('Candidate consent is required to proceed.');
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('display_name', displayName.trim());
      formData.append('consent', 'true');
      if (githubUsername.trim()) {
        formData.append('github_username', githubUsername.trim());
      }
      if (portfolioUrl.trim()) {
        formData.append('portfolio_url', portfolioUrl.trim());
      }
      formData.append('resume', resumeFile);

      const res = await api.createCandidate(roleId!, formData);
      setCandidateId(res.candidate_id);
      setIngestionStatus('INGESTING');
    } catch (err: any) {
      setError(err.message || 'Failed to register candidate.');
      setSubmitting(false);
    }
  };

  // Poll ingestion status every 2 seconds
  useEffect(() => {
    if (!candidateId || ingestionStatus === 'READY' || ingestionStatus === 'FAILED') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const data = await api.getIngestionStatus(candidateId);
        setIngestionStatus(data.status);
        setIngestionSteps(data.steps || []);

        if (data.status === 'READY') {
          clearInterval(interval);
          setTimeout(() => {
            navigate(`/candidates/${candidateId}`);
          }, 1500);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [candidateId, ingestionStatus, navigate]);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Add Candidate for Screening</h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload candidate materials to extract evidence and schedule an objective readiness assessment.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {error}
          </div>
        )}

        {/* Ingestion Progress View */}
        {candidateId ? (
          <div className="space-y-6 py-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto animate-pulse">
              <Clock className="w-8 h-8" />
            </div>

            <div>
              <h2 className="text-lg font-heading font-bold text-white">
                {ingestionStatus === 'READY' ? 'Ingestion Complete!' : 'Extracting Candidate Evidence...'}
              </h2>
              <p className="text-xs text-slate-400">
                Running Call 1 (Extraction) and deterministic relevance analysis in the background.
              </p>
            </div>

            <div className="max-w-md mx-auto text-left space-y-2 bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs">
              {ingestionSteps.map((step, idx) => (
                <div key={idx} className="flex items-center space-x-2.5">
                  {step.status === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  ) : step.status === 'in_progress' ? (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin flex-shrink-0" />
                  ) : (
                    <Clock className="w-4 h-4 text-slate-600 flex-shrink-0" />
                  )}
                  <span className="font-mono text-slate-300 capitalize">{step.step.replace('_', ' ')}</span>
                  {step.detail && <span className="text-[11px] text-slate-500 truncate">- {step.detail}</span>}
                </div>
              ))}
            </div>

            {ingestionStatus === 'READY' && (
              <div className="pt-2">
                <Link
                  to={`/candidates/${candidateId}`}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all"
                >
                  <span>Proceed to Candidate Signal</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            )}
          </div>
        ) : (
          /* Form View */
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Candidate Full Name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g. Alex Chen"
                className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                  <Github className="w-3.5 h-3.5 text-slate-400" />
                  <span>GitHub Username or URL</span>
                </label>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  placeholder="e.g. alexchen"
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                  <Globe className="w-3.5 h-3.5 text-slate-400" />
                  <span>Portfolio URL (Max 1)</span>
                </label>
                <input
                  type="url"
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  placeholder="https://alexchen.dev"
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Resume Upload */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Resume Document (PDF, DOCX, TXT)</label>
              <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-800 hover:border-emerald-500/40 rounded-2xl p-6 cursor-pointer transition-colors bg-slate-950/40">
                <Upload className="w-6 h-6 text-emerald-400 mb-2" />
                <span className="text-xs text-slate-300 font-medium">
                  {resumeFile ? resumeFile.name : 'Click to select or drag and drop resume'}
                </span>
                <span className="text-[10px] text-slate-500 mt-1">25 MB max limit with magic byte verification</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setResumeFile(e.target.files[0]);
                  }}
                  className="hidden"
                />
              </label>
            </div>

            {/* Privacy & Consent Disclaimer */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-start space-x-2.5">
                <Shield className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-slate-400 leading-relaxed">
                  <span className="text-slate-200 font-semibold block mb-0.5">Privacy Notice & Scope of Data Collection</span>
                  CandidateLens fetches public metadata strictly for the provided GitHub handle and analyzes the single portfolio link.
                  Protected demographic attributes are purged before LLM processing. All uploaded resumes and analysis artifacts are retained
                  for 90 days and can be purged immediately on demand.
                </div>
              </div>

              <label className="flex items-center space-x-2.5 text-xs text-slate-300 cursor-pointer pt-2 border-t border-slate-800 select-none">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-0"
                />
                <span className="font-medium">
                  Candidate has provided explicit consent for resume parsing and public footprint retrieval.
                </span>
              </label>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => navigate(`/roles/${roleId}`)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !consent || !resumeFile || !displayName.trim()}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20 disabled:opacity-50"
              >
                {submitting ? 'Initiating Ingestion...' : 'Register & Start Ingestion'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
