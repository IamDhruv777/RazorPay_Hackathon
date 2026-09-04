from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import ExceptionModel, PriorityScore
import uuid
from datetime import datetime, timezone

async def prioritize_exceptions(db: AsyncSession, run_id: str):
    from sqlalchemy import select
    
    stmt = select(ExceptionModel).where(ExceptionModel.run_id == run_id)
    exceptions = (await db.execute(stmt)).scalars().all()
    
    now = datetime.now(timezone.utc)
    
    scores = []
    
    for exc in exceptions:
        # 1. Financial Exposure Weight (0-40 points)
        # Assuming max exposure around 10,000 for normalization
        exposure = exc.financial_exposure or 0.0
        exposure_score = min(40.0, (exposure / 10000.0) * 40.0)
        
        # 2. Severity Weight (0-30 points)
        severity_score = {"RED": 30.0, "YELLOW": 15.0, "GREEN": 5.0}.get(exc.severity, 0.0)
        
        # 3. Age Weight (0-15 points)
        # Older is worse
        age_days = (now - exc.transaction_ts.replace(tzinfo=timezone.utc)).days if exc.transaction_ts else 0
        age_score = min(15.0, age_days * 1.5)
        
        # 4. Cluster Impact (0-15 points)
        cluster_score = 15.0 if exc.cluster_id else 0.0
        
        total = exposure_score + severity_score + age_score + cluster_score
        
        ps = PriorityScore(
            id=f"PRI-{uuid.uuid4().hex[:8]}",
            entity_type="EXCEPTION",
            entity_id=exc.id,
            total_score=total,
            component_scores={
                "exposure_score": round(exposure_score, 2),
                "severity_score": round(severity_score, 2),
                "age_score": round(age_score, 2),
                "cluster_score": round(cluster_score, 2)
            }
        )
        db.add(ps)
        scores.append(ps)
        
    await db.commit()
    return scores
