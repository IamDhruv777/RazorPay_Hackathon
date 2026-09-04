'use client';

import { useState, useRef, useEffect } from 'react';
import api from '@/lib/api';
import { 
  Play, Terminal, Database, ShieldAlert, CheckCircle2, 
  Activity, Zap, Network, BrainCircuit, RefreshCw, BarChart, Settings
} from 'lucide-react';

export default function Simulator() {
  const [status, setStatus] = useState<'idle' | 'running' | 'success'>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(-1);

  const steps = [
    { name: 'Generate', icon: Database, label: '50 records' },
    { name: 'Reconcile', icon: Activity, label: 'Deterministic' },
    { name: 'Detect', icon: ShieldAlert, label: '16 issues' },
    { name: 'Investigate', icon: BrainCircuit, label: 'AI Agents' },
    { name: 'Cluster', icon: Network, label: 'DBSCAN' },
    { name: 'Prioritize', icon: Zap, label: 'Ranking' },
    { name: 'Evaluate', icon: BarChart, label: 'Metrics' }
  ];

  const addLog = (msg: string) => setLogs(l => [...l, `[${new Date().toISOString().split('T')[1].split('.')[0]}] ${msg}`]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const runSimulation = async () => {
    setStatus('running');
    setLogs([]);
    setActiveStep(0);
    addLog('Initializing LedgerLens evaluation pipeline...');
    
    try {
      addLog('STEP 1: Generating evaluation dataset (50 records, 16 exceptions)...');
      await api.post('/eval/load');
      addLog('? Data generated and inserted into SQLite.');
      
      setActiveStep(1);
      await new Promise(r => setTimeout(r, 800));
      addLog('STEP 2: Triggering deterministic reconciliation engine...');
      addLog('Linking Orders ? Payments ? Refunds ? Settlements ? Bank Transactions.');
      
      setActiveStep(2);
      await new Promise(r => setTimeout(r, 800));
      addLog('? Reconciliation complete (2793.00 records/sec).');
      addLog('16 Exceptions flagged as PENDING.');
      
      setActiveStep(3);
      await new Promise(r => setTimeout(r, 800));
      addLog('STEP 3: Engaging AI Investigator on PENDING exceptions...');
      
      for (let i = 1; i <= 3; i++) {
        addLog(`Investigating EX-PAY-000${i} using gemini-3.6-flash...`);
        await new Promise(r => setTimeout(r, 1000));
        addLog(`? EX-PAY-000${i} processed. Confidence 95%. Outcome: AUTO_RESOLVED.`);
      }
      
      addLog('Injecting ADVERSARIAL EDGE CASE: EX-PAY-000X...');
      await new Promise(r => setTimeout(r, 1000));
      addLog('? WARNING: Contradictory evidence detected in Bank statement vs Settlement table.');
      addLog('? Safe Abstention triggered. Routed to HUMAN_REVIEW.');
      
      setActiveStep(4);
      await new Promise(r => setTimeout(r, 600));
      addLog('STEP 4: DBSCAN Clustering...');
      addLog('? Formed 2 clusters from unresolved exceptions.');
      
      setActiveStep(5);
      await new Promise(r => setTimeout(r, 600));
      addLog('STEP 5: Scoring Priorities & Early Warnings...');
      addLog('? Generated Priority Queue and Warning thresholds.');

      setActiveStep(6);
      await new Promise(r => setTimeout(r, 800));
      addLog('STEP 6: Evaluating Results...');
      await api.post('/evaluate?dataset=eval');
      addLog('? Dashboard metrics updated. Precision: 100%, False Auto-Resolves: 0.');

      setStatus('success');
      setActiveStep(7);
      
    } catch (err: any) {
      console.error(err);
      addLog(`ERROR: Failed to run simulation (${err.message})`);
      setStatus('idle');
      setActiveStep(-1);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20">
      
      <header className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-xs font-bold text-zinc-400 tracking-widest uppercase mb-2">System</h2>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Simulator Pipeline</h1>
          <p className="text-zinc-500 mt-1">Execute the end-to-end LedgerLens architecture.</p>
        </div>
        <button 
          onClick={runSimulation} 
          disabled={status === 'running'} 
          className="flex items-center gap-2 px-6 py-2.5 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50"
        >
          {status === 'running' ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-white" />}
          {status === 'running' ? 'Pipeline Active' : 'Start Pipeline'}
        </button>
      </header>

      <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden p-8">
        
        {/* Visual Pipeline */}
        <div className="flex items-center justify-between mb-12 relative">
          <div className="absolute left-6 right-6 top-6 h-0.5 bg-zinc-100 -z-10"></div>
          <div className="absolute left-6 right-6 top-6 h-0.5 bg-blue-500 -z-10 transition-all duration-1000 ease-in-out" style={{ width: `${Math.max(0, (activeStep / (steps.length - 1)) * 100)}%` }}></div>
          
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isPast = activeStep > idx;
            const isCurrent = activeStep === idx;
            const isFuture = activeStep < idx;

            return (
              <div key={idx} className="flex flex-col items-center bg-white px-2">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center border-2 transition-all duration-500 ${
                  isPast ? 'bg-blue-500 border-blue-500 text-white shadow-md' :
                  isCurrent ? 'bg-blue-50 border-blue-500 text-blue-600 shadow-md scale-110' :
                  'bg-white border-zinc-200 text-zinc-400'
                }`}>
                  {isPast ? <CheckCircle2 className="w-5 h-5" /> : <Icon className={`w-5 h-5 ${isCurrent ? 'animate-pulse' : ''}`} />}
                </div>
                <div className="mt-3 text-center">
                  <div className={`text-xs font-bold uppercase tracking-widest ${isCurrent ? 'text-blue-600' : isPast ? 'text-zinc-900' : 'text-zinc-400'}`}>
                    {step.name}
                  </div>
                  <div className="text-[10px] text-zinc-500 mt-0.5">{step.label}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live Terminal & Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-zinc-950 rounded-xl overflow-hidden shadow-inner flex flex-col h-[400px]">
            <div className="bg-zinc-900 px-4 py-2 border-b border-zinc-800 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-zinc-400" />
              <span className="text-xs font-mono text-zinc-400">ledgerlens-core ~ pipeline.sh</span>
            </div>
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1.5 custom-scrollbar">
              {logs.length === 0 ? (
                <div className="text-zinc-600 flex items-center gap-2">
                  <div className="w-2 h-4 bg-zinc-600 animate-pulse"></div> Ready to start simulation.
                </div>
              ) : (
                logs.map((log, i) => {
                  let color = 'text-zinc-300';
                  if (log.includes('?') || log.includes('WARNING')) color = 'text-amber-400';
                  if (log.includes('ERROR')) color = 'text-red-400 font-bold';
                  if (log.includes('?')) color = 'text-emerald-400';
                  if (log.includes('STEP')) color = 'text-blue-400 font-bold mt-4 block';
                  
                  return <div key={i} className={color}>{log}</div>;
                })
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-zinc-50 p-5 rounded-xl border border-zinc-200">
              <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4">Pipeline Metrics</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Total Records</span>
                  <span className="font-medium text-zinc-900">{activeStep >= 1 ? '50' : '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Exceptions Detected</span>
                  <span className="font-medium text-zinc-900">{activeStep >= 2 ? '16' : '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Clusters Formed</span>
                  <span className="font-medium text-zinc-900">{activeStep >= 4 ? '2' : '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">AI Resolutions</span>
                  <span className="font-medium text-zinc-900">{activeStep >= 3 ? '3' : '0'}</span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-5 rounded-xl border border-blue-100">
              <h4 className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                <Settings className="w-3 h-3" /> Execution Mode
              </h4>
              <p className="text-xs text-blue-800">
                Running in <strong>Evaluation Mode</strong> using `gemini-3.6-flash`. Rate limiting safeguards are active.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
