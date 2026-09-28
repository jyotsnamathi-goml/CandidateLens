import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Link as LinkIcon,
  RefreshCw,
  Trash2,
  ChevronRight,
  Shield,
  Clock,
  Copy,
  Check,
  ExternalLink,
  Target,
  FileCheck,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../api/client';
import { CandidateResultResponse } from '../api/types';
import { BandBadge } from '../components/BandBadge';
import { ConfidenceMeter } from '../components/ConfidenceMeter';
import { ScoreBreakdown } from '../components/ScoreBreakdown';
import { EvidenceCard } from '../components/EvidenceCard';
import { FlagCard } from '../components/FlagCard';
import { TimelineView } from '../components/TimelineView';
import { AssessmentAnalysis } from '../components/AssessmentAnalysis';
import { InterviewProbes } from '../components/InterviewProbes';
import { NotesSection } from '../components/NotesSection';

export const CandidateReport: React.FC = () => {
  const { candidateId } = useParams<{ candidateId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [assessmentLink, setAssessmentLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery<CandidateResultResponse>({
    queryKey: ['candidateResult', candidateId],
    queryFn: () => api.getCandidateResult(candidateId!),
    enabled: !!candidateId,
    refetchInterval: (query) => {
      // Auto refetch if still evaluating or in assessment
      const status = query.state.data?.status;
      return status === 'EVALUATING' || status === 'IN_ASSESSMENT' ? 3000 : false;
    },
  });

  const generateLinkMutation = useMutation({
    mutationFn: () => api.createAssessmentLink(candidateId!),
    onSuccess: (res) => {
      setAssessmentLink(res.link);
      navigator.clipboard.writeText(res.link);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    },
    onError: (err: any) => {
      alert(err.message || 'Failed to generate assessment link.');
    },
  });

  const rerunEvalMutation = useMutation({
    mutationFn: () => api.rerunEvaluation(candidateId!),
    onSuccess: () => {
      setActionMsg('Evaluation re-run scheduled. Refreshing results...');
      setTimeout(() => setActionMsg(null), 4000);
      refetch();
    },
  });

  const deleteCandidateMutation = useMutation({
    mutationFn: () => api.deleteCandidate(candidateId!),
    onSuccess: () => {
      alert('Candidate data purged.');
      navigate('/roles');
    },
  });

  if (isLoading) {
    return <div className="max-w-7xl mx-auto p-8 animate-pulse text-slate-500">Loading candidate signal...</div>;
  }

  const report = data?.report;
  const status = data?.status || 'READY';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb & Action Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Link to="/roles" className="hover:text-emerald-400 transition-colors">Roles</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link to={`/roles/${data?.role_id}`} className="hover:text-emerald-400 transition-colors">
            {report?.role_title || 'Role'}
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-slate-200 font-medium">{report?.display_name || 'Candidate'}</span>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => generateLinkMutation.mutate()}
            disabled={generateLinkMutation.isPending}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-semibold transition-colors"
          >
            <LinkIcon className="w-3.5 h-3.5" />
            <span>{copied ? 'Link Copied!' : 'Assessment Link'}</span>
          </button>

          <button
            onClick={() => rerunEvalMutation.mutate()}
            disabled={rerunEvalMutation.isPending}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${rerunEvalMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Re-run Evaluation</span>
          </button>

          <button
            onClick={() => {
              if (confirm('Permanently purge this candidate and all artifacts?')) {
                deleteCandidateMutation.mutate();
              }
            }}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 text-xs font-semibold transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Purge Data</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs">
          {actionMsg}
        </div>
      )}

      {/* Generated Link Alert Banner */}
      {assessmentLink && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Check className="w-4 h-4 flex-shrink-0" />
            <span className="font-semibold">Candidate Assessment Link Generated & Copied to Clipboard:</span>
            <code className="bg-slate-900 px-2 py-0.5 rounded text-slate-300 font-mono select-all">
              {assessmentLink}
            </code>
          </div>
          <a
            href={assessmentLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-400 hover:underline flex items-center space-x-1 font-semibold"
          >
            <span>Open Candidate View</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      )}

      {/* In-Progress or Pending Assessment Notice */}
      {status !== 'COMPLETED' && (
        <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mx-auto">
            <Clock className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-xl font-heading font-bold text-white">
            {status === 'READY'
              ? 'Candidate Ingestion Ready — Assessment Not Completed'
              : status === 'IN_ASSESSMENT'
              ? 'Candidate Assessment in Progress...'
              : status === 'EVALUATING'
              ? 'Evaluating Assessment Answers...'
              : 'Assessment Pending'}
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Generate an assessment link to invite the candidate to complete the 6-question practical assessment.
            Once completed, Call 3 will evaluate all answers concurrently and generate the full readiness signal.
          </p>
          <button
            onClick={() => generateLinkMutation.mutate()}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20"
          >
            <LinkIcon className="w-4 h-4" />
            <span>Generate & Copy Assessment Link</span>
          </button>
        </div>
      )}

      {/* Hero Signal Header */}
      {report && (
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <h1 className="text-3xl sm:text-4xl font-heading font-bold text-white tracking-tight">
                  {report.display_name}
                </h1>
                <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                  {report.role_title}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <BandBadge band={report.band} size="lg" />
                <div className="h-6 w-px bg-slate-800 mx-1 hidden sm:block" />
                <ConfidenceMeter confidence={report.confidence} showReason={false} />
                <div className="h-6 w-px bg-slate-800 mx-1 hidden sm:block" />
                <div className="flex items-baseline space-x-1.5 bg-slate-800/60 px-3 py-1.5 rounded-xl border border-slate-700">
                  <span className="text-xs uppercase font-mono text-slate-400">Readiness Score:</span>
                  <span className="text-xl font-heading font-bold text-emerald-400">{report.score.toFixed(1)}</span>
                  <span className="text-xs text-slate-500">/ 100</span>
                </div>
              </div>
            </div>

            {/* Disclaimer & Hash */}
            <div className="lg:max-w-xs text-right space-y-2">
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-[11px] text-slate-400 text-left">
                <Shield className="w-3.5 h-3.5 text-emerald-400 inline mr-1 -mt-0.5" />
                <span className="font-semibold text-slate-300">Disclaimer:</span> {report.disclaimer}
              </div>
              {data?.scoring_inputs_hash && (
                <div className="text-[10px] font-mono text-slate-500" title="Verifiable deterministic scoring inputs hash">
                  Input Hash: {data.scoring_inputs_hash.slice(0, 16)}...
                </div>
              )}
            </div>
          </div>

          {/* Plain-Language Confidence & Sufficiency Banner */}
          <div className="p-4 bg-slate-900/40 rounded-2xl border border-slate-800/80 space-y-2 text-xs">
            <p className="text-slate-300 leading-relaxed font-medium">
              <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[11px] mr-2">
                Evaluation Rationale:
              </span>
              {report.confidence_reason}
            </p>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              <span className="text-slate-300 font-semibold uppercase tracking-wider mr-2">
                Footprint Sufficiency ({report.sufficiency.toUpperCase()}):
              </span>
              {report.sufficiency_impact}
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: Score Breakdown + Evidence */}
      {report && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Score Breakdown (7 cols) */}
          <div className="lg:col-span-7 space-y-8">
            <ScoreBreakdown items={report.component_breakdown} totalScore={report.score} />

            {/* Strengths & Gaps */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
              <h2 className="text-lg font-heading font-semibold text-white">Demonstrated Strengths</h2>
              <div className="space-y-3">
                {report.strengths.map((str, i) => (
                  <div key={i} className="flex items-start space-x-3 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/60">
                    <FileCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <p className="text-xs text-slate-200 leading-relaxed">{str.text}</p>
                      {str.refs.length > 0 && (
                        <div className="flex items-center space-x-1 font-mono text-[10px] text-slate-500">
                          <span>Grounding Refs:</span>
                          {str.refs.map((r) => (
                            <span key={r} className="bg-slate-800 px-1 py-0.2 rounded text-slate-400">{r}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {report.gaps && report.gaps.length > 0 && (
                <>
                  <h3 className="text-sm font-heading font-semibold text-slate-300 pt-3">Identified Competency Gaps</h3>
                  <div className="space-y-2">
                    {report.gaps.map((gap, i) => (
                      <div key={i} className="flex items-start space-x-3 p-3 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-300">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <span>{gap.text}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Assessment Analysis with Quotes */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-lg font-heading font-semibold text-white">Practical Assessment Analysis</h2>
              <p className="text-xs text-slate-400">
                Detailed 7-dimension scoring for each question with verbatim candidate quotes supporting levels above 2.
              </p>
              <AssessmentAnalysis evaluations={report.assessment_analysis} />
            </div>
          </div>

          {/* Right Column: Evidence, Flags, Timeline, Probes (5 cols) */}
          <div className="lg:col-span-5 space-y-8">
            {/* Areas to Verify (Flags) */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-heading font-semibold text-white">Areas to Verify</h2>
                <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  {report.flags?.length || 0} flagged
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Potential claim-scope gaps or artifact mismatches for interviewer exploration. Worded neutrally.
              </p>

              {report.flags && report.flags.length > 0 ? (
                <div className="space-y-3">
                  {report.flags.map((flag, idx) => (
                    <FlagCard key={idx} flag={flag} />
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl text-xs text-emerald-400 flex items-center space-x-2">
                  <Check className="w-4 h-4 flex-shrink-0" />
                  <span>No unresolved claim gaps or evidence mismatches identified.</span>
                </div>
              )}
            </div>

            {/* Targeted Interview Probes */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-heading font-semibold text-white">Round 1 Interview Focus</h2>
              </div>
              <p className="text-xs text-slate-400">
                Generated practical probes targeting areas of highest verification value.
              </p>
              <InterviewProbes probes={report.interview_probes} />
            </div>

            {/* Evidence Timeline */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-lg font-heading font-semibold text-white">Progression Timeline</h2>
              <TimelineView observations={report.timeline_observations} />
            </div>

            {/* Supporting Evidence Items */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-lg font-heading font-semibold text-white">
                Supporting Evidence ({report.evidence_items?.length || 0})
              </h2>
              <div className="space-y-3">
                {report.evidence_items?.map((ev) => (
                  <EvidenceCard key={ev.evidence_id} item={ev} />
                ))}
              </div>
            </div>

            {/* HR Notes / Override */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-lg font-heading font-semibold text-white">Interviewer Notes & Override</h2>
              <NotesSection candidateId={candidateId!} notes={report.notes} onNoteAdded={refetch} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
