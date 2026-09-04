# LedgerLens

**From reconciliation to financial control.**

LedgerLens is an autonomous AI Finance Controller that reconciles fragmented financial records, detects exceptions, investigates root causes, prioritizes financial exposure, surfaces early warnings, and determines whether the books are ready to close — end to end, without a spreadsheet.

![Next.js](https://img.shields.io/badge/Next.js-16.3-black?logo=nextdotjs)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-async-003B57?logo=sqlite)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?logo=scikit-learn)
![Gemini](https://img.shields.io/badge/Gemini-2.5--pro-4285F4?logo=google)
![Three.js](https://img.shields.io/badge/Three.js-0.185-black?logo=threedotjs)

---

## Table of Contents

1. [What is LedgerLens?](#what-is-ledgerlens)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [Real-World Scenario](#real-world-scenario)
5. [Key Features](#key-features)
6. [Product Walkthrough](#product-walkthrough)
7. [How It Works](#how-it-works)
8. [System Architecture](#system-architecture)
9. [End-to-End Data Flow](#end-to-end-data-flow)
10. [Reconciliation Architecture](#reconciliation-architecture)
11. [AI Investigation Architecture](#ai-investigation-architecture)
12. [Root-Cause & Incident Intelligence](#root-cause--incident-intelligence)
13. [Financial Exposure Model](#financial-exposure-model)
14. [Priority Scoring](#priority-scoring)
15. [Early Warning System](#early-warning-system)
16. [Finance Close Readiness](#finance-close-readiness)
17. [Evaluation & Benchmarking](#evaluation--benchmarking)
18. [Baseline Comparison](#baseline-comparison)
19. [Failure Recovery & Safe Abstention](#failure-recovery--safe-abstention)
20. [Engineering Challenges & Solutions](#engineering-challenges--solutions)
21. [Technical Decisions](#technical-decisions)
22. [Security & Trust](#security--trust)
23. [Tech Stack](#tech-stack)
24. [Project Structure](#project-structure)
25. [Testing](#testing)
26. [Installation](#installation)
27. [Configuration](#configuration)
28. [Running the Demo](#running-the-demo)
29. [5-Minute Demo](#5-minute-demo)
30. [Roadmap](#roadmap)
31. [Limitations](#limitations)
32. [Hackathon](#hackathon)
33. [Team](#team)
34. [License](#license)
35. [References](#references)

---

## What is LedgerLens?

LedgerLens is not a reconciliation table. It is not an AI chatbot layered over a spreadsheet. It is a control system that closes a finance-operations loop:

```
VERIFY → DETECT → INVESTIGATE → PRIORITIZE → PREVENT → CLOSE
```

A merchant's financial records live across multiple systems: orders, payments, refunds, settlements, and bank transactions. These records frequently disagree — because of legitimate reasons (fees, refunds, timing) and problematic ones (duplicate charges, orphan payments, missing credits).

A naive system stops at: **"These numbers don't match."**

LedgerLens asks: **"Why don't they match?"** Then: **"How much money is actually exposed?"** Then: **"Is this part of a larger incident?"** Then: **"What should the finance team investigate first?"** Then: **"Can the books safely close?"**

---

## The Problem

A merchant processes thousands of payments each month. Five separate systems record parts of that activity:

- **Orders** — what the customer purchased
- **Payments** — what was captured by the gateway
- **Refunds** — what was returned
- **Settlements** — what the gateway claims to have paid out
- **Bank Transactions** — what actually arrived

These records can disagree for legitimate reasons (gateway fees, GST on fees, timing delays, partial refunds) or problematic ones (duplicate charges, missing settlements, split payouts, orphan payments with no matching order).

A finance team trying to reconcile this manually has to match each payment to its order, settlement, refund, and bank entry — then determine whether a discrepancy is a fee, a refund, a delay, or a real error — then identify whether ten similar exceptions share one upstream cause — then rank which exceptions carry the most financial risk — then decide when the books are safe to close.

At small volumes this is tedious. At scale, it becomes error-prone, slow, and expensive. Spreadsheets do not catch patterns. They do not generate warnings. They do not tell you what to fix first.

---

## The Solution

```
RAW FINANCIAL RECORDS
        ↓
    NORMALIZATION
        ↓
DETERMINISTIC RECONCILIATION
        ↓
   EXCEPTION DETECTION
        ↓
  ROOT-CAUSE CLUSTERING
        ↓
   INCIDENT DETECTION
        ↓
  FINANCIAL EXPOSURE
        ↓
    PRIORITIZATION
        ↓
  AI INVESTIGATION (for ambiguous cases)
        ↓
  AUTO-RESOLVE / ESCALATE
        ↓
   EARLY WARNING
        ↓
FINANCE CLOSE READINESS
```

Each stage is independently verifiable. Financial truth is owned by deterministic logic. The LLM is restricted to interpretation and explanation.

---

## Real-World Scenario

> These scenarios illustrate the system's reasoning. Labelled as illustrative.

**Case 1 — Auto-resolved**

| Record | Amount |
|---|---|
| Order | ₹5,000 |
| Payment captured | ₹5,000 |
| Refund | ₹500 |
| Gateway fee | ₹90 |
| Settlement received | ₹4,410 |

A naive match flags a ₹590 mismatch. LedgerLens computes: ₹500 refund + ₹90 fee = ₹590 explained variance. Confidence: 0.97. **AUTO-RESOLVED.**

**Case 2 — Escalated**

| Record | Value |
|---|---|
| Payment captured | ₹8,000 |
| Settlement record | ₹8,000 |
| Bank credit | ₹0 |
| Settlement due date | Passed |

LedgerLens gathers evidence: payment exists, settlement exists, no corresponding bank credit found, due date has passed. Evidence is real but incomplete — a forced resolution could clear a genuinely missing credit. System refuses to auto-resolve. Outcome: **ESCALATE → HUMAN REVIEW.**

---

## Key Features

### A. Multi-Source Reconciliation

Reconciles five linked financial entities per payment chain: Orders → Payments → Refunds → Settlements → Bank Transactions.

### B. 17 Exception Types

| Type | Description |
|---|---|
| `FEE_DIFFERENCE` | Gateway fee differs from expected calculation |
| `TAX_DIFFERENCE` | GST on fee varies from computed value |
| `PARTIAL_REFUND` | Refund amount less than full payment |
| `FULL_REFUND` | Full refund processed, settlement adjustment expected |
| `DELAYED_SETTLEMENT` | Settlement arrived past expected T+2 window |
| `MISSING_SETTLEMENT` | No settlement record for a captured payment |
| `MISSING_BANK_CREDIT` | Settlement record exists but no bank credit found |
| `DUPLICATE_PAYMENT` | Same order charged more than once |
| `ORPHAN_PAYMENT` | Payment exists with no matching order |
| `AMOUNT_MISMATCH` | Payment and settlement amounts disagree |
| `INCORRECT_REFERENCE` | Gateway reference does not match expected pattern |
| `SPLIT_SETTLEMENT` | Single payment settled in multiple parts |
| `MULTIPLE_REFUNDS` | More refunds issued than expected for one payment |
| `CONFLICTING_TIMESTAMPS` | Record dates are logically inconsistent |
| `INCOMPLETE_EVIDENCE` | Related records partially missing |
| `AMBIGUOUS` | Evidence exists but is insufficient to determine outcome |
| `CONTRADICTORY_EVIDENCE` | Records exist but directly contradict each other |

### C. Resolution Policy

Each exception type has an explicit resolution policy:

- **Auto-resolvable** (`FEE_DIFFERENCE`, `FULL_REFUND`, `PARTIAL_REFUND`) — resolved automatically above the confidence threshold (default: 0.95)
- **Always escalated** (`AMBIGUOUS`, `AMOUNT_MISMATCH`, `CONTRADICTORY_EVIDENCE`) — never auto-resolved regardless of confidence
- **Always human review** (`ORPHAN_PAYMENT`, `DELAYED_SETTLEMENT`) — routed to the review queue

### D. Root-Cause Clustering (DBSCAN)

Exceptions are grouped using DBSCAN on two features: temporal proximity (scaled to 2-hour units) and exception type. Clusters surface groups of related exceptions that likely share a single upstream cause.

### E. Incident Detection

The incident engine compares the current period's exception type distribution against a historical baseline. Types that show a statistically significant increase (>50% rise) are flagged as systemic incidents.

### F. Financial Exposure Model

Each exception carries `gross_amount`, `known_adjustments`, `resolved_amount`, `unresolved_amount`, and `financial_exposure`. Payment IDs are used as deduplication keys to prevent the same money from being counted across multiple exception totals.

### G. Priority Scoring

A transparent, deterministic composite score (0–100) — see [Priority Scoring](#priority-scoring).

### H. Early Warning System

When clusters form with growing membership relative to recent baselines, a `HIGH_RISK_CLUSTER` signal is raised — before an exception reaches critical severity.

### I. Finance Close Readiness

Evaluates five deterministic controls and returns `READY`, `READY_WITH_REVIEW`, or `NOT_READY`.

### J. Safe Abstention

When evidence is contradictory or the LLM fails, the system routes to `HUMAN_REVIEW` and logs an audit event. Financial truth is never guessed.

---

## Product Walkthrough

| Route | Screen | Purpose |
|---|---|---|
| `/dashboard` | Dashboard | Finance control centre — KPIs, control score, exposure summary |
| `/transactions` | Transactions | Searchable ledger of all payment records |
| `/exceptions` | Exception Queue | Triage view ranked by financial exposure |
| `/exceptions/[id]` | Exception Detail | Evidence-driven investigation + AI analysis + audit trail |
| `/root-causes` | Root Causes | Exception cluster groups by type and temporal burst |
| `/incidents` | What Changed? | Systemic incident detection vs historical baseline |
| `/early-warnings` | Early Warnings | Emerging risk signals from cluster growth |
| `/priority` | Priority Queue | AI-ranked action list by composite risk score |
| `/close-readiness` | Close Readiness | Deterministic pass/fail gate for period close |
| `/evaluation` | Evaluation | Benchmark accuracy against ground truth |
| `/simulate` | Simulator | End-to-end system demonstration with custom data |

---

## How It Works

### 1 — Ingest
CSV files (orders, payments, refunds, settlements, bank_transactions) are uploaded via `/api/ingest` or loaded from the demo dataset via `/api/demo/load`. Each upload creates a `ReconciliationRun` in `PENDING` status.

### 2 — Normalize
Standardises timestamps (→ UTC), strips formatting from amount fields, enforces ID formats, and rejects invalid records.

### 3 — Reconcile
The `ReconciliationEngine` groups all records by payment ID (the central source of truth) and checks each chain across five matching levels. Deterministic only — no LLM involved.

### 4 — Detect
Failed chains raise a typed exception (`DELAYED_SETTLEMENT`, `AMOUNT_MISMATCH`, etc.) with severity (`GREEN`, `YELLOW`, `RED`) and an initial confidence score.

### 5 — Cluster
`cluster_exceptions()` runs DBSCAN (`eps=1.5`, `min_samples=2`) over all exceptions for the run. Features: timestamp in 2-hour units + type encoding.

### 6 — Detect Incidents
`detect_incidents()` compares exception type counts in the current period against a historical baseline window. Significant spikes are stored as `Incident` records.

### 7 — Calculate Exposure
Each exception's exposure = gross amount − verified adjustments (fees, confirmed refunds, matched bank credits). Same payment ID cannot contribute exposure twice.

### 8 — Prioritize
`prioritize_exceptions()` scores every exception across four components and writes `PriorityScore` records. Fully deterministic.

### 9 — Investigate
For ambiguous exceptions, the AI service builds a sanitised context packet and submits it to Gemini 2.5 Pro with structured output mode. The LLM returns `root_cause`, `reasoning_summary`, `llm_confidence`, and `recommended_action`.

### 10 — Resolve or Escalate
The `resolve()` function applies the resolution policy. Confidence ≥ 0.95 + auto-resolvable type → `AUTO_RESOLVED`. Otherwise → `REVIEW` or `ESCALATED`.

### 11 — Early Warning
`detect_early_warnings()` scans open clusters. Clusters meeting the criteria generate `EarlyWarning` records.

### 12 — Close Readiness
`assess_close_readiness()` evaluates five deterministic controls and writes a `CloseAssessment` with a 0–100 score and status.

### 13 — Evaluate
The evaluation pipeline compares outputs against a hidden ground-truth file. Computes precision, recall, F1, auto-resolution accuracy, false auto-resolution count, and safe abstention rate.

---

## System Architecture

```mermaid
graph TD
    USER["User / Finance Analyst"]
    FRONTEND["Next.js 16 Frontend\nTypeScript · Tailwind · Recharts · Three.js"]
    API["FastAPI Backend\nPython 3.12 async"]
    ORCH["ReconciliationEngine\nControl Orchestrator"]

    subgraph DATA["Data Layer"]
        DB1["Orders · Payments\nRefunds · Settlements\nBank Transactions"]
        DB2["Exceptions · Clusters · Incidents\nWarnings · Priority · Assessments"]
    end

    subgraph ENGINES["Finance Engines (deterministic)"]
        E1["Reconciliation"]
        E2["DBSCAN Clustering"]
        E3["Incident Detection"]
        E4["Exposure Calculation"]
        E5["Prioritization"]
        E6["Close Readiness"]
        E7["Early Warning"]
    end

    subgraph AI["AI Layer"]
        CTX["Evidence Context Builder"]
        LLM["Gemini 2.5 Pro\nStructured Output"]
        SAFE["Safe Abstention\non failure"]
    end

    EVAL["Evaluation Pipeline\nGround Truth Comparison"]

    USER --> FRONTEND --> API --> ORCH
    ORCH --> ENGINES
    ORCH --> DB1
    ENGINES --> DB2
    ORCH --> CTX --> LLM --> SAFE
    DB2 --> EVAL
```

---

## End-to-End Data Flow

```mermaid
flowchart LR
    CSV["CSV Upload\nor Demo Load"] --> VAL["Validation\n+ Normalization"]
    VAL --> DB["Database\nRun: PENDING"]
    DB --> RECON["Reconciliation\ndeterministic"]
    RECON --> EXC["Exception Detection\n17 types"]
    EXC --> CONF["Confidence Scoring"]
    CONF --> RESOLVE["Auto-Resolve\nor Escalate"]
    RESOLVE --> CLUSTER["DBSCAN\nClustering"]
    CLUSTER --> INC["Incident Detection\nbaseline comparison"]
    INC --> PRIO["Priority Scoring"]
    PRIO --> WARN["Early Warnings"]
    WARN --> CLOSE["Close Readiness"]
    CLOSE --> AUDIT["Audit Trail"]
    AUDIT --> UI["Dashboard / API"]
```

---

## Reconciliation Architecture

Payment-centric model — each payment is the root of its chain:

| Level | Match Criteria |
|---|---|
| 1 | Payment ID → Order (via `order_id`) |
| 2 | Payment ID → Settlement (via `payment_id`) |
| 3 | Settlement → Bank Transaction (via payout reference in narration) |
| 4 | Amount: payment = order, settlement = payment − fee − GST |
| 5 | Refund accounting: sum of refunds against settlement adjustments |

Deterministic matching runs first. If all five levels pass → `HEALTHY`. Any failure → typed exception.

**Configurable tolerances:**
- `FUZZY_MATCH_WINDOW_HOURS` (default: 6h)
- `STRICT_MATCH_WINDOW_HOURS` (default: 24h)
- `AMOUNT_TOLERANCE_INR` (default: ₹0.01)

---

## AI Investigation Architecture

```
Exception Record + Linked Financial Records (sanitised)
        ↓
   Context Packet (JSON)
        ↓
   Gemini 2.5 Pro (structured output mode)
        ↓
   InvestigationResultSchema:
     · root_cause: str
     · reasoning_summary: str
     · llm_confidence: float [0.0–1.0]
     · recommended_action: AUTO_RESOLVE | REVIEW | ESCALATE
        ↓
   Resolution Policy (deterministic gate)
        ↓
   Final Outcome + Audit Event
```

**What the LLM cannot do:** write to the database, access raw financial records directly, invent amounts, override the resolution policy, or initiate financial actions.

---

## Root-Cause & Incident Intelligence

```
ExceptionA ─┐
ExceptionB ─┼─► CLUSTER (same type, same time window)
ExceptionC ─┘         │
                       ▼
                  INCIDENT (type growing faster than baseline)
                       │
                       ▼
              EARLY WARNING (cluster meets exposure threshold)
```

A cluster means: *these exceptions are likely related.*
An incident means: *this type is occurring faster than historically normal.*
An early warning means: *act before this cluster grows further.*

---

## Financial Exposure Model

| Field | Description |
|---|---|
| `gross_amount` | Full value of the payment chain |
| `known_adjustments` | Confirmed fees + refunds + matched bank credits |
| `resolved_amount` | Portion accounted for and closed |
| `unresolved_amount` | `gross_amount − known_adjustments − resolved_amount` |
| `financial_exposure` | Portion of unresolved representing genuine risk |

Payment IDs serve as primary keys for exposure aggregation — the same payment cannot contribute to multiple totals simultaneously.

---

## Priority Scoring

| Component | Max Points | What it Measures |
|---|---|---|
| Financial Exposure | 40 | Scaled log of `financial_exposure` |
| Severity | 30 | `RED`=30, `YELLOW`=20, `GREEN`=10 |
| Age | 15 | Time open since detection (linear, max at 30 days) |
| Cluster Membership | 15 | Whether the exception belongs to an open cluster |
| **Total** | **100** | |

The score is deterministic, transparent, and reproducible across identical inputs.

---

## Early Warning System

After each pipeline run, the early warning service scans open `ExceptionCluster` records. Clusters meeting the configured exposure or pattern criteria generate an `EarlyWarning` record:

- `signal_type: HIGH_RISK_CLUSTER`
- `severity: HIGH`
- `estimated_exposure`

This is pattern-reactive: it fires when a cluster forms, not after it has already caused material damage.

---

## Finance Close Readiness

Five deterministic controls evaluated per run:

1. **Revenue Verified %** — fraction of total volume fully reconciled
2. **Critical Exception Count** — any `RED` severity exceptions remaining
3. **Unresolved Exposure** — total `financial_exposure` across open exceptions
4. **Pending Human Reviews** — exceptions awaiting an operator decision
5. **Active Incidents** — open systemic incidents not yet resolved

| Score | Status |
|---|---|
| ≥ 90 | `READY` |
| 70–89 | `READY_WITH_REVIEW` |
| < 70 | `NOT_READY` |

---

## Evaluation & Benchmarking

The evaluation pipeline proves outputs are not guesses.

**Design:** The synthetic data generator injects exceptions of known types into a linked payment dataset. Ground truth (actual exception types and expected resolutions) is written to `data/eval_ground_truth/` — a directory the application never reads during normal operation. Only the evaluation pipeline reads it, at eval time, for comparison.

**Reproducibility:** `GENERATOR_SEED=42` — every evaluation run on the same dataset produces identical benchmark results.

**Demo run metrics (current benchmark environment):**

| Metric | Value |
|---|---|
| Records ingested | 51 |
| Matched (healthy) | 35 |
| Exceptions detected | 16 |
| Auto-resolved | 0 |
| Escalated | 11 |
| Total transaction volume | ₹77,249 |
| Unresolved exposure | ₹30,984 |
| Deterministic processing time | ~51ms |

> Full evaluation (F1, precision, recall) runs against the 50-record eval dataset via `POST /api/eval/load` → `POST /api/reconcile/{run_id}` → `POST /api/evaluate`. Requires an active LLM API key for AI-investigated exceptions.

---

## Baseline Comparison

A deterministic-only baseline (`evaluation/baseline_comparison.py`) performs strict exact-ID matching: payment → settlement (by payment_id), settlement → bank (by payout reference in narration), and exact amount equality.

**What exact-ID matching misses:** fee and GST arithmetic, delayed settlement timing windows, partial refund adjustments, split settlements, and missing bank credits without a direct reference match.

LedgerLens extends beyond exact-ID matching with the full multi-level reconciliation hierarchy and the AI investigation layer for ambiguous cases.

---

## Failure Recovery & Safe Abstention

**LLM unavailable or rate-limited:**

1. The investigation service returns `None` from the LLM client
2. Resolution policy falls back to `HUMAN_REVIEW`
3. Audit event logged: `investigation_failed`
4. Exception marked `PENDING_REVIEW` in the database
5. Surfaces in the exception queue on the dashboard

No exception is silently dropped. No auto-resolution occurs when the LLM fails.

**`CONTRADICTORY_EVIDENCE` and `AMBIGUOUS` types** are hardcoded as `ALWAYS_ESCALATE` in the resolution policy — a 0.99 LLM confidence score does not unlock auto-resolution for these types.

> **Design principle:** Automate what can be verified. Investigate what can be explained. Escalate what cannot be safely resolved.

---

## Engineering Challenges & Solutions

### 1 — Over-relying on the LLM

**Initial design:** A single LLM prompt was responsible for detecting anomalies, determining root causes, and generating priority scores.

**Problems:** The LLM hallucinated financial values, invented transaction amounts not present in the records, and took 10+ seconds per exception.

**Solution:** Financial truth moved entirely to deterministic Python. The LLM is now restricted to one task: interpret a pre-built evidence context and return a structured recommendation. Core deterministic processing runs in ~51ms. LLM investigation is asynchronous and has materially higher latency.

---

### 2 — Evaluation Was Not Reproducible

**Initial design:** Evaluation ran against randomly generated data.

**Problem:** Metrics changed on every run, making it impossible to determine whether a code change improved or degraded accuracy.

**Solution:** Introduced `GENERATOR_SEED=42` and a deterministic ground-truth file in a separate directory (`data/eval_ground_truth/`) never accessed during normal operation. Every evaluation now runs against the same dataset.

---

### 3 — Downstream Pipeline Stages Returned Zero

**Problem 1:** Reconciliation completed, but clustering, incident detection, priority, and close-readiness services were independent steps that had to be explicitly triggered. They had never been called.

**Problem 2:** DBSCAN had a timestamp scaling bug. `e.transaction_ts.timestamp()` was not being divided by 7200 (to convert to 2-hour units), so timestamps were in raw epoch seconds (~1.7 billion). With `eps=1.5`, no two exceptions were ever within distance — everything was classified as noise.

**Solution:** Fixed the operator precedence bug. Implemented explicit pipeline orchestration after reconciliation. All five downstream stages now run sequentially.

---

### 4 — Vite to Next.js Migration

**Initial design:** Frontend built as a Vite SPA.

**Problem:** A 10+ page application with a persistent sidebar layout and nested routing became difficult to maintain. Layout state was not preserved across client-side navigation.

**Solution:** Migrated to Next.js 16 App Router. Route groups (`(dashboard)`, `(marketing)`, `(auth)`) provide clean layout separation. `layout.tsx` handles persistent sidebar state across all dashboard pages.

---

## Technical Decisions

### Why deterministic logic, not end-to-end AI?
Financial outputs must be reproducible and auditable. A reconciliation result that changes depending on LLM temperature is not acceptable in a finance context. Deterministic logic owns the numbers. AI owns the interpretation.

### Why Gemini with structured output mode?
Structured output mode (JSON schema enforcement) eliminates hallucinated fields and allows the LLM response to be parsed directly into `InvestigationResultSchema` without prompt engineering for format compliance. The system also supports OpenAI and Anthropic via the same abstract interface.

### Why DBSCAN?
DBSCAN does not require a pre-specified number of clusters and handles noise (unclustered exceptions) natively. In a payment exception context, the number of clusters per run is unknown in advance, and isolated exceptions are common. A centroid-based algorithm would force every exception into a cluster, misrepresenting the data.

### Why a synthetic deterministic generator?
The Razorpay Buildathon track requires a 50+ record synthetic data batch. Beyond the requirement, a deterministic generator with a hidden ground-truth file allows the evaluation pipeline to measure accuracy objectively — not possible with real merchant data or randomly generated data.

### Why SQLite in demo / PostgreSQL in production?
The demo uses SQLite via `aiosqlite` for zero-dependency local setup. The application is configured for `asyncpg` + PostgreSQL in production via the `DATABASE_URL` environment variable.

### Why Next.js over Vite?
After migrating from Vite mid-build, Next.js App Router route groups and `layout.tsx` files solved persistent layout state, nested routing, and API proxying (preventing CORS issues) cleanly.

---

## Security & Trust

**AI boundary:** The LLM receives a sanitised context object — not direct database access. It cannot write to the database, initiate financial actions, or access records outside the exception it is investigating.

**Financial calculations:** All arithmetic is deterministic Python. LLM outputs influence the `recommended_action` field only — the resolution policy is a separate deterministic gate.

**Human approval:** Any exception where confidence < `AUTO_RESOLVE_THRESHOLD` is routed to human review with a full audit trail.

| Variable | Sensitivity | Notes |
|---|---|---|
| `GEMINI_API_KEY` | Server-only secret | Never exposed to client |
| `DATABASE_URL` | Server-only secret | Connection string |
| `OPENAI_API_KEY` | Server-only secret | Optional |
| `ANTHROPIC_API_KEY` | Server-only secret | Optional |
| `AUTO_RESOLVE_THRESHOLD` | Server config | Controls resolution safety |
| `BACKEND_CORS_ORIGINS` | Server config | Client origin whitelist |

No secrets are exposed via `NEXT_PUBLIC_*` variables.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Frontend framework | Next.js | 16.3.4 | Application routing and layout |
| UI language | TypeScript | 5 | Type-safe frontend |
| Styling | Tailwind CSS + shadcn/ui | latest | Design system |
| Animation | Framer Motion | 13.2 | UI transitions and cursor effects |
| 3D / WebGL | Three.js + React Three Fiber | 0.185 / 9.7 | Black Hole visual effect on login |
| Charts | Recharts | 3.10 | Dashboard visualisations |
| Backend language | Python | 3.12 | Services and API |
| API framework | FastAPI | 0.115 | Async REST API |
| ORM | SQLAlchemy (async) | 2.0.35 | Database access layer |
| Database (demo) | SQLite (aiosqlite) | — | Local zero-dependency setup |
| Database (production) | PostgreSQL (asyncpg) | — | Configured via DATABASE_URL |
| Data processing | Pandas + NumPy | 2.2 / 2.1 | Financial record normalisation |
| ML | scikit-learn (DBSCAN) | 1.9 | Exception cluster detection |
| LLM — primary | Gemini 2.5 Pro | — | AI investigation (structured output) |
| LLM — optional | OpenAI GPT-4o / Claude | — | Fallback via provider abstraction |
| Migrations | Alembic | 1.13.3 | Database schema management |
| Structured logging | structlog | 24.4 | Audit trail |

---

## Project Structure

```
ledgerlens/
├── backend/
│   ├── api/routes/
│   │   ├── controller.py      # Dashboard data endpoints
│   │   ├── exceptions.py      # Exception CRUD + approve/reject/investigate
│   │   ├── ingest.py          # CSV upload + demo/eval load
│   │   ├── reconcile.py       # Reconciliation trigger
│   │   ├── evaluate.py        # Evaluation pipeline trigger
│   │   └── metrics.py         # Run summary metrics
│   ├── evaluation/
│   │   ├── evaluator.py       # Ground-truth comparison pipeline
│   │   ├── baseline_comparison.py
│   │   └── benchmark.py
│   ├── models/__init__.py     # All SQLAlchemy ORM models
│   ├── services/
│   │   ├── reconciliation.py  # Core deterministic engine
│   │   ├── investigation.py   # AI investigation service
│   │   ├── clustering.py      # DBSCAN clustering
│   │   ├── incident_engine.py # Incident detection
│   │   ├── early_warning.py   # Warning generation
│   │   ├── prioritization.py  # Priority scoring
│   │   ├── close_readiness.py # Close assessment
│   │   ├── confidence.py      # Confidence scoring
│   │   ├── resolution.py      # Resolution policy
│   │   └── audit.py           # Audit trail logging
│   ├── config.py
│   ├── database.py
│   └── main.py
├── generator/
│   ├── data_generator.py      # Deterministic synthetic data (seed=42)
│   └── distributions.py       # Payment, amount, fee distributions
├── frontend/src/
│   ├── app/
│   │   ├── (auth)/            # Login, Signup
│   │   ├── (dashboard)/       # All dashboard pages + layout.tsx
│   │   └── (marketing)/       # Landing page, How It Works
│   ├── components/
│   │   ├── effects/           # BlackHole, CursorWaveGrid, UserCursor, TextReveal3D
│   │   └── ui/                # shadcn/ui base components
│   └── lib/api.ts             # Axios client (Next.js rewrite proxy)
├── tests/unit/
│   ├── test_confidence.py
│   ├── test_normalization.py
│   └── test_resolution_policy.py
├── alembic/                   # Database migrations
├── requirements.txt
└── .env.example
```

---

## Testing

**Unit tests — 54 passing (3.51s):**

| Test File | Coverage |
|---|---|
| `test_confidence.py` | Confidence scoring edge cases |
| `test_normalization.py` | Amount parsing, timestamp handling, ID validation |
| `test_resolution_policy.py` | All 17 exception type policies, severity mapping, confidence bands |

```bash
pytest tests/ -v
# ============================= 54 passed in 3.51s ==============================
```

**Evaluation pipeline:** Runs against the deterministic 50-record eval dataset. Measures detection precision, recall, F1, and auto-resolution accuracy against hidden ground truth.

**Baseline comparison:** Exact-ID matching baseline runs alongside the full pipeline to demonstrate what LedgerLens adds beyond simple exact matching.

**Failure testing:** `evaluation/failure_test.py` tests system behaviour when the LLM is unavailable — confirms all exceptions fall back to `HUMAN_REVIEW` with no silent auto-resolutions.

---

## Installation

```bash
# 1. Clone
git clone https://github.com/IamDhruv777/RazorPay_Hackathon.git
cd RazorPay_Hackathon

# 2. Python environment
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux

pip install -r requirements.txt

# 3. Frontend
cd frontend
npm install
cd ..

# 4. Environment
cp .env.example .env
# Edit .env — add GEMINI_API_KEY at minimum
```

---

## Configuration

**`.env`** (backend):

```env
# LLM — at minimum, set one provider key
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=               # optional
ANTHROPIC_API_KEY=            # optional

# Database — SQLite for demo, PostgreSQL for production
DATABASE_URL=sqlite+aiosqlite:///./ledgerlens.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ledgerlens

# Reconciliation tuning
FUZZY_MATCH_WINDOW_HOURS=6
STRICT_MATCH_WINDOW_HOURS=24
AMOUNT_TOLERANCE_INR=0.01

# Resolution thresholds
AUTO_RESOLVE_THRESHOLD=0.95
REVIEW_THRESHOLD=0.75

# App
BACKEND_CORS_ORIGINS=http://localhost:3000
GENERATOR_SEED=42
```

**`frontend/.env.local`**:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running the Demo

**Terminal 1 — Backend:**
```bash
.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm run dev
```

Open `http://localhost:3000`

**Load demo data:**
```bash
# Load demo dataset (seed=42)
curl -X POST http://localhost:8000/api/demo/load
# Returns: {"run_id": "..."}

# Trigger reconciliation
curl -X POST http://localhost:8000/api/reconcile/{run_id}
```

Or use the **Simulator** page at `/simulate` to trigger from the UI.

**Sign in:** `demo@ledgerlens.com` / `demo123`

---

## 5-Minute Demo

| Time | Action |
|---|---|
| 0:00–0:30 | Open `localhost:3000` — show landing page and Cursor Wave Grid |
| 0:30–1:00 | Navigate to `/auth/login` — Black Hole WebGL effect — sign in |
| 1:00–1:45 | Dashboard — control score 68/100 NOT READY, ₹30,984 exposure |
| 1:45–2:30 | `/exceptions` — 16 anomalies, explain types, click one for detail |
| 2:30–3:10 | `/incidents` — 3 systemic spikes; `/root-causes` — 6 clusters |
| 3:10–3:45 | `/priority` — ranked action list with score breakdown |
| 3:45–4:30 | `/close-readiness` — 68.14 NOT READY, what it takes to close |
| 4:30–5:00 | Return to dashboard — closing statement |

---

## Roadmap

**✅ Built**
- Multi-source deterministic reconciliation (5 entity types)
- 17 exception types with typed detection and resolution policy
- DBSCAN clustering
- Incident detection vs historical baseline
- AI investigation with structured output and safe abstention
- Financial exposure model with deduplication
- Priority scoring (4-component deterministic)
- Early warning system
- Close readiness assessment (5-control deterministic gate)
- Evaluation pipeline with ground-truth comparison
- Deterministic synthetic data generator (seed=42)
- 54 unit tests passing
- Full dashboard UI (10 pages)

**🔜 Near-Term**
- Expanded evaluation dataset (1,000 records)
- Richer temporal anomaly detection
- Multi-merchant workspace support

**🔮 Future**
- Live Razorpay API integration
- Accounting system connectors (Tally, QuickBooks, Zoho Books)
- Role-based access control
- Production-grade authentication (OAuth2, SSO)
- Distributed processing for high-volume batches

---

## Limitations

- Benchmark uses synthetic linked data. Not real merchant production data.
- AI investigation layer depends on an external LLM API. Without a valid key, all ambiguous exceptions fall back to human review.
- Resolution policies are prototype-level finance rules, not production banking policies reviewed by a compliance team.
- Demo dataset (51 records) is small by production standards. Performance at 100K+ records has not been benchmarked.
- DBSCAN parameters are configured for the demo dataset size and have not been tuned for larger volumes.
- Close-readiness controls are heuristic. A real deployment would require finance-team-configured policies per merchant.

---

## Hackathon

**Event:** Razorpay AI Buildathon 2026  
**Track:** 04 — AI Finance Controller  
**Objective:** Build an autonomous AI agent that closes the finance-operations loop over a 50+ record synthetic payment batch.

---

## Team

- **Dhruv Madderlawar** — Lead Developer

---

## License

MIT

---

## References

- [Razorpay AI Buildathon](https://razorpay.com)
- [Razorpay Payment APIs](https://razorpay.com/docs/api/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js App Router](https://nextjs.org/docs/app)
- [scikit-learn DBSCAN](https://scikit-learn.org/stable/modules/clustering.html#dbscan)
- [Google Generative AI (Gemini)](https://ai.google.dev)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Three.js](https://threejs.org)
- [Recharts](https://recharts.org)
- [Framer Motion](https://www.framer.com/motion/)
