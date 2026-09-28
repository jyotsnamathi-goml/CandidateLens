"""
Deterministic Timeline analysis service.
Analyzes chronological progression of dated evidence items and produces factual observations
(never psychological claims or assumptions about learning).
"""

from datetime import datetime

from app.schemas.domain import TimelineObservation
from app.schemas.llm import EvidenceItem


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    val = date_str.strip().lower()
    if val in ["present", "current", "now"]:
        return datetime.now()
    try:
        # e.g. YYYY-MM
        parts = val.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        return datetime(year, month, 1)
    except Exception:
        return None


def generate_timeline_observations(evidence_items: list[EvidenceItem]) -> list[TimelineObservation]:
    """Generate deterministic timeline observations with linked evidence IDs."""
    observations: list[TimelineObservation] = []

    # Filter and sort items with dates
    dated_items = []
    for ev in evidence_items:
        start_dt = parse_date(ev.date_start)
        if start_dt:
            dated_items.append((start_dt, ev))

    dated_items.sort(key=lambda x: x[0])

    if not dated_items:
        return observations

    # 1. Recency Observation
    latest_dt, latest_ev = dated_items[-1]
    years_since_latest = (datetime.now() - latest_dt).days / 365.25
    if years_since_latest < 1.0:
        observations.append(
            TimelineObservation(
                observation=f"Active hands-on development documented within the last 12 months in '{latest_ev.title}'.",
                evidence_refs=[latest_ev.evidence_id],
                trend_type="recency",
            )
        )
    else:
        observations.append(
            TimelineObservation(
                observation=f"Most recent dated project artifact is '{latest_ev.title}' from {latest_ev.date_start or 'earlier'}.",
                evidence_refs=[latest_ev.evidence_id],
                trend_type="recency",
            )
        )

    # 2. Complexity / Technical Depth Trend
    if len(dated_items) >= 2:
        earlier_items = dated_items[: len(dated_items) // 2]
        later_items = dated_items[len(dated_items) // 2 :]

        avg_early_depth = sum(ev.attributes.technical_depth for _, ev in earlier_items) / len(earlier_items)
        avg_late_depth = sum(ev.attributes.technical_depth for _, ev in later_items) / len(later_items)

        refs = [ev.evidence_id for _, ev in dated_items]
        if avg_late_depth >= avg_early_depth + 0.15:
            observations.append(
                TimelineObservation(
                    observation="Progression from foundational implementations to higher-complexity architectural ownership over documented periods.",
                    evidence_refs=refs[:4],
                    trend_type="complexity",
                )
            )
        else:
            observations.append(
                TimelineObservation(
                    observation="Consistent technical depth maintained across documented project timeline.",
                    evidence_refs=refs[:4],
                    trend_type="complexity",
                )
            )

    # 3. Solo vs Collaborative Trend
    collab_items = [ev for _, ev in dated_items if ev.attributes.collaboration >= 0.7]
    if collab_items:
        observations.append(
            TimelineObservation(
                observation=f"Documented collaborative contributions in {len(collab_items)} project(s), including team repositories or public open-source contributions.",
                evidence_refs=[ev.evidence_id for ev in collab_items],
                trend_type="collaboration",
            )
        )

    return observations
