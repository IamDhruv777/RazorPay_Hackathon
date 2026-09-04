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
from backend.services.investigation import investigate_exception, GeminiClient
from backend.evaluation.evaluator import run_evaluation_pipeline

# Monkey patch to simulate 429 Rate Limit Error
async def _mock_investigate(self, prompt: str):
    raise Exception("429 Too Many Requests - Rate Limit Exceeded")

GeminiClient.investigate = _mock_investigate

async def run_failure_test(n_records: int = 100, dataset_name: str = "failure_test"):
    print("Running FAILURE TEST: AI Unavailable / Rate Limited")
    async with AsyncSessionLocal() as db:
        # 1. Wipe old data
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
        
        gen = DataGenerator(seed=999)
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
        import os
        GROUND_TRUTH_DIR = Path(os.getcwd()) / "data" / "eval_ground_truth"
        gt_path = GROUND_TRUTH_DIR / f"{dataset_name}_ground_truth.json"
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump([gt.__dict__ for gt in batch.ground_truth], f, indent=2)
            
        # 3. Deterministic Reconciliation
        print("Running deterministic reconciliation...")
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
        await db.commit()
        print(f"Deterministic reconciliation complete. Found {summary['exceptions']} exceptions.")
        
        # 4. AI Investigation (Mocked to fail)
        from sqlalchemy.orm import selectinload
        stmt = select(ExceptionModel).options(selectinload(ExceptionModel.investigations)).where(ExceptionModel.run_id == run_id)
        res = await db.execute(stmt)
        exceptions = res.scalars().all()
        
        print("Engaging AI (simulating 429 API failure)...")
        for exc in exceptions:
            if exc.status == "PENDING":
                await investigate_exception(exc, db)
                await db.commit()
                
        # 5. Compute Metrics via evaluator
        print("Evaluating results...")
        eval_run_id, metrics = await run_evaluation_pipeline(gt_path, dataset_name, db)
        
        # Verification Checks
        assert metrics["total_ai_unavailable_fallback"] == len(exceptions), "Fallback count mismatch!"
        assert metrics["false_auto_resolution_count"]["value"] == 0, "AI hallucinated an auto-resolution during a failure!"
        assert metrics["ai_investigations"]["value"] == 0, "AI actually investigated something?"
        print("==================================================")
        print("FAILURE TEST PASSED")
        print(f"Total Exceptions: {len(exceptions)}")
        print(f"Safely Escalated Fallbacks: {metrics['total_ai_unavailable_fallback']}")
        print(f"False Auto-Resolutions: 0 (No hallucinations)")
        print("Deterministic reconciliation remained functional.")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_failure_test())
