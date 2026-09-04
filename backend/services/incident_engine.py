from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from backend.models import Payment, ExceptionModel, Incident
import uuid
from datetime import datetime

async def detect_incidents(db: AsyncSession, run_id: str, baseline_start: datetime, baseline_end: datetime, current_start: datetime, current_end: datetime):
    # This function compares current period against baseline.
    # It aggregates volume and exception types.
    
    # 1. Total volume comparison
    stmt = select(func.count(Payment.id), func.sum(Payment.amount)).where(and_(Payment.payment_ts >= current_start, Payment.payment_ts <= current_end))
    curr_count, curr_vol = (await db.execute(stmt)).first()
    curr_count = curr_count or 0; curr_vol = curr_vol or 0.0

    stmt = select(func.count(Payment.id), func.sum(Payment.amount)).where(and_(Payment.payment_ts >= baseline_start, Payment.payment_ts <= baseline_end))
    base_count, base_vol = (await db.execute(stmt)).first()
    base_count = base_count or 0; base_vol = base_vol or 0.0
    
    # 2. Exception comparison
    stmt = select(ExceptionModel.type, func.count(ExceptionModel.id), func.sum(ExceptionModel.financial_exposure)).where(
        and_(ExceptionModel.transaction_ts >= current_start, ExceptionModel.transaction_ts <= current_end)
    ).group_by(ExceptionModel.type)
    curr_exc = {row[0]: {"count": row[1], "exposure": float(row[2] or 0)} for row in (await db.execute(stmt)).all()}

    stmt = select(ExceptionModel.type, func.count(ExceptionModel.id), func.sum(ExceptionModel.financial_exposure)).where(
        and_(ExceptionModel.transaction_ts >= baseline_start, ExceptionModel.transaction_ts <= baseline_end)
    ).group_by(ExceptionModel.type)
    base_exc = {row[0]: {"count": row[1], "exposure": float(row[2] or 0)} for row in (await db.execute(stmt)).all()}

    incidents = []
    
    # Find types that spiked significantly (e.g. > 50% increase and at least 5 absolute increase)
    for exc_type, curr_data in curr_exc.items():
        base_data = base_exc.get(exc_type, {"count": 0, "exposure": 0.0})
        if curr_data["count"] > base_data["count"] * 1.5 and (curr_data["count"] - base_data["count"]) >= 1:
            # We detected a systemic incident!
            inc = Incident(
                id=f"INCIDENT-{uuid.uuid4().hex[:8]}",
                title=f"Spike in {exc_type}",
                start_ts=current_start,
                end_ts=current_end,
                exposure=curr_data["exposure"],
                confidence=0.85,
                status="DETECTED"
            )
            db.add(inc)
            incidents.append(inc)
            
    await db.commit()
    return incidents

