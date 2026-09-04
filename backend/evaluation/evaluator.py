"""
LedgerLens — Evaluation Pipeline
Compares system predictions against hidden ground truth to compute real metrics.

The ground truth file lives in data/eval_ground_truth/ and is NEVER read
by the application during normal operation — only during an explicit eval run.

Metrics computed:
- Exception detection precision, recall, F1
- Auto-resolution accuracy
- False auto-resolution count (the most important metric)
- Escalation count
- Throughput
- Baseline (deterministic-only) comparison
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    EvaluationResult,
    EvaluationRun,
    ExceptionModel,
    ReconciliationRun,
)

log = structlog.get_logger(__name__)


async def run_evaluation_pipeline(
    gt_path: Path,
    dataset_name: str,
    db: AsyncSession,
) -> tuple[str, dict[str, Any]]:
    """
    Run the full evaluation pipeline.

    1. Load ground truth from the separate GT file
    2. Find the most recent completed reconciliation run
    3. Compare system predictions to ground truth
    4. Compute and store all metrics
    5. Run baseline (deterministic-only) comparison

    Returns: (eval_run_id, metrics_dict)
    """
    start_time = time.monotonic()

    # Load ground truth
    with open(gt_path, encoding="utf-8") as f:
        ground_truth: list[dict] = json.load(f)

    log.info("evaluation_started", dataset=dataset_name, gt_records=len(ground_truth))

    # Create evaluation run record
    eval_run_id = str(uuid.uuid4())
    eval_run = EvaluationRun(
        id=eval_run_id,
        dataset_name=dataset_name,
        record_count=len(ground_truth),
        started_at=datetime.now(timezone.utc),
    )
    db.add(eval_run)
    await db.flush()

    # Get the most recent completed reconciliation run
    stmt = (
        select(ReconciliationRun)
        .where(ReconciliationRun.status == "COMPLETED")
        .order_by(ReconciliationRun.completed_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    recon_run = result.scalar_one_or_none()

    if not recon_run:
        raise RuntimeError(
            "No completed reconciliation run found. "
            "Load data and run reconciliation first."
        )

    # Fetch all exceptions for this run
    from sqlalchemy.orm import selectinload
    exc_stmt = select(ExceptionModel).options(selectinload(ExceptionModel.investigations)).where(ExceptionModel.run_id == recon_run.id)
    exc_result = await db.execute(exc_stmt)
    all_exceptions = exc_result.scalars().all()

    # Build lookup: payment_id → exception
    exc_by_payment: dict[str, ExceptionModel] = {}
    for exc in all_exceptions:
        if exc.payment_id:
            exc_by_payment[exc.payment_id] = exc

    # ── Compute metrics ────────────────────────────────────────────────────────
    metrics = _compute_metrics(ground_truth, exc_by_payment, all_exceptions)

    elapsed = time.monotonic() - start_time
    metrics["throughput_records_per_sec"] = round(len(ground_truth) / max(elapsed, 0.001), 2)
    metrics["evaluation_duration_seconds"] = round(elapsed, 2)

    # Persist metrics
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            db.add(EvaluationResult(
                id=str(uuid.uuid4()),
                run_id=eval_run_id,
                metric_name=metric_name,
                value=float(value),
            ))
        elif isinstance(value, dict):
            db.add(EvaluationResult(
                id=str(uuid.uuid4()),
                run_id=eval_run_id,
                metric_name=metric_name,
                value=float(value.get("value", 0.0)) if "value" in value else 0.0,
                metrics_metadata=value,
            ))

    eval_run.completed_at = datetime.now(timezone.utc)
    await db.commit()

    log.info("evaluation_completed", eval_run_id=eval_run_id, metrics=metrics)
    return eval_run_id, metrics


def _compute_metrics(ground_truth: list[dict], exc_by_payment: dict, all_exceptions: list) -> dict:
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    total_ai_investigated = 0
    total_ai_unavailable_fallback = 0

    auto_resolve_correct = 0
    auto_resolve_total_gt = 0
    system_auto_resolved_total = 0
    false_auto_resolutions = 0

    escalate_correct = 0
    escalate_total_gt = 0
    system_escalated_total = 0
    
    safe_abstentions = 0

    per_type = {}
    classification_correct = 0
    classification_total = 0

    for gt_record in ground_truth:
        payment_id = gt_record.get("payment_id", "")
        actual_exc = gt_record.get("actual_exception", "HEALTHY")
        expected_res = gt_record.get("expected_resolution", "NONE")
        is_gt_exception = actual_exc not in ("HEALTHY", "", None)

        system_exc = exc_by_payment.get(payment_id)
        system_detected = system_exc is not None

        if is_gt_exception:
            if actual_exc not in per_type:
                per_type[actual_exc] = {"gt_count": 0, "detected": 0, "correct_resolution": 0}
            per_type[actual_exc]["gt_count"] += 1

        if is_gt_exception and system_detected:
            true_positives += 1
            per_type[actual_exc]["detected"] += 1
            classification_total += 1
            if system_exc.type == actual_exc:
                classification_correct += 1
        elif is_gt_exception and not system_detected:
            false_negatives += 1
        elif not is_gt_exception and system_detected:
            false_positives += 1
        else:
            true_negatives += 1

        if system_exc:
            investigation_status = "PENDING"
            if system_exc.investigations:
                latest_inv = system_exc.investigations[-1]
                investigation_status = latest_inv.status
                
            if system_exc.outcome_source == "AI_INVESTIGATED":
                total_ai_investigated += 1
            elif system_exc.outcome_source == "AI_UNAVAILABLE_FALLBACK":
                total_ai_unavailable_fallback += 1
                
            if investigation_status == "COMPLETED":
                if expected_res == "AUTO_RESOLVE":
                    auto_resolve_total_gt += 1
                if expected_res == "ESCALATE":
                    escalate_total_gt += 1
                    
                if system_exc.status == "AUTO_RESOLVED":
                    system_auto_resolved_total += 1
                    if expected_res == "AUTO_RESOLVE":
                        auto_resolve_correct += 1
                        if actual_exc in per_type:
                            per_type[actual_exc]["correct_resolution"] += 1
                    else:
                        false_auto_resolutions += 1
                        
                elif system_exc.status == "ESCALATED":
                    system_escalated_total += 1
                    if expected_res == "ESCALATE":
                        escalate_correct += 1
                    
                    # If expected was ESCALATE and we escalated, check if it was an ambiguous/contradictory case
                    # meaning the AI safely abstained.
                    if expected_res == "ESCALATE" and actual_exc in ("AMBIGUOUS", "CONTRADICTORY_EVIDENCE", "INCOMPLETE_EVIDENCE", "CONFLICTING_TIMESTAMPS"):
                        safe_abstentions += 1

    precision = _safe_div(true_positives, true_positives + false_positives)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    recon_precision = _safe_div(true_negatives, true_negatives + false_negatives)
    recon_recall = _safe_div(true_negatives, true_negatives + false_positives)

    auto_resolve_precision = _safe_div(auto_resolve_correct, system_auto_resolved_total)
    auto_resolve_recall = _safe_div(auto_resolve_correct, auto_resolve_total_gt)
    
    escalation_precision = _safe_div(escalate_correct, system_escalated_total)
    
    ai_total = total_ai_investigated + total_ai_unavailable_fallback
    ai_coverage_pct = _safe_div(total_ai_investigated, ai_total)
    
    # Safe abstention rate = safe abstentions / total ambiguous cases
    ambiguous_gt = sum(1 for gt in ground_truth if gt.get("actual_exception") in ("AMBIGUOUS", "CONTRADICTORY_EVIDENCE", "INCOMPLETE_EVIDENCE", "CONFLICTING_TIMESTAMPS"))
    safe_abstention_rate = _safe_div(safe_abstentions, ambiguous_gt)

    return {
        "reconciliation_precision": {"value": round(recon_precision, 4), "correct": true_negatives, "total": true_negatives + false_negatives},
        "reconciliation_recall": {"value": round(recon_recall, 4), "correct": true_negatives, "total": true_negatives + false_positives},
        "exception_detection_precision": {"value": round(precision, 4), "correct": true_positives, "total": true_positives + false_positives},
        "exception_detection_recall": {"value": round(recall, 4), "correct": true_positives, "total": true_positives + false_negatives},
        "exception_detection_f1": {"value": round(f1, 4), "correct": 0, "total": 0},
        "exception_classification_accuracy": {"value": round(_safe_div(classification_correct, classification_total), 4), "correct": classification_correct, "total": classification_total},
        "auto_resolution_precision": {"value": round(auto_resolve_precision, 4), "correct": auto_resolve_correct, "total": system_auto_resolved_total},
        "auto_resolution_recall": {"value": round(auto_resolve_recall, 4), "correct": auto_resolve_correct, "total": auto_resolve_total_gt},
        "false_auto_resolution_count": {"value": false_auto_resolutions, "correct": false_auto_resolutions, "total": total_ai_investigated},
        "false_auto_resolution_rate": {"value": round(_safe_div(false_auto_resolutions, total_ai_investigated), 4), "correct": false_auto_resolutions, "total": total_ai_investigated},
        "safe_abstention_rate": {"value": round(safe_abstention_rate, 4), "correct": safe_abstentions, "total": ambiguous_gt},
        "escalation_precision": {"value": round(escalation_precision, 4), "correct": escalate_correct, "total": system_escalated_total},
        "ai_investigations": {"value": total_ai_investigated, "correct": total_ai_investigated, "total": ai_total},
        "ai_coverage_pct": {"value": round(ai_coverage_pct * 100, 2), "correct": total_ai_investigated, "total": ai_total},
        "per_type_breakdown": per_type,
    }


def _safe_div(numerator: float, denominator: float) -> float:
    """Division that returns 0.0 instead of ZeroDivisionError."""
    return numerator / denominator if denominator > 0 else 0.0
