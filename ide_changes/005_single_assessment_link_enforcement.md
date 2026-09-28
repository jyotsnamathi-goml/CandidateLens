# IDE Changes: 005 - Single Assessment Link Enforcement

## Summary
- Enforced strictly one persistent assessment session and link per candidate:
  - In `backend/app/routers/assessment.py`, updated `create_assessment_link` to check for any existing session for the candidate. If a session already exists, it immediately returns the candidate's single stable link without invoking `generate_question_plan` again or generating duplicate sessions.
  - Added `get_assessment_link` endpoint (`GET /api/v1/candidates/{candidate_id}/assessment-link`) to retrieve the candidate's active link idempotently.
  - Added `resolve_assessment_session` helper supporting lookups by session `token_jti`, `candidate_id`, and signed tokens.
  - Added `assessment_link` field to `CandidateFullResultOut` schema and populated it in `backend/app/routers/results.py`.
  - In `backend/app/services/evaluation.py`, updated session selection to prioritize sessions with recorded turns so evaluations are never blocked by stale empty sessions.
  - In `frontend/src/pages/CandidateReport.tsx`, updated UI to display the single persistent link with a one-click copy button, preventing accidental regeneration.
- Cleaned up redundant duplicate empty sessions in the database, retaining the active session and completed submission for candidate `jyotsan` (`c_4f0a2996bea2`).
- All 24 unit and integration tests passing.
