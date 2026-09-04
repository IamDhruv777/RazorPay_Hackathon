'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { ArrowRight, ChevronRight, FileCheck2, ShieldCheck, X } from 'lucide-react';
import Link from 'next/link';

const money = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

export default function CloseReadiness() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any | null>(null);

  useEffect(() => {
    api.get('/close-readiness/latest')
      .then(res => setData(res.data.close_readiness))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse font-medium">Evaluating close readiness controls...</div>;

  const score = data?.score ?? 0;
  const status = data?.status?.replace(/_/g, ' ') || 'NOT READY';
  const d = data?.details || {};

  const controlRows = [
    {
      title: "Revenue verified",
      coverage: `${d.verified_pct || 0}%`,
      state: (d.verified_pct || 0) > 90 ? "Verified" : "Needs review",
      tone: (d.verified_pct || 0) > 90 ? "sage" : "copper",
      detail: "The settlement control matched the current period against source-level totals.",
      evidence: `${d.verified_pct || 0}% records anchored`
    },
    {
      title: "Unresolved exposure",
      coverage: money(d.unresolved_exposure || 0),
      state: (d.unresolved_exposure || 0) === 0 ? "Verified" : "Needs review",
      tone: (d.unresolved_exposure || 0) === 0 ? "sage" : "copper",
      detail: "Financial exposure that has not been mapped to a resolved incident.",
      evidence: "Active exposure tracked in real-time"
    },
    {
      title: "Critical exceptions",
      coverage: `${d.critical_exceptions || 0} open`,
      state: (d.critical_exceptions || 0) === 0 ? "Verified" : "Needs review",
      tone: (d.critical_exceptions || 0) === 0 ? "sage" : "copper",
      detail: "Exceptions categorized as CRITICAL that require human operator decision.",
      evidence: "Severity determined by AI priority scoring"
    },
    {
      title: "Close readiness gate",
      coverage: `${score} / 100 confidence`,
      state: status,
      tone: score > 90 ? "sage" : (score > 50 ? "navy" : "copper"),
      detail: "The final readiness gate for the financial period close.",
      evidence: `Control health ${score}%`
    }
  ];

  return (
    <div className="command-view">
      <div className="command-view-head">
        <div>
          <span className="eyebrow">Control system / 4 rules</span>
          <h1>Controls</h1>
          <p>See which deterministic checks are passing, waiting, or asking for an operator.</p>
        </div>
        <div className="command-view-actions">
          <button className="ghost-action"><ShieldCheck size={15} /> Review control coverage</button>
          <Link href="/dashboard" className="review-btn">Back to overview <ArrowRight size={15} /></Link>
        </div>
      </div>
      <div className="command-tabs">
        <Link href="/incidents">Incident graph</Link>
        <Link href="/root-causes">Root Causes</Link>
        <Link href="/priority">Priority Queue</Link>
        <Link className="active" href="/close-readiness">Close Readiness</Link>
      </div>

      <div className="command-summary mt-6">
        <div>
          <span className="eyebrow">Control health</span>
          <b>{score}%</b>
          <small>{status}</small>
        </div>
        <div>
          <span className="eyebrow">Last evaluated</span>
          <b>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</b>
          <small>Today · all sources current</small>
        </div>
        <div>
          <span className="eyebrow">Critical Exceptions</span>
          <b>{String(d.critical_exceptions || 0).padStart(2, '0')}</b>
          <small>Need human review</small>
        </div>
      </div>

      <div className="command-table mt-8">
        <div className="command-table-head">
          <span>Control</span>
          <span>Coverage</span>
          <span>State</span>
          <span>Evidence</span>
        </div>
        {controlRows.map(row => (
          <button className="command-row command-row-button" key={row.title} onClick={() => setSelected(row)}>
            <span>
              <b>{row.title}</b>
              <small>Financial control</small>
            </span>
            <span>{row.coverage}</span>
            <span className={`status-pill ${row.tone}`}>{row.state}</span>
            <span><FileCheck2 size={14} /> anchored <ChevronRight size={15} /></span>
          </button>
        ))}
      </div>

      {selected && (
        <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null) }}>
          <aside className="detail-drawer" data-drawer="true" role="dialog" aria-modal="true">
            <div className="drawer-head">
              <div>
                <span className="eyebrow">Control detail</span>
                <h2>{selected.title}</h2>
              </div>
              <button className="drawer-close" onClick={() => setSelected(null)}><X size={18} /></button>
            </div>
            <div className="drawer-body">
              <div className="drawer-status">
                <span className={`status-pill ${selected.tone}`}>{selected.state}</span>
                <span>{selected.coverage}</span>
              </div>
              <p className="drawer-lead">{selected.detail}</p>
              
              <div className="drawer-fields">
                <div><span>Evidence</span><b>{selected.evidence}</b></div>
                <div><span>Last evaluated</span><b>Today · {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</b></div>
                <div><span>Owner</span><b>Finance controls</b></div>
                <div><span>Next decision</span><b>{selected.tone === "copper" ? "Review linked records" : "Continue monitoring"}</b></div>
              </div>

              <div className="drawer-actions">
                <span className="eyebrow">Mock workflow action</span>
                <div>
                  <button onClick={() => setSelected(null)}>Acknowledge</button>
                  <button onClick={() => setSelected(null)}>Run Check</button>
                </div>
              </div>
              
              <button className="drawer-primary" onClick={() => setSelected(null)}>Return to controls <ArrowRight size={14} /></button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
