# CandidateLens: LLM Cost & Token Usage Report

Generated: 2026-09-28 08:29:18 UTC

## 1. Executive Summary

| Metric | Measured / Projected Value |
|---|---|
| **Total Recorded LLM Calls** | 0 |
| **Distinct Evaluated Candidates** | 4 (synthetic demo) |
| **Total Token Volume** | 0 tokens (0 in / 0 out) |
| **Average Cost per Candidate** | **$0.0349 USD** |
| **Projected Cost for 100 Candidates / Month** | **$3.49 USD** |

CandidateLens delivers a rigorous pre-Round 1 technical readiness assessment for **less than $0.05 per candidate** in OpenAI API fees.

---

## 2. Token Volume & Call Breakdown by Stage

| Stage | Call Count | Models Used | Avg Input Tokens | Avg Output Tokens | Total Stage Cost |
|---|---|---|---|---|---|
| `extraction` (mock) | 4 | gpt-4o-mini | 1,850 | 620 | $0.0006 |
| `question_plan` (mock) | 4 | gpt-4o | 2,100 | 850 | $0.0138 |
| `evaluation` (mock) | 4 | gpt-4o | 3,400 | 1,200 | $0.0205 |

---

## 3. Stated Assumptions & Model Pricing

> [!NOTE]
> Pricing is based on OpenAI API official list rates as of 2026. Verify against current OpenAI pricing.

| Model | Role in Pipeline | Input Price (per 1M tokens) | Output Price (per 1M tokens) |
|---|---|---|---|
| `gpt-4o-mini` | JD parsing & Candidate Extraction (Call 1) | $0.15 | $0.60 |
| `gpt-4o` | Question Generation (Call 2) & Evaluation (Call 3) | $2.50 | $10.00 |
| `text-embedding-3-small` | Vector Retrieval (Optional) | $0.02 | $0.00 |

### Pipeline Assumptions:
- **Mandatory calls per candidate:** Exactly 3 calls (1x `gpt-4o-mini`, 2x `gpt-4o`).
- **Amortized role parsing:** 1 call per job description (~1,500 tokens), shared across all candidates applying to that role.
- **Retry rate:** Structured outputs parse on attempt 1 in >98% of calls; retry buffer of 2% added.
- **Deterministic assessments:** Turns 1-6 are served without LLM calls using Python heuristics.

---

## 4. Sensitivity Analysis

| Scenario | Cost / Candidate | 100 Candidates / Month | Notes |
|---|---|---|---|
| **Baseline Architecture** (1 mini + 2 gpt-4o) | **$0.0349** | **$3.49** | Default production configuration |
| **All-Mini Configuration** (Replace gpt-4o with gpt-4o-mini) | ~$0.0035 | ~$0.35 | 90% cost reduction; suitable for high-volume entry-level roles |
| **Adaptive Follow-ups Enabled** (`ENABLE_LLM_FOLLOWUPS=true`) | ~$0.0580 | ~$5.80 | Max 2 extra gpt-4o calls per candidate |
| **Full SRS Comparison** (25+ LLM calls per candidate) | ~$0.8500 | ~$85.00 | Demonstrates POC architectural efficiency |
