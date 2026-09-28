"""
Retention Purge Script for CandidateLens.
Deletes candidate records, files, and artifacts where retention_until < now().
"""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.db import SessionLocal
from app.models import Audit, Candidate


def purge_expired_candidates():
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    expired = db.query(Candidate).filter(Candidate.retention_until < now).all()

    print(f"Found {len(expired)} candidate(s) past retention expiration ({now.isoformat()}).")

    for cand in expired:
        cid = cand.candidate_id
        # Delete uploads
        u_dir = settings.uploads_path / cid
        if u_dir.exists():
            shutil.rmtree(u_dir, ignore_errors=True)

        # Delete artifacts
        a_dir = settings.artifacts_path / cid
        if a_dir.exists():
            shutil.rmtree(a_dir, ignore_errors=True)

        db.delete(cand)
        audit = Audit(
            entity_id=cid,
            action="DATA_RETENTION_PURGE",
            detail={"purged_at": now.isoformat()},
        )
        db.add(audit)
        print(f"Purged expired candidate: {cid}")

    db.commit()
    db.close()
    print("Purge completed.")


if __name__ == "__main__":
    purge_expired_candidates()
