"""
LedgerLens — Audit Trail Logger
Records every significant action during exception investigation.
Logs are structured (JSON-compatible) and persisted to the database.
"""
from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AuditEvent

log = structlog.get_logger(__name__)


async def log_event(
    db: AsyncSession,
    exception_id: str,
    action: str,
    *,
    tool_used: str | None = None,
    input_ref: str | None = None,
    evidence_summary: str | None = None,
    decision: str | None = None,
    confidence: float | None = None,
    user_action: str | None = None,
) -> AuditEvent:
    """
    Persist a single audit event for an exception.

    Every call to an AI tool, every decision made, every human action
    is recorded here. This is the primary evidence that the system
    did what it claims to have done.

    Args:
        db:               Active async database session.
        exception_id:     The exception this event belongs to.
        action:           Short description of what happened.
        tool_used:        Name of the AI tool called (if any).
        input_ref:        The ID or reference passed to the tool.
        evidence_summary: Brief summary of what the tool returned.
        decision:         Final decision made at this step.
        confidence:       Confidence score at time of decision.
        user_action:      If a human acted (APPROVED/REJECTED).

    Returns:
        The persisted AuditEvent ORM instance.
    """
    event = AuditEvent(
        exception_id=exception_id,
        ts=datetime.now(timezone.utc),
        action=action,
        tool_used=tool_used,
        input_ref=input_ref,
        evidence_summary=evidence_summary,
        decision=decision,
        confidence=confidence,
        user_action=user_action,
    )
    db.add(event)
    await db.flush()  # Get the ID without committing

    # Also emit as structured log for observability
    log.info(
        "audit_event",
        exception_id=exception_id,
        action=action,
        tool_used=tool_used,
        input_ref=input_ref,
        decision=decision,
        confidence=confidence,
    )

    return event


# ─── Pre-defined action constants (used throughout the codebase) ──────────────
class Actions:
    EXCEPTION_CREATED       = "exception_created"
    INVESTIGATION_STARTED   = "investigation_started"
    TOOL_CALLED             = "tool_called"
    TOOL_RETURNED_EMPTY     = "tool_returned_empty"
    INVESTIGATION_COMPLETED = "investigation_completed"
    AI_UNAVAILABLE          = "ai_investigation_unavailable"
    AUTO_RESOLVED           = "auto_resolved"
    ESCALATED               = "escalated"
    SENT_FOR_REVIEW         = "sent_for_review"
    HUMAN_APPROVED          = "human_approved"
    HUMAN_REJECTED          = "human_rejected"
    CRITICAL_OVERRIDE       = "critical_type_override_applied"
