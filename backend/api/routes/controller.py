import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from backend.database import get_db
from backend.models import ExceptionCluster, Incident, PriorityScore, EarlyWarning, CloseAssessment, ReconciliationRun, Payment

log = structlog.get_logger(__name__)
router = APIRouter()

async def get_latest_run_id(db: AsyncSession):
    stmt = select(ReconciliationRun.id).where(ReconciliationRun.status == "COMPLETED").order_by(desc(ReconciliationRun.started_at)).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

@router.get("/clusters/latest")
async def get_latest_clusters(db: AsyncSession = Depends(get_db)):
    stmt = select(ExceptionCluster).order_by(desc(ExceptionCluster.created_at)).limit(20)
    result = await db.execute(stmt)
    return {"clusters": result.scalars().all()}

@router.get("/incidents/latest")
async def get_latest_incidents(db: AsyncSession = Depends(get_db)):
    stmt = select(Incident).order_by(desc(Incident.created_at)).limit(10)
    result = await db.execute(stmt)
    return {"incidents": result.scalars().all()}

@router.get("/warnings/latest")
async def get_latest_warnings(db: AsyncSession = Depends(get_db)):
    stmt = select(EarlyWarning).order_by(desc(EarlyWarning.detected_at)).limit(10)
    result = await db.execute(stmt)
    return {"warnings": result.scalars().all()}

@router.get("/priority/latest")
async def get_latest_priority(db: AsyncSession = Depends(get_db)):
    stmt = select(PriorityScore).where(PriorityScore.entity_type == "EXCEPTION").order_by(desc(PriorityScore.total_score)).limit(10)
    result = await db.execute(stmt)
    return {"priorities": result.scalars().all()}

@router.get("/close-readiness/latest")
async def get_latest_close_readiness(db: AsyncSession = Depends(get_db)):
    run_id = await get_latest_run_id(db)
    if not run_id: return {"close_readiness": None}
    stmt = select(CloseAssessment).where(CloseAssessment.run_id == run_id).order_by(desc(CloseAssessment.created_at)).limit(1)
    result = await db.execute(stmt)
    return {"close_readiness": result.scalar_one_or_none()}

@router.get("/transactions/latest")
async def get_latest_transactions(db: AsyncSession = Depends(get_db)):
    stmt = select(Payment).order_by(desc(Payment.payment_ts)).limit(50)
    result = await db.execute(stmt)
    return {"transactions": result.scalars().all()}

