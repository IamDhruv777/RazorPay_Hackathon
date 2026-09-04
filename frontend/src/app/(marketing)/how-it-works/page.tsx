'use client';

import Link from 'next/link';
import { ArrowLeft, BookOpen, ShieldCheck, Zap } from 'lucide-react';

export default function HowItWorks() {
  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-8 bg-white p-12 rounded-3xl shadow-sm border border-zinc-200">
        <Link href="/" className="inline-flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to home
        </Link>
        
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900">How LedgerLens Works</h1>
        <p className="text-lg text-zinc-600">LedgerLens is an autonomous finance controller that acts as a continuous auditor for your payment infrastructure.</p>
        
        <div className="space-y-6 mt-8">
          <div className="flex gap-4">
            <div className="mt-1 w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
              <Zap className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 text-lg">1. Continuous Ingestion</h3>
              <p className="text-zinc-600 mt-1">We pull normalized data from orders, payments, refunds, settlements, and bank statements automatically.</p>
            </div>
          </div>
          
          <div className="flex gap-4">
            <div className="mt-1 w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 text-lg">2. AI Investigation</h3>
              <p className="text-zinc-600 mt-1">When a discrepancy occurs, our deterministic engine detects it, and our LLM agent investigates the root cause, collecting evidence like a human analyst.</p>
            </div>
          </div>
          
          <div className="flex gap-4">
            <div className="mt-1 w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
              <BookOpen className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 text-lg">3. Autonomous Resolution</h3>
              <p className="text-zinc-600 mt-1">Safe, high-confidence issues are auto-resolved with a full audit trail. Ambiguous edge-cases are escalated to your team.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
