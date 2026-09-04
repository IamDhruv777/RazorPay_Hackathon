import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db, AsyncSessionLocal
from backend.models import Order, Payment, Refund, Settlement, BankTransaction

async def compute_baseline():
    GROUND_TRUTH_DIR = Path("data/eval_ground_truth")
    gt_path = GROUND_TRUTH_DIR / "benchmark_ground_truth.json"
    
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
        
    async with AsyncSessionLocal() as db:
        orders = (await db.execute(select(Order))).scalars().all()
        payments = (await db.execute(select(Payment))).scalars().all()
        refunds = (await db.execute(select(Refund))).scalars().all()
        settlements = (await db.execute(select(Settlement))).scalars().all()
        banks = (await db.execute(select(BankTransaction))).scalars().all()
        
    # EXACT-ID Matching Logic
    # An exception is raised if an exact match is NOT found across the chain using IDs only.
    # Order -> Payment (by order_id)
    # Payment -> Settlement (by payment_id)
    # Payment -> Refund (by payment_id)
    # Settlement -> Bank (by payout_reference == narration or similar? No, strict ID. Bank has no ID link to settlement except UTR in narration)
    
    # Simple strict exact match:
    # A chain is healthy IF:
    # payment has 1 order
    # payment has 1 settlement
    # if settlement, it has 1 bank transaction where narration CONTAINS payout_reference
    # amounts must match exactly:
    # order amount == payment amount
    # settlement amount == payment amount - fee - tax (wait, exact-id matching doesn't know fee math, so maybe it just assumes amount matches or uses strict fee)
    
    # Actually, a simple baseline: we just check if every Payment has a Settlement. If not, missing settlement exception.
    # If it has a settlement, does the settlement have a bank transaction? If not, missing bank credit.
    # Are amounts exactly equal?
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0
    
    for gt in ground_truth:
        actual_exc = gt.get("actual_exception", "HEALTHY")
        is_gt_exception = actual_exc not in ("HEALTHY", "", None)
        
        # Simulate baseline detection
        payment_id = gt["payment_id"]
        
        p = next((x for x in payments if x.id == payment_id), None)
        if not p:
            is_detected = True
        else:
            s = next((x for x in settlements if x.payment_id == p.id), None)
            if not s:
                is_detected = True
            else:
                b = next((x for x in banks if s.payout_reference in x.narration), None)
                if not b:
                    is_detected = True
                else:
                    if p.amount != s.amount + s.fee_amount + s.tax_amount:
                        is_detected = True
                    elif s.amount != b.credit_amount:
                        is_detected = True
                    else:
                        is_detected = False
                        
        if is_gt_exception and is_detected:
            true_positives += 1
        elif is_gt_exception and not is_detected:
            false_negatives += 1
        elif not is_gt_exception and is_detected:
            false_positives += 1
        else:
            true_negatives += 1
            
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print("=== EXACT-ID BASELINE ===")
    print(f"Precision: {precision*100:.2f}%")
    print(f"Recall: {recall*100:.2f}%")
    print(f"F1: {f1*100:.2f}%")
    print(f"TP: {true_positives}, FP: {false_positives}, FN: {false_negatives}, TN: {true_negatives}")

if __name__ == "__main__":
    asyncio.run(compute_baseline())
