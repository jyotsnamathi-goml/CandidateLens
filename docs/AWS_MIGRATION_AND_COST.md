# CandidateLens: AWS Production Migration Path & Cost Model

This document outlines the production migration architecture from the local CandidateLens proof-of-concept to an enterprise-grade, serverless AWS infrastructure.

---

## 1. POC to AWS Production Mapping

| POC Component | AWS Production Equivalent | Rationale & Architectural Nuance |
|---|---|---|
| **FastAPI Backend (Local Uvicorn)** | **AWS Lambda (Container) + API Gateway HTTP API** via `Mangum` | Serverless autoscaling from 0 to thousands of concurrent candidate assessments with zero idle compute costs. |
| **SQLite (`data/candidatelens.db`)** | **Amazon DynamoDB (On-Demand Capacity)** | Single-digit millisecond latency at any scale. Partition key = `candidate_id`, sort key = `item_type`. Auto-configured TTL attributes for 90-day retention purging. |
| **Local File Storage (`data/uploads/`, `data/artifacts/`)** | **Amazon S3 (Encrypted at Rest via SSE-KMS)** | Secure, encrypted candidate resume and artifact storage with automated S3 Lifecycle Rules for 90-day deletion. |
| **FastAPI `BackgroundTasks`** | **AWS Step Functions + Amazon SQS (+ Dead Letter Queue)** | Guaranteed state machine orchestration with resilient retry policies for ingestion, extraction, and evaluation workflows. |
| **Local JWT & Auth** | **Amazon Cognito User Pools** (for HR) + **AWS KMS Signed Tokens** (for Candidate links) | Enterprise federated SAML/OIDC SSO for enterprise HR staff; tamper-proof asymmetric KMS signatures for candidate access links. |
| **Local `.env` Configuration** | **AWS Secrets Manager & SSM Parameter Store** | Secure credential rotation for API keys (`OPENAI_API_KEY`, `GITHUB_TOKEN`) with fine-grained IAM policy scoping. |
| **OpenAI API Direct** | **Amazon Bedrock (Claude 3.5 / Llama 3) or AWS PrivateLink to OpenAI** | Enterprise VPC data perimeter guarantees, ensuring zero candidate evaluation data is retained or used for foundation model retraining. |
| **In-Memory FAISS (Optional)** | **FAISS in Lambda Memory / Amazon OpenSearch Serverless** | Cached in Lambda ephemeral `/tmp` storage, or OpenSearch Serverless for high-scale multi-role embeddings. |
| **Python JSON Logging** | **Amazon CloudWatch Logs Insights + AWS X-Ray** | Distributed tracing across microservice boundaries with automated alerting on elevated token usage or latency anomalies. |
| **Vite React Dev Server** | **Amazon CloudFront CDN + Amazon S3 Static Hosting** | Global edge distribution with sub-50ms static asset delivery and HTTPS enforcement. |

---

## 2. Infrastructure Cost Model & Levers

### Baseline Fixed Infrastructure Cost: ~$0.00 / month
Because the entire target architecture is **100% serverless** (Lambda, API Gateway HTTP API, DynamoDB On-Demand, S3, CloudFront), there are no provisioned clusters (no persistent EC2 instances, no NAT Gateways, no provisioned DB instances). In periods of zero hiring activity, the infrastructure cost approaches $0.

### Primary Variable Cost: LLM Token Volume
The dominant variable cost in CandidateLens is LLM token consumption. The table below illustrates the cost advantage of the CandidateLens 3-call architecture compared to full-featured legacy agentic workflows:

| Assessment Architecture | LLM Calls / Candidate | Measured Cost / Candidate | Monthly Cost (100 Candidates) |
|---|---|---|---|
| **CandidateLens POC (Production Mode)** | **3 mandatory calls** | **$0.035** | **$3.50** |
| **CandidateLens (Adaptive Follow-ups)** | 5 calls max | $0.058 | $5.80 |
| **CandidateLens (All-Mini Configuration)** | 3 calls (gpt-4o-mini) | $0.0035 | $0.35 |
| **Traditional Agentic SRS Pipeline** | 25 - 30 recursive calls | $0.850 - $1.40 | $85.00 - $140.00 |

### Cost Lever Analysis
1. **Model Selection**: Using `gpt-4o-mini` for the high-token extraction stage and reserving `gpt-4o` solely for reasoning tasks (question planning and holistic evaluation) keeps 80% of token volume at $0.15/1M tokens.
2. **Deterministic Turn Serving**: Turns 1 through 6 in the practical assessment are served via Python heuristics, eliminating 6 round-trip LLM calls per candidate.
3. **Amortized Role Competency Derivation**: Job descriptions are parsed once per role rather than repeatedly per applicant.

---

## 3. Estimating Enterprise Production Costs

To model infrastructure costs for specific regional throughput and enterprise volume:
1. Navigate to the official [AWS Pricing Calculator](https://calculator.aws/#/).
2. Select your target region (e.g. `us-east-1` or `eu-west-1`).
3. Add:
   - **AWS Lambda**: Request volume = `Candidates * 12 invocations`, Avg duration = `1,200 ms`, Memory = `512 MB`.
   - **Amazon DynamoDB**: On-Demand read/write units corresponding to candidate assessment volume.
   - **Amazon S3**: Standard storage for resumes (~2 MB per candidate) with 90-day expiration.
   - **Amazon CloudFront**: Standard edge tier.
4. Add OpenAI / Amazon Bedrock token estimates from `docs/COST_REPORT.md`.
