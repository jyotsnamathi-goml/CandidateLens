# CandidateLens: Assumptions & Architecture Decisions

This document records the architectural decisions, trade-offs, and operational assumptions made in the CandidateLens local proof-of-concept.

---

## 1. Core Operating Principles

1. **Candidate Readiness Signal, Not an Automated Hiring Decision**:
   - The platform serves as an objective, pre-Round 1 evaluation tool to assist technical interviewers and hiring managers.
   - It outputs a Readiness Band (`Strong Readiness`, `Moderate Readiness`, `Needs Verification`) alongside a Confidence rating (`High`, `Medium`, `Low`) and granular grounded evidence.

2. **Sparse Evidence vs. Negative Evidence**:
   - Sparse public footprints (e.g. candidates with proprietary closed-source careers) automatically down-weight public footprint metrics and redistribute weight onto the practical assessment.
   - Sparse evidence alone **never** places a candidate into `Needs Verification`.

3. **Neutral Verification Framing**:
   - No accusatory language (`dishonest`, `lied`, `fake`, `fraud`, `cheat`) is permitted in prompt outputs, code, or UI.
   - Findings are framed as `potential_mismatch`, `claim_scope_gap`, or `insufficient_evidence`.

4. **Strict Grounding & Substring Verification**:
   - Findings and dimension scores > 2 require verbatim quotes or verifiable references to evidence IDs, claim IDs, or question IDs.
   - Unreferenced statements are discarded by post-processing validators.

---

## 2. LLM Call Architecture & Token Efficiency

- **Total Mandatory Calls Per Candidate:** Exactly 3 calls:
  1. *Candidate Extraction* (`gpt-4o-mini`): Parses resume, GitHub metadata, and portfolio page into structured evidence and claims.
  2. *Question Plan Generation* (`gpt-4o`): Generates 4 JD scenario questions and 2 candidate project/verification questions, with prepared follow-ups.
  3. *Single-Pass Evaluation* (`gpt-4o`): Evaluates all 6 answered questions at once against 1-5 rubrics, extracting quotes, flags, strengths, gaps, and probes.
- **Amortized Job Description Call:** 1 call per role (`gpt-4o-mini`) derives 4–6 ranked competencies, which are shared by all candidates for that role.
- **Offline Mock Mode (`LLM_MOCK=true`)**: Enabled by default, providing realistic deterministic responses for full end-to-end testing without external network or API key dependencies.

---

## 3. Security & Privacy Decisions

- **Untrusted Candidate Data:** Delimiters (`<resume>`, `<github>`, `<candidate_answers>`) and explicit system prompt rules isolate candidate text and prevent prompt injection attacks.
- **SSRF Protection:** Web portfolio fetch uses DNS pre-resolution checking against loopback (`127.0.0.0/8`, `::1`), private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and AWS/GCP metadata endpoints (`169.254.169.254`), with validation maintained across redirects.
- **Privacy & Fairness:** Candidate names, demographics, and photos are stripped before passing context to LLMs; internal processing relies strictly on anonymized `candidate_id`.
