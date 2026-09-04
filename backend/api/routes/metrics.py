"""
LedgerLens — Metrics API Route
Returns summary metrics for the most recent reconciliation run.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import ReconciliationRun, ExceptionModel

router = APIRouter()


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Return dashboard KPI metrics: matched, exceptions, auto-resolved,
    escalated, critical, total amount, unresolved amount.
    """
    # Get the most recent completed run
    stmt = (
        select(ReconciliationRun)
        .where(ReconciliationRun.status == "COMPLETED")
        .order_by(ReconciliationRun.completed_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()

    if not run:
        return {
            "has_data": False,
            "message": "No completed reconciliation runs found. Load demo data and run reconciliation.",
        }

    # Count critical exceptions
    critical_stmt = select(func.count()).where(
        ExceptionModel.run_id == run.id,
        ExceptionModel.severity == "RED",
        ExceptionModel.status.in_(["PENDING", "ESCALATED"]),
    )
    critical_result = await db.execute(critical_stmt)
    critical_count = critical_result.scalar() or 0

    # Count review required
    review_stmt = select(func.count()).where(
        ExceptionModel.run_id == run.id,
        ExceptionModel.status == "PENDING",
    )
    review_result = await db.execute(review_stmt)
    review_count = review_result.scalar() or 0

    return {
        "has_data": True,
        "run_id": run.id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "record_count": run.record_count,
        "matched_count": run.matched_count,
        "exception_count": run.exception_count,
        "auto_resolved_count": run.auto_resolved_count,
        "escalated_count": run.escalated_count,
        "review_required_count": review_count,
        "critical_count": critical_count,
        "total_amount": float(run.total_amount) if run.total_amount else 0.0,
        "unresolved_amount": float(run.unresolved_amount) if run.unresolved_amount else 0.0,
        "processing_seconds": run.processing_seconds,
    }
