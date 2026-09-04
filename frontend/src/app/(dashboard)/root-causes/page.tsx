'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { ArrowRight, ChevronRight, Network, Target, Zap } from 'lucide-react';
import Link from 'next/link';

const money = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

export default function RootCauses() {
  const [clusters, setClusters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/clusters/latest')
      .then(res => setClusters(res.data.clusters || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse font-medium">Analyzing root-cause clusters...</div>;

  return (
    <div className="command-view">
      <div className="command-view-head">
        <div>
          <span className="eyebrow">Root-Cause Intelligence</span>
          <h1>Exception Clusters</h1>
          <p>Many exceptions. Fewer underlying problems. Connect systemic issues to underlying causes.</p>
        </div>
        <div className="command-view-actions">
          <button className="ghost-action"><Network size={15} /> Analyze Clusters</button>
          <Link href="/dashboard" className="review-btn">Back to overview <ArrowRight size={15} /></Link>
        </div>
      </div>
      <div className="command-tabs">
        <Link href="/incidents">Incident graph</Link>
        <Link className="active" href="/root-causes">Root Causes</Link>
        <Link href="/early-warnings">Early Warnings</Link>
      </div>

      <div className="action-callout mt-6" style={{ marginTop: '2rem' }}>
        <div>
          <span className="eyebrow">DBSCAN Clustering Active</span>
          <h2>Address the root cause,<br /><em>not just the symptoms.</em></h2>
        </div>
        <p>Ranked by clustered financial impact and confidence of the root cause hypothesis.</p>
      </div>

      <div className="action-list" style={{ marginTop: '2rem' }}>
        {clusters.length > 0 ? clusters.map((c, i) => (
          <div className="action-row" key={c.id}>
            <button className="action-row-button" style={{ paddingLeft: '20px' }}>
              <span className="action-index">{String(i + 1).padStart(2, '0')}</span>
              <span>
                <b>{c.root_cause_hypothesis || 'Systemic Delay'}</b>
                <small><Target size={12} /> {c.exception_ids?.length || 0} exceptions · Cluster {c.id.split('-')[1] || c.id}</small>
              </span>
              <strong>{money(c.total_exposure || 0)}</strong>
              <span className={`status-pill ${c.status === 'OPEN' ? 'copper' : 'sage'}`}>{c.status || 'OPEN'}</span>
              <ChevronRight size={16} />
            </button>
          </div>
        )) : (
          <div className="empty-actions">
            No systemic root causes detected. Pattern matching is active.
          </div>
        )}
      </div>
      
      {clusters.length > 0 && (
        <div className="action-foot">
          <Zap size={16} />
          <span><b>{clusters.length} root cause hypotheses generated.</b> Review associated incident graphs for details.</span>
        </div>
      )}
    </div>
  );
}
