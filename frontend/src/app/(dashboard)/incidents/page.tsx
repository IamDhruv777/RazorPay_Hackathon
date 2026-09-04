'use client';

import { useEffect, useRef, useState } from "react";
import api from '@/lib/api';
import { ArrowRight, ChevronRight, GitBranch, Minus, Plus, Radar, ShieldCheck, Target, X, Zap } from "lucide-react";
import Link from "next/link";

type Kind = "incidents";

const money = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

function ViewShell({ kind, children }: { kind: Kind; children: React.ReactNode }) {
  const config = {
    eyebrow: "Investigation / relationship graph",
    title: "Incident graph",
    subtitle: "Connect exceptions, records, sources, and owners into one operational thread.",
    icon: GitBranch,
    action: "Open a relationship"
  };
  const Icon = config.icon;
  return (
    <div className="command-view">
      <div className="command-view-head">
        <div>
          <span className="eyebrow">{config.eyebrow}</span>
          <h1>{config.title}</h1>
          <p>{config.subtitle}</p>
        </div>
        <div className="command-view-actions">
          <button className="ghost-action"><Icon size={15} /> {config.action}</button>
          <Link href="/dashboard" className="review-btn">Back to overview <ArrowRight size={15} /></Link>
        </div>
      </div>
      <div className="command-tabs">
        <Link href="/dashboard">Overview</Link>
        <Link href="/transactions">Transactions</Link>
        <Link href="/exceptions">Exceptions</Link>
        <Link className="active" href="/incidents">Incident graph</Link>
      </div>
      {children}
    </div>
  );
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/incidents/latest')
      .then(res => setIncidents(res.data.incidents || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const [zoom, setZoom] = useState(1);
  const [tip, setTip] = useState<string | null>(null);
  const [shared, setShared] = useState(false);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  const shareView = () => {
    const url = window.location.href;
    const copy = navigator.clipboard?.writeText(url) ?? Promise.resolve();
    copy.then(() => {
      setShared(true);
      window.setTimeout(() => setShared(false), 2200);
    });
  };

  const dragRef = useRef({ active: false, startX: 0, startY: 0, originX: 0, originY: 0 });
  const startDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    dragRef.current = { active: true, startX: event.clientX, startY: event.clientY, originX: pan.x, originY: pan.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current.active) return;
    setPan({ x: dragRef.current.originX + event.clientX - dragRef.current.startX, y: dragRef.current.originY + event.clientY - dragRef.current.startY });
  };
  const endDrag = () => { dragRef.current.active = false; };

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse font-medium">Loading incident graph...</div>;

  const mainInc = incidents[0] || { id: "INC-000", title: "Baseline stable", exposure: 0, status: "Resolved" };

  return (
    <ViewShell kind="incidents">
      <div className="incident-toolbar">
        <span className="eyebrow">Relationship canvas · {Math.round(zoom * 100)}% · drag to pan</span>
        <div>
          <button onClick={() => setZoom(value => Math.max(.7, value - .1))} aria-label="Zoom out"><Minus size={15} /></button>
          <button onClick={() => setZoom(value => Math.min(1.5, value + .1))} aria-label="Zoom in"><Plus size={15} /></button>
          <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>Reset view</button>
          <button className="share-view-button" onClick={shareView}>Share View</button>
        </div>
      </div>
      {shared && <div className="graph-share-toast" role="status">View link copied to clipboard <X size={14} /></div>}
      <div className="incident-stage">
        <div className="incident-graph incident-graph-zoom" style={{ "--graph-scale": zoom, "--graph-x": `${pan.x}px`, "--graph-y": `${pan.y}px` } as React.CSSProperties} onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={endDrag} onPointerLeave={() => { endDrag(); setTip(null); }}>
          <div className="graph-line line-a" />
          <div className="graph-line line-b" />
          <button className="graph-node node-center" onMouseEnter={() => setTip(`${mainInc.id} · ${mainInc.status} incident`)} onFocus={() => setTip(`${mainInc.id} · ${mainInc.status} incident`)}>
            <GitBranch size={18} />
            <b>{mainInc.id}</b>
            <small>{mainInc.status} incident</small>
          </button>
          <button className="graph-node node-top" onMouseEnter={() => setTip("Bank X · source freshness verified")} onFocus={() => setTip("Bank X · source freshness verified")}>
            <span className="graph-dot sage" />
            <b>Bank X</b>
            <small>source</small>
          </button>
          <button className="graph-node node-left" onMouseEnter={() => setTip(`Exception · ${money(mainInc.exposure || 0)} exposure`)} onFocus={() => setTip(`Exception · ${money(mainInc.exposure || 0)} exposure`)}>
            <span className="graph-dot copper" />
            <b>Exception</b>
            <small>{money(mainInc.exposure || 0)}</small>
          </button>
          <button className="graph-node node-right" onMouseEnter={() => setTip("Records · linked trail")} onFocus={() => setTip("Records · linked trail")}>
            <span className="graph-dot sage" />
            <b>Records</b>
            <small>linked trail</small>
          </button>
          {tip && <div className="graph-tooltip" role="status">{tip}</div>}
        </div>
        <div className="incident-list">
          <span className="eyebrow">Open clusters</span>
          {incidents.length > 0 ? incidents.map(inc => (
            <button key={inc.id}>
              <span>
                <b>{inc.id} · {inc.title}</b>
                <small>{money(inc.exposure || 0)} · linked evidence</small>
              </span>
              <strong className={inc.status === "OPEN" || inc.status === "CRITICAL" ? "copper-text" : ""}>{inc.status}</strong>
              <ChevronRight size={15} />
            </button>
          )) : (
            <div className="p-4 text-sm text-zinc-500">No active incidents detected.</div>
          )}
        </div>
      </div>
    </ViewShell>
  );
}
