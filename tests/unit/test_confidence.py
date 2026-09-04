"""
LedgerLens — Confidence Calculator Unit Tests
"""
import pytest

from backend.services.confidence import (
    ConfidenceComponents,
    compute_confidence,
    confidence_for_deterministic_match,
    evidence_completeness_score,
)


class TestConfidenceFormula:
    def test_perfect_evidence_gives_high_score(self):
        """
        Max possible score is 0.99 (not 1.0) because LLM confidence is capped at 0.95.
        Formula: 0.4*1 + 0.2*1 + 0.2*1 + 0.2*0.95 = 0.99
        This is intentional — the LLM cannot push the score to 100%.
        """
        components = ConfidenceComponents(
            deterministic_confidence=1.0,
            evidence_completeness=1.0,
            source_consistency=1.0,
            llm_confidence=1.0,
        )
        result = compute_confidence(components)
        assert result.score == pytest.approx(0.99, abs=0.001)   # LLM capped at 0.95
        assert result.routing == "AUTO_RESOLVE"

    def test_zero_evidence_gives_low_score(self):
        components = ConfidenceComponents(
            deterministic_confidence=0.0,
            evidence_completeness=0.0,
            source_consistency=0.0,
            llm_confidence=0.0,
        )
        result = compute_confidence(components)
        assert result.score == pytest.approx(0.0, abs=0.001)
        assert result.routing == "ESCALATE"

    def test_llm_confidence_is_capped_at_0_95(self):
        """LLM's own confidence cannot exceed 0.95 in the formula."""
        components = ConfidenceComponents(
            deterministic_confidence=0.0,
            evidence_completeness=0.0,
            source_consistency=0.0,
            llm_confidence=1.0,  # LLM claims 100% — should be capped
        )
        result = compute_confidence(components)
        # Only the LLM component contributes: 0.20 * 0.95 = 0.19
        assert result.score == pytest.approx(0.19, abs=0.001)

    def test_fee_difference_typical_case(self):
        """
        Typical FEE_DIFFERENCE: strong deterministic match (level 1),
        all records found, sources agree, LLM very confident.
        Should auto-resolve.
        """
        components = ConfidenceComponents(
            deterministic_confidence=1.0,   # exact payment_id match
            evidence_completeness=1.0,      # order + payment + settlement + bank all found
            source_consistency=1.0,         # amounts add up exactly
            llm_confidence=0.99,
        )
        result = compute_confidence(components)
        assert result.routing == "AUTO_RESOLVE"
        assert result.score >= 0.95

    def test_ambiguous_case_gives_low_confidence(self):
        """Ambiguous exception: two plausible causes → low score → ESCALATE."""
        components = ConfidenceComponents(
            deterministic_confidence=0.70,  # level-5 match at best
            evidence_completeness=0.80,     # most records found
            source_consistency=0.40,        # sources partially disagree
            llm_confidence=0.55,            # LLM is uncertain
        )
        result = compute_confidence(components)
        assert result.routing == "ESCALATE"


class TestDeterministicMatchConfidence:
    def test_level1_is_perfect(self):
        assert confidence_for_deterministic_match(1) == 1.00

    def test_level5_is_lower(self):
        assert confidence_for_deterministic_match(5) == 0.70

    def test_unknown_level_returns_safe_default(self):
        assert confidence_for_deterministic_match(99) == 0.50


class TestEvidenceCompleteness:
    def test_all_present(self):
        score = evidence_completeness_score(
            has_order=True,
            has_payment=True,
            has_settlement=True,
            has_bank=True,
        )
        assert score == 1.0

    def test_missing_bank(self):
        """MISSING_BANK_CREDIT: bank is absent — completeness should be < 1."""
        score = evidence_completeness_score(
            has_order=True,
            has_payment=True,
            has_settlement=True,
            has_bank=False,
        )
        assert score == pytest.approx(0.75, abs=0.001)

    def test_with_refund_present(self):
        score = evidence_completeness_score(
            has_order=True,
            has_payment=True,
            has_settlement=True,
            has_bank=True,
            has_refund=True,
        )
        assert score == 1.0

    def test_with_refund_missing(self):
        score = evidence_completeness_score(
            has_order=True,
            has_payment=True,
            has_settlement=True,
            has_bank=True,
            has_refund=False,
        )
        assert score == pytest.approx(0.8, abs=0.001)
