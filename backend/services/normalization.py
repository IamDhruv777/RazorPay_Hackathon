"""
LedgerLens — Data Normalization Service
Cleans and standardizes raw ingested financial records before reconciliation.

Rules:
- Every transformation is logged — no silent alterations
- Ambiguous data is flagged, not silently corrected
- Timezone: all timestamps converted to UTC
- Amounts: stripped of currency symbols, commas, whitespace → Decimal
- IDs: strip whitespace, preserve original casing
- Currency: default to INR if blank/unknown
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import structlog

log = structlog.get_logger(__name__)


# ─── Amount Normalization ─────────────────────────────────────────────────────

_AMOUNT_PATTERN = re.compile(r"[₹,\s]")  # Characters to strip from amounts


def normalize_amount(raw: Any, field_name: str, record_id: str) -> Decimal | None:
    """
    Normalize an amount field to Decimal with 2 decimal places.

    Handles: "₹5,000.00", "5000", "5,000 INR", 5000.0 (float), 5000 (int)
    Returns None + logs if the value cannot be parsed.
    Does NOT silently round to 0 on parse failure.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        log.warning("amount_missing", field=field_name, record_id=record_id)
        return None
    if isinstance(raw, (int, float)):
        try:
            val = Decimal(str(round(float(raw), 2)))
            return val
        except InvalidOperation:
            log.error("amount_parse_failed", field=field_name, record_id=record_id, raw=raw)
            return None
    if isinstance(raw, str):
        cleaned = _AMOUNT_PATTERN.sub("", raw.strip())
        # Remove trailing currency codes like "INR"
        cleaned = re.sub(r"[A-Z]{3}$", "", cleaned).strip()
        try:
            val = Decimal(cleaned)
            if str(raw).strip() != cleaned:
                log.info(
                    "amount_normalized",
                    field=field_name,
                    record_id=record_id,
                    raw=raw,
                    normalized=str(val),
                )
            return val
        except InvalidOperation:
            log.error("amount_parse_failed", field=field_name, record_id=record_id, raw=raw)
            return None
    log.error("amount_unexpected_type", field=field_name, record_id=record_id, type=type(raw).__name__)
    return None


# ─── Timestamp Normalization ──────────────────────────────────────────────────

_TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y",
]


def normalize_timestamp(raw: Any, field_name: str, record_id: str) -> datetime | None:
    """
    Parse and normalize a timestamp to UTC-aware datetime.
    Logs the format used if it was non-ISO (indicates input data quality issues).
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        log.warning("timestamp_missing", field=field_name, record_id=record_id)
        return None

    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            log.info("timestamp_assumed_utc", field=field_name, record_id=record_id)
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)

    if isinstance(raw, str):
        raw = raw.strip()
        for fmt in _TS_FORMATS:
            try:
                dt = datetime.strptime(raw, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                if fmt != "%Y-%m-%dT%H:%M:%S%z":
                    log.info(
                        "timestamp_non_iso",
                        field=field_name,
                        record_id=record_id,
                        format_used=fmt,
                        raw=raw,
                    )
                return dt
            except ValueError:
                continue
        log.error("timestamp_parse_failed", field=field_name, record_id=record_id, raw=raw)
        return None

    log.error("timestamp_unexpected_type", field=field_name, record_id=record_id, type=type(raw).__name__)
    return None


# ─── ID Normalization ─────────────────────────────────────────────────────────

def normalize_id(raw: Any, field_name: str, record_id: str = "") -> str | None:
    """Strip whitespace from IDs. Preserve original casing. Return None if blank."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    cleaned = str(raw).strip()
    if not cleaned:
        return None
    if cleaned != str(raw):
        log.info("id_whitespace_stripped", field=field_name, record_id=record_id, raw=repr(raw))
    return cleaned


def normalize_currency(raw: Any, field_name: str, record_id: str) -> str:
    """Normalize currency code. Default to INR. Warn if something unexpected."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)) or str(raw).strip() == "":
        log.info("currency_defaulted_to_inr", field=field_name, record_id=record_id)
        return "INR"
    code = str(raw).strip().upper()
    if len(code) != 3:
        log.warning("currency_unusual", field=field_name, record_id=record_id, raw=raw)
        return "INR"
    return code


# ─── DataFrame Row Normalizer ─────────────────────────────────────────────────

def normalize_order_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize a single order row. Returns None if the row is too malformed to use."""
    rid = normalize_id(row.get("id"), "id") or "UNKNOWN"
    amount = normalize_amount(row.get("amount"), "amount", rid)
    if amount is None:
        log.error("order_row_rejected", reason="unparseable_amount", record_id=rid)
        return None
    return {
        "id":               rid,
        "merchant_id":      normalize_id(row.get("merchant_id"), "merchant_id", rid),
        "customer_id":      normalize_id(row.get("customer_id"), "customer_id", rid),
        "order_ts":         normalize_timestamp(row.get("order_ts"), "order_ts", rid),
        "amount":           amount,
        "currency":         normalize_currency(row.get("currency"), "currency", rid),
        "status":           str(row.get("status", "")).strip().lower() or "unknown",
        "payment_reference": normalize_id(row.get("payment_reference"), "payment_reference", rid),
        "run_id":           normalize_id(row.get("run_id"), "run_id", rid),
    }


def normalize_payment_row(row: dict[str, Any]) -> dict[str, Any] | None:
    rid = normalize_id(row.get("id"), "id") or "UNKNOWN"
    amount = normalize_amount(row.get("amount"), "amount", rid)
    if amount is None:
        log.error("payment_row_rejected", reason="unparseable_amount", record_id=rid)
        return None
    return {
        "id":               rid,
        "order_id":         normalize_id(row.get("order_id"), "order_id", rid),
        "payment_ts":       normalize_timestamp(row.get("payment_ts"), "payment_ts", rid),
        "amount":           amount,
        "currency":         normalize_currency(row.get("currency"), "currency", rid),
        "status":           str(row.get("status", "")).strip().lower() or "unknown",
        "method":           str(row.get("method", "")).strip().lower() or "unknown",
        "gateway_reference": normalize_id(row.get("gateway_reference"), "gateway_reference", rid),
        "run_id":           normalize_id(row.get("run_id"), "run_id", rid),
    }


def normalize_refund_row(row: dict[str, Any]) -> dict[str, Any] | None:
    rid = normalize_id(row.get("id"), "id") or "UNKNOWN"
    amount = normalize_amount(row.get("amount"), "amount", rid)
    if amount is None:
        log.error("refund_row_rejected", reason="unparseable_amount", record_id=rid)
        return None
    return {
        "id":         rid,
        "payment_id": normalize_id(row.get("payment_id"), "payment_id", rid),
        "order_id":   normalize_id(row.get("order_id"), "order_id", rid),
        "refund_ts":  normalize_timestamp(row.get("refund_ts"), "refund_ts", rid),
        "amount":     amount,
        "status":     str(row.get("status", "")).strip().lower() or "unknown",
        "reason":     str(row.get("reason", "")).strip() or None,
        "run_id":     normalize_id(row.get("run_id"), "run_id", rid),
    }


def normalize_settlement_row(row: dict[str, Any]) -> dict[str, Any] | None:
    rid = normalize_id(row.get("id"), "id") or "UNKNOWN"
    amount = normalize_amount(row.get("amount"), "amount", rid)
    if amount is None:
        log.error("settlement_row_rejected", reason="unparseable_amount", record_id=rid)
        return None
    return {
        "id":              rid,
        "payment_id":      normalize_id(row.get("payment_id"), "payment_id", rid),
        "order_id":        normalize_id(row.get("order_id"), "order_id", rid),
        "settlement_ts":   normalize_timestamp(row.get("settlement_ts"), "settlement_ts", rid),
        "amount":          amount,
        "fee_amount":      normalize_amount(row.get("fee_amount"), "fee_amount", rid) or Decimal("0.00"),
        "tax_amount":      normalize_amount(row.get("tax_amount"), "tax_amount", rid) or Decimal("0.00"),
        "status":          str(row.get("status", "")).strip().lower() or "unknown",
        "payout_reference": normalize_id(row.get("payout_reference"), "payout_reference", rid),
        "run_id":          normalize_id(row.get("run_id"), "run_id", rid),
    }


def normalize_bank_row(row: dict[str, Any]) -> dict[str, Any] | None:
    rid = normalize_id(row.get("id"), "id") or "UNKNOWN"
    return {
        "id":              rid,
        "transaction_ts":  normalize_timestamp(row.get("transaction_ts"), "transaction_ts", rid),
        "credit_amount":   normalize_amount(row.get("credit_amount"), "credit_amount", rid) or Decimal("0.00"),
        "debit_amount":    normalize_amount(row.get("debit_amount"), "debit_amount", rid) or Decimal("0.00"),
        "reference":       normalize_id(row.get("reference"), "reference", rid),
        "narration":       str(row.get("narration", "")).strip() or None,
        "run_id":          normalize_id(row.get("run_id"), "run_id", rid),
    }


# ─── CSV DataFrame Normalizer ─────────────────────────────────────────────────

def normalize_dataframe(
    df: pd.DataFrame,
    table: str,
    run_id: str,
) -> tuple[list[dict], list[str]]:
    """
    Normalize all rows in a DataFrame for a given table.

    Returns:
        (good_rows, rejected_ids) — rejected rows are not inserted.
    """
    row_normalizers = {
        "orders":            normalize_order_row,
        "payments":          normalize_payment_row,
        "refunds":           normalize_refund_row,
        "settlements":       normalize_settlement_row,
        "bank_transactions": normalize_bank_row,
    }
    normalizer = row_normalizers.get(table)
    if not normalizer:
        raise ValueError(f"Unknown table: {table}")

    good, rejected = [], []
    for _, row in df.iterrows():
        raw = row.to_dict()
        raw["run_id"] = run_id
        normalized = normalizer(raw)
        if normalized is None:
            rejected.append(str(raw.get("id", "UNKNOWN")))
        else:
            good.append(normalized)

    log.info(
        "normalization_complete",
        table=table,
        total=len(df),
        accepted=len(good),
        rejected=len(rejected),
        run_id=run_id,
    )
    return good, rejected
