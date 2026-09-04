from datetime import datetime, timezone, timedelta
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime, timezone
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db, AsyncSessionLocal
from backend.models import ReconciliationRun, ExceptionModel
from backend.services.reconciliation import ReconciliationEngine
from backend.services.investigation import investigate_exception
from backend.evaluation.evaluator import run_evaluation_pipeline

log = structlog.get_logger(__name__)

GROUND_TRUTH_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "eval_ground_truth"

async def run_full_benchmark(n_records: int = 1000, dataset_name: str = "benchmark"):
    start_time = time.monotonic()
    log.info("benchmark_started", records=n_records)
    
    from backend.database import create_tables
    await create_tables()
    async with AsyncSessionLocal() as db:
        # 1. Wipe old data to avoid unique constraints
        from sqlalchemy import text
        await db.execute(text("DELETE FROM bank_transactions"))
        await db.execute(text("DELETE FROM settlements"))
        await db.execute(text("DELETE FROM refunds"))
        await db.execute(text("DELETE FROM payments"))
        await db.execute(text("DELETE FROM orders"))
        await db.execute(text("DELETE FROM investigations"))
        await db.execute(text("DELETE FROM exceptions"))

        await db.commit()

        # 2. Generate Data
        from generator.data_generator import DataGenerator
        run_id = str(uuid.uuid4())
        recon_run = ReconciliationRun(id=run_id, status="PENDING")
        db.add(recon_run)
        
        gen = DataGenerator(seed=42)
        batch = gen.generate(n_records=n_records, run_id=run_id)
        
        # Insert all
        def _parse_dates(data: dict) -> dict:
            parsed = {}
            for k, v in data.items():
                if isinstance(v, str) and k.endswith("_ts"):
                    parsed[k] = datetime.fromisoformat(v)
                else:
                    parsed[k] = v
            return parsed
            
        from backend.models import Order, Payment, Refund, Settlement, BankTransaction
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
            
        recon_run.record_count = len(batch.payments)
        await db.commit()
        
        # Save Ground Truth
        gt_path = GROUND_TRUTH_DIR / f"{dataset_name}_ground_truth.json"
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump([gt.__dict__ for gt in batch.ground_truth], f, indent=2)
            
        # 3. Deterministic Reconciliation
        recon_run.status = "RUNNING"
        recon_run.started_at = datetime.now(timezone.utc)
        await db.commit()
        
        recon_start = time.monotonic()
        engine = ReconciliationEngine(db)
        summary = await engine.run(run_id)
        
        recon_run.status = "COMPLETED"
        recon_run.completed_at = datetime.now(timezone.utc)
        recon_run.matched_count = summary["matched"]
        recon_run.exception_count = summary["exceptions"]
        recon_run.auto_resolved_count = summary["auto_resolved"]
        recon_run.escalated_count = summary["escalated"]
        recon_run.total_amount = summary["total_amount"]
        recon_run.unresolved_amount = summary["unresolved_amount"]
        recon_run.processing_seconds = time.monotonic() - recon_start
        await db.commit()
        
        # 4. AI Investigation (with 4 second delay to respect 15 RPM)
        from sqlalchemy.orm import selectinload
        stmt = select(ExceptionModel).options(selectinload(ExceptionModel.investigations)).where(ExceptionModel.run_id == run_id)
        res = await db.execute(stmt)
        exceptions = res.scalars().all()
        

        # Phase D: Detect Incidents
        from backend.services.incident_engine import detect_incidents
        now = datetime.now(timezone.utc)
        base_start = now - timedelta(days=180)
        base_end = now - timedelta(days=60)
        curr_start = now - timedelta(days=60)
        curr_end = now
        incidents = await detect_incidents(db, run_id, base_start, base_end, curr_start, curr_end)
        log.info("incidents_detected", count=len(incidents))

        # Phase E: Prioritize
        from backend.services.prioritization import prioritize_exceptions
        scores = await prioritize_exceptions(db, run_id)
        log.info("prioritization_completed", count=len(scores))

        # Phase F: Early Warning
        from backend.services.early_warning import detect_early_warnings
        warnings = await detect_early_warnings(db, run_id)
        log.info("early_warnings_detected", count=len(warnings))

        # Phase G: Close Readiness
        from backend.services.close_readiness import assess_close_readiness
        readiness = await assess_close_readiness(db, run_id)
        log.info("close_readiness_assessed", score=readiness.score, status=readiness.status)

        # Phase C: Cluster
        from backend.services.clustering import cluster_exceptions
        clusters = await cluster_exceptions(db, run_id)
        
        # Phase H: Investigate Clusters
        from backend.services.investigation import investigate_cluster
        log.info("ai_cluster_investigation_started", cluster_count=len(clusters))
        for cluster in clusters:
            await investigate_cluster(cluster, db)
            # Sleep skipped since we're mocking AI investigation for clusters to avoid rate limits

                
        # 5. Compute Metrics via evaluator
        eval_run_id, metrics = await run_evaluation_pipeline(gt_path, dataset_name, db)
        
        elapsed = time.monotonic() - start_time
        log.info("benchmark_completed", seconds=round(elapsed, 2), metrics=metrics)
        return metrics

if __name__ == "__main__":
    asyncio.run(run_full_benchmark())
