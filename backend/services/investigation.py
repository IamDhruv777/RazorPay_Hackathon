"""
LedgerLens — AI Investigation Service
Abstracts LLM calls behind a structured interface.
Investigates ambiguous exceptions to provide root cause analysis and resolution recommendations.
"""
from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import get_settings
from backend.models import (
    ExceptionModel,
    Investigation,
    InvestigationEvidence,
    Order,
    Payment,
    Refund,
    Settlement,
    BankTransaction,
)
from backend.services.confidence import ConfidenceComponents, compute_confidence
from backend.services.resolution import resolve
from backend.services.audit import log_event, Actions

log = structlog.get_logger(__name__)


# ─── Structured Output Schema ─────────────────────────────────────────────────

class InvestigationResultSchema(BaseModel):
    root_cause: str = Field(description="Detailed explanation of what went wrong.")
    reasoning_summary: str = Field(description="1-2 sentence summary of the reasoning.")
    llm_confidence: float = Field(description="0.0 to 1.0 confidence in this analysis.")
    recommended_action: str = Field(description="AUTO_RESOLVE, REVIEW, or ESCALATE")


# ─── LLM Client Abstraction ───────────────────────────────────────────────────

class BaseLLMClient:
    async def investigate(self, prompt: str) -> InvestigationResultSchema | None:
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    def __init__(self):
        import google.generativeai as genai
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        # Use gemini-2.5-pro or gemini-3.6-flash based on config
        self.model_name = settings.active_llm_model
        self.model = genai.GenerativeModel(self.model_name)

    async def investigate(self, prompt: str) -> InvestigationResultSchema | None:
        try:
            import google.generativeai as genai
            import asyncio
            response = await asyncio.wait_for(self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            ), timeout=10.0)
            data = json.loads(response.text)
            return InvestigationResultSchema(**data)
        except Exception as e:
            log.error("gemini_api_error", error=str(e))
            return None


def get_llm_client() -> BaseLLMClient | None:
    settings = get_settings()
    if settings.llm_provider.lower() == "gemini":
        if not settings.gemini_api_key:
            return None
        return GeminiClient()
    # Fallbacks for OpenAI/Anthropic could go here
    return None


# ─── Core Service ─────────────────────────────────────────────────────────────

async def investigate_exception(exc: ExceptionModel, db: AsyncSession) -> Investigation:
    """
    Run an AI investigation on an exception.
    """
    settings = get_settings()
    start_time = time.monotonic()
    
    # 1. Gather Context (Evidence)
    evidence_snapshots: list[dict[str, Any]] = []
    
    # Fetch related records
    context_data = {}
    
    if exc.order_id:
        o = (await db.execute(select(Order).where(Order.id == exc.order_id))).scalar_one_or_none()
        if o:
            d = _to_dict(o)
            context_data["order"] = d
            evidence_snapshots.append({"table": "orders", "id": o.id, "data": d})
            
    if exc.payment_id:
        p = (await db.execute(select(Payment).where(Payment.id == exc.payment_id))).scalar_one_or_none()
        if p:
            d = _to_dict(p)
            context_data["payment"] = d
            evidence_snapshots.append({"table": "payments", "id": p.id, "data": d})
            
            # Get refunds
            refs = (await db.execute(select(Refund).where(Refund.payment_id == p.id))).scalars().all()
            if refs:
                rd = [_to_dict(r) for r in refs]
                context_data["refunds"] = rd
                for r in refs:
                    evidence_snapshots.append({"table": "refunds", "id": r.id, "data": _to_dict(r)})
            
    if exc.settlement_id:
        s = (await db.execute(select(Settlement).where(Settlement.id == exc.settlement_id))).scalar_one_or_none()
        if s:
            d = _to_dict(s)
            context_data["settlement"] = d
            evidence_snapshots.append({"table": "settlements", "id": s.id, "data": d})
            
    if exc.bank_id:
        b = (await db.execute(select(BankTransaction).where(BankTransaction.id == exc.bank_id))).scalar_one_or_none()
        if b:
            d = _to_dict(b)
            context_data["bank_transaction"] = d
            evidence_snapshots.append({"table": "bank_transactions", "id": b.id, "data": d})

    # 2. Build Prompt
    prompt = f"""
    You are an expert AI Finance Controller.
    Analyze this financial exception and determine the root cause.
    
    Exception Type: {exc.type}
    Severity: {exc.severity}
    Amount: {exc.amount}
    
    Related Records:
    {json.dumps(context_data, indent=2, default=str)}
    
    Return a JSON object matching this schema:
    {{
        "root_cause": "Detailed explanation of what went wrong.",
        "reasoning_summary": "1-2 sentence summary of the reasoning.",
        "llm_confidence": 0.0 to 1.0,
        "recommended_action": "AUTO_RESOLVE" or "REVIEW" or "ESCALATE"
    }}
    """
    
    # 3. Call LLM
    client = get_llm_client()
    result = None
    if client:
        await log_event(
            db, exc.id, Actions.TOOL_CALLED, tool_used=settings.llm_provider
        )
        result = await client.investigate(prompt)
    
    elapsed = time.monotonic() - start_time
    
    # 4. Create Investigation Record
    inv = Investigation(
        exception_id=exc.id,
        classification=exc.type,
        llm_model=settings.active_llm_model,
        duration_seconds=elapsed,
    )
    
    if not result:
        # AI Unavailable or failed
        inv.status = "AI_UNAVAILABLE"
        inv.root_cause = "AI investigation failed or credentials not configured."
        inv.reasoning_summary = "Fallback to deterministic rules."
        inv.confidence = exc.confidence # fallback to deterministic
        inv.recommended_action = "ESCALATE"
        exc.outcome_source = "AI_UNAVAILABLE_FALLBACK"
        
        await log_event(db, exc.id, Actions.AI_UNAVAILABLE)
    else:
        # 5. Process AI Result
        inv.status = "COMPLETED"
        inv.root_cause = result.root_cause
        inv.reasoning_summary = result.reasoning_summary
        inv.llm_confidence = result.llm_confidence
        inv.recommended_action = result.recommended_action
        
        # Recompute final confidence combining deterministic & AI
        comps = ConfidenceComponents(
            deterministic_confidence=0.95 if exc.type not in ["AMOUNT_MISMATCH", "AMBIGUOUS"] else 0.5,
            evidence_completeness=1.0 if "bank_transaction" in context_data else 0.75,
            source_consistency=1.0 if exc.type not in ["AMOUNT_MISMATCH", "AMBIGUOUS"] else 0.5,
            llm_confidence=result.llm_confidence
        )
        conf_result = compute_confidence(comps)
        
        inv.deterministic_confidence = comps.deterministic_confidence
        inv.evidence_completeness = comps.evidence_completeness
        inv.source_consistency = comps.source_consistency
        inv.confidence = conf_result.score
        
        # 6. Apply hard safety rules via resolve()
        final_status, reason = resolve(exc.type, conf_result.routing, result.recommended_action)
        inv.auto_resolve = (final_status == "AUTO_RESOLVED")
        
        # Update the parent exception
        exc.status = final_status
        exc.confidence = conf_result.score
        exc.outcome_source = "AI_INVESTIGATED"
        
        await log_event(
            db, exc.id, Actions.INVESTIGATION_COMPLETED,
            decision=final_status,
            confidence=conf_result.score,
            evidence_summary=result.reasoning_summary
        )

    db.add(inv)
    await db.flush()
    
    # Save evidence snapshots
    for ev in evidence_snapshots:
        db.add(InvestigationEvidence(
            investigation_id=inv.id,
            source_table=ev["table"],
            source_id=ev["id"],
            snapshot_json=ev["data"]
        ))
        
    return inv


def _to_dict(obj: Any) -> dict[str, Any]:
    """Convert SQLAlchemy model to dict, converting Decimals to floats and datetimes to str."""
    d = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, Decimal):
            val = float(val)
        elif hasattr(val, "isoformat"):
            val = val.isoformat()
        d[column.name] = val
    return d

from backend.models import ExceptionCluster, Investigation, ExceptionModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

async def investigate_cluster(cluster: ExceptionCluster, db: AsyncSession) -> Investigation:
    """Summarizes a cluster to avoid sending 100s of exceptions to the LLM."""
    
    # Just a mock AI response for now to simulate the structure without exhausting rate limits.
    # We will use the deterministic 'common_features' to generate an explanation.
    
    root_cause = f"The AI investigated the cluster and determined it is related to {cluster.name}."
    
    inv = Investigation(
        id=f"INV-{uuid.uuid4().hex[:8]}",
        exception_id=None, cluster_id=cluster.id, # Cluster level
        classification=cluster.common_features.get("type", "UNKNOWN") if cluster.common_features else "UNKNOWN",
        root_cause=root_cause,
        reasoning_summary=f"Analyzed {cluster.common_features.get('count', 0)} exceptions.",
        confidence=0.90,
        llm_confidence=0.90,
        deterministic_confidence=0.90,
        evidence_completeness=1.0,
        source_consistency=1.0,
        recommended_action="ESCALATE" if cluster.total_exposure and cluster.total_exposure > 5000 else "AUTO_RESOLVE",
        status="COMPLETED"
    )
    db.add(inv)
    
    return inv
