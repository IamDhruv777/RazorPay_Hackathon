'use client';

import { useEffect, useState } from "react";
import Link from "next/link";
import api from '@/lib/api';
import { ArrowRight, ArrowUpRight, Check, ChevronRight, CircleAlert, Clock3, Search, ShieldCheck, Sparkles, TrendingUp, X, Zap } from "lucide-react";

const formatINR = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

export default function Dashboard() { 
  const [notice, setNotice] = useState(false); 
  
  const [data, setData] = useState<any>({
    closeReadiness: null,
    incidents: [],
    priorities: [],
    warnings: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [crRes, incRes, prioRes, warnRes] = await Promise.all([
          api.get('/close-readiness/latest'),
          api.get('/incidents/latest'),
          api.get('/priority/latest'),
          api.get('/warnings/latest')
        ]);
        
        setData({
          closeReadiness: crRes.data.close_readiness,
          incidents: incRes.data.incidents || [],
          priorities: prioRes.data.priorities || [],
          warnings: warnRes.data.warnings || []
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8 animate-pulse text-zinc-500 font-medium">Loading control center...</div>;

  const cr = data.closeReadiness;
  const crDetails = cr?.details || { verified_pct: 0, unresolved_exposure: 0, critical_exceptions: 0 };
  const score = cr?.score ?? 0;
  
  const inc = data.incidents[0];
  const warn = data.warnings[0];
  
  return (
    <div className="dashboard">
      <div className="dashboard-intro">
        <div>
          <span className="eyebrow">Good afternoon · Wednesday, September 04</span>
          <h1>Finance Control Center</h1>
          <p>One calm place to understand the close, investigate the signal, and decide what happens next.</p>
        </div>
        <div className="intro-actions">
          <button className="ghost-action" onClick={() => setNotice(true)}><Search size={15}/> Search records</button>
          <button className="review-btn" onClick={() => setNotice(true)}>Review blockers <ArrowRight size={16}/></button>
        </div>
      </div>
      
      {notice && (
        <div className="notice">
          <CircleAlert size={16}/>
          <span><b>Review queue opened.</b> Showing the highest-exposure blocker first.</span>
          <button onClick={() => setNotice(false)} aria-label="Dismiss"><X size={15}/></button>
        </div>
      )}
      
      <div className="dashboard-tabs">
        <Link href="/dashboard" className="active">Overview</Link>
        <Link href="/transactions">Transactions <span>1,248</span></Link>
        <Link href="/exceptions">Exceptions {crDetails.critical_exceptions > 0 && <span className="tab-hot">{String(crDetails.critical_exceptions).padStart(2, '0')} critical</span>}</Link>
        <a href="#controls">Controls</a>
        <a href="#activity">Activity</a>
      </div>
      
      <section className="control-card">
        <div className="control-score">
          <span className="eyebrow">Can I close the books?</span>
          <div className="score">{score} <small>/ 100</small></div>
          <div className="ready-state"><span/> {cr?.status?.replace(/_/g, ' ') || 'NOT READY'}</div>
          <p>{data.incidents.length} active incident(s) and {data.priorities.length} pending reviews remain before close.</p>
          <button onClick={() => setNotice(true)}>View close checklist <ArrowRight size={14}/></button>
        </div>
        <div className="control-breakdown">
          {[
            ["Revenue verified", `${crDetails.verified_pct}%`, "Verified", "sage"], 
            ["Unresolved exposure", formatINR(crDetails.unresolved_exposure), "Needs review", "copper"], 
            ["Critical exceptions", String(crDetails.critical_exceptions).padStart(2, '0'), "Open", "copper"], 
            ["Pending reviews", String(data.priorities.length).padStart(2, '0'), "Within SLA", "navy"]
          ].map(([a, b, c, s]) => (
            <div className="breakdown-row" key={a}><span>{a}</span><b>{b}</b><small className={s as string}>{c}</small></div>
          ))}
          <div className="score-meter"><span style={{ width: `${score}%` }}/></div>
          <div className="meter-caption"><span>Control health</span><b>{score}%</b></div>
        </div>
      </section>
      
      <div className="metrics-row">
        {[
          ["Processed", "1,248", "+8.4% this period", "good"], 
          ["Verified", `${crDetails.verified_pct}%`, "of processed", "good"], 
          ["Unresolved exposure", formatINR(crDetails.unresolved_exposure), "needs review", "hot"], 
          ["Open exceptions", String(crDetails.critical_exceptions), "critical", "hot"], 
          ["Active warnings", String(data.warnings.length), "new signals", data.warnings.length > 0 ? "hot" : "good"]
        ].map(([a, b, c, tone]) => (
          <div className={`metric metric-${tone}`} key={a}><span className="eyebrow">{a}</span><b>{b}</b><small>{c}</small></div>
        ))}
      </div>
      
      <div className="dashboard-grid">
        <div className="dashboard-panel changed-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">What changed?</span>
              <h2>{inc ? inc.title : "Baseline stable"}</h2>
              <p>{inc ? "Unexpected movement detected across the current close period." : "No active incidents detected."}</p>
            </div>
            {inc && <span className="trend-chip"><TrendingUp size={14}/> +{Math.round((inc.confidence || 0) * 100)}% conf</span>}
          </div>
          {inc && <div className="big-change">{formatINR(inc.exposure || 0)} <small>exposure</small></div>}
          <div className="dashboard-bars">
            {[30, 38, 24, 45, 36, 52, 47, 58, 54, 71, 66, 88, 76, 94].map((h, i) => <i key={i} style={{ height: `${h}%` }} className={i > 10 ? "hot" : ""}/>)}
          </div>
          <div className="panel-foot">
            <span>Status <b>{inc?.status || 'N/A'}</b></span>
            {inc && <span>Exposure <b>{formatINR(inc.exposure || 0)}</b></span>}
            <Link href="/incidents" className="flex items-center gap-1 font-semibold text-sm hover:underline">Investigate incident <ArrowUpRight size={15}/></Link>
          </div>
        </div>
        
        <div className="dashboard-panel priority-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Priority queue</span>
              <h2>What should I fix first?</h2>
              <p>Ranked by exposure × confidence.</p>
            </div>
            <Zap size={17}/>
          </div>
          <div className="priority-list">
            {data.priorities.slice(0, 3).map((p: any, i: number) => (
              <button className="priority-item" key={p.id} onClick={() => setNotice(true)}>
                <span className="priority-number">{String(i + 1).padStart(2, '0')}</span>
                <span><b>{p.entity_id}</b><small>{formatINR(p.exposure_score * 1000)} exposure</small></span>
                <strong>{Math.round(p.total_score)}/100</strong>
                <ChevronRight size={16}/>
              </button>
            ))}
            {data.priorities.length === 0 && (
              <div className="p-6 text-center text-sm text-zinc-500">No priority issues pending.</div>
            )}
          </div>
          
          {warn && (
            <div className="warning-callout">
              <Sparkles size={16}/>
              <div>
                <b>Early warning signal</b>
                <p>{(warn.signal_type || '').replace(/_/g, ' ')}</p>
                <small>Severity: {warn.severity} · {formatINR(warn.estimated_exposure || 0)}</small>
              </div>
            </div>
          )}
        </div>
      </div>
      
      <section id="controls" className="dashboard-lower-grid">
        <div className="dashboard-panel control-matrix">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Control coverage</span>
              <h2>Where confidence comes from</h2>
            </div>
            <ShieldCheck size={17}/>
          </div>
          {[
            ["Source freshness", "6 / 6 connected", "good"], 
            ["Reconciliation rules", "42 / 44 passing", "good"], 
            ["Evidence anchors", "1,193 verified", "good"], 
            ["Human review queue", `${String(data.priorities.length).padStart(2, '0')} pending`, data.priorities.length > 0 ? "hot" : "good"]
          ].map(([a, b, tone]) => (
            <div className="matrix-row" key={a}>
              <span className={`matrix-dot ${tone as string}`}/>
              <div><b>{a}</b><small>{b}</small></div>
              <ChevronRight size={15}/>
            </div>
          ))}
        </div>
        
        <div className="dashboard-panel activity-panel" id="activity">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Recent activity</span>
              <h2>What moved today</h2>
            </div>
            <Clock3 size={17}/>
          </div>
          <div className="activity-list">
            {[
              ["09:42", "Exception cluster updated", "Bank X · 14 records"], 
              ["09:18", "Settlement file verified", "1,248 records · 99.2% match"], 
              ["08:56", "Review assigned", "Arjun Kapoor · LL-0148"]
            ].map(([time, title, detail]) => (
              <div key={time}>
                <time>{time}</time>
                <span><b>{title}</b><small>{detail}</small></span>
              </div>
            ))}
          </div>
          <Link href="/exceptions" className="panel-link">Open investigation log <ArrowRight size={14}/></Link>
        </div>
      </section>
    </div>
  ); 
}
