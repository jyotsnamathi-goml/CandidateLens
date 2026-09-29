import {
  AssessmentSession,
  CandidateResultResponse,
  CandidateSummary,
  CostSummary,
  EvidenceItem,
  IngestionStep,
  JDCompetency,
  Role,
} from './types';

const BASE_URL = '/api/v1';

export function getAuthToken(): string | null {
  return localStorage.getItem('candidatelens_jwt');
}

export function setAuthToken(token: string) {
  localStorage.setItem('candidatelens_jwt', token);
}

export function removeAuthToken() {
  localStorage.removeItem('candidatelens_jwt');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.error?.message || errorMsg;
    } catch {
      // fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const data = await request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setAuthToken(data.access_token);
    return data;
  },

  // Roles
  getRoles: () => request<Role[]>('/roles'),
  getRole: (roleId: string) => request<Role>(`/roles/${roleId}`),
  createRole: (title: string, jd_text: string, role_family: string) =>
    request<Role>('/roles', {
      method: 'POST',
      body: JSON.stringify({ title, jd_text, role_family }),
    }),
  createRoleUpload: (formData: FormData) =>
    request<Role>('/roles/upload', {
      method: 'POST',
      body: formData,
    }),
  updateCompetencies: (roleId: string, competencies: JDCompetency[]) =>
    request<Role>(`/roles/${roleId}/competencies`, {
      method: 'PATCH',
      body: JSON.stringify({ competencies }),
    }),
  getRoleCandidates: (roleId: string) =>
    request<CandidateSummary[]>(`/roles/${roleId}/results`),

  // Candidates
  createCandidate: (roleId: string, formData: FormData) =>
    request<{ candidate_id: string }>(`/roles/${roleId}/candidates`, {
      method: 'POST',
      body: formData,
    }),
  getCandidate: (candidateId: string) =>
    request<any>(`/candidates/${candidateId}`),
  getIngestionStatus: (candidateId: string) =>
    request<{ status: string; steps: IngestionStep[] }>(`/candidates/${candidateId}/ingestion`),
  getEvidence: (candidateId: string) =>
    request<{ candidate_id: string; evidence: EvidenceItem[]; sufficiency: string }>(`/candidates/${candidateId}/evidence`),
  deleteCandidate: (candidateId: string) =>
    request<{ message: string }>(`/candidates/${candidateId}`, { method: 'DELETE' }),

  // Results & Reports
  getCandidateResult: (candidateId: string) =>
    request<CandidateResultResponse>(`/candidates/${candidateId}/result`),
  rerunEvaluation: (candidateId: string) =>
    request<{ message: string }>(`/candidates/${candidateId}/evaluate`, { method: 'POST' }),
  addNote: (candidateId: string, text: string, is_override: boolean) =>
    request<any>(`/candidates/${candidateId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ text, is_override }),
    }),

  // Assessment Links
  createAssessmentLink: (candidateId: string) =>
    request<{ link: string; token: string; expires_at: string }>(`/candidates/${candidateId}/assessment-link`, {
      method: 'POST',
    }),
  getAssessmentSession: (token: string) =>
    request<AssessmentSession>(`/assessment/${token}`),
  submitAnswer: (token: string, answer_text: string, time_taken_seconds: number, tab_switches: number = 0) =>
    request<any>(`/assessment/${token}/answers`, {
      method: 'POST',
      body: JSON.stringify({ answer_text, time_taken_seconds, tab_switches }),
    }),

  // Admin Costs
  getCosts: () => request<CostSummary>('/admin/costs'),
};
