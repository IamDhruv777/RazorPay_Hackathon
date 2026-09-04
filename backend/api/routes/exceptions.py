"""
LedgerLens — Exceptions API Routes
List, filter, detail, investigate, approve/reject exceptions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import AuditEvent, ExceptionModel, Investigation

router = APIRouter()


@router.get("/exceptions")
async def list_exceptions(
    run_id: str | None = Query(default=None, description="Filter by reconciliation run"),
    severity: str | None = Query(default=None, description="GREEN, YELLOW, or RED"),
    status: str | None = Query(default=None, description="PENDING, AUTO_RESOLVED, ESCALATED, HUMAN_REVIEWED"),
    exception_type: str | None = Query(default=None, description="Exception type (e.g. MISSING_BANK_CREDIT)"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List exceptions with optional filters.
    Frontend uses this for the exceptions table.
    """
    stmt = select(ExceptionModel)

    if run_id:
        stmt = stmt.where(ExceptionModel.run_id == run_id)
    if severity:
        stmt = stmt.where(ExceptionModel.severity == severity.upper())
    if status:
        stmt = stmt.where(ExceptionModel.status == status.upper())
    if exception_type:
        stmt = stmt.where(ExceptionModel.type == exception_type.upper())

    stmt = stmt.order_by(ExceptionModel.detected_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    exceptions = result.scalars().all()

    return [
        {
            "id": e.id,
            "run_id": e.run_id,
            "type": e.type,
            "severity": e.severity,
            "amount": float(e.amount),
            "confidence": e.confidence,
            "status": e.status,
            "order_id": e.order_id,
            "payment_id": e.payment_id,
            "settlement_id": e.settlement_id,
            "bank_id": e.bank_id,
            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
        }
        for e in exceptions
    ]


@router.get("/exceptions/{exception_id}")
async def get_exception_detail(
    exception_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Full exception detail including latest investigation + evidence + audit trail.
    This is what the Exception Detail page loads.
    """
    stmt = (
        select(ExceptionModel)
        .where(ExceptionModel.id == exception_id)
        .options(
            selectinload(ExceptionModel.investigations).selectinload(Investigation.evidence),
            selectinload(ExceptionModel.audit_events),
        )
    )
    result = await db.execute(stmt)
    exc = result.scalar_one_or_none()

    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found")

    # Latest investigation
    investigation = None
    if exc.investigations:
        latest = sorted(exc.investigations, key=lambda i: i.created_at, reverse=True)[0]
        investigation = {
            "id": latest.id,
            "classification": latest.classification,
            "root_cause": latest.root_cause,
            "reasoning_summary": latest.reasoning_summary,
            "confidence": latest.confidence,
            "llm_confidence": latest.llm_confidence,
            "deterministic_confidence": latest.deterministic_confidence,
            "evidence_completeness": latest.evidence_completeness,
            "source_consistency": latest.source_consistency,
            "recommended_action": latest.recommended_action,
            "auto_resolve": latest.auto_resolve,
            "llm_model": latest.llm_model,
            "token_usage": latest.token_usage,
            "duration_seconds": latest.duration_seconds,
            "status": latest.status,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
            "evidence": [
                {
                    "source_table": ev.source_table,
                    "source_id": ev.source_id,
                    "snapshot": ev.snapshot_json,
                    "retrieved_at": ev.retrieved_at.isoformat() if ev.retrieved_at else None,
                }
                for ev in latest.evidence
            ],
        }

    # Audit trail (chronological)
    audit = [
        {
            "id": ae.id,
            "ts": ae.ts.isoformat() if ae.ts else None,
            "action": ae.action,
            "tool_used": ae.tool_used,
            "input_ref": ae.input_ref,
            "evidence_summary": ae.evidence_summary,
            "decision": ae.decision,
            "confidence": ae.confidence,
            "user_action": ae.user_action,
        }
        for ae in sorted(exc.audit_events, key=lambda a: a.ts or "")
    ]

    return {
        "id": exc.id,
        "run_id": exc.run_id,
        "type": exc.type,
        "severity": exc.severity,
        "amount": float(exc.amount),
        "confidence": exc.confidence,
        "status": exc.status,
        "order_id": exc.order_id,
        "payment_id": exc.payment_id,
        "refund_id": exc.refund_id,
        "settlement_id": exc.settlement_id,
        "bank_id": exc.bank_id,
        "detected_at": exc.detected_at.isoformat() if exc.detected_at else None,
        "resolved_at": exc.resolved_at.isoformat() if exc.resolved_at else None,
        "human_approved_by": exc.human_approved_by,
        "human_approved_at": exc.human_approved_at.isoformat() if exc.human_approved_at else None,
        "investigation": investigation,
        "audit_trail": audit,
    }


@router.post("/exceptions/{exception_id}/investigate")
async def trigger_investigation(
    exception_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger AI investigation for an exception.
    The investigation runs synchronously and returns the result.
    If the LLM API is unavailable, returns AI_UNAVAILABLE status — does not crash.
    """
    from backend.services.investigation import investigate_exception

    stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
    result = await db.execute(stmt)
    exc = result.scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found")

    investigation = await investigate_exception(exc, db)
    await db.commit()

    return {
        "exception_id": exception_id,
        "investigation_id": investigation.id,
        "status": investigation.status,
        "confidence": investigation.confidence,
        "recommended_action": investigation.recommended_action,
        "reasoning_summary": investigation.reasoning_summary,
        "auto_resolve": investigation.auto_resolve,
    }


@router.post("/exceptions/{exception_id}/approve")
async def approve_resolution(
    exception_id: str,
    approved_by: str = Query(default="finance_user"),
    db: AsyncSession = Depends(get_db),
):
    """Human approves the AI's recommended resolution."""
    from datetime import datetime, timezone
    from backend.services.audit import log_event, Actions

    stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
    result = await db.execute(stmt)
    exc = result.scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found")

    exc.status = "HUMAN_REVIEWED"
    exc.human_approved_by = approved_by
    exc.human_approved_at = datetime.now(timezone.utc)

    await log_event(
        db, exception_id,
        action=Actions.HUMAN_APPROVED,
        decision="APPROVED",
        user_action=f"Approved by {approved_by}",
    )
    await db.commit()
    return {"exception_id": exception_id, "status": "HUMAN_REVIEWED", "approved_by": approved_by}


@router.post("/exceptions/{exception_id}/reject")
async def reject_resolution(
    exception_id: str,
    rejected_by: str = Query(default="finance_user"),
    db: AsyncSession = Depends(get_db),
):
    """Human rejects the AI's recommended resolution — sends back to ESCALATED."""
    from datetime import datetime, timezone
    from backend.services.audit import log_event, Actions

    stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
    result = await db.execute(stmt)
    exc = result.scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found")

    exc.status = "ESCALATED"
    exc.human_approved_by = rejected_by
    exc.human_approved_at = datetime.now(timezone.utc)

    await log_event(
        db, exception_id,
        action=Actions.HUMAN_REJECTED,
        decision="REJECTED",
        user_action=f"Rejected by {rejected_by}",
    )
    await db.commit()
    return {"exception_id": exception_id, "status": "ESCALATED", "rejected_by": rejected_by}


@router.get("/exceptions/{exception_id}/audit")
async def get_audit_trail(
    exception_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the full audit trail for an exception."""
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.exception_id == exception_id)
        .order_by(AuditEvent.ts.asc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        {
            "id": ae.id,
            "ts": ae.ts.isoformat() if ae.ts else None,
            "action": ae.action,
            "tool_used": ae.tool_used,
            "input_ref": ae.input_ref,
            "evidence_summary": ae.evidence_summary,
            "decision": ae.decision,
            "confidence": ae.confidence,
            "user_action": ae.user_action,
        }
        for ae in events
    ]
