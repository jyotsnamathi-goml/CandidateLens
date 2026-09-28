from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_hr_user
from app.db import get_db
from app.schemas.api import CostSummaryOut
from app.services.costs import get_cost_summary

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/costs", response_model=CostSummaryOut)
def get_costs(
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Retrieve cost aggregation per candidate, totals, and projected 100-candidate monthly cost."""
    summary = get_cost_summary(db)
    return CostSummaryOut(**summary)
