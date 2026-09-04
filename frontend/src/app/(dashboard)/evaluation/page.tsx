'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Target, CheckCircle2, ShieldAlert, BarChart, Database, Zap, RefreshCw } from 'lucide-react';

export default function Evaluation() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    setLoading(true);
    try {
      const resp = await api.get('/evaluate/latest');
      setData(resp.data);
    } catch (err) {
      console.error(err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const runEval = async () => {
    setRunning(true);
    try {
      const resp = await api.post('/evaluate?dataset=eval');
      setData(resp.data.metrics); // or fetchLatest()
      await fetchLatest();
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse">Loading technical evaluation...</div>;
  if (error && !data) return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col items-center text-center mt-20">
      <Target className="w-16 h-16 text-zinc-200 mb-6" />
      <h2 className="text-xl font-medium text-zinc-900 mb-2">No Evaluation Data</h2>
      <p className="text-zinc-500 mb-8 max-w-md">The evaluation pipeline has not been run against the ground truth dataset yet.</p>
      <button onClick={runEval} disabled={running} className="px-6 py-2.5 bg-zinc-900 text-white rounded-lg font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50">
        {running ? 'Running Evaluation...' : 'Run Benchmark'}
      </button>
    </div>
  );

  const m = data?.metrics || {};

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 pb-20">
      
      <header className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-xs font-bold text-zinc-400 tracking-widest uppercase mb-2">Technical Control</h2>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Evaluation Console</h1>
          <p className="text-zinc-500 mt-1">Ground truth benchmark vs LedgerLens Engine</p>
        </div>
        <button onClick={runEval} disabled={running} className="flex items-center gap-2 px-4 py-2 bg-white border border-zinc-200 shadow-sm text-zinc-700 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
          {running ? 'Evaluating...' : 'Re-run Evaluation'}
        </button>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-sm">
          <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-1 flex items-center gap-2">
            <Database className="w-4 h-4" /> Dataset
          </div>
          <div className="text-2xl font-semibold text-zinc-900">{data?.record_count || 1000} records</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-sm">
          <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-1 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" /> Known Issues
          </div>
          <div className="text-2xl font-semibold text-amber-600">{m.total_ground_truth?.value || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-sm col-span-2">
          <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-1">Pipeline</div>
          <div className="flex items-center gap-6 mt-2">
            <div>
              <span className="text-sm font-medium text-zinc-900 block">LedgerLens v2</span>
              <span className="text-xs text-zinc-500">Autonomous FinOps Engine</span>
            </div>
            <div className="w-px h-8 bg-zinc-200" />
            <div>
              <span className="text-sm font-medium text-emerald-600 block">Exact-ID Baseline</span>
              <span className="text-xs text-zinc-500">Legacy match approach</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        
        {/* Detection Engine */}
        <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-zinc-100 bg-zinc-50/50">
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-500" /> Exception Detection (Reconciliation)
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 p-6 gap-6">
            <div className="flex flex-col">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Detection Precision</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-bold text-zinc-900">
                  {((m.detection_precision?.value || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-zinc-500 font-medium">
                {m.true_positives?.value || 0} / {(m.true_positives?.value || 0) + (m.false_positives?.value || 0)}
              </div>
            </div>
            
            <div className="flex flex-col border-l border-zinc-100 pl-6">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Detection Recall</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-bold text-zinc-900">
                  {((m.detection_recall?.value || 0) * 100).toFixed(1)}%
                </span>
                <span className="text-sm font-medium text-emerald-600 mb-1 bg-emerald-50 px-2 rounded">
                  vs {(m.baseline_recall?.value * 100 || 0).toFixed(1)}% base
                </span>
              </div>
              <div className="text-sm text-zinc-500 font-medium">
                {m.true_positives?.value || 0} / {m.total_ground_truth?.value || 1}
              </div>
            </div>

            <div className="flex flex-col border-l border-zinc-100 pl-6">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">F1 Score</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-bold text-blue-600">
                  {((m.detection_f1?.value || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-zinc-500 font-medium">
                Harmonic mean
              </div>
            </div>
          </div>
        </section>

        {/* AI Investigation Engine */}
        <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-zinc-100 bg-zinc-50/50">
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" /> AI Investigation & Resolution
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 p-6 gap-6">
            <div className="flex flex-col">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Auto-Resolution Precision</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-bold text-zinc-900">
                  {((m.resolution_precision?.value || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-emerald-600 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {m.true_resolutions?.value || 0} correct resolutions
              </div>
            </div>
            
            <div className="flex flex-col border-l border-zinc-100 pl-6">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">False Auto-Resolutions</div>
              <div className="flex items-end gap-3 mb-2">
                <span className={`text-4xl font-bold ${(m.false_resolutions?.value || 0) > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                  {m.false_resolutions?.value || 0}
                </span>
              </div>
              <div className="text-sm text-zinc-500 font-medium">
                Critical failure rate metric
              </div>
            </div>

            <div className="flex flex-col border-l border-zinc-100 pl-6">
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Safe Abstention Rate</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-bold text-zinc-900">
                  {((m.safe_abstention_rate?.value || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-zinc-500 font-medium">
                {m.abstained_investigations?.value || 0} escalated to human
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
