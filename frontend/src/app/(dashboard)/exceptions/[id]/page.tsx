'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import { 
  ArrowLeft, Search, CheckCircle2, XCircle, 
  AlertTriangle, ShieldAlert, Clock, Database, 
  Bot, RefreshCw, ChevronRight, Activity
} from 'lucide-react';

export default function ExceptionDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [investigating, setInvestigating] = useState(false);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const resp = await api.get(`/exceptions/${id}`);
      setData(resp.data);
    } catch (err) {
      console.error(err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const runInvestigation = async () => {
    setInvestigating(true);
    try {
      await api.post(`/exceptions/${id}/investigate`);
      await fetchData(); // Refresh data
    } catch (err) {
      console.error("Failed to run investigation", err);
    } finally {
      setInvestigating(false);
    }
  };

  const formatINR = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse">Loading exception details...</div>;
  if (error || !data) return <div className="p-8 text-red-500">Failed to load exception data.</div>;

  const FlowNode = ({ label, id, isMissing }: { label: string, id: string | null, isMissing: boolean }) => (
    <div className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 min-w-[120px] ${
      isMissing 
        ? 'border-red-200 bg-red-50 text-red-700' 
        : id 
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
          : 'border-zinc-200 bg-zinc-50 text-zinc-400 border-dashed'
    }`}>
      <span className="text-xs font-bold uppercase tracking-widest mb-2 opacity-70">{label}</span>
      {isMissing ? (
        <XCircle className="w-6 h-6 mb-1 text-red-500" />
      ) : id ? (
        <CheckCircle2 className="w-6 h-6 mb-1 text-emerald-500" />
      ) : (
        <div className="w-6 h-6 mb-1" />
      )}
      <span className="text-xs font-medium truncate max-w-[100px]">{id || 'None'}</span>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-zinc-50">
      
      {/* Header bar */}
      <div className="bg-white border-b border-zinc-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link href="/exceptions" className="p-2 -ml-2 text-zinc-400 hover:text-zinc-600 rounded-md hover:bg-zinc-100 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="h-6 w-px bg-zinc-200" />
          <div>
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-0.5">Investigation Workspace</div>
            <h1 className="text-xl font-semibold text-zinc-900">{data.id}</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase ${
            data.severity === 'CRITICAL' ? 'bg-red-100 text-red-700 border border-red-200' :
            data.severity === 'HIGH' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 
            'bg-zinc-100 text-zinc-700 border border-zinc-200'
          }`}>
            {data.severity} SEVERITY
          </span>
          <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase bg-zinc-100 text-zinc-700 border border-zinc-200">
            CONFIDENCE: {Math.round(data.confidence * 100)}%
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full space-y-8 pb-20">
        
        {/* Top Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-1">Exposure</div>
            <div className="text-3xl font-semibold tracking-tight text-red-600">{formatINR(data.amount)}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-1">Type</div>
            <div className="text-lg font-medium text-zinc-900 mt-2">{data.type?.replace(/_/g, ' ')}</div>
          </div>
          <div>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-1">Status</div>
            <div className="flex items-center gap-2 mt-2 font-medium text-zinc-700">
              {data.status === 'AUTO_RESOLVED' ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <ShieldAlert className="w-5 h-5 text-amber-500" />}
              {data.status?.replace(/_/g, ' ')}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-1">Detected</div>
            <div className="text-sm font-medium text-zinc-900 mt-2 flex items-center gap-2">
              <Clock className="w-4 h-4 text-zinc-400" />
              {new Date(data.detected_at).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Financial Flow */}
        <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-6 overflow-x-auto">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">Financial Flow</h3>
          <div className="flex items-center justify-between min-w-max gap-2 pb-2">
            <FlowNode label="Order" id={data.order_id} isMissing={!data.order_id && data.type.includes('ORDER')} />
            <div className="flex-1 h-0.5 bg-zinc-200 min-w-[30px]"></div>
            <FlowNode label="Payment" id={data.payment_id} isMissing={!data.payment_id && data.order_id !== null} />
            <div className="flex-1 h-0.5 bg-zinc-200 min-w-[30px]"></div>
            <FlowNode label="Refund" id={data.refund_id} isMissing={false} />
            <div className="flex-1 h-0.5 bg-zinc-200 min-w-[30px]"></div>
            <FlowNode label="Settlement" id={data.settlement_id} isMissing={!data.settlement_id && data.payment_id !== null && !data.refund_id} />
            <div className="flex-1 h-0.5 bg-zinc-200 min-w-[30px]"></div>
            <FlowNode label="Bank" id={data.bank_id} isMissing={!data.bank_id && data.settlement_id !== null} />
          </div>
        </section>

        {/* AI Investigation */}
        <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">AI Investigation</h3>
                <p className="text-xs text-zinc-500">Autonomous analysis engine</p>
              </div>
            </div>
            {!data.investigation && (
              <button 
                onClick={runInvestigation}
                disabled={investigating}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {investigating ? <><RefreshCw className="w-4 h-4 animate-spin" /> Investigating...</> : 'Run Investigation'}
              </button>
            )}
          </div>
          
          <div className="p-8 space-y-8">
            {data.investigation ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3">What We Found</h4>
                    <p className="text-zinc-900 leading-relaxed font-medium">{data.investigation.classification}</p>
                    
                    <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mt-8 mb-3">Why This Explains The Issue</h4>
                    <p className="text-zinc-700 leading-relaxed text-sm bg-zinc-50 p-4 rounded-xl border border-zinc-100">{data.investigation.reasoning_summary}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3">Recommended Action</h4>
                    <div className="bg-blue-50 text-blue-900 p-4 rounded-xl border border-blue-100 font-medium">
                      {data.investigation.recommended_action}
                    </div>
                    
                    <div className="mt-8 flex gap-8">
                      <div>
                        <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">Confidence</h4>
                        <div className="text-2xl font-semibold text-zinc-900">{Math.round(data.investigation.confidence * 100)}%</div>
                      </div>
                      <div>
                        <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">Auto-Resolve</h4>
                        <div className="text-2xl font-semibold text-zinc-900">{data.investigation.auto_resolve ? 'Yes' : 'No'}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-6 border-t border-zinc-100">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Evidence Collected</h4>
                  <div className="grid gap-3">
                    {data.investigation.evidence?.map((ev: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-4 bg-zinc-50 p-3 rounded-lg border border-zinc-200">
                        <Database className="w-4 h-4 text-zinc-400" />
                        <div className="text-sm">
                          <span className="font-semibold text-zinc-700">{ev.source_table}</span>
                          <span className="text-zinc-400 mx-2">/</span>
                          <span className="text-zinc-600 font-mono text-xs">{ev.source_id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <Activity className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
                <h4 className="text-zinc-900 font-medium mb-2">No investigation recorded</h4>
                <p className="text-zinc-500 text-sm">Run the AI Investigation to gather evidence and determine the root cause.</p>
              </div>
            )}
          </div>
        </section>
        
        {/* Audit Trail */}
        {data.audit_trail?.length > 0 && (
          <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-zinc-100">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Audit Trail</h3>
            </div>
            <div className="p-6">
              <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-zinc-200 before:to-transparent">
                {data.audit_trail.map((event: any, i: number) => (
                  <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-zinc-100 text-zinc-500 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10">
                      <Clock className="w-4 h-4" />
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-zinc-200 shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold uppercase text-zinc-500">{event.action.replace(/_/g, ' ')}</span>
                        <time className="text-[10px] text-zinc-400 font-medium">{new Date(event.ts).toLocaleTimeString()}</time>
                      </div>
                      <div className="text-sm text-zinc-800 font-medium">{event.decision}</div>
                      {event.evidence_summary && <div className="text-xs text-zinc-500 mt-2 bg-zinc-50 p-2 rounded-md border border-zinc-100">{event.evidence_summary}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
