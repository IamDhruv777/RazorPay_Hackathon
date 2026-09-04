from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Payment, ExceptionModel, CloseAssessment
import uuid

async def assess_close_readiness(db: AsyncSession, run_id: str) -> CloseAssessment:
    from sqlalchemy import select, func
    
    # Total payments
    total_payments = (await db.execute(select(func.count(Payment.id)))).scalar() or 0
    
    # Exceptions
    stmt = select(ExceptionModel).where(ExceptionModel.run_id == run_id)
    exceptions = (await db.execute(stmt)).scalars().all()
    
    exception_count = len(exceptions)
    verified_pct = ((total_payments - exception_count) / total_payments * 100.0) if total_payments > 0 else 100.0
    
    critical_count = sum(1 for e in exceptions if e.severity == "RED")
    unresolved_exp = sum(e.financial_exposure or 0.0 for e in exceptions if e.status in ("PENDING", "ESCALATED"))
    
    score = 100.0
    
    # Deductions
    score -= (critical_count * 5)
    score -= (unresolved_exp / 1000.0)
    score = max(0.0, score)
    
    if score >= 95 and critical_count == 0:
        status = "READY"
    elif score >= 80:
        status = "READY_WITH_REVIEW"
    else:
        status = "NOT_READY"
        
    assessment = CloseAssessment(
        id=f"CLOSE-{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        score=round(score, 2),
        status=status,
        details={
            "verified_pct": round(verified_pct, 2),
            "critical_exceptions": critical_count,
            "unresolved_exposure": unresolved_exp
        }
    )
    db.add(assessment)
    await db.commit()
    
    return assessment
