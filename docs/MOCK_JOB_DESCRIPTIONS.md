# Mock Job Descriptions for CandidateLens Testing

This document contains 3 production-grade, highly structured Job Descriptions (JDs) tailored for testing the CandidateLens platform across **Frontend**, **Backend**, and **Machine Learning** roles.

---

## 1. Frontend Role: Senior Frontend Engineer (React / TypeScript)
* **Role Family**: `frontend`
* **File**: [`data/sample_jds/frontend_engineer_jd.txt`](file:///d:/GOML/CandidateLens/data/sample_jds/frontend_engineer_jd.txt)

```text
Role: Senior Frontend Engineer (React / TypeScript)
Department: Engineering
Location: Remote / Hybrid

About the Role:
We are looking for a Senior Frontend Engineer to architect and build mission-critical, high-performance web applications. You will take ownership of the client-side architecture, lead performance profiling initiatives, and ensure state consistency across complex data workflows.

Key Responsibilities:
- Design, build, and maintain scalable web interfaces using React 18+, TypeScript, and modern CSS architecture.
- Optimize frontend web performance, ensuring Core Web Vitals (LCP < 2.5s, FID/INP < 200ms, CLS < 0.1), bundle code splitting, and sub-second page loads.
- Architect robust client-side state management (Zustand, Redux Toolkit, or TanStack Query) and optimistic UI updates for real-time collaboration.
- Implement comprehensive client-side telemetry, error tracking (Sentry/Datadog), and automated testing suites (Jest, React Testing Library, Playwright).
- Collaborate with backend engineers on GraphQL/REST API contracts, pagination strategies, and streaming endpoints (Server-Sent Events / WebSockets).

Required Qualifications & Competencies:
1. React & TypeScript Architecture: Deep mastery of React lifecycle, custom hooks, virtual DOM reconciliation, strict TypeScript typing, and reusable component libraries.
2. Web Performance & Core Web Vitals: Hands-on experience with bundle optimization, tree-shaking, memory leak prevention, virtualization (virtual scrolling for 10k+ DOM nodes), and Chrome DevTools profiling.
3. State Management & Asynchronous Data: Expertise in caching strategies, optimistic UI mutations, race condition mitigation, and normalized client caches.
4. Testing & Code Quality: Strong discipline in end-to-end testing, integration testing, accessibility (WCAG 2.1 AA), and robust CI/CD pipelines.
5. System Design & Frontend Security: Solid knowledge of XSS mitigation, Content Security Policy (CSP), token storage security, and micro-frontend or monorepo patterns.
```

---

## 2. Backend Role: Senior Backend Engineer (Distributed Systems)
* **Role Family**: `backend`
* **File**: [`data/sample_jds/backend_engineer_jd.txt`](file:///d:/GOML/CandidateLens/data/sample_jds/backend_engineer_jd.txt)

```text
Role: Senior Backend Engineer (Distributed Systems)
Department: Core Infrastructure
Location: Remote / Hybrid

About the Role:
We are seeking an experienced Senior Backend Engineer to design and scale our high-throughput transactional backend services and event-driven data pipelines. You will lead the architecture of distributed workflows, high-availability data stores, and resilient microservices handling millions of requests daily.

Key Responsibilities:
- Design, implement, and operate low-latency REST and gRPC microservices in Go or Python (FastAPI/AsyncIO).
- Architect reliable event-driven messaging and streaming architectures using Apache Kafka, RabbitMQ, or AWS SQS/SNS.
- Design normalized and high-performance database models in PostgreSQL and Redis, ensuring zero data loss, strict ACID compliance, and idempotency across distributed transactions.
- Implement robust fault tolerance mechanisms: circuit breakers, distributed locking (Redlock / PG advisory locks), exponential backoff retries, and rate limiters.
- Build observability pipelines with OpenTelemetry, Prometheus, and Grafana, optimizing p99 latency and system throughput under heavy traffic spikes.

Required Qualifications & Competencies:
1. Distributed Systems & Concurrency: Deep understanding of CAP theorem, consensus protocols, distributed locks, idempotency keys, and concurrent race-condition prevention.
2. Database Design & Performance Tuning: Advanced SQL mastery, index tuning (B-Tree, GIN, Partial), isolation levels (Read Committed, Repeatable Read, Serializable), connection pooling (PgBouncer), and partition pruning.
3. Event-Driven Architecture & Messaging: Hands-on experience with Kafka consumer groups, partition rebalancing, at-least-once vs exactly-once semantics, and dead-letter queues.
4. Fault Tolerance & Resilience: Proven track record implementing circuit breakers, rate limiting (token bucket / leaky bucket), failover strategies, and graceful degradation.
5. Observability & Performance Profiling: Expertise analyzing flamegraphs, p99 latency bottlenecks, memory profiling (pprof/tracemalloc), and distributed tracing context propagation.
```

---

## 3. Machine Learning Role: Machine Learning Engineer (LLMs & Inference)
* **Role Family**: `ml`
* **File**: [`data/sample_jds/ml_engineer_jd.txt`](file:///d:/GOML/CandidateLens/data/sample_jds/ml_engineer_jd.txt)

```text
Role: Machine Learning Engineer (LLMs & Distributed Inference)
Department: AI & Applied ML
Location: Remote / Hybrid

About the Role:
We are looking for a Machine Learning Engineer to build and deploy production-grade Large Language Model (LLM) pipelines, vector search retrieval architectures (RAG), and high-throughput model inference engines. You will bridge the gap between machine learning research and scalable production infrastructure.

Key Responsibilities:
- Design, fine-tune, and deploy transformer-based foundation models and LLMs using PyTorch, Hugging Face, and vLLM / TensorRT-LLM.
- Build production Retrieval-Augmented Generation (RAG) pipelines, integrating vector databases (Pinecone, Qdrant, Milvus, or pgvector) with hybrid sparse/dense retrieval and rerankers.
- Optimize inference throughput and latency via quantization (AWQ, GPTQ, FP8), KV caching, batch scheduling (continuous batching), and multi-GPU tensor parallelism.
- Implement comprehensive LLM evaluation frameworks: hallucination detection, semantic grounding, prompt injection defenses, and latency/cost telemetry tracking.
- Collaborate with backend teams to package ML pipelines into production microservices (FastAPI, Ray Serve, Triton Inference Server) with containerized CI/CD.

Required Qualifications & Competencies:
1. Transformer Architectures & LLM Fine-Tuning: Deep technical grasp of self-attention mechanisms, PEFT/LoRA fine-tuning, context length scaling (RoPE), and instruction dataset curation.
2. Production RAG & Vector Search: Hands-on experience with vector embedding generation, chunking strategies, cosine/HNSW indexing, hybrid BM25 + dense search, and reciprocal rank fusion.
3. Inference Optimization & Model Serving: Practical mastery of vLLM, TensorRT-LLM, KV cache management, model quantization techniques, and GPU memory profiling (CUDA memory / VRAM management).
4. Safety, Evaluation & Guardrails: Expertise in prompt injection defense, output schema validation (Pydantic / Instructor), synthetic benchmark evaluation, and cost-per-token budgeting.
5. ML Engineering & Production Deployment: Strong proficiency in Python, PyTorch, Docker, Ray Serve / Triton, distributed training basics, and OpenTelemetry for ML tracing.
```

---

## How to Use These JDs in the Application

1. Open **[http://localhost:5173/roles](http://localhost:5173/roles)**.
2. Click **Create New Role** or **Upload JD**.
3. Copy-paste the text or upload one of the text files above.
4. CandidateLens will parse the role, extract 4–6 ranked technical competencies with importance ratings, and classify the role family automatically.
