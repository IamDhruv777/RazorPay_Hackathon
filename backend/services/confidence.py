"""
LedgerLens — Confidence Calculator
Combines deterministic match confidence, evidence completeness,
source consistency, and (capped) LLM self-confidence into a single score.

This prevents the LLM from being the sole authority on its own reliability.
Formula:
    final = 0.40 * det + 0.20 * evidence + 0.20 * consistency + 0.20 * llm_capped

Thresholds (configurable via settings):
    ≥ AUTO_RESOLVE_THRESHOLD → eligible for auto-resolve (if type allows)
    ≥ REVIEW_THRESHOLD       → review queue
    < REVIEW_THRESHOLD       → escalate
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.config import get_settings


@dataclass
class ConfidenceComponents:
    """All four inputs to the confidence formula."""
    deterministic_confidence: float   # 0.0–1.0, from matching hierarchy level
    evidence_completeness: float      # 0.0–1.0, fraction of expected records found
    source_consistency: float         # 0.0–1.0, do independent sources agree?
    llm_confidence: float             # 0.0–1.0, agent's self-estimate


@dataclass
class ConfidenceResult:
    """Final confidence score plus routing decision and all components."""
    score: float                       # 0.0–1.0
    routing: str                       # AUTO_RESOLVE / REVIEW / ESCALATE
    components: ConfidenceComponents


# Weights — sum to 1.0
_W_DET   = 0.40
_W_EVID  = 0.20
_W_CONS  = 0.20
_W_LLM   = 0.20
_LLM_CAP = 0.95   # LLM confidence is capped at 95% regardless of what the model says


def compute_confidence(components: ConfidenceComponents) -> ConfidenceResult:
    """
    Compute the weighted final confidence score and determine routing.

    Args:
        components: All four confidence inputs.

    Returns:
        ConfidenceResult with score and routing decision.
    """
    settings = get_settings()

    # Clamp all inputs to [0, 1]
    det   = max(0.0, min(1.0, components.deterministic_confidence))
    evid  = max(0.0, min(1.0, components.evidence_completeness))
    cons  = max(0.0, min(1.0, components.source_consistency))
    llm   = max(0.0, min(_LLM_CAP, components.llm_confidence))

    score = round(
        _W_DET  * det
        + _W_EVID * evid
        + _W_CONS * cons
        + _W_LLM  * llm,
        4,
    )

    # Routing — CRITICAL type override is NOT applied here.
    # It is applied in resolution.py so the policy is in one clear place.
    if score >= settings.auto_resolve_threshold:
        routing = "AUTO_RESOLVE"
    elif score >= settings.review_threshold:
        routing = "REVIEW"
    else:
        routing = "ESCALATE"

    return ConfidenceResult(score=score, routing=routing, components=components)


def confidence_for_deterministic_match(match_level: int) -> float:
    """
    Returns the deterministic_confidence for a given matching hierarchy level.
    Used when there is no AI investigation (pure deterministic path).
    """
    level_confidence = {
        1: 1.00,   # Exact payment_id
        2: 0.95,   # Exact order_id + amount
        3: 0.93,   # Gateway reference exact
        4: 0.80,   # Customer + amount + timestamp window
        5: 0.70,   # Amount + timestamp + relational
    }
    return level_confidence.get(match_level, 0.50)


def evidence_completeness_score(
    has_order: bool,
    has_payment: bool,
    has_settlement: bool,
    has_bank: bool,
    has_refund: bool | None = None,  # None means "not expected"
) -> float:
    """
    Computes evidence completeness as fraction of *expected* records found.
    'has_refund=None' means the exception type doesn't require a refund check.
    """
    expected = [has_order, has_payment, has_settlement, has_bank]
    if has_refund is not None:
        expected.append(has_refund)
    if not expected:
        return 0.0
    return round(sum(1 for v in expected if v) / len(expected), 4)
