export type ReadinessBand = 'Strong Readiness' | 'Moderate Readiness' | 'Needs Verification';
export type ConfidenceLevel = 'High' | 'Medium' | 'Low';
export type SufficiencyLevel = 'rich' | 'partial' | 'sparse';

export interface JDCompetency {
  name: string;
  description: string;
  rank: number;
  importance: 'critical' | 'important' | 'nice_to_have';
}

export interface Role {
  role_id: string;
  title: string;
  jd_text: string;
  competencies: JDCompetency[];
  role_family: string;
  created_at: string;
}

export interface CandidateSummary {
  candidate_id: string;
  display_name: string;
  status: string;
  band?: ReadinessBand;
  confidence?: ConfidenceLevel;
  score?: number;
  sufficiency?: SufficiencyLevel;
  created_at: string;
}

export interface IngestionStep {
  step: string;
  status: 'pending' | 'in_progress' | 'success' | 'warning' | 'failed';
  detail: string;
  timestamp: string;
}

export interface EvidenceItem {
  evidence_id: string;
  type: string;
  title: string;
  technologies: string[];
  role?: string;
  responsibilities: string[];
  date_start?: string;
  date_end?: string;
  outcomes: string[];
  provenance: 'candidate_provided' | 'public_evidence' | 'model_inference';
  source_url?: string;
  attributes: {
    jd_relevance: number;
    technical_depth: number;
    ownership: number;
    collaboration: number;
    recency: number;
    evidence_strength: number;
  };
}

export interface FlagItem {
  type: 'potential_mismatch' | 'claim_scope_gap' | 'insufficient_evidence';
  severity: 'low' | 'medium' | 'high';
  public_evidence?: string;
  candidate_statement?: string;
  refs: string[];
  action_text: string;
}

export interface FindingItem {
  text: string;
  refs: string[];
}

export interface DimensionScore {
  score: number;
  quote: string;
}

export interface QuestionEvaluation {
  question_id: string;
  technical_correctness: DimensionScore;
  technical_depth: DimensionScore;
  mechanism: DimensionScore;
  trade_offs: DimensionScore;
  problem_solving: DimensionScore;
  communication: DimensionScore;
  specificity: DimensionScore;
  competency?: string;
}

export interface ScoreBreakdownItem {
  name: string;
  label: string;
  weight: number;
  score: number;
  weighted_score: number;
  inputs: Record<string, any>;
  source_description: string;
}

export interface TimelineObservation {
  observation: string;
  evidence_refs: string[];
  trend_type: 'complexity' | 'consistency' | 'recency' | 'collaboration';
}

export interface ReadinessReport {
  candidate_id: string;
  role_id: string;
  role_title: string;
  display_name: string;
  band: ReadinessBand;
  confidence: ConfidenceLevel;
  confidence_reason: string;
  score: number;
  disclaimer: string;
  component_breakdown: ScoreBreakdownItem[];
  sufficiency: SufficiencyLevel;
  sufficiency_impact: string;
  strengths: FindingItem[];
  gaps?: FindingItem[];
  verification_points: FindingItem[];
  flags: FlagItem[];
  timeline_observations: TimelineObservation[];
  evidence_items: EvidenceItem[];
  assessment_analysis: QuestionEvaluation[];
  interview_probes: string[];
  notes: Array<{ author: string; text: string; is_override: boolean; created_at: string }>;
  created_at: string;
}

export interface CandidateResultResponse {
  candidate_id: string;
  role_id: string;
  status: string;
  assessment_link?: string;
  report?: ReadinessReport;
  scoring_inputs_hash?: string;
}

export interface AssessmentSession {
  session_id: string;
  candidate_name: string;
  role_title: string;
  state: string;
  total_planned: number;
  current_turn: number;
  max_turns: number;
  question?: {
    question_id: string;
    kind: string;
    competency?: string;
    text: string;
    follow_up_if_vague?: string;
  };
  is_followup: boolean;
  time_remaining_seconds: number;
}

export interface CostSummary {
  total_cost_usd: number;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  avg_cost_per_candidate_usd: number;
  projected_100_candidates_usd: number;
  calls_by_stage: Record<string, number>;
  cost_by_model: Record<string, number>;
  recent_calls: Array<{
    call_id: string;
    candidate_id?: string;
    stage: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    latency_ms: number;
    est_cost_usd: number;
    ok: boolean;
    mock: boolean;
    created_at: string;
  }>;
}
