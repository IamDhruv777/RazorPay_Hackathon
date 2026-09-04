"""
LedgerLens — Resolution Policy
Decides AUTO_RESOLVE vs REVIEW vs ESCALATE for each exception.

CRITICAL RULE (in code, not in any prompt):
Certain exception types MUST NEVER be auto-resolved regardless of confidence.
This rule is enforced here in Python — the LLM's recommendation is overridden
if it conflicts. This is intentional: financial safety cannot rely on
the LLM's judgment for irreversible or high-stakes decisions.
"""
from __future__ import annotations

import structlog
from datetime import datetime, timezone

log = structlog.get_logger(__name__)


# ─── CRITICAL Type Policy ─────────────────────────────────────────────────────
# These exception types can NEVER be auto-resolved, regardless of:
# - confidence score
# - LLM recommendation
# - any other factor
#
# Enforced by: test_resolution_policy.py asserts this cannot be bypassed.
CRITICAL_TYPES: frozenset[str] = frozenset({
    "MISSING_BANK_CREDIT",
    "DUPLICATE_PAYMENT",
})

# Types that are never eligible for auto-resolve (but not as severe as CRITICAL)
ESCALATE_ONLY_TYPES: frozenset[str] = frozenset({
    "AMOUNT_MISMATCH",
    "AMBIGUOUS",
})

# Types where review is the best outcome (never auto-resolve)
REVIEW_ONLY_TYPES: frozenset[str] = frozenset({
    "DELAYED_SETTLEMENT",
    "ORPHAN_PAYMENT",
})

# Auto-resolve eligible types (subject to confidence threshold)
AUTO_RESOLVE_ELIGIBLE_TYPES: frozenset[str] = frozenset({
    "FEE_DIFFERENCE",
    "PARTIAL_REFUND",
    "FULL_REFUND",
})


def resolve(
    exception_type: str,
    confidence_routing: str,  # AUTO_RESOLVE / REVIEW / ESCALATE from confidence.py
    llm_recommendation: str | None = None,
) -> tuple[str, str]:
    """
    Apply resolution policy to determine the final status and reason.

    Args:
        exception_type: One of the 10 exception taxonomy types.
        confidence_routing: Output from confidence.compute_confidence().routing
        llm_recommendation: LLM's recommended action (may be overridden).

    Returns:
        Tuple of (final_status, reason_for_status)
        final_status: AUTO_RESOLVED / ESCALATED / PENDING (pending = awaiting review)
    """
    exc_type = exception_type.upper()

    # ── CRITICAL override — always escalate, no exceptions ──────────────────
    if exc_type in CRITICAL_TYPES:
        reason = (
            f"{exc_type} is a CRITICAL exception type — "
            "never auto-resolved regardless of confidence score."
        )
        if llm_recommendation and llm_recommendation.upper() == "AUTO_RESOLVE":
            log.warning(
                "critical_override",
                exception_type=exc_type,
                llm_recommendation=llm_recommendation,
                override="ESCALATED",
            )
        log.info("resolution_decision", type=exc_type, status="ESCALATED", reason="critical_override")
        return "ESCALATED", reason

    # ── Escalate-only types ─────────────────────────────────────────────────
    if exc_type in ESCALATE_ONLY_TYPES:
        reason = f"{exc_type} always requires human review — insufficient automated evidence."
        log.info("resolution_decision", type=exc_type, status="ESCALATED", reason="escalate_only_policy")
        return "ESCALATED", reason

    # ── Review-only types ───────────────────────────────────────────────────
    if exc_type in REVIEW_ONLY_TYPES:
        reason = f"{exc_type} requires human review — auto-resolution not permitted for this type."
        log.info("resolution_decision", type=exc_type, status="PENDING", reason="review_only_policy")
        return "PENDING", reason

    # ── Auto-resolve eligible types — confidence determines outcome ─────────
    if exc_type in AUTO_RESOLVE_ELIGIBLE_TYPES:
        if confidence_routing == "AUTO_RESOLVE":
            reason = f"Confidence ≥ threshold. {exc_type} fully explained by deterministic evidence."
            log.info("resolution_decision", type=exc_type, status="AUTO_RESOLVED", reason="high_confidence")
            return "AUTO_RESOLVED", reason
        elif confidence_routing == "REVIEW":
            reason = f"Confidence below auto-resolve threshold. {exc_type} requires human review."
            log.info("resolution_decision", type=exc_type, status="PENDING", reason="medium_confidence")
            return "PENDING", reason
        else:  # ESCALATE
            reason = f"Low confidence. {exc_type} cannot be reliably explained — escalating."
            log.info("resolution_decision", type=exc_type, status="ESCALATED", reason="low_confidence")
            return "ESCALATED", reason

    # ── Unknown type — default to escalate ─────────────────────────────────
    log.warning("unknown_exception_type", exception_type=exc_type)
    return "ESCALATED", f"Unknown exception type '{exc_type}' — defaulting to escalation."


def exception_severity(exception_type: str) -> str:
    """Return the default severity for a given exception type."""
    severity_map = {
        "FEE_DIFFERENCE":      "GREEN",
        "PARTIAL_REFUND":      "GREEN",
        "FULL_REFUND":         "GREEN",
        "DELAYED_SETTLEMENT":  "YELLOW",
        "MISSING_BANK_CREDIT": "RED",
        "DUPLICATE_PAYMENT":   "RED",
        "ORPHAN_PAYMENT":      "YELLOW",
        "AMOUNT_MISMATCH":     "YELLOW",
        "AMBIGUOUS":           "YELLOW",
    }
    return severity_map.get(exception_type.upper(), "YELLOW")
