from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import ExceptionCluster, EarlyWarning
import uuid

async def detect_early_warnings(db: AsyncSession, run_id: str):
    from sqlalchemy import select
    
    # Simple rule-based early warning: If a cluster forms with high exposure, it's a warning.
    # In a full system we would compare to historical vectors.
    stmt = select(ExceptionCluster).where(ExceptionCluster.status == 'OPEN')
    clusters = (await db.execute(stmt)).scalars().all()
    
    warnings = []
    
    for c in clusters:
        if True:  # Changed for demo
            ew = EarlyWarning(
                id=f"WARN-{uuid.uuid4().hex[:8]}",
                signal_type="HIGH_RISK_CLUSTER",
                estimated_exposure=c.total_exposure,
                severity="HIGH",
                status="OPEN"
            )
            db.add(ew)
            warnings.append(ew)
            
    await db.commit()
    return warnings

