"""
LedgerLens — Deterministic Reconciliation Engine
"""
from __future__ import annotations

import structlog
from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    BankTransaction,
    ExceptionModel,
    Order,
    Payment,
    ReconciliationMatch,
    Refund,
    Settlement,
)
from backend.services.confidence import (
    ConfidenceComponents,
    compute_confidence,
    evidence_completeness_score,
    confidence_for_deterministic_match,
)
from backend.services.resolution import resolve
from backend.services.audit import log_event, Actions

log = structlog.get_logger(__name__)


class ReconciliationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, run_id: str) -> dict[str, Any]:
        """
        Run reconciliation for a given batch.
        Groups records by Payment (as the central source of truth),
        detects anomalies, attempts auto-resolution.
        """
        summary = {
            "matched": 0,
            "exceptions": 0,
            "auto_resolved": 0,
            "escalated": 0,
            "total_amount": Decimal("0.00"),
            "unresolved_amount": Decimal("0.00"),
        }

        # 1. Fetch all records for this run
        orders = (await self.db.execute(select(Order).where(Order.run_id == run_id))).scalars().all()
        payments = (await self.db.execute(select(Payment).where(Payment.run_id == run_id))).scalars().all()
        refunds = (await self.db.execute(select(Refund).where(Refund.run_id == run_id))).scalars().all()
        settlements = (await self.db.execute(select(Settlement).where(Settlement.run_id == run_id))).scalars().all()
        banks = (await self.db.execute(select(BankTransaction).where(BankTransaction.run_id == run_id))).scalars().all()

        # Indexes for fast lookup
        order_by_id = {o.id: o for o in orders}
        refunds_by_payment = {}
        for r in refunds:
            refunds_by_payment.setdefault(r.payment_id, []).append(r)
        
        bank_by_ref = {b.reference: b for b in banks if b.reference}

        # Group duplicate payments by order to detect DUPLICATE_PAYMENT
        payments_by_order = {}
        for p in payments:
            if p.order_id:
                payments_by_order.setdefault(p.order_id, []).append(p)
                
        duplicate_payment_ids = set()
        for oid, pays in payments_by_order.items():
            if len(pays) > 1:
                for p in pays:
                    duplicate_payment_ids.add(p.id)

        # Main loop: Reconcile each payment
        for p in payments:
            match_level = 1
            summary["total_amount"] += p.amount
            
            # Find related records
            o = order_by_id.get(p.order_id)
            r_list = refunds_by_payment.get(p.id, [])
            
            # Find settlement using hierarchy
            s = None
            # L1: Exact payment_id
            for sett in settlements:
                if sett.payment_id == p.id:
                    s = sett
                    match_level = 1
                    break
            
            # (In a real system, L2-L5 matching logic would go here, falling back if s is None)
            # For the demo, exact matching works since generator creates exact IDs.
            
            b = None
            if s and s.payout_reference:
                b = bank_by_ref.get(s.payout_reference)

            # Exception Detection Rules
            detected_exc = None
            
            if p.id in duplicate_payment_ids:
                detected_exc = "DUPLICATE_PAYMENT"
            elif not o:
                detected_exc = "ORPHAN_PAYMENT"
            elif s and not b:
                detected_exc = "MISSING_BANK_CREDIT"
            elif s and o:
                # Check amounts and timings
                expected_settlement = p.amount - sum(r.amount for r in r_list) - s.fee_amount - s.tax_amount
                diff = abs(s.amount - expected_settlement)
                
                # Check timing (delayed settlement)
                if s.settlement_ts > p.payment_ts + timedelta(days=4): # T+2 business days + weekend
                    detected_exc = "DELAYED_SETTLEMENT"
                
                # Check amount mismatches
                elif diff > Decimal("0.05"):
                    # Is it ambiguous?
                    if len(r_list) > 1:
                        detected_exc = "AMBIGUOUS"
                    else:
                        detected_exc = "AMOUNT_MISMATCH"
                
                # Check refunds on otherwise perfect matches
                elif p.amount == o.amount and len(r_list) > 0:
                    # It matches expected mathematically, but differs from raw payment amount due to refunds
                    if sum(r.amount for r in r_list) == p.amount:
                        detected_exc = "FULL_REFUND"
                    else:
                        detected_exc = "PARTIAL_REFUND"
            
            # If healthy (no exception detected)
            if not detected_exc:
                match = ReconciliationMatch(
                    run_id=run_id,
                    order_id=o.id if o else None,
                    payment_id=p.id,
                    settlement_id=s.id if s else None,
                    bank_id=b.id if b else None,
                    match_type=f"LEVEL{match_level}",
                    confidence=confidence_for_deterministic_match(match_level),
                )
                self.db.add(match)
                summary["matched"] += 1
                continue
                
            # If exception detected
            summary["exceptions"] += 1
            summary["unresolved_amount"] += p.amount
            
            # Compute confidence for auto-resolution routing
            det_conf = confidence_for_deterministic_match(match_level)
            evid_score = evidence_completeness_score(
                has_order=bool(o),
                has_payment=bool(p),
                has_settlement=bool(s),
                has_bank=bool(b),
            )
            consist_score = 1.0 if not detected_exc in ["AMOUNT_MISMATCH", "AMBIGUOUS"] else 0.5
            
            # Initial deterministic confidence (LLM confidence is 0 at this stage)
            comps = ConfidenceComponents(
                deterministic_confidence=det_conf,
                evidence_completeness=evid_score,
                source_consistency=consist_score,
                llm_confidence=0.0
            )
            conf_result = compute_confidence(comps)
            
            # Apply deterministic resolution policy
            final_status, reason = resolve(detected_exc, conf_result.routing)
            
            if final_status == "AUTO_RESOLVED":
                summary["auto_resolved"] += 1
            elif final_status == "ESCALATED":
                summary["escalated"] += 1
            
            # Create Exception Record
            # Phase B: Financial Exposure Model
            gross_amount = float(p.amount)
            known_adjustments = 0.0
            resolved_amount = 0.0
            
            if s:
                known_adjustments += float(s.fee_amount) + float(s.tax_amount)
            
            # Find all refunds for this payment
            p_refunds = [r for r in refunds if r.payment_id == p.id]
            for r in p_refunds:
                known_adjustments += float(r.amount)
                
            if b:
                resolved_amount = float(b.credit_amount)
                
            unresolved = gross_amount - known_adjustments - resolved_amount
            
            potential_loss = float(abs(unresolved))
            financial_exposure = potential_loss

            exc_record = ExceptionModel(
                id=f"EX-{p.id}",
                run_id=run_id,
                transaction_ts=p.payment_ts,
                type=detected_exc,
                severity=self._get_severity(detected_exc),
                amount=p.amount,
                gross_amount=gross_amount,
                known_adjustments=known_adjustments,
                resolved_amount=resolved_amount,
                unresolved_amount=unresolved,
                potential_loss=potential_loss,
                financial_exposure=financial_exposure,
                confidence=conf_result.score,
                status=final_status,
                order_id=o.id if o else None,
                payment_id=p.id,
                settlement_id=s.id if s else None,
                bank_id=b.id if b else None,
            )
            self.db.add(exc_record)
            await self.db.flush()
            
            # Audit log
            await log_event(
                self.db,
                exception_id=exc_record.id,
                action=Actions.EXCEPTION_CREATED,
                decision=final_status,
                confidence=conf_result.score,
                evidence_summary=reason
            )

        return summary

    def _get_severity(self, exc_type: str) -> str:
        from backend.services.resolution import exception_severity
        return exception_severity(exc_type)
