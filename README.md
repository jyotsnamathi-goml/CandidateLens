# CandidateLens

> *See beyond the resume. Assess for readiness.*

CandidateLens is a production-grade, local proof-of-concept AI platform that delivers an objective, explainable **Candidate Readiness Signal** before a candidate enters Round 1 of technical hiring.

It evaluates candidate resumes, public GitHub artifacts, and optional portfolio links, then guides candidates through an adaptive, text-based practical assessment. All answers are evaluated in a single pass with anchored 1–5 rubrics and verbatim quotes, producing a deterministic readiness band and confidence rating.

CandidateLens is **cheap by design**: running on **only 3 mandatory LLM calls per candidate** (~$0.035 in OpenAI API fees), with an offline mock mode that requires no external API keys.

---

## Quickstart in 5 Commands

### 1. Clone & Enter Directory
```bash
cd candidatelens
```

### 2. Setup Environment
```bash
cp .env.example .env
```
*(By default, `LLM_MOCK=true` is enabled so you can run the entire platform offline without an OpenAI API key).*

### 3. Install Dependencies
```bash
make setup
```
*(Or install manually: `pip install -r backend/requirements.txt` and `cd frontend && npm install`).*

### 4. Seed Demo Roles & Candidates
```bash
make seed
```
*(Pre-populates 1 Distributed Backend Engineer role and 4 synthetic candidates representing key hiring scenarios).*

### 5. Launch Application
In two separate terminals:
```bash
# Terminal 1: Backend API (FastAPI)
make run-backend
# Running at http://localhost:8000

# Terminal 2: Frontend Dashboard (Vite + React)
make run-frontend
# Running at http://localhost:5173
```

---

## Demo Credentials & Walkthrough

1. Open your browser to **`http://localhost:5173`**.
2. Log in with the default HR credentials:
   - **Username:** `hr`
   - **Password:** `adminpassword123`
3. Explore the pre-seeded candidates under **Senior Backend Engineer - Distributed Systems**:
   - **Alex Chen (Strong Readiness, High Confidence, 88.0):** Rich evidence, high scores, verified GitHub metrics.
   - **Jordan Lee (Needs Verification, Medium Confidence, 66.6):** High-level claims with shallow practical assessment depth.
   - **Samira Khan (Strong Readiness, Medium Confidence, 81.5):** **Sparse footprint fairness demonstration.** Samira has no public GitHub repos; her evidence weights were automatically halved and redistributed to the practical assessment. Sparse evidence alone never triggered `Needs Verification`.
   - **Morgan Reed (Moderate Readiness, Medium Confidence, 65.6):** **Planted contradiction demonstration.** Resume claimed architecture of a distributed Raft engine, but public repo was a 1-commit fork, generating a neutral `claim_scope_gap` verification flag.

For a full hackathon presentation guide, see [docs/DEMO_SCRIPT.md](file:///c:/Users/rmdiw/OneDrive/Desktop/New%20folder/docs/DEMO_SCRIPT.md).

---

## Switching Between Mock & Real OpenAI API Mode

CandidateLens works completely offline out-of-the-box using realistic mock fixtures.

To switch to **Live OpenAI API Mode**:
1. Open `.env`.
2. Add your OpenAI API key:
   ```dotenv
   OPENAI_API_KEY=sk-your-actual-api-key-here
   LLM_MOCK=false
   ```
3. Restart the backend: `make run-backend`.

---

## Testing & Quality Checks

Run the automated test suite and linters with:

```bash
# Run all 24 backend unit, security, and E2E tests
cd backend && pytest -v

# Run Python linter
cd backend && ruff check .

# Validate Frontend TypeScript & Build
cd frontend && npm run build
```

---

## Architecture & LLM Call Economy

```
[HR] JD + Resume + GitHub + optional 1 portfolio URL
        │
        ▼ (background worker)
  Parse resume (Python) ── GitHub top repos (Python) ── Fetch portfolio (Python)
        │
        ▼
 ┌────────────────────────────┐
 │ LLM CALL 1: EXTRACTION     │  gpt-4o-mini (Cheap, structured evidence & claims)
 └─────────────┬──────────────┘
               ▼
 Python: relevance matching, timeline, sufficiency, commit share (No LLM)
               ▼
 ┌────────────────────────────┐
 │ LLM CALL 2: QUESTION PLAN  │  gpt-4o (4 JD scenarios + 2 candidate project questions)
 └─────────────┬──────────────┘
               ▼
 Candidate answers Q1..Q6 (Served via Python heuristics; <1s latency per turn)
               ▼
 ┌────────────────────────────┐
 │ LLM CALL 3: EVALUATION     │  gpt-4o (Single pass across ALL answers + quotes)
 └─────────────┬──────────────┘
               ▼
 Python: Grounding validator, quote verification, deterministic scoring engine
```

### Detailed Documentation:
- [docs/ARCHITECTURE.md](file:///c:/Users/rmdiw/OneDrive/Desktop/New%20folder/docs/ARCHITECTURE.md): Full system architecture with Mermaid sequence diagram.
- [docs/ASSUMPTIONS.md](file:///c:/Users/rmdiw/OneDrive/Desktop/New%20folder/docs/ASSUMPTIONS.md): Design decisions, security principles, and scoring formulas.
- [docs/COST_REPORT.md](file:///c:/Users/rmdiw/OneDrive/Desktop/New%20folder/docs/COST_REPORT.md): Measured token volumes and 100-candidate monthly cost projection ($3.50/month).
- [docs/AWS_MIGRATION_AND_COST.md](file:///c:/Users/rmdiw/OneDrive/Desktop/New%20folder/docs/AWS_MIGRATION_AND_COST.md): Enterprise serverless AWS production mapping.
