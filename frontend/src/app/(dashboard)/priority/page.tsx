'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { ArrowRight, ChevronRight, Target, UsersRound, Zap, X } from 'lucide-react';
import Link from 'next/link';

export default function PriorityQueue() {
  const [priorities, setPriorities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any | null>(null);
  
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkState, setBulkState] = useState<string | null>(null);

  useEffect(() => {
    api.get('/priority/latest')
      .then(res => setPriorities(res.data.priorities || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const toggle = (id: string) => setSelectedIds(ids => ids.includes(id) ? ids.filter(i => i !== id) : [...ids, id]);
  const allSelected = priorities.length > 0 && selectedIds.length === priorities.length;

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse font-medium">Loading priority queue...</div>;

  return (
    <div className="command-view">
      <div className="command-view-head">
        <div>
          <span className="eyebrow">Prevention / owner queue</span>
          <h1>Action queue</h1>
          <p>Make the next best finance decision visible, assigned, and easy to close.</p>
        </div>
        <div className="command-view-actions">
          <button className="ghost-action"><Target size={15} /> Prioritize the queue</button>
          <Link href="/dashboard" className="review-btn">Back to overview <ArrowRight size={15} /></Link>
        </div>
      </div>
      <div className="command-tabs">
        <Link href="/incidents">Incident graph</Link>
        <Link href="/root-causes">Root Causes</Link>
        <Link className="active" href="/priority">Priority Queue</Link>
        <Link href="/close-readiness">Close Readiness</Link>
      </div>

      <div className="action-callout mt-6">
        <div>
          <span className="eyebrow">Recommended operating order</span>
          <h2>Fix the exposure,<br /><em>then close the loop.</em></h2>
        </div>
        <p>Ranked by financial impact, confidence, and the time remaining in this close period.</p>
      </div>

      <div className="bulk-toolbar mt-8">
        <label>
          <input type="checkbox" checked={allSelected} onChange={() => setSelectedIds(allSelected ? [] : priorities.map(r => r.id))} /> Select all
        </label>
        <span>{selectedIds.length} selected</span>
        <div>
          <button disabled={!selectedIds.length} onClick={() => { setBulkState('Approved selected items'); setTimeout(() => setBulkState(null), 3000); }}>Approve selected</button>
          <button disabled={!selectedIds.length} onClick={() => { setBulkState('Assigned selected items'); setTimeout(() => setBulkState(null), 3000); }}>Assign selected</button>
        </div>
      </div>

      {bulkState && (
        <div className="bulk-feedback" role="status">
          <Zap size={14} />{bulkState} · no backend change made
          <button onClick={() => setBulkState(null)} aria-label="Dismiss"><X size={14} /></button>
        </div>
      )}

      <div className="action-list">
        {priorities.map((row, i) => (
          <div className="action-row action-row-with-check" key={row.id}>
            <input type="checkbox" checked={selectedIds.includes(row.id)} onChange={() => toggle(row.id)} />
            <button className="action-row-button" onClick={() => setSelected(row)}>
              <span className="action-index">{String(i + 1).padStart(2, '0')}</span>
              <span>
                <b>{row.entity_id}</b>
                <small><UsersRound size={12} /> {row.entity_type} · Score: {Math.round(row.total_score)}</small>
              </span>
              <strong>{Math.round(row.total_score)}/100</strong>
              <span className="status-pill copper">Review</span>
              <ChevronRight size={16} />
            </button>
          </div>
        ))}
        {priorities.length === 0 && (
          <div className="empty-actions">No actions match this due-date view.</div>
        )}
      </div>

      <div className="action-foot">
        <Zap size={16} />
        <span><b>{priorities.length} actions require human review.</b> Ranked by AI severity score.</span>
      </div>

      {selected && (
        <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null) }}>
          <aside className="detail-drawer" data-drawer="true" role="dialog" aria-modal="true">
            <div className="drawer-head">
              <div>
                <span className="eyebrow">Action detail</span>
                <h2>{selected.entity_id}</h2>
              </div>
              <button className="drawer-close" onClick={() => setSelected(null)}><X size={18} /></button>
            </div>
            <div className="drawer-body">
              <div className="drawer-status">
                <span className="status-pill copper">Review</span>
                <strong>{Math.round(selected.total_score)} / 100 Score</strong>
              </div>
              <p className="drawer-lead">This item requires human review based on the priority scoring model.</p>
              
              <div className="drawer-fields">
                <div><span>Entity Type</span><b>{selected.entity_type}</b></div>
                <div><span>Component Score (Exposure)</span><b>{Math.round(selected.component_scores?.exposure_score * 100) || 0}</b></div>
                <div><span>Component Score (Age)</span><b>{Math.round(selected.component_scores?.age_score * 100) || 0}</b></div>
                <div><span>Component Score (Confidence)</span><b>{Math.round(selected.component_scores?.confidence_score * 100) || 0}</b></div>
              </div>

              <div className="drawer-actions">
                <span className="eyebrow">Mock workflow action</span>
                <div>
                  <button onClick={() => setSelected(null)}>Approve</button>
                  <button onClick={() => setSelected(null)}>Reject</button>
                  <button onClick={() => setSelected(null)}>Assign</button>
                </div>
              </div>
              <button className="drawer-primary" onClick={() => setSelected(null)}>Return to action queue <ArrowRight size={14} /></button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
