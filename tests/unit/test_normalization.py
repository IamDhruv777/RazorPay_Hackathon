"""
LedgerLens — Normalization Unit Tests
"""
from decimal import Decimal

import pytest

from backend.services.normalization import (
    normalize_amount,
    normalize_currency,
    normalize_id,
    normalize_timestamp,
)


class TestAmountNormalization:
    def test_plain_integer(self):
        result = normalize_amount(5000, "amount", "PAY-001")
        assert result == Decimal("5000")

    def test_float(self):
        result = normalize_amount(5000.50, "amount", "PAY-001")
        assert result == Decimal("5000.5")

    def test_rupee_symbol_and_commas(self):
        result = normalize_amount("₹5,000.00", "amount", "PAY-001")
        assert result == Decimal("5000.00")

    def test_amount_with_currency_code(self):
        result = normalize_amount("5000 INR", "amount", "PAY-001")
        assert result == Decimal("5000")

    def test_plain_string_number(self):
        result = normalize_amount("4410.32", "amount", "PAY-001")
        assert result == Decimal("4410.32")

    def test_none_returns_none(self):
        result = normalize_amount(None, "amount", "PAY-001")
        assert result is None

    def test_unparseable_string_returns_none(self):
        result = normalize_amount("not-a-number", "amount", "PAY-001")
        assert result is None


class TestTimestampNormalization:
    def test_iso_with_timezone(self):
        raw = "2025-03-15T10:30:00+05:30"
        result = normalize_timestamp(raw, "order_ts", "ORD-001")
        assert result is not None
        assert result.tzinfo is not None
        # Should be UTC
        assert result.hour == 5  # 10:30 IST = 05:00 UTC

    def test_iso_without_timezone_assumed_utc(self):
        raw = "2025-03-15T10:30:00"
        result = normalize_timestamp(raw, "order_ts", "ORD-001")
        assert result is not None
        assert result.hour == 10  # No conversion needed, already assumed UTC

    def test_none_returns_none(self):
        result = normalize_timestamp(None, "order_ts", "ORD-001")
        assert result is None

    def test_unparseable_returns_none(self):
        result = normalize_timestamp("not-a-date", "order_ts", "ORD-001")
        assert result is None


class TestIdNormalization:
    def test_strips_whitespace(self):
        assert normalize_id("  PAY-001  ", "id") == "PAY-001"

    def test_preserves_casing(self):
        assert normalize_id("PAY-001", "id") == "PAY-001"

    def test_none_returns_none(self):
        assert normalize_id(None, "id") is None

    def test_empty_string_returns_none(self):
        assert normalize_id("", "id") is None
        assert normalize_id("   ", "id") is None


class TestCurrencyNormalization:
    def test_valid_inr(self):
        assert normalize_currency("INR", "currency", "ORD-001") == "INR"

    def test_lowercase_normalized(self):
        assert normalize_currency("inr", "currency", "ORD-001") == "INR"

    def test_none_defaults_to_inr(self):
        assert normalize_currency(None, "currency", "ORD-001") == "INR"

    def test_blank_defaults_to_inr(self):
        assert normalize_currency("", "currency", "ORD-001") == "INR"

    def test_usd_passes_through(self):
        assert normalize_currency("USD", "currency", "ORD-001") == "USD"
