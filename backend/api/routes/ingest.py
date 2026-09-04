"""
LedgerLens — Ingestion & Demo Load API Routes
Accepts CSV uploads or loads the built-in demo dataset.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import (
    BankTransaction,
    Merchant,
    Order,
    Payment,
    ReconciliationRun,
    Refund,
    Settlement,
)
from backend.services.normalization import normalize_dataframe

router = APIRouter()

# Valid column sets for each source type
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "orders":            ["id", "merchant_id", "customer_id", "order_ts", "amount", "currency", "status"],
    "payments":          ["id", "order_id", "payment_ts", "amount", "currency", "status", "method"],
    "refunds":           ["id", "payment_id", "order_id", "refund_ts", "amount", "status"],
    "settlements":       ["id", "payment_id", "order_id", "settlement_ts", "amount", "fee_amount", "tax_amount", "status"],
    "bank_transactions": ["id", "transaction_ts", "credit_amount", "debit_amount"],
}

_MODEL_MAP = {
    "orders":            Order,
    "payments":          Payment,
    "refunds":           Refund,
    "settlements":       Settlement,
    "bank_transactions": BankTransaction,
}


async def _load_csv_to_db(
    df: pd.DataFrame,
    table: str,
    run_id: str,
    db: AsyncSession,
) -> tuple[int, list[str]]:
    """Normalize and bulk-insert a DataFrame for a given table."""
    good_rows, rejected_ids = normalize_dataframe(df, table, run_id)

    model_class = _MODEL_MAP[table]
    for row in good_rows:
        # Convert Decimal to float for SQLAlchemy Numeric columns that need it
        db.add(model_class(**row))

    return len(good_rows), rejected_ids


@router.post("/ingest")
async def ingest_csv_files(
    orders: UploadFile | None = File(default=None),
    payments: UploadFile | None = File(default=None),
    refunds: UploadFile | None = File(default=None),
    settlements: UploadFile | None = File(default=None),
    bank_transactions: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest CSV files for any combination of source types.
    Validates required columns before inserting.
    Creates a ReconciliationRun in PENDING status.
    """
    uploads = {
        "orders":            orders,
        "payments":          payments,
        "refunds":           refunds,
        "settlements":       settlements,
        "bank_transactions": bank_transactions,
    }

    if not any(v for v in uploads.values()):
        raise HTTPException(status_code=400, detail="At least one CSV file must be provided.")

    run_id = str(uuid.uuid4())
    run = ReconciliationRun(id=run_id, status="PENDING")
    db.add(run)
    await db.flush()

    results: dict[str, dict] = {}
    total_records = 0
    validation_errors: list[str] = []

    for table, upload in uploads.items():
        if upload is None:
            continue

        # Validate file type
        if not upload.filename or not upload.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail=f"File for '{table}' must be a .csv file. Got: {upload.filename}",
            )

        content = await upload.read()
        try:
            import io
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse CSV for '{table}': {str(e)}. "
                       "Check that the file is valid CSV.",
            )

        # Column validation
        required = set(REQUIRED_COLUMNS.get(table, []))
        present = set(df.columns.str.lower())
        missing = required - present
        if missing:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"Missing required columns in '{table}'",
                    "missing_columns": sorted(missing),
                    "present_columns": sorted(present),
                    "hint": f"Required: {sorted(required)}",
                },
            )

        inserted, rejected = await _load_csv_to_db(df, table, run_id, db)
        results[table] = {"rows_in_file": len(df), "inserted": inserted, "rejected": rejected}
        total_records += inserted

    run.record_count = total_records
    await db.commit()

    return {
        "run_id": run_id,
        "status": "PENDING",
        "total_records_inserted": total_records,
        "per_table": results,
        "next_step": f"POST /api/reconcile/{run_id} to run reconciliation",
    }


@router.post("/demo/load")
async def load_demo_dataset(db: AsyncSession = Depends(get_db)):
    """
    Load the deterministic demo dataset (seed=42, ~150 records).
    Idempotent: generates fresh data each call with the same seed.
    Returns a run_id ready for reconciliation.
    """
    from generator.data_generator import DataGenerator

    run_id = str(uuid.uuid4())
    run = ReconciliationRun(id=run_id, status="PENDING")
    db.add(run)
    await db.flush()

    # Ensure demo merchant exists
    merchant_id = "MERCHANT-001"
    from sqlalchemy import select
    m_stmt = select(Merchant).where(Merchant.id == merchant_id)
    m_result = await db.execute(m_stmt)
    if not m_result.scalar_one_or_none():
        db.add(Merchant(id=merchant_id, name="Demo Merchant (LedgerLens)"))
        await db.flush()

    # Generate demo batch (deterministic, seed=42, 150 records)
    gen = DataGenerator(seed=42)
    batch = gen.generate(n_records=150, run_id=run_id)

    from datetime import datetime

    def _parse_dates(data: dict) -> dict:
        parsed = {}
        for k, v in data.items():
            if isinstance(v, str) and k.endswith("_ts"):
                parsed[k] = datetime.fromisoformat(v)
            else:
                parsed[k] = v
        return parsed

    # Insert all records
    total = 0
    for order_data in batch.orders:
        db.add(Order(**{k: v for k, v in _parse_dates(order_data).items() if v is not None or k in ("order_id", "payment_reference")}))
        total += 1
    for payment_data in batch.payments:
        db.add(Payment(**_parse_dates(payment_data)))
        total += 1
    for refund_data in batch.refunds:
        db.add(Refund(**_parse_dates(refund_data)))
    for settlement_data in batch.settlements:
        db.add(Settlement(**_parse_dates(settlement_data)))
    for bank_data in batch.bank_transactions:
        db.add(BankTransaction(**_parse_dates(bank_data)))

    run.record_count = len(batch.payments)  # Payment chains = "records"
    await db.commit()

    exception_counts: dict[str, int] = {}
    for gt in batch.ground_truth:
        exception_counts[gt.actual_exception] = exception_counts.get(gt.actual_exception, 0) + 1

    return {
        "run_id": run_id,
        "status": "PENDING",
        "message": "Demo dataset loaded (seed=42, deterministic)",
        "records": {
            "orders": len(batch.orders),
            "payments": len(batch.payments),
            "refunds": len(batch.refunds),
            "settlements": len(batch.settlements),
            "bank_transactions": len(batch.bank_transactions),
        },
        "injected_exceptions": exception_counts,
        "next_step": f"POST /api/reconcile/{run_id} to run reconciliation",
    }


@router.post("/eval/load")
async def load_eval_dataset(db: AsyncSession = Depends(get_db)):
    """Inject the deterministic 50-record eval dataset directly into DB."""
    from sqlalchemy import text
    await db.execute(text("DELETE FROM bank_transactions"))
    await db.execute(text("DELETE FROM settlements"))
    await db.execute(text("DELETE FROM refunds"))
    await db.execute(text("DELETE FROM payments"))
    await db.execute(text("DELETE FROM orders"))
    await db.commit()

    from generator.data_generator import DataGenerator
    run_id = str(uuid.uuid4())
    run = ReconciliationRun(id=run_id, status="PENDING")
    db.add(run)

    # Generate 50 records deterministically (keeps exceptions < 15, within free tier rate limit)
    gen = DataGenerator(seed=42)
    batch = gen.generate(n_records=50, run_id=run_id)

    from datetime import datetime

    def _parse_dates(data: dict) -> dict:
        parsed = {}
        for k, v in data.items():
            if isinstance(v, str) and k.endswith("_ts"):
                parsed[k] = datetime.fromisoformat(v)
            else:
                parsed[k] = v
        return parsed

    # Insert all records
    for order_data in batch.orders:
        db.add(Order(**{k: v for k, v in _parse_dates(order_data).items() if v is not None or k in ("order_id", "payment_reference")}))
    for payment_data in batch.payments:
        db.add(Payment(**_parse_dates(payment_data)))
    for refund_data in batch.refunds:
        db.add(Refund(**_parse_dates(refund_data)))
    for settlement_data in batch.settlements:
        db.add(Settlement(**_parse_dates(settlement_data)))
    for bank_data in batch.bank_transactions:
        db.add(BankTransaction(**_parse_dates(bank_data)))

    run.record_count = len(batch.payments)
    await db.commit()

    return {
        "run_id": run_id,
        "status": "PENDING",
        "message": "Eval dataset loaded (seed=42, deterministic)",
        "records": {
            "orders": len(batch.orders),
            "payments": len(batch.payments),
            "refunds": len(batch.refunds),
            "settlements": len(batch.settlements),
            "bank_transactions": len(batch.bank_transactions),
        }
    }
