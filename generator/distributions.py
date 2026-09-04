"""
LedgerLens — Realistic Synthetic Data Distributions
Realistic Indian merchant/customer data for the generator.
All lists curated for believability.
"""
import numpy as np

# ─── Merchant Names ────────────────────────────────────────────────────────────
MERCHANT_NAMES = [
    "Nykaa Fashion Pvt Ltd",
    "Zomato Food Services",
    "boAt Lifestyle",
    "Mamaearth Cosmetics",
    "Bewakoof Brands Pvt Ltd",
    "Wow Skin Science",
    "The Man Company",
    "mCaffeine",
    "Plum Goodness",
    "Sugar Cosmetics",
    "Noise Electronics",
    "Fire-Boltt Devices",
    "Lenskart Solutions",
    "Wakefit Innovations",
    "Duroflex Mattresses",
    "DailyObjects",
    "Mokobara Luggage",
    "Atomberg Technologies",
    "Renee Cosmetics",
    "Pilgrim India",
]

# ─── Payment Method Distribution ──────────────────────────────────────────────
PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]
PAYMENT_METHOD_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

# ─── Order Amount Distribution ────────────────────────────────────────────────
# Realistic Indian e-commerce price points
ORDER_AMOUNTS = [199, 299, 349, 499, 599, 699, 799, 999, 1199, 1299, 1499,
                 1999, 2499, 2999, 3499, 3999, 4999, 5999, 7999, 9999]
# Higher weight toward mid-range
ORDER_AMOUNT_WEIGHTS = [0.04, 0.04, 0.05, 0.10, 0.06, 0.05, 0.08, 0.10,
                        0.06, 0.05, 0.08, 0.06, 0.07, 0.04, 0.03, 0.03,
                        0.05, 0.03, 0.02, 0.06]

# ─── Razorpay Fee Structure ────────────────────────────────────────────────────
FEE_RATE = 0.018            # 1.8% of transaction amount
GST_ON_FEE_RATE = 0.18      # 18% GST on the processing fee

# ─── Settlement Timing ────────────────────────────────────────────────────────
# T+1 to T+3 business days (Razorpay standard T+2)
SETTLEMENT_DELAY_DAYS_WEIGHTS = {1: 0.15, 2: 0.65, 3: 0.20}

# ─── Order Status Distribution ────────────────────────────────────────────────
ORDER_STATUSES = ["paid", "attempted", "created"]
ORDER_STATUS_WEIGHTS = [0.85, 0.10, 0.05]

# ─── Refund Reasons ───────────────────────────────────────────────────────────
REFUND_REASONS = [
    "Product not received",
    "Wrong item delivered",
    "Item damaged on arrival",
    "Customer request - size issue",
    "Duplicate order placed",
    "Quality not as described",
    "Changed mind",
    "Delivery partner issue",
]

# ─── Bank Narration Templates ─────────────────────────────────────────────────
BANK_NARRATION_TEMPLATES = [
    "NEFT/RAZORPAY/{ref}/SETTLEMENT",
    "IMPS/RAZORPAY TECHNOLOGIES/{ref}",
    "RTGS/RAZORPAY/{ref}/PAYOUT",
    "UPI/RAZORPAY/{ref}/CREDIT",
    "CREDIT/RAZORPAY SETTLEMENT/{ref}",
]

# ─── Exception Injection Configuration ────────────────────────────────────────
# (fraction of total records that should be each exception type)
# Used by the generator to decide how many anomalies to inject
EXCEPTION_DISTRIBUTION = {
    "FEE_DIFFERENCE":      0.01,
    "TAX_DIFFERENCE":      0.01,
    "PARTIAL_REFUND":      0.02,
    "FULL_REFUND":         0.01,
    "DELAYED_SETTLEMENT":  0.02,
    "MISSING_SETTLEMENT":  0.02,
    "MISSING_BANK_CREDIT": 0.02,
    "DUPLICATE_PAYMENT":   0.01,
    "ORPHAN_PAYMENT":      0.01,
    "AMOUNT_MISMATCH":     0.01,
    "INCORRECT_REFERENCE": 0.01,
    "SPLIT_SETTLEMENT":    0.01,
    "MULTIPLE_REFUNDS":    0.01,
    "CONFLICTING_TIMESTAMPS": 0.01,
    "INCOMPLETE_EVIDENCE": 0.01,
    "AMBIGUOUS":           0.01,
    "CONTRADICTORY_EVIDENCE": 0.01,
}


def sample_amount(rng: np.random.Generator) -> float:
    """Sample a realistic order amount from the Indian e-commerce distribution."""
    weights = np.array(ORDER_AMOUNT_WEIGHTS, dtype=float)
    weights = weights / weights.sum()   # normalize to exactly 1.0 (avoids float precision errors)
    return float(rng.choice(ORDER_AMOUNTS, p=weights))


def sample_payment_method(rng: np.random.Generator) -> str:
    weights = np.array(PAYMENT_METHOD_WEIGHTS, dtype=float)
    weights = weights / weights.sum()
    return str(rng.choice(PAYMENT_METHODS, p=weights))


def sample_settlement_delay(rng: np.random.Generator) -> int:
    days = list(SETTLEMENT_DELAY_DAYS_WEIGHTS.keys())
    weights = list(SETTLEMENT_DELAY_DAYS_WEIGHTS.values())
    return int(rng.choice(days, p=weights))


def compute_fee(amount: float) -> tuple[float, float]:
    """
    Returns (fee_amount, tax_amount) for a given transaction amount.
    Fee = 1.8% of amount. GST = 18% of fee. Both rounded to 2 decimal places.
    """
    fee = round(amount * FEE_RATE, 2)
    tax = round(fee * GST_ON_FEE_RATE, 2)
    return fee, tax


def compute_settlement_amount(payment_amount: float, refund_amount: float = 0.0) -> tuple[float, float, float]:
    """
    Returns (settlement_amount, fee_amount, tax_amount).
    settlement_amount = payment_amount - refund_amount - fee_amount - tax_amount
    """
    net = payment_amount - refund_amount
    fee, tax = compute_fee(payment_amount)  # Fee on full payment
    settlement = round(net - fee - tax, 2)
    return settlement, fee, tax
