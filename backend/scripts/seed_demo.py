"""
Seed script for CandidateLens Demo.
Creates 1 Role and 4 Synthetic Candidates illustrating all critical edge cases:
1. Strong Candidate (Alex Chen) -> Strong Readiness, High Confidence.
2. Moderate Candidate (Jordan Lee) -> Moderate Readiness, Medium Confidence.
3. Sparse-Footprint Candidate (Samira Khan) -> Strong Readiness, Medium Confidence (never penalized by sparseness alone).
4. Planted Contradiction Candidate (Morgan Reed) -> Triggers neutral 'claim_scope_gap' or 'potential_mismatch' flag.
All offline and runnable with LLM_MOCK=true.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import Audit, Candidate, Claim, Evidence, Profile, Result, Role, Turn
from app.models import Session as DBSession
from app.schemas.llm import EvidenceItem
from app.services.report import build_readiness_report
from app.services.scoring import (
    compute_score,
    hash_scoring_inputs,
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("--- Seeding CandidateLens Demo Data ---")

    # 1. Clean existing demo data
    db.query(Audit).delete()
    db.query(Result).delete()
    db.query(Turn).delete()
    db.query(DBSession).delete()
    db.query(Profile).delete()
    db.query(Claim).delete()
    db.query(Evidence).delete()
    db.query(Candidate).delete()
    db.query(Role).delete()
    db.commit()

    # 2. Create Role
    role = Role(
        role_id="r_backend_001",
        title="Senior Backend Engineer - Distributed Systems",
        jd_text="""We are seeking a Senior Backend Engineer to architect high-throughput distributed systems.
Key Responsibilities:
- Design fault-tolerant, concurrent microservices handling 20k+ RPS.
- Architect and optimize PostgreSQL databases, transaction isolation, and declarative partitioning.
- Build resilient APIs with circuit breakers, idempotency, and bulkhead isolation.
- Lead observability, latency profiling, and distributed tracing.
- Maintain CI/CD pipelines and zero-downtime database migrations.
""",
        competencies=[
            {
                "name": "Distributed System Design & Concurrency",
                "description": "Designing high-throughput, fault-tolerant architectures, managing state, caching, and race conditions.",
                "rank": 1,
                "importance": "critical",
            },
            {
                "name": "Database Internals & Data Modeling",
                "description": "SQL schema design, query optimization, indexing strategies, transactions, and ACID guarantees.",
                "rank": 2,
                "importance": "critical",
            },
            {
                "name": "API Architecture & Reliability",
                "description": "REST/gRPC interfaces, idempotency, rate limiting, and defensive resilience patterns.",
                "rank": 3,
                "importance": "important",
            },
            {
                "name": "Observability & Performance Profiling",
                "description": "Distributed tracing, telemetry, latency profiling, and root-cause incident analysis.",
                "rank": 4,
                "importance": "important",
            },
        ],
        role_family="backend",
    )
    db.add(role)
    db.commit()
    print("Created Role: Senior Backend Engineer - Distributed Systems")

    # Helper to create candidate artifacts
    def make_candidate(
        cand_id: str,
        name: str,
        gh_user: str,
        sufficiency: str,
        score: float,
        band: str,
        confidence: str,
        conf_reason: str,
        flags: list,
        ev_items: list,
        claims_list: list,
        turns_data: list,
        obs_list: list,
    ):
        cand = Candidate(
            candidate_id=cand_id,
            role_id=role.role_id,
            display_name=name,
            github_username=gh_user,
            portfolio_url=f"https://{gh_user.lower()}.dev" if gh_user else None,
            linkedin_url=f"https://www.linkedin.com/in/{gh_user.lower()}" if gh_user else None,
            resume_path=f"data/uploads/{cand_id}/resume.pdf",
            consent={"accepted": True, "timestamp": datetime.now(timezone.utc).isoformat(), "scope": ["resume", "github", "linkedin"]},
            status="COMPLETED",
            ingestion_log=[
                {"step": "resume_parsing", "status": "success", "detail": "Parsed resume."},
                {"step": "github_fetch", "status": "success", "detail": f"Processed {gh_user}."},
                {"step": "linkedin_fetch", "status": "success", "detail": f"Processed LinkedIn {gh_user}."},
                {"step": "llm_extraction", "status": "success", "detail": "Extracted evidence."},
                {"step": "deterministic_processing", "status": "success", "detail": f"Sufficiency: {sufficiency}."},
            ],
            retention_until=datetime.now(timezone.utc) + timedelta(days=90),
        )
        db.add(cand)

        # Profile
        profile = Profile(
            candidate_id=cand_id,
            sufficiency=sufficiency,
            uncovered_competencies=[] if sufficiency != "sparse" else ["Observability & Performance Profiling"],
            timeline=[o.model_dump() for o in obs_list],
            relevance={"Distributed System Design & Concurrency": {"best_score": 0.9}},
            github_metrics={"username": gh_user, "user_commit_share": 0.85 if sufficiency != "sparse" else 0.0},
        )
        db.add(profile)

        # Evidence
        for ev in ev_items:
            e_row = Evidence(
                candidate_id=cand_id,
                evidence_id=ev["evidence_id"],
                type=ev["type"],
                data=ev,
                provenance=ev["provenance"],
            )
            db.add(e_row)

        # Claims
        for cl in claims_list:
            c_row = Claim(
                candidate_id=cand_id,
                claim_id=cl["claim_id"],
                text=cl["text"],
                scope=cl["scope"],
                linked_evidence=cl.get("linked_evidence", []),
                verification="pending",
            )
            db.add(c_row)

        # Session & Turns
        sess = DBSession(
            session_id=f"sess_{cand_id}",
            candidate_id=cand_id,
            state="DONE",
            question_plan=[],
            turn_count=len(turns_data),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
            token_jti=f"jti_{cand_id}",
            used=True,
        )
        db.add(sess)

        for i, t in enumerate(turns_data):
            turn_row = Turn(
                session_id=sess.session_id,
                turn_no=i + 1,
                question_id=t["q_id"],
                kind=t.get("kind", "planned"),
                question_text=t["q_text"],
                answer_text=t["a_text"],
                answer_words=len(t["a_text"].split()),
                time_taken_seconds=120,
            )
            db.add(turn_row)

        # Component scores
        components = {
            "jd_alignment": score,
            "technical_depth_evidence": score - 5 if sufficiency != "sparse" else 50.0,
            "ownership_activity": 85.0 if sufficiency != "sparse" else 45.0,
            "practical_problem_solving": score + 2,
            "technical_quality_assessment": score + 1,
            "communication": 85.0,
            "evidence_consistency": 90.0 if not flags else 60.0,
        }
        final_score, weights = compute_score(components, sufficiency=sufficiency, sparse_factor=settings.SPARSE_FACTOR)

        from app.schemas.llm import EvaluationResult
        mock_eval = EvaluationResult.model_validate({
            "per_question": [
                {
                    "question_id": f"q{i+1}",
                    "competency": "Distributed System Design & Concurrency",
                    "technical_correctness": {"score": 4 if score > 75 else 3, "quote": t["a_text"][:60]},
                    "technical_depth": {"score": 4 if score > 75 else 3, "quote": t["a_text"][:60]},
                    "mechanism": {"score": 4 if score > 75 else 3, "quote": t["a_text"][:60]},
                    "trade_offs": {"score": 4 if score > 75 else 2, "quote": t["a_text"][:60]},
                    "problem_solving": {"score": 4 if score > 75 else 3, "quote": t["a_text"][:60]},
                    "communication": {"score": 4, "quote": t["a_text"][:60]},
                    "specificity": {"score": 4 if score > 75 else 2, "quote": t["a_text"][:60]},
                }
                for i, t in enumerate(turns_data)
            ],
            "evidence_consistency": "high" if not flags else "low",
            "consistency_rationale": "Answers demonstrate verified engineering depth." if not flags else "Scope gap noted between resume claim and repository artifacts.",
            "flags": flags,
            "strengths": [
                {"text": "Demonstrated rigorous understanding of concurrency control and idempotency.", "refs": ["q1", "ev_001"]},
                {"text": "Structured problem decomposition in production debugging scenarios.", "refs": ["q2", "q3"]},
            ],
            "gaps": [{"text": "Limited explicit discussion of gRPC service mesh integration.", "refs": ["q4"]}],
            "verification_points": [{"text": fl["action_text"], "refs": fl["refs"]} for fl in flags],
            "interview_probes": [
                "Ask candidate to walk through their locking protocol under a network partition scenario.",
                "Probe on specific database indexing strategies used for high-frequency writes.",
            ],
            "competencies_assessed": [c["name"] for c in role.competencies],
        })

        # Report assembly
        ev_objs = [EvidenceItem.model_validate(e) for e in ev_items]
        report = build_readiness_report(
            candidate_id=cand_id,
            role_id=role.role_id,
            role_title=role.title,
            display_name=name,
            band=band,
            confidence=confidence,
            confidence_reason=conf_reason,
            score=final_score,
            components=components,
            adjusted_weights=weights,
            sufficiency=sufficiency,
            eval_result=mock_eval,
            evidence_items=ev_objs,
            timeline_obs=obs_list,
        )

        res = Result(
            candidate_id=cand_id,
            role_id=role.role_id,
            evaluation=mock_eval.model_dump(),
            component_scores=components,
            score=final_score,
            band=band,
            confidence=confidence,
            confidence_reason=conf_reason,
            flags=flags,
            report=report.model_dump(),
            scoring_inputs_hash=hash_scoring_inputs(components, weights, sufficiency),
        )
        db.add(res)
        db.commit()
        print(f"Created Candidate: {name} [{band} | {confidence} Confidence | Score {final_score}]")

    # CANDIDATE 1: Strong Candidate (Alex Chen)
    from app.schemas.domain import TimelineObservation
    obs1 = [
        TimelineObservation(observation="Active contributions in high-throughput task scheduler across 2023.", evidence_refs=["ev_001"], trend_type="recency"),
        TimelineObservation(observation="Progression from single-node scripts to distributed locking microservices.", evidence_refs=["ev_001"], trend_type="complexity"),
    ]
    ev1 = [
        {
            "evidence_id": "ev_001",
            "type": "project",
            "title": "Distributed Task Scheduler (TaskFlow)",
            "technologies": ["Python", "FastAPI", "Redis", "PostgreSQL", "Docker"],
            "role": "Lead Architect",
            "responsibilities": ["Implemented Redlock algorithm", "Built heartbeat worker failover"],
            "date_start": "2023-01",
            "date_end": "2023-11",
            "outcomes": ["15,000 tasks/second with sub-20ms latency"],
            "provenance": "public_evidence",
            "source_url": "https://github.com/alexchen/taskflow",
            "attributes": {"jd_relevance": 0.95, "technical_depth": 0.90, "ownership": 0.90, "collaboration": 0.70, "recency": 0.85, "evidence_strength": 0.90},
        }
    ]
    cl1 = [{"claim_id": "cl_001", "text": "Architected distributed locking system resilient to network partitions", "scope": "designed", "linked_evidence": ["ev_001"]}]
    turns1 = [
        {"q_id": "q1", "q_text": "How do you guarantee idempotency in payment webhooks?", "a_text": "We enforce idempotency by inserting an idempotency key with a unique constraint in PostgreSQL within the same database transaction. A Redis distributed lock prevents concurrent processing."},
        {"q_id": "q2", "q_text": "How would you partition a 180M row table?", "a_text": "Use declarative range partitioning by month and create local indexes using CREATE INDEX CONCURRENTLY to avoid blocking writes."},
        {"q_id": "q3", "q_text": "How do you prevent cascading failure from slow upstream services?", "a_text": "Wrap the external call in a circuit breaker with 500ms timeouts and isolate connection pools using a bulkhead pattern."},
        {"q_id": "q4", "q_text": "Debugging 1,200ms latency spike with low CPU.", "a_text": "Analyze distributed trace waterfalls to isolate pool acquisition delays, and check pg_stat_activity lock wait states."},
    ]
    make_candidate(
        cand_id="c_alex_chen",
        name="Alex Chen",
        gh_user="alexchen",
        sufficiency="rich",
        score=88.5,
        band="Strong Readiness",
        confidence="High",
        conf_reason="Confidence is High because public footprint is well-documented; practical assessment thoroughly covered all critical competencies.",
        flags=[],
        ev_items=ev1,
        claims_list=cl1,
        turns_data=turns1,
        obs_list=obs1,
    )

    # CANDIDATE 2: Moderate/Weak Candidate (Jordan Lee)
    obs2 = [TimelineObservation(observation="Single repository with sporadic commit activity in 2022.", evidence_refs=["ev_002"], trend_type="recency")]
    ev2 = [
        {
            "evidence_id": "ev_002",
            "type": "project",
            "title": "Basic CRUD API",
            "technologies": ["Python", "Flask", "SQLite"],
            "role": "Developer",
            "responsibilities": ["Created REST endpoints"],
            "date_start": "2022-01",
            "date_end": "2022-05",
            "outcomes": ["Internal toy service"],
            "provenance": "public_evidence",
            "source_url": "https://github.com/jordanlee/crud-api",
            "attributes": {"jd_relevance": 0.55, "technical_depth": 0.40, "ownership": 0.50, "collaboration": 0.30, "recency": 0.40, "evidence_strength": 0.50},
        }
    ]
    cl2 = [{"claim_id": "cl_002", "text": "Built web backend services", "scope": "built", "linked_evidence": ["ev_002"]}]
    turns2 = [
        {"q_id": "q1", "q_text": "How do you guarantee idempotency in payment webhooks?", "a_text": "I would check if the order exists in the database and then update it if it does not."},
        {"q_id": "q2", "q_text": "How would you partition a 180M row table?", "a_text": "I would add an index to the table to make lookups faster."},
        {"q_id": "q3", "q_text": "How do you prevent cascading failure?", "a_text": "Add a try catch block around the HTTP request and retry three times."},
        {"q_id": "q4", "q_text": "Debugging 1,200ms latency spike with low CPU.", "a_text": "Look at application print logs to see which line is taking time."},
    ]
    make_candidate(
        cand_id="c_jordan_lee",
        name="Jordan Lee",
        gh_user="jordanlee",
        sufficiency="partial",
        score=58.0,
        band="Needs Verification",
        confidence="Medium",
        conf_reason="Confidence is Medium because assessment covered competencies with concise answers; identified minor claim scope gaps for verification.",
        flags=[],
        ev_items=ev2,
        claims_list=cl2,
        turns_data=turns2,
        obs_list=obs2,
    )

    # CANDIDATE 3: Sparse-Footprint Candidate (Samira Khan)
    # AC-5: Sparse footprint gets lower confidence, but is NOT in Needs Verification solely due to sparseness!
    obs3 = [TimelineObservation(observation="No public repositories found; relies on resume claims and practical assessment.", evidence_refs=[], trend_type="recency")]
    ev3 = [
        {
            "evidence_id": "ev_003",
            "type": "work_experience",
            "title": "Enterprise Core Banking Backend",
            "technologies": ["Java", "Spring Boot", "Oracle SQL", "Kafka"],
            "role": "Senior Engineer",
            "responsibilities": ["Proprietary ledger settlement engine"],
            "date_start": "2021-03",
            "date_end": "2024-01",
            "outcomes": ["Processed 40M daily transactions"],
            "provenance": "candidate_provided",
            "source_url": None,
            "attributes": {"jd_relevance": 0.85, "technical_depth": 0.85, "ownership": 0.70, "collaboration": 0.80, "recency": 0.90, "evidence_strength": 0.40},
        }
    ]
    cl3 = [{"claim_id": "cl_003", "text": "Engineered enterprise distributed ledger in private proprietary environment", "scope": "built", "linked_evidence": ["ev_003"]}]
    turns3 = [
        {"q_id": "q1", "q_text": "How do you guarantee idempotency in payment webhooks?", "a_text": "In our banking ledger we maintained a unique hash of the payload and source event ID inside an ACID transaction with SERIALIZABLE isolation, rejecting duplicates at commit time."},
        {"q_id": "q2", "q_text": "How would you partition a 180M row table?", "a_text": "We partitioned by event timestamp using daily partitions with rolling retention, automating partition creation via pg_partman and indexing concurrently."},
        {"q_id": "q3", "q_text": "How do you prevent cascading failure?", "a_text": "We deployed Resilience4j circuit breakers with rate limiters and dedicated executor pools per downstream partner."},
        {"q_id": "q4", "q_text": "Debugging 1,200ms latency spike with low CPU.", "a_text": "Inspect thread dump lock contention in JVM, connection pool checkout duration in HikariCP, and database wait events in pg_stat_activity."},
    ]
    make_candidate(
        cand_id="c_samira_khan",
        name="Samira Khan",
        gh_user="",
        sufficiency="sparse",
        score=84.0,
        band="Strong Readiness",
        confidence="Medium",
        conf_reason="Confidence is Medium because public footprint is sparse; practical assessment thoroughly covered all critical competencies.",
        flags=[],
        ev_items=ev3,
        claims_list=cl3,
        turns_data=turns3,
        obs_list=obs3,
    )

    # CANDIDATE 4: Planted Contradiction Candidate (Morgan Reed)
    # AC-4: Planted contradiction demo candidate produces at least one neutral flag
    obs4 = [TimelineObservation(observation="Forked repository with minimal original commits.", evidence_refs=["ev_004"], trend_type="recency")]
    ev4 = [
        {
            "evidence_id": "ev_004",
            "type": "project",
            "title": "Distributed Multi-Region Consensus Engine",
            "technologies": ["Go", "Raft"],
            "role": "Fork Contributor",
            "responsibilities": ["Forked repository from HashiCorp Raft"],
            "date_start": "2023-04",
            "date_end": "2023-05",
            "outcomes": ["Modified 1 documentation line"],
            "provenance": "public_evidence",
            "source_url": "https://github.com/morganreed/raft-fork",
            "attributes": {"jd_relevance": 0.80, "technical_depth": 0.35, "ownership": 0.15, "collaboration": 0.20, "recency": 0.60, "evidence_strength": 0.35},
        }
    ]
    cl4 = [{"claim_id": "cl_004", "text": "Solely architected and implemented enterprise Raft multi-region consensus engine from scratch", "scope": "designed", "linked_evidence": ["ev_004"]}]
    turns4 = [
        {"q_id": "q1", "q_text": "How do you guarantee idempotency in payment webhooks?", "a_text": "I use Raft consensus to replicate all webhook events across data centers."},
        {"q_id": "q2", "q_text": "How would you partition a 180M row table?", "a_text": "I split the tables across different servers manually."},
        {"q_id": "q3", "q_text": "How do you prevent cascading failure?", "a_text": "Restart the application instances when errors appear in the logs."},
        {"q_id": "q4", "q_text": "Debugging 1,200ms latency spike with low CPU.", "a_text": "Restart the server and increase memory allocation."},
    ]
    flags4 = [
        {
            "type": "claim_scope_gap",
            "severity": "medium",
            "public_evidence": "Public artifact 'raft-fork' indicates a forked repository with 1 documentation commit.",
            "candidate_statement": "Resume claim 'Solely architected and implemented enterprise Raft multi-region consensus engine from scratch'.",
            "refs": ["ev_004", "cl_004"],
            "action_text": "Ask candidate for a concrete technical walkthrough of their personal code contributions versus the upstream library.",
        }
    ]
    make_candidate(
        cand_id="c_morgan_reed",
        name="Morgan Reed",
        gh_user="morganreed",
        sufficiency="partial",
        score=63.0,
        band="Moderate Readiness",
        confidence="Medium",
        conf_reason="Confidence is Medium because public footprint provides moderate evidence; identified minor claim scope gaps for verification.",
        flags=flags4,
        ev_items=ev4,
        claims_list=cl4,
        turns_data=turns4,
        obs_list=obs4,
    )

    db.close()
    print("--- Seeding Completed Successfully! ---")


if __name__ == "__main__":
    seed()
