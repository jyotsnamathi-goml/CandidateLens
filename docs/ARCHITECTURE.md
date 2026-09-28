# CandidateLens: System Architecture & Data Flow

This document details the architectural design and operational pipeline of **CandidateLens**, an explainable Candidate Readiness Signal platform.

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Inputs ["Input Ingestion"]
        JD["Job Description (JD)"]
        CV["Resume (PDF / DOCX / TXT)"]
        GH["GitHub Username / URL"]
        WEB["Optional Portfolio URL"]
    end

    subgraph Phase1 ["Role Creation (Amortized)"]
        JD --> JDCall["LLM JD Parser (gpt-4o-mini)"]
        JDCall --> Comps["4-6 Ranked Competencies"]
    end

    subgraph Phase2 ["Evidence Extraction & Ingestion"]
        CV --> TextParser["Python Document Parser (pypdf/docx)"]
        GH --> GHClient["GitHub Client (Top 3 repos, Commits, README)"]
        WEB --> WebFetch["Web Fetcher (SSRF-Guarded Trafilatura)"]
        TextParser & GHClient & WebFetch & Comps --> Call1["LLM Call 1: Extraction (gpt-4o-mini)"]
        Call1 --> EvClaims["Structured Evidence & Claims"]
    end

    subgraph Phase3 ["Deterministic Processing (No LLM)"]
        EvClaims & Comps --> Relevance["Relevance Matching (TF-IDF + Overlap)"]
        EvClaims --> Timeline["Timeline Generator (Deterministic Trends)"]
        EvClaims & Relevance --> Sufficiency["Sufficiency Classifier (Rich / Partial / Sparse)"]
    end

    subgraph Phase4 ["Adaptive Practical Assessment"]
        Sufficiency & Comps & EvClaims --> Call2["LLM Call 2: Question Plan (gpt-4o)"]
        Call2 --> QPlan["6 Planned Questions (4 JD + 2 Project) + Prepared Follow-ups"]
        QPlan --> CandidateUI["Candidate Assessment UI (Token-Scoped Session)"]
        CandidateUI --> Heuristics["Python Vague Answer Heuristic (<40 words, generic)"]
        Heuristics --> FollowUp["Serve Prepared Follow-Up (Max 1/question, 8 total)"]
    end

    subgraph Phase5 ["Single-Pass Evaluation & Scoring"]
        CandidateUI --> Call3["LLM Call 3: Evaluation (gpt-4o)"]
        Call3 --> RawEval["Raw Evaluation (1-5 Anchored Rubrics + Quotes)"]
        RawEval --> Validators["Grounding & Quote Validators + Anti-Accusatory Filter"]
        Validators --> ScoringEngine["Deterministic Python Scoring Engine"]
        Sufficiency --> SparseRedistribution["Sparse Weight Redistribution (Halve Evidence)"]
        SparseRedistribution --> ScoringEngine
        ScoringEngine --> ReportAssembler["Report Assembly (No LLM)"]
        ReportAssembler --> Report["Candidate Readiness Signal Report"]
    end

    subgraph HRView ["HR Evaluation Experience"]
        Report --> HRDashboard["HR Dashboard (Band, Confidence, Breakdown, Flags, Probes)"]
    end
```

---

## 2. Key Architecture Principles

1. **3 Mandatory LLM Calls**:
   - `Call 1 (Extraction)`: High-volume, inexpensive extraction using `gpt-4o-mini`.
   - `Call 2 (Question Plan)`: Tailored 6-question practical assessment using `gpt-4o`.
   - `Call 3 (Evaluation)`: Concurrently evaluates all answers and aligns them against verified evidence in a single pass using `gpt-4o`.
   - *1 Amortized Call per Role*: Extracts 4–6 competencies once per job description.

2. **Deterministic Computation Where Appropriate**:
   - Sufficiency classification (`Rich`, `Partial`, `Sparse`), timeline observations, keyword/competency relevance, scoring math, and report narrative assembly are executed 100% in Python.
   - Guaranteed reproducibility: Storing `scoring_inputs_hash` ensures identical inputs always yield identical score and band outputs.

3. **Multi-Layered Guardrails**:
   - **SSRF Guard**: Pre-validates IP addresses and redirects against loopback, private, link-local, and cloud metadata blocks.
   - **Prompt Delimiters**: Delimiters (`<resume>`, `<github>`, `<candidate_answers>`) wrap untrusted candidate text to prevent instruction override.
   - **Grounding Validator**: Strips findings, gaps, and flags that do not resolve to valid evidence, claim, or question IDs.
   - **Language Filter**: Replaces accusatory phrasing with neutral verification terms.
