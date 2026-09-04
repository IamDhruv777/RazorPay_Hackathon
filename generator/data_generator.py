"""
LedgerLens   Deterministic Synthetic Data Generator
Seed=42   reproducible across all machines and runs.

Generates linked records: Order   Payment   Refund   Settlement   Bank
with intentionally injected exceptions whose ground truth is saved
to a SEPARATE file (data/eval_ground_truth/) never read by the app.

Usage:
    python -m generator.data_generator --mode dev     # 1000 records
    python -m generator.data_generator --mode eval    # 500 records
    python -m generator.data_generator --mode demo    # 150 records

Output CSVs (in data/{mode}/):
    orders.csv, payments.csv, refunds.csv, settlements.csv, bank_transactions.csv
"""
from __future__ import annotations

import argparse
import json
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from generator.distributions import (
    BANK_NARRATION_TEMPLATES,
    EXCEPTION_DISTRIBUTION,
    MERCHANT_NAMES,
    REFUND_REASONS,
    compute_fee,
    compute_settlement_amount,
    sample_amount,
    sample_payment_method,
    sample_settlement_delay,
)

#     Output Paths                                                              
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
GROUND_TRUTH_DIR = ROOT / "data" / "eval_ground_truth"


#     ID Generation                                                             

def _make_id(prefix: str, n: int) -> str:
    return f"{prefix}-{n:05d}"


#     Date/Time Helpers                                                         

BASE_DATE = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _rand_ts(rng: np.random.Generator, days_spread: int = 180) -> datetime:
    """Random timestamp within [BASE_DATE, BASE_DATE + days_spread]."""
    offset_seconds = int(rng.integers(0, days_spread * 86400))
    return BASE_DATE + timedelta(seconds=offset_seconds)


def _business_days_later(ts: datetime, days: int) -> datetime:
    """Advance by `days` calendar days (simplified   no holiday calendar)."""
    return ts + timedelta(days=days)


#     Ground Truth Record                                                       

@dataclass
class GroundTruthRecord:
    payment_id: str
    order_id: str
    actual_exception: str          # e.g. "FEE_DIFFERENCE" or "HEALTHY"
    expected_resolution: str       # AUTO_RESOLVE / ESCALATE / REVIEW / NONE
    expected_root_cause: str       # human-readable cause
    injected: bool = True
    incident_id: str | None = None
    cluster_id: str | None = None



#     Raw Record Containers                                                     

@dataclass
class GeneratedBatch:
    orders: list[dict[str, Any]] = field(default_factory=list)
    payments: list[dict[str, Any]] = field(default_factory=list)
    refunds: list[dict[str, Any]] = field(default_factory=list)
    settlements: list[dict[str, Any]] = field(default_factory=list)
    bank_transactions: list[dict[str, Any]] = field(default_factory=list)
    ground_truth: list[GroundTruthRecord] = field(default_factory=list)


#     Core Generator                                                            

class DataGenerator:
    """
    Generates a linked batch of financial records with intentionally injected
    exceptions. Ground truth is tracked separately and never written to the
    main data CSVs.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.py_rng = random.Random(seed)
        self._order_counter = 0
        self._payment_counter = 0
        self._refund_counter = 0
        self._settlement_counter = 0
        self._bank_counter = 0
        self._exception_counter = 0

    #    ID helpers                                                             

    def _oid(self) -> str:
        self._order_counter += 1
        return _make_id("ORD", self._order_counter)

    def _pid(self) -> str:
        self._payment_counter += 1
        return _make_id("PAY", self._payment_counter)

    def _rid(self) -> str:
        self._refund_counter += 1
        return _make_id("REF", self._refund_counter)

    def _sid(self) -> str:
        self._settlement_counter += 1
        return _make_id("SET", self._settlement_counter)

    def _bid(self) -> str:
        self._bank_counter += 1
        return _make_id("BNK", self._bank_counter)

    def _gref(self) -> str:
        """Unique gateway reference (e.g. Razorpay internal)."""
        return f"RZP{self._payment_counter:08d}"

    def _pref(self) -> str:
        """Payout reference used on settlement + bank."""
        return f"POUT{self._settlement_counter:08d}"

    #    Healthy record builder                                                 

    def _make_healthy_chain(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[dict, dict, dict | None, dict, dict, GroundTruthRecord]:
        """
        Build a clean Order -> Payment -> Settlement -> Bank chain.
        No refund in the healthy case.
        Returns (order, payment, refund_or_None, settlement, bank, gt).
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)

        order = {
            "id": self._oid(), "merchant_id": merchant_id, "customer_id": customer_id,
            "amount": amount, "currency": "INR", "status": "paid",
            "order_ts": order_ts.isoformat(), "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"], "amount": amount,
            "currency": "INR", "status": "captured", "method": sample_payment_method(self.rng),
            "gateway_reference": self._gref(), "payment_ts": payment_ts.isoformat(), "run_id": run_id,
        }
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = payment_ts + timedelta(days=delay_days)
        settlement_amount, fee, tax = compute_settlement_amount(amount)
        payout_ref = self._pref()

        settlement = {
            "id": self._sid(), "payment_id": payment["id"], "order_id": order["id"],
            "amount": settlement_amount, "fee_amount": fee,
            "tax_amount": tax, 
            "status": "processed", "payout_reference": payout_ref,
            "settlement_ts": settlement_ts.isoformat(), "run_id": run_id,
        }
        
        narration_template = str(self.rng.choice(BANK_NARRATION_TEMPLATES))
        narration = narration_template.format(ref=payout_ref)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 12)))

        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="HEALTHY",
            expected_resolution="NONE",
            expected_root_cause="Perfect match",
            injected=False,
        )

        return order, payment, None, settlement, bank, gt
    #    Exception injectors                                                    

    def _inject_fee_difference(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        FEE_DIFFERENCE: order amount = payment amount, but settlement has correct
        fee deducted. System should auto-resolve by explaining the fee.
        No actual anomaly - this tests whether the reconciliation engine
        understands fee deductions vs. treating them as mismatches.
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))

        settlement_amount, fee, tax = compute_settlement_amount(amount)
        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="FEE_DIFFERENCE",
            expected_resolution="AUTO_RESOLVE",
            expected_root_cause=f"Settlement {settlement_amount} = Payment {amount} - Fee {fee} - Tax {tax}",
        )
        return [order], [payment], [], [settlement], [bank], gt

    def _inject_partial_refund(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        PARTIAL_REFUND: Payment captured, then partially refunded.
        Settlement = payment - partial_refund - fee - tax.
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)

        # Refund is 10%-50% of the payment
        refund_frac = round(float(self.rng.uniform(0.1, 0.5)), 2)
        refund_amount = round(amount * refund_frac, 2)
        refund_ts = payment_ts + timedelta(hours=int(self.rng.integers(2, 48)))

        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))
        settlement_amount, fee, tax = compute_settlement_amount(amount, refund_amount)

        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        refund = {
            "id": self._rid(), "payment_id": payment["id"], "order_id": order["id"],
            "refund_ts": refund_ts.isoformat(), "amount": refund_amount,
            "status": "processed", "reason": self.py_rng.choice(REFUND_REASONS),
            "run_id": run_id,
        }
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="PARTIAL_REFUND",
            expected_resolution="AUTO_RESOLVE",
            expected_root_cause=(
                f"Payment {amount} - Refund {refund_amount} - Fee {fee} - Tax {tax} = "
                f"Settlement {settlement_amount}"
            ),
        )
        return [order], [payment], [refund], [settlement], [bank], gt

    def _inject_full_refund(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """FULL_REFUND: Payment fully refunded. Settlement amount = 0 (or very small)."""
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        refund_ts = payment_ts + timedelta(hours=int(self.rng.integers(1, 24)))
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))
        settlement_amount, fee, tax = compute_settlement_amount(amount, amount)
        # settlement_amount will be near 0 or slightly negative (fee only)

        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "refunded",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "refunded", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        refund = {
            "id": self._rid(), "payment_id": payment["id"], "order_id": order["id"],
            "refund_ts": refund_ts.isoformat(), "amount": amount,
            "status": "processed", "reason": self.py_rng.choice(REFUND_REASONS),
            "run_id": run_id,
        }
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": max(0.0, settlement_amount), "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": max(0.0, settlement_amount), "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="FULL_REFUND",
            expected_resolution="AUTO_RESOLVE",
            expected_root_cause=f"Full refund of {amount} processed. Settlement near zero.",
        )
        return [order], [payment], [refund], [settlement], [bank], gt

    def _inject_delayed_settlement(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """DELAYED_SETTLEMENT: Settlement arrives 5-7 days late instead of T+2."""
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = int(self.rng.integers(5, 8))  # 5-7 days   late
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 12)))
        settlement_amount, fee, tax = compute_settlement_amount(amount)
        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="DELAYED_SETTLEMENT",
            expected_resolution="REVIEW",
            expected_root_cause=f"Settlement delayed {delay_days} days (expected T+2).",
        )
        return [order], [payment], [], [settlement], [bank], gt

    def _inject_missing_bank_credit(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        MISSING_BANK_CREDIT (CRITICAL): Settlement record exists but
        no corresponding bank transaction was found.
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        settlement_amount, fee, tax = compute_settlement_amount(amount)
        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        #   No bank transaction generated   this IS the anomaly
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="MISSING_BANK_CREDIT",
            expected_resolution="ESCALATE",
            expected_root_cause=f"Settlement {settlement_amount} exists (ref: {payout_ref}), no matching bank credit found.",
        )
        return [order], [payment], [], [settlement], [], gt

    def _inject_duplicate_payment(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        DUPLICATE_PAYMENT (CRITICAL): Same order paid twice.
        Two payments, two settlements, two bank credits.
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts1 = order_ts + timedelta(minutes=int(self.rng.integers(1, 10)))
        payment_ts2 = payment_ts1 + timedelta(minutes=int(self.rng.integers(1, 5)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts1, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))
        settlement_amount, fee, tax = compute_settlement_amount(amount)
        gateway_ref1 = self._gref()
        payout_ref1 = self._pref()
        gateway_ref2 = self._gref()
        payout_ref2 = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment1 = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts1.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref1, "run_id": run_id,
        }
        payment2 = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts2.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref2, "run_id": run_id,
        }
        order["payment_reference"] = payment1["id"]
        settlement1 = {
            "id": self._sid(), "payment_id": payment1["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref1, "run_id": run_id,
        }
        settlement2 = {
            "id": self._sid(), "payment_id": payment2["id"],
            "order_id": order["id"],
            "settlement_ts": (settlement_ts + timedelta(hours=1)).isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref2, "run_id": run_id,
        }
        narration1 = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref1)
        narration2 = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref2)
        bank1 = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref1, "narration": narration1, "run_id": run_id,
        }
        bank2 = {
            "id": self._bid(),
            "transaction_ts": (bank_ts + timedelta(hours=1)).isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref2, "narration": narration2, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment1["id"], order_id=order["id"],
            actual_exception="DUPLICATE_PAYMENT",
            expected_resolution="ESCALATE",
            expected_root_cause=f"Order {order['id']} has 2 captured payments: {payment1['id']}, {payment2['id']}",
        )
        return (
            [order],
            [payment1, payment2],
            [],
            [settlement1, settlement2],
            [bank1, bank2],
            gt,
        )

    def _inject_orphan_payment(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """ORPHAN_PAYMENT: Payment exists but references a non-existent order."""
        payment_ts = _rand_ts(self.rng)
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        gateway_ref = self._gref()

        payment = {
            "id": self._pid(), "order_id": None,  # No order!
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id="",
            actual_exception="ORPHAN_PAYMENT",
            expected_resolution="REVIEW",
            expected_root_cause=f"Payment {payment['id']} ({amount}) has no linked order.",
        )
        return [], [payment], [], [], [], gt

    def _inject_amount_mismatch(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        AMOUNT_MISMATCH: Settlement amount does not match any explainable
        combination (no refund to account for the gap).
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))

        correct_settlement, fee, tax = compute_settlement_amount(amount)
        # Introduce an unexplained discrepancy (not a fee, not a refund)
        discrepancy = round(float(self.rng.choice([50, 100, 150, 200, 250])), 2)
        wrong_settlement = round(correct_settlement - discrepancy, 2)

        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": wrong_settlement, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": wrong_settlement, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="AMOUNT_MISMATCH",
            expected_resolution="ESCALATE",
            expected_root_cause=(
                f"Settlement {wrong_settlement} differs from expected {correct_settlement} "
                f"by {discrepancy}. No refund found to explain gap."
            ),
        )
        return [order], [payment], [], [settlement], [bank], gt

    def _inject_ambiguous(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], GroundTruthRecord]:
        """
        AMBIGUOUS: Two plausible explanations, neither definitively eliminates the other.
        Implemented as: two small refunds + settlement differs by an amount
        that could be explained by either refund alone or a fee calculation,
        making the root cause uncertain.
        """
        order_ts = base_ts if base_ts else _rand_ts(self.rng)
        # Jitter the order_ts slightly by a few minutes if base_ts was provided, so they aren't completely identical
        if base_ts:
            order_ts += timedelta(seconds=int(self.rng.integers(-3600, 3600)))
        payment_ts = order_ts + timedelta(minutes=int(self.rng.integers(1, 30)))
        amount = sample_amount(self.rng)
        method = sample_payment_method(self.rng)
        delay_days = sample_settlement_delay(self.rng)
        settlement_ts = _business_days_later(payment_ts, delay_days)
        bank_ts = settlement_ts + timedelta(hours=int(self.rng.integers(1, 6)))

        # Two small refunds of similar amounts   ambiguous which applies
        refund_a = round(amount * 0.15, 2)
        refund_b = round(amount * 0.12, 2)
        refund_ts_a = payment_ts + timedelta(hours=int(self.rng.integers(1, 12)))
        refund_ts_b = payment_ts + timedelta(hours=int(self.rng.integers(12, 36)))

        # Settlement uses only ONE of the refunds (unclear which)
        settlement_amount, fee, tax = compute_settlement_amount(amount, refund_a)
        gateway_ref = self._gref()
        payout_ref = self._pref()

        order = {
            "id": self._oid(), "merchant_id": merchant_id,
            "customer_id": customer_id, "order_ts": order_ts.isoformat(),
            "amount": amount, "currency": "INR", "status": "paid",
            "payment_reference": None, "run_id": run_id,
        }
        payment = {
            "id": self._pid(), "order_id": order["id"],
            "payment_ts": payment_ts.isoformat(), "amount": amount,
            "currency": "INR", "status": "captured", "method": method,
            "gateway_reference": gateway_ref, "run_id": run_id,
        }
        order["payment_reference"] = payment["id"]
        refund1 = {
            "id": self._rid(), "payment_id": payment["id"], "order_id": order["id"],
            "refund_ts": refund_ts_a.isoformat(), "amount": refund_a,
            "status": "processed", "reason": "Customer request - size issue", "run_id": run_id,
        }
        refund2 = {
            "id": self._rid(), "payment_id": payment["id"], "order_id": order["id"],
            "refund_ts": refund_ts_b.isoformat(), "amount": refund_b,
            "status": "processed", "reason": "Quality not as described", "run_id": run_id,
        }
        settlement = {
            "id": self._sid(), "payment_id": payment["id"],
            "order_id": order["id"], "settlement_ts": settlement_ts.isoformat(),
            "amount": settlement_amount, "fee_amount": fee, "tax_amount": tax,
            "status": "processed", "payout_reference": payout_ref, "run_id": run_id,
        }
        narration = self.py_rng.choice(BANK_NARRATION_TEMPLATES).format(ref=payout_ref)
        bank = {
            "id": self._bid(), "transaction_ts": bank_ts.isoformat(),
            "credit_amount": settlement_amount, "debit_amount": 0.00,
            "reference": payout_ref, "narration": narration, "run_id": run_id,
        }
        gt = GroundTruthRecord(
            payment_id=payment["id"], order_id=order["id"],
            actual_exception="AMBIGUOUS",
            expected_resolution="ESCALATE",
            expected_root_cause=(
                f"Two refunds ({refund_a}, {refund_b}) present. Settlement suggests "
                f"only one was applied but cannot determine which definitively."
            ),
        )
        return [order], [payment], [refund1, refund2], [settlement], [bank], gt

    #    Exception dispatch table                                               

    _INJECTORS = {
        "FEE_DIFFERENCE": "_inject_fee_difference",
        "TAX_DIFFERENCE": "_inject_tax_difference",
        "PARTIAL_REFUND": "_inject_partial_refund",
        "FULL_REFUND": "_inject_full_refund",
        "DELAYED_SETTLEMENT": "_inject_delayed_settlement",
        "MISSING_SETTLEMENT": "_inject_missing_settlement",
        "MISSING_BANK_CREDIT": "_inject_missing_bank_credit",
        "DUPLICATE_PAYMENT": "_inject_duplicate_payment",
        "ORPHAN_PAYMENT": "_inject_orphan_payment",
        "AMOUNT_MISMATCH": "_inject_amount_mismatch",
        "INCORRECT_REFERENCE": "_inject_incorrect_reference",
        "SPLIT_SETTLEMENT": "_inject_split_settlement",
        "MULTIPLE_REFUNDS": "_inject_multiple_refunds",
        "CONFLICTING_TIMESTAMPS": "_inject_conflicting_timestamps",
        "INCOMPLETE_EVIDENCE": "_inject_incomplete_evidence",
        "AMBIGUOUS": "_inject_ambiguous",
        "CONTRADICTORY_EVIDENCE": "_inject_contradictory_evidence",
    }

    #    Main generate method                                                   


    def _inject_tax_difference(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        orders, payments, refunds, settlements, banks, gt = self._inject_fee_difference(merchant_id, customer_id, run_id)
        gt.actual_exception = "TAX_DIFFERENCE"
        # Overcharge tax slightly
        settlements[0]["tax_amount"] += 1.0
        settlements[0]["amount"] -= 1.0
        banks[0]["credit_amount"] -= 1.0
        return orders, payments, refunds, settlements, banks, gt

    def _inject_missing_settlement(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "MISSING_SETTLEMENT"
        gt.expected_resolution = "ESCALATE"
        # Return all except settlement
        return [order], [payment], ([refund] if refund else []), [], [bank], gt

    def _inject_incorrect_reference(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "INCORRECT_REFERENCE"
        gt.expected_resolution = "AUTO_RESOLVE"
        bank["narration"] = bank["narration"].replace(settlement["payout_reference"], "UNKNOWN-REF")
        return [order], [payment], ([refund] if refund else []), [settlement], [bank], gt

    def _inject_split_settlement(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "SPLIT_SETTLEMENT"
        gt.expected_resolution = "ESCALATE"
        
        # Split the bank transaction into two
        bank1 = bank.copy()
        bank2 = bank.copy()
        bank1["id"] = self._bid()
        bank2["id"] = self._bid()
        bank1["credit_amount"] = round(bank["credit_amount"] / 2, 2)
        bank2["credit_amount"] = round(bank["credit_amount"] - bank1["credit_amount"], 2)
        
        return [order], [payment], ([refund] if refund else []), [settlement], [bank1, bank2], gt

    def _inject_multiple_refunds(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "MULTIPLE_REFUNDS"
        gt.expected_resolution = "ESCALATE"
        
        refunds = []
        if not refund:
            refund = {
                "id": self._rid(),
                "payment_id": payment["id"],
                "amount": round(payment["amount"] / 2, 2),
                "refund_ts": _business_days_later(datetime.fromisoformat(payment["payment_ts"]), 1).isoformat(),
                "status": "processed",
                "reason": "Customer request",
                "run_id": run_id,
            }
        
        refund2 = refund.copy()
        if 'refund_ts' not in refund2: refund2['refund_ts'] = refund.get('refund_ts', payment['payment_ts'])
        refund2["id"] = self._rid()
        refund2["refund_ts"] = _business_days_later(datetime.fromisoformat(refund.get("refund_ts", payment["payment_ts"])), 1).isoformat()
        refunds = [refund, refund2]
        
        return [order], [payment], refunds, [settlement], [bank], gt

    def _inject_conflicting_timestamps(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "CONFLICTING_TIMESTAMPS"
        gt.expected_resolution = "ESCALATE"
        # Bank transaction happened before payment?
        
        from datetime import datetime, timedelta
        dt = datetime.fromisoformat(bank["transaction_ts"])
        dt -= timedelta(days=10)
        bank["transaction_ts"] = dt.isoformat()

        return [order], [payment], ([refund] if refund else []), [settlement], [bank], gt

    def _inject_incomplete_evidence(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "INCOMPLETE_EVIDENCE"
        gt.expected_resolution = "ESCALATE"
        # Missing order and payment entirely
        return [], [], [], [settlement], [bank], gt

    def _inject_contradictory_evidence(
        self, merchant_id: str, customer_id: str, run_id: str | None = None, base_ts: datetime | None = None
    ):
        order, payment, refund, settlement, bank, gt = self._make_healthy_chain(merchant_id, customer_id, run_id)
        gt.actual_exception = "CONTRADICTORY_EVIDENCE"
        gt.expected_resolution = "ESCALATE"
        # Settlement says 100 fee, but bank says something completely different and UTR doesn't match
        settlement["fee_amount"] = 100.0
        bank["credit_amount"] = settlement["amount"] + 50.0
        bank["narration"] = "RTGS/COMPLETELY/WRONG/UTR"
        return [order], [payment], ([refund] if refund else []), [settlement], [bank], gt


    def generate(self, n_records: int, run_id: str | None = None) -> GeneratedBatch:
        batch = GeneratedBatch()
        from datetime import timedelta

        plan: list[dict] = []
        
        n_incident_records = int(n_records * 0.10)
        n_background_records = n_records - n_incident_records
        
        # INCIDENT 1: Bank Settlement Delay
        i1_records = int(n_incident_records * 0.4)
        i1_start = BASE_DATE + timedelta(days=30, hours=14)
        for _ in range(i1_records):
            exc = "DELAYED_SETTLEMENT" if self.py_rng.random() < 0.7 else "MISSING_BANK_CREDIT"
            plan.append({"type": exc, "ts": i1_start, "incident_id": "INC-001", "cluster_id": "CLUSTER-BANK-DELAY"})
            
        # INCIDENT 2: Gateway Fee Routing Bug
        i2_records = int(n_incident_records * 0.3)
        i2_start = BASE_DATE + timedelta(days=90, hours=9)
        for _ in range(i2_records):
            exc = "FEE_DIFFERENCE" if self.py_rng.random() < 0.5 else "TAX_DIFFERENCE"
            plan.append({"type": exc, "ts": i2_start, "incident_id": "INC-002", "cluster_id": "CLUSTER-FEE-BUG"})
            
        # INCIDENT 3: System API Retry Loop
        i3_records = n_incident_records - i1_records - i2_records
        i3_start = BASE_DATE + timedelta(days=150, hours=11)
        for _ in range(i3_records):
            exc = "DUPLICATE_PAYMENT" if self.py_rng.random() < 0.5 else "MULTIPLE_REFUNDS"
            plan.append({"type": exc, "ts": i3_start, "incident_id": "INC-003", "cluster_id": "CLUSTER-RETRY-LOOP"})
            
        # Background exceptions
        background_exceptions = []
        for exc_type, fraction in EXCEPTION_DISTRIBUTION.items():
            count = max(1, round(n_background_records * fraction))
            background_exceptions.extend([exc_type] * count)
            
        for exc_type in background_exceptions:
            plan.append({"type": exc_type, "ts": _rand_ts(self.rng), "incident_id": None, "cluster_id": None})
            
        # Pad with healthy
        while len(plan) < n_records:
            plan.append({"type": None, "ts": _rand_ts(self.rng), "incident_id": None, "cluster_id": None})
            
        # Shuffle
        self.py_rng.shuffle(plan)

        merchant_id = "MERCHANT-001"
        cust_counter = 0

        for slot in plan:
            cust_counter += 1
            customer_id = f"CUST-{cust_counter:06d}"
            
            slot_type = slot["type"]
            slot_ts = slot["ts"]

            if slot_type is None:
                # Healthy chain
                order, payment, refund, settlement, bank, gt = self._make_healthy_chain(
                    merchant_id, customer_id, run_id, base_ts=slot_ts
                )
                batch.orders.append(order)
                batch.payments.append(payment)
                if refund:
                    batch.refunds.append(refund)
                batch.settlements.append(settlement)
                batch.bank_transactions.append(bank)
                
                gt.incident_id = slot["incident_id"]
                gt.cluster_id = slot["cluster_id"]
                batch.ground_truth.append(gt)
            else:
                # Inject exception
                injector_name = self._INJECTORS[slot_type]
                injector = getattr(self, injector_name)
                orders, payments, refunds, settlements, banks, gt = injector(
                    merchant_id, customer_id, run_id, base_ts=slot_ts
                )
                batch.orders.extend(orders)
                batch.payments.extend(payments)
                batch.refunds.extend(refunds)
                batch.settlements.extend(settlements)
                batch.bank_transactions.extend(banks)
                
                gt.incident_id = slot["incident_id"]
                gt.cluster_id = slot["cluster_id"]
                batch.ground_truth.append(gt)

        return batch

    #    Save to CSV                                                            

    def save(self, batch: GeneratedBatch, mode: str) -> None:
        """
        Writes CSVs to data/{mode}/ and ground truth to data/eval_ground_truth/{mode}_gt.json.
        Ground truth is NEVER written inside data/{mode}/ so the app can't accidentally read it.
        """
        out_dir = DATA_DIR / mode
        out_dir.mkdir(parents=True, exist_ok=True)
        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

        def _save(records: list[dict], name: str) -> None:
            if records:
                df = pd.DataFrame(records)
                df.to_csv(out_dir / f"{name}.csv", index=False)
                print(f"  [ok] {name}.csv -- {len(records)} rows")

        print(f"\n[generator] Writing {mode} dataset to {out_dir}/")
        _save(batch.orders, "orders")
        _save(batch.payments, "payments")
        _save(batch.refunds, "refunds")
        _save(batch.settlements, "settlements")
        _save(batch.bank_transactions, "bank_transactions")

        # Ground truth   separate path, separate file
        gt_path = GROUND_TRUTH_DIR / f"{mode}_ground_truth.json"
        gt_records = [
            {
                "payment_id": gt.payment_id,
                "order_id": gt.order_id,
                "actual_exception": gt.actual_exception,
                "expected_resolution": gt.expected_resolution,
                "expected_root_cause": gt.expected_root_cause,
                "injected": gt.injected,
            }
            for gt in batch.ground_truth
        ]
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt_records, f, indent=2, ensure_ascii=False)

        print(f"  [ok] Ground truth ({len(gt_records)} exceptions) -> {gt_path}")
        print(f"\n[generator] Summary:")
        print(f"  Orders:             {len(batch.orders)}")
        print(f"  Payments:           {len(batch.payments)}")
        print(f"  Refunds:            {len(batch.refunds)}")
        print(f"  Settlements:        {len(batch.settlements)}")
        print(f"  Bank transactions:  {len(batch.bank_transactions)}")
        print(f"  Exceptions injected:{len(batch.ground_truth)}")
        healthy = len(batch.payments) - len(batch.ground_truth)
        print(f"  Healthy chains:     {healthy}")
        exc_types: dict[str, int] = {}
        for gt in batch.ground_truth:
            exc_types[gt.actual_exception] = exc_types.get(gt.actual_exception, 0) + 1
        print("  Exception breakdown:")
        for exc_type, count in sorted(exc_types.items()):
            print(f"    {exc_type:<25} {count}")


#     CLI                                                                       

MODES = {
    "dev":  1000,
    "eval": 50,
    "demo": 150,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="LedgerLens synthetic data generator")
    parser.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="demo",
        help="Dataset size: dev=1000, eval=500, demo=150",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    n = MODES[args.mode]
    print(f"[generator] Generating {args.mode} dataset ({n} records, seed={args.seed})")
    gen = DataGenerator(seed=args.seed)
    batch = gen.generate(n)
    gen.save(batch, args.mode)


if __name__ == "__main__":
    main()
