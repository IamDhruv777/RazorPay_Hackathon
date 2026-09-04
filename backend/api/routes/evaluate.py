"""
LedgerLens — Evaluation API Route
Runs the evaluation pipeline against held-out ground truth.
Returns real metrics — never hardcoded.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import EvaluationResult, EvaluationRun, ExceptionModel, ReconciliationRun

router = APIRouter()

GROUND_TRUTH_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "eval_ground_truth"


@router.post("/evaluate")
async def run_evaluation(
    dataset: str = "eval",
    db: AsyncSession = Depends(get_db),
):
    """
    Run evaluation pipeline against a named ground truth dataset.
    Returns precision, recall, F1, auto-resolution accuracy,
    false-auto-resolution count, and baseline comparison.

    All numbers come from code, not hardcoded.
    """
    from backend.evaluation.evaluator import run_evaluation_pipeline

    gt_path = GROUND_TRUTH_DIR / f"{dataset}_ground_truth.json"
    if not gt_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Ground truth file not found: {gt_path}",
                "hint": f"Run: python -m generator.data_generator --mode {dataset}",
            },
        )

    eval_run_id, metrics = await run_evaluation_pipeline(gt_path, dataset, db)
    return {
        "evaluation_run_id": eval_run_id,
        "dataset": dataset,
        "metrics": metrics,
    }


@router.get("/evaluate/latest")
async def get_latest_evaluation(db: AsyncSession = Depends(get_db)):
    """Retrieve the most recent evaluation run."""
    stmt = select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(1)
    result = await db.execute(stmt)
    eval_run = result.scalar_one_or_none()
    if not eval_run:
        raise HTTPException(status_code=404, detail="No evaluation runs found")
    
    return await get_evaluation_results(eval_run.id, db)

@router.get("/evaluate/{eval_run_id}")
async def get_evaluation_results(
    eval_run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve stored evaluation results for a completed eval run."""
    stmt = select(EvaluationRun).where(EvaluationRun.id == eval_run_id)
    result = await db.execute(stmt)
    eval_run = result.scalar_one_or_none()
    if not eval_run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {eval_run_id} not found")

    results_stmt = select(EvaluationResult).where(EvaluationResult.run_id == eval_run_id)
    results_result = await db.execute(results_stmt)
    results = results_result.scalars().all()

    return {
        "id": eval_run.id,
        "dataset": eval_run.dataset_name,
        "record_count": eval_run.record_count,
        "started_at": eval_run.started_at.isoformat() if eval_run.started_at else None,
        "completed_at": eval_run.completed_at.isoformat() if eval_run.completed_at else None,
        "metrics": {r.metric_name: {"value": r.value, "metadata": r.metrics_metadata} for r in results},
    }
