# CandidateLens: Hackathon Demo Script & Walkthrough

This script provides a 5-minute presentation walkthrough of CandidateLens for judges, recruiters, and engineering leaders.

---

## 1. Setup & Launch (30 seconds)

### A. Start the Backend
```bash
cd backend
uvicorn app.main:app --port 8000 --reload
```
*Verification:* Navigate to `http://localhost:8000/health` -> `{"status":"ok","mock_mode":true}`.

### B. Start the Frontend
```bash
cd frontend
npm run dev
```
*Verification:* Open `http://localhost:5173`.

### C. Seed Demo Data (Optional - if fresh reset is desired)
```bash
cd backend
python scripts/seed_demo.py
```

---

## 2. Walkthrough Narrative

### Step 1: HR Login & The Core Thesis (45 seconds)
1. Navigate to `http://localhost:5173`.
2. Login with:
   - **Username:** `hr`
   - **Password:** `adminpassword123`
3. **Presenter Talking Point:**
   > *"Hiring teams are flooded with resumes that look identical on paper. But resumes summarize claims, not readiness. CandidateLens is designed to give technical hiring managers an objective, grounded **Candidate Readiness Signal** before Round 1 interviews—running on just 3 LLM calls per candidate with zero hallucinations."*

---

### Step 2: Role Management & Amortized Parsing (45 seconds)
1. Click **Roles** in the navigation bar.
2. Open **Senior Backend Engineer - Distributed Systems**.
3. Point out the extracted **Competencies**:
   - `Distributed System Design & Concurrency`
   - `Database Internals & Data Modeling`
   - `API Architecture & Reliability`
   - `Observability & Performance Profiling`
4. **Presenter Talking Point:**
   > *"When HR posts a job description, CandidateLens executes a single, amortized small-model call (`gpt-4o-mini`) to extract 4 to 6 core competencies. HR can drag-to-reorder or edit competencies. This single call is shared across hundreds of applicants, reducing per-candidate role parsing costs to fractions of a cent."*

---

### Step 3: Candidate 1 — Alex Chen (Strong Readiness) (60 seconds)
1. On the Role Detail page, click on **Alex Chen**.
2. Highlight the Hero Header:
   - **Readiness Band Badge:** `Strong Readiness` (Green)
   - **Confidence Meter:** `High` (3 of 3 dots active)
   - **Score:** `88.0 / 100`
   - **Disclaimer:** *"Candidate Readiness Signal, not a hiring decision."*
3. Explore the **Interactive Score Breakdown**:
   - Show how Practical Problem Solving, Technical Quality, and Evidence Consistency are mapped from anchored 1-5 rubrics.
4. Show the **Grounding & Evidence Cards**:
   - Point to `Distributed Task Scheduler (TaskFlow)` with its verified GitHub metrics and provenance tag (`public_evidence`).
5. Show **Assessment Analysis**:
   - Expand Question 1. Point out the verbatim supporting quote extracted directly from the candidate's answer.
   - Point to the quote validator safeguard: *"Every score above 2 must be justified by an exact candidate quote; unquoted claims are capped at 2."*
6. Review **Interview Probes**:
   - Point out targeted probes for the interviewer: e.g., *"Ask candidate to walk through their locking protocol under a network partition scenario."*

---

### Step 4: Candidate 3 — Samira Khan (Sparse Footprint) (60 seconds)
1. Return to Candidates and click **Samira Khan**.
2. **Presenter Talking Point:**
   > *"Here is a critical fairness test: Samira has worked in closed-source enterprise banking with no public GitHub footprint. Traditional AI screening tools penalize candidates with zero public repos. Let's see what CandidateLens does."*
3. Show the **Confidence & Weight Redistribution**:
   - Confidence is **Medium** (capped because public evidence is sparse).
   - Sufficiency is **Sparse**.
   - Point to the Banner: *"Because public footprint was sparse, evidence weights were reduced by 50% and redistributed to the practical assessment. Sparse evidence never by itself lowers the readiness band."*
   - Because Samira demonstrated deep distributed systems reasoning in her assessment, her band is **Strong Readiness** (`81.5 / 100`).

---

### Step 5: Candidate 4 — Morgan Reed (Planted Contradiction) (45 seconds)
1. Return to Candidates and click **Morgan Reed**.
2. Point to the **Areas to Verify (Flag Card)**:
   - Flag Type: `claim_scope_gap` (Neutral amber badge).
   - **Public Artifact:** `raft-fork` indicates a forked repository with 1 documentation commit.
   - **Resume Claim:** *"Solely architected and implemented enterprise Raft multi-region consensus engine from scratch."*
   - **Interviewer Action:** *"Ask candidate for a concrete technical walkthrough of their personal code contributions versus the upstream library."*
3. **Presenter Talking Point:**
   > *"Notice the tone: CandidateLens never accuses the candidate of lying or faking. It neutrally flags the scope gap and equips the Round 1 interviewer with an exact, respectful probe to clarify during the interview."*

---

### Step 6: Live Cost Monitoring & AWS Projection (45 seconds)
1. Click **Admin Costs** in the navigation bar.
2. Show the live dashboard:
   - **Measured Cost per Candidate:** ~$0.035 - $0.045
   - **Projected Cost for 100 Candidates / Month:** ~$3.50 - $4.50
   - Show the breakdown across `extraction`, `question_plan`, and `evaluation`.
3. Conclude:
   > *"CandidateLens replaces expensive, subjective resume reviews with an explainable, grounded, and cost-effective readiness signal—empowering hiring teams to make smarter, fairer interview decisions for under $0.05 per candidate."*
