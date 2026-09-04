"""
LedgerLens — SQLAlchemy ORM Models
All tables correspond 1:1 with the schema in the implementation plan.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


# ─── Core Financial Records ───────────────────────────────────────────────────

class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    orders: Mapped[list["Order"]] = relationship(back_populates="merchant")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # ORD-XXXXX
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=True)
    order_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=True
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="orders")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    refunds: Mapped[list["Refund"]] = relationship(back_populates="order")
    settlements: Mapped[list["Settlement"]] = relationship(back_populates="order")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # PAY-XXXXX
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    payment_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # upi/card/netbanking/wallet
    gateway_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=True
    )

    order: Mapped["Order | None"] = relationship(back_populates="payments")
    refunds: Mapped[list["Refund"]] = relationship(back_populates="payment")
    settlement: Mapped["Settlement | None"] = relationship(back_populates="payment")


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # REF-XXXXX
    payment_id: Mapped[str | None] = mapped_column(ForeignKey("payments.id"), nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    refund_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=True
    )

    payment: Mapped["Payment | None"] = relationship(back_populates="refunds")
    order: Mapped["Order | None"] = relationship(back_populates="refunds")


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # SET-XXXXX
    payment_id: Mapped[str | None] = mapped_column(ForeignKey("payments.id"), nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    settlement_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    payout_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=True
    )

    payment: Mapped["Payment | None"] = relationship(back_populates="settlement")
    order: Mapped["Order | None"] = relationship(back_populates="settlements")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # BNK-XXXXX
    transaction_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=True
    )


# ─── Reconciliation Layer ─────────────────────────────────────────────────────

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")  # RUNNING/COMPLETED/FAILED
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    exception_count: Mapped[int] = mapped_column(Integer, default=0)
    auto_resolved_count: Mapped[int] = mapped_column(Integer, default=0)
    escalated_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    unresolved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    processing_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    matches: Mapped[list["ReconciliationMatch"]] = relationship(back_populates="run")
    exceptions: Mapped[list["ExceptionModel"]] = relationship(back_populates="run")


class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("reconciliation_runs.id"), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    settlement_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_type: Mapped[str] = mapped_column(String(20), nullable=False)  # LEVEL1..LEVEL5
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped["ReconciliationRun"] = relationship(back_populates="matches")


# ─── Exception Handling ───────────────────────────────────────────────────────



class ExceptionCluster(Base):
    __tablename__ = "exception_clusters"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    common_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    exceptions: Mapped[list["ExceptionModel"]] = relationship(back_populates="cluster")

class ExceptionModel(Base):
    __tablename__ = "exceptions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # EX-XXXXX
    run_id: Mapped[str] = mapped_column(ForeignKey("reconciliation_runs.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)   # GREEN/YELLOW/RED
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    outcome_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # PENDING / AUTO_RESOLVED / ESCALATED / HUMAN_REVIEWED

    order_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    refund_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    settlement_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    transaction_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    human_approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    human_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


    gross_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    known_adjustments: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    unresolved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    potential_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    financial_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)

    cluster_id: Mapped[str | None] = mapped_column(ForeignKey("exception_clusters.id"), nullable=True)
    cluster: Mapped["ExceptionCluster"] = relationship(back_populates="exceptions")

    run: Mapped["ReconciliationRun"] = relationship(back_populates="exceptions")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="exception")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="exception")


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    exception_id: Mapped[str | None] = mapped_column(ForeignKey("exceptions.id"), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Composite confidence score (final)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Individual confidence components (for transparency)
    llm_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    deterministic_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    source_consistency: Mapped[float] = mapped_column(Float, default=0.0)

    recommended_action: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # AUTO_RESOLVE / ESCALATE / REVIEW
    auto_resolve: Mapped[bool] = mapped_column(Boolean, default=False)

    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    outcome_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # PENDING / COMPLETED / AI_UNAVAILABLE / FAILED


    gross_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    known_adjustments: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    unresolved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    potential_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    financial_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)


    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


    
    evidence: Mapped[list["InvestigationEvidence"]] = relationship(back_populates="investigation")
    exception: Mapped["ExceptionModel"] = relationship(back_populates="investigations")


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(
        ForeignKey("investigations.id"), nullable=False
    )
    source_table: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    investigation: Mapped["Investigation"] = relationship(back_populates="evidence")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    exception_id: Mapped[str | None] = mapped_column(ForeignKey("exceptions.id"), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_action: Mapped[str | None] = mapped_column(String(100), nullable=True)

    exception: Mapped["ExceptionModel"] = relationship(back_populates="audit_events")


# ─── Evaluation ───────────────────────────────────────────────────────────────

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["EvaluationResult"]] = relationship(back_populates="run")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    metrics_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # e.g. {"per_type": {"FEE_DIFFERENCE": {"precision": 0.95, ...}}}

    run: Mapped["EvaluationRun"] = relationship(back_populates="results")

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

class HistoricalPattern(Base):
    __tablename__ = "historical_patterns"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pattern_type: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_vector: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    frequency: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

class EarlyWarning(Base):
    __tablename__ = "early_warnings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    estimated_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    
class PriorityScore(Base):
    __tablename__ = "priority_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False) # EXCEPTION or CLUSTER
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    component_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class CloseAssessment(Base):
    __tablename__ = "close_assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # READY, READY_WITH_REVIEW, NOT_READY
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
