'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { ArrowRight, ChevronRight, Radar, X } from 'lucide-react';
import Link from 'next/link';

const money = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

export default function EarlyWarnings() {
  const [warnings, setWarnings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any | null>(null);

  useEffect(() => {
    api.get('/warnings/latest')
      .then(res => setWarnings(res.data.warnings || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse font-medium">Scanning for emerging patterns...</div>;

  return (
    <div className="command-view">
      <div className="command-view-head">
        <div>
          <span className="eyebrow">Investigation / current period</span>
          <h1>Signal log</h1>
          <p>A readable trail of the moments that moved the close away from its baseline.</p>
        </div>
        <div className="command-view-actions">
          <button className="ghost-action"><Radar size={15} /> Trace a signal</button>
          <Link href="/dashboard" className="review-btn">Back to overview <ArrowRight size={15} /></Link>
        </div>
      </div>
      <div className="command-tabs">
        <Link href="/incidents">Incident graph</Link>
        <Link href="/root-causes">Root Causes</Link>
        <Link className="active" href="/early-warnings">Early Warnings</Link>
      </div>

      <div className="signal-hero">
        <div>
          <span className="eyebrow">The question</span>
          <h2>What moved outside<br /><em>the expected range?</em></h2>
        </div>
        <div className="signal-hero-number">
          <b>{warnings.length}</b>
          <small>emerging signals<br />vs historical baseline</small>
        </div>
      </div>

      <div className="signal-log">
        {warnings.length > 0 ? warnings.map((row) => (
          <button className="signal-log-row signal-log-button" key={row.id} onClick={() => setSelected(row)}>
            <time>{new Date(row.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
            <span className={`signal-mark ${row.severity === 'HIGH' ? 'copper' : 'navy'}`} />
            <div>
              <b>{(row.signal_type || '').replace(/_/g, ' ')}</b>
              <small>{money(row.estimated_exposure || 0)} exposure</small>
            </div>
            <span className="signal-meta">{row.severity} SEVERITY</span>
            <ChevronRight size={16} />
          </button>
        )) : (
          <div className="empty-actions" style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            No emerging signals detected today.
          </div>
        )}
      </div>

      {selected && (
        <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null) }}>
          <aside className="detail-drawer" data-drawer="true" role="dialog" aria-modal="true">
            <div className="drawer-head">
              <div>
                <span className="eyebrow">Signal detail · {new Date(selected.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <h2>{(selected.signal_type || '').replace(/_/g, ' ')}</h2>
              </div>
              <button className="drawer-close" onClick={() => setSelected(null)} aria-label="Close detail drawer"><X size={18} /></button>
            </div>
            <div className="drawer-body">
              <div className={`drawer-signal-mark ${selected.severity === 'HIGH' ? 'copper' : 'navy'}`}>
                <Radar size={18} />
                <span>{selected.severity} SEVERITY</span>
              </div>
              <p className="drawer-lead">The system detected an anomaly outside the historical baseline. This signal has been logged for review before it escalates into a close-period incident.</p>
              
              <div className="drawer-fields">
                <div><span>Observed at</span><b>{new Date(selected.detected_at).toLocaleString()}</b></div>
                <div><span>Exposure</span><b>{money(selected.estimated_exposure || 0)}</b></div>
                <div><span>Classification</span><b>{(selected.signal_type || '').replace(/_/g, ' ')}</b></div>
                <div><span>Status</span><b>{selected.status}</b></div>
              </div>

              <div className="drawer-actions">
                <span className="eyebrow">Investigation steps</span>
                <div>
                  <button onClick={() => setSelected(null)}>Acknowledge</button>
                  <button onClick={() => setSelected(null)}>Dismiss</button>
                </div>
              </div>
              
              <Link className="drawer-primary" href="/incidents" onClick={() => setSelected(null)}>
                Open related incidents <ArrowRight size={14} />
              </Link>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
