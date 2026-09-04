"""
LedgerLens — Resolution Policy Unit Tests

The most important test in this file:
    test_critical_types_cannot_be_auto_resolved

This test asserts that MISSING_BANK_CREDIT and DUPLICATE_PAYMENT
are always escalated, regardless of confidence score or LLM recommendation.
If this test fails, the financial safety guarantee is broken.
"""
import pytest

from backend.services.resolution import (
    AUTO_RESOLVE_ELIGIBLE_TYPES,
    CRITICAL_TYPES,
    ESCALATE_ONLY_TYPES,
    REVIEW_ONLY_TYPES,
    exception_severity,
    resolve,
)


class TestCriticalTypePolicy:
    """
    CRITICAL: These exception types must NEVER be auto-resolved.
    The LLM recommendation is overridden if it conflicts.
    """

    @pytest.mark.parametrize("exc_type", list(CRITICAL_TYPES))
    def test_critical_types_cannot_be_auto_resolved(self, exc_type: str):
        """Even with perfect confidence + LLM recommending auto-resolve → ESCALATED."""
        status, reason = resolve(
            exception_type=exc_type,
            confidence_routing="AUTO_RESOLVE",
            llm_recommendation="AUTO_RESOLVE",
        )
        assert status == "ESCALATED", (
            f"SAFETY VIOLATION: {exc_type} was not escalated despite being CRITICAL. "
            f"Got status='{status}'. This indicates the financial safety policy has been bypassed."
        )

    @pytest.mark.parametrize("exc_type", list(CRITICAL_TYPES))
    def test_critical_types_always_escalated_regardless_of_llm(self, exc_type: str):
        """Test every possible LLM recommendation — all must result in ESCALATED."""
        for llm_rec in ["AUTO_RESOLVE", "REVIEW", "ESCALATE", None]:
            status, _ = resolve(
                exception_type=exc_type,
                confidence_routing="AUTO_RESOLVE",
                llm_recommendation=llm_rec,
            )
            assert status == "ESCALATED", (
                f"{exc_type} was not escalated with llm_recommendation={llm_rec!r}"
            )

    @pytest.mark.parametrize("exc_type", list(CRITICAL_TYPES))
    def test_critical_types_always_escalated_regardless_of_routing(self, exc_type: str):
        """Test every possible confidence routing — all must result in ESCALATED."""
        for routing in ["AUTO_RESOLVE", "REVIEW", "ESCALATE"]:
            status, _ = resolve(
                exception_type=exc_type,
                confidence_routing=routing,
            )
            assert status == "ESCALATED", (
                f"{exc_type} was not escalated with confidence_routing={routing!r}"
            )


class TestAutoResolveEligibleTypes:
    """GREEN exception types: eligible for auto-resolve at high confidence."""

    @pytest.mark.parametrize("exc_type", list(AUTO_RESOLVE_ELIGIBLE_TYPES))
    def test_auto_resolve_at_high_confidence(self, exc_type: str):
        status, _ = resolve(exc_type, confidence_routing="AUTO_RESOLVE")
        assert status == "AUTO_RESOLVED"

    @pytest.mark.parametrize("exc_type", list(AUTO_RESOLVE_ELIGIBLE_TYPES))
    def test_review_at_medium_confidence(self, exc_type: str):
        status, _ = resolve(exc_type, confidence_routing="REVIEW")
        assert status == "PENDING"

    @pytest.mark.parametrize("exc_type", list(AUTO_RESOLVE_ELIGIBLE_TYPES))
    def test_escalate_at_low_confidence(self, exc_type: str):
        status, _ = resolve(exc_type, confidence_routing="ESCALATE")
        assert status == "ESCALATED"


class TestEscalateOnlyTypes:
    """Types that always escalate regardless of confidence."""

    @pytest.mark.parametrize("exc_type", list(ESCALATE_ONLY_TYPES))
    def test_always_escalated(self, exc_type: str):
        for routing in ["AUTO_RESOLVE", "REVIEW", "ESCALATE"]:
            status, _ = resolve(exc_type, confidence_routing=routing)
            assert status == "ESCALATED", f"{exc_type} should always escalate (got {status})"


class TestReviewOnlyTypes:
    """Types that always go to review queue regardless of confidence."""

    @pytest.mark.parametrize("exc_type", list(REVIEW_ONLY_TYPES))
    def test_always_review(self, exc_type: str):
        for routing in ["AUTO_RESOLVE", "REVIEW", "ESCALATE"]:
            status, _ = resolve(exc_type, confidence_routing=routing)
            assert status == "PENDING", f"{exc_type} should always go to review (got {status})"


class TestSeverityMapping:
    def test_critical_types_are_red(self):
        for exc_type in CRITICAL_TYPES:
            assert exception_severity(exc_type) == "RED"

    def test_auto_resolve_types_are_green(self):
        for exc_type in AUTO_RESOLVE_ELIGIBLE_TYPES:
            assert exception_severity(exc_type) == "GREEN"

    def test_unknown_type_defaults_to_yellow(self):
        assert exception_severity("TOTALLY_UNKNOWN_TYPE") == "YELLOW"
