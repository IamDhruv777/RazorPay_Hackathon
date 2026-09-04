"""
LedgerLens — Reconciliation API Route
Triggers the deterministic reconciliation engine on a pending run.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import ReconciliationRun

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    """List all reconciliation runs."""
    stmt = select(ReconciliationRun).order_by(ReconciliationRun.started_at.desc()).limit(50)
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "record_count": r.record_count,
            "matched_count": r.matched_count,
            "exception_count": r.exception_count,
            "auto_resolved_count": r.auto_resolved_count,
            "escalated_count": r.escalated_count,
            "total_amount": float(r.total_amount) if r.total_amount else 0.0,
            "processing_seconds": r.processing_seconds,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get status and summary for a specific reconciliation run."""
    stmt = select(ReconciliationRun).where(ReconciliationRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "id": run.id,
        "status": run.status,
        "record_count": run.record_count,
        "matched_count": run.matched_count,
        "exception_count": run.exception_count,
        "auto_resolved_count": run.auto_resolved_count,
        "escalated_count": run.escalated_count,
        "total_amount": float(run.total_amount) if run.total_amount else 0.0,
        "unresolved_amount": float(run.unresolved_amount) if run.unresolved_amount else 0.0,
        "processing_seconds": run.processing_seconds,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.post("/reconcile/{run_id}")
async def run_reconciliation(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Run the full reconciliation pipeline on an ingested batch.
    Steps: normalization check → matching → exception detection → auto-resolve/escalate.
    AI investigation is NOT triggered here (that's per-exception via POST /investigate).
    """
    from backend.services.reconciliation import ReconciliationEngine

    stmt = select(ReconciliationRun).where(ReconciliationRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    if run.status == "RUNNING":
        raise HTTPException(status_code=409, detail="Reconciliation already in progress for this run")
    if run.status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Reconciliation already completed for this run. Create a new run.")

    run.status = "RUNNING"
    run.started_at = datetime.now(timezone.utc)
    await db.commit()

    start_time = time.monotonic()
    try:
        engine = ReconciliationEngine(db)
        summary = await engine.run(run_id)
        elapsed = time.monotonic() - start_time

        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        run.matched_count = summary["matched"]
        run.exception_count = summary["exceptions"]
        run.auto_resolved_count = summary["auto_resolved"]
        run.escalated_count = summary["escalated"]
        run.total_amount = summary["total_amount"]
        run.unresolved_amount = summary["unresolved_amount"]
        run.processing_seconds = elapsed
        await db.commit()

        log.info(
            "reconciliation_completed",
            run_id=run_id,
            matched=summary["matched"],
            exceptions=summary["exceptions"],
            seconds=round(elapsed, 2),
        )

        return {
            "run_id": run_id,
            "status": "COMPLETED",
            "matched": summary["matched"],
            "exceptions": summary["exceptions"],
            "auto_resolved": summary["auto_resolved"],
            "escalated": summary["escalated"],
            "total_amount": float(summary["total_amount"]),
            "unresolved_amount": float(summary["unresolved_amount"]),
            "processing_seconds": round(elapsed, 2),
        }

    except Exception as e:
        elapsed = time.monotonic() - start_time
        run.status = "FAILED"
        run.completed_at = datetime.now(timezone.utc)
        run.processing_seconds = elapsed
        await db.commit()
        log.error("reconciliation_failed", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")
