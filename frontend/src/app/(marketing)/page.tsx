'use client';

import { Suspense, useState, lazy } from "react";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, BarChart3, Check, ChevronRight, Clock3, FileCheck2, GitBranch, Layers3, LockKeyhole, Play, Radar, ShieldCheck, Target, TrendingUp, UsersRound, X } from "lucide-react";
import TextReveal3D from "@/components/effects/TextReveal3D";

const CursorWaveGrid = lazy(() => import("@/components/effects/CursorWaveGrid"));

const mark = "/manus-storage/ledgerlens-mark_40847c0c.png";
const sources = ["Orders", "Payments", "Refunds", "Settlements", "Bank", "Invoices"];
const method = [["01", "Connect every source", "One evidence layer across payments, settlements, refunds, and bank records."], ["02", "Reconcile what changed", "Surface mismatches before they become close-period surprises."], ["03", "Trace the cause", "Follow financial relationships across records, entities, and incidents."], ["04", "Prioritize exposure", "Put the highest-confidence, highest-impact work first."], ["05", "Close with confidence", "Keep every decision explainable after the period is locked."]];

function OrbitStage() {
  const nodes = [["Payments", "good"], ["Settlement", "good"], ["Exception", "hot"], ["Bank", "muted"], ["Incident", "muted"]];
  return <div className="orbit-stage"><div className="orbit-glow"/><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-core"><img src={mark} alt=""/><span className="font-serif">CONTROL<br/>GRAPH</span></div>{nodes.map(([label, tone, ], i) => <div key={label} className={`orbit-node orbit-${i} ${tone}`}><span/><b>{label}</b><small>{tone === "hot" ? "needs review" : tone === "good" ? "verified" : "linked"}</small></div>)}<div className="orbit-readout"><span className="pulse"/> live evidence graph <b>94% confidence</b></div><div className="orbit-depth-card"><span className="eyebrow">Exposure surfaced</span><strong>₹4.82L</strong><small>83 linked transactions · 4 critical</small></div></div>;
}

function FlowVisual() {
  return <div className="flow-visual"><div className="flow-grid"/><div className="flow-caption"><span className="eyebrow">Live relationship map</span><span>1,000+ records become legible</span></div><OrbitStage/></div>;
}

export default function Landing() {
  const [plan, setPlan] = useState<string | null>(null);
  return (
    <div className="landing">
      <nav className="public-nav">
        <Link href="/" className="brand-lockup"><img className="brand-mark-image" src={mark} alt=""/><span className="font-serif">LEDGERLENS</span></Link>
        <div className="nav-links"><a href="#product">Product</a><a href="#workflow">How it works</a><a href="#evidence">Evidence</a><a href="#trust">Trust layer</a><a href="#resources">Resources</a></div>
        <div className="nav-actions">
          <Link href="/auth/login" className="text-link">Sign in</Link>
          <Link href="/dashboard" className="nav-cta font-bold">Enter control center <ArrowUpRight size={15}/></Link>
        </div>
      </nav>

      {/* ── HERO: cursor-reactive particle grid behind content ── */}
      <section className="hero expanded-hero" style={{ position: 'relative', isolation: 'isolate' }}>
        {/* Canvas layer — z-index 0, pointer-events none (handled inside component) */}
        <Suspense fallback={null}>
          <CursorWaveGrid />
        </Suspense>

        {/* Content sits above canvas naturally because of DOM order + z-index */}
        <div className="hero-copy" style={{ position: 'relative', zIndex: 1 }}>
          <div className="hero-kicker"><span className="kicker-rule"/> AI FINANCE CONTROLLER</div>
          <h1 className="font-serif">Know what's happening with your money<span className="copper-dot">.</span><br/><em>Before it becomes a problem.</em></h1>
          <p>An AI Finance Controller for teams that need financial operations to be explainable, not just automated. LedgerLens reconciles records, investigates exceptions, detects incident patterns, and tells you when the books are ready to close.</p>
          <div className="hero-actions">
            <Link href="/dashboard" className="primary-cta font-bold tracking-[0.15em]">Enter Finance Control Center <ArrowRight size={17}/></Link>
            <a href="#product" className="secondary-cta"><span className="play-circle"><Play size={12} fill="currentColor"/></span> See how it works</a>
          </div>
          <div className="hero-meta"><span><ShieldCheck size={15}/> Evidence-backed decisions</span><span><LockKeyhole size={14}/> Safe by design</span><span><Clock3 size={14}/> Built for close periods</span></div>
        </div>
        <div className="hero-art" style={{ position: 'relative', zIndex: 1 }}><FlowVisual/></div>
      </section>

      <section className="trust-logos">
        <span>For finance teams who own the close</span>
        <div><b className="font-serif">Northstar Labs</b><b className="font-serif">ORBIT COMMERCE</b><b className="font-serif">HARBORLINE</b><b className="font-serif">MERIDIAN PAY</b><b className="font-serif">VANTA WORKS</b></div>
      </section>

      <section className="signal-strip">
        <span>VERIFY</span><i>→</i><span>UNDERSTAND</span><i>→</i><span>PRIORITIZE</span><i>→</i><span>PREVENT</span><i>→</i><span>CLOSE</span>
      </section>

      {/* ── PRODUCT SECTION: 3D Text Reveal ── */}
      <section id="product" className="story-section product-overview">
        <div className="section-rail"><span className="eyebrow">01 / The controller</span><span className="rail-line"/><span className="rail-note">One system of financial trust</span></div>
        <div className="story-body">
          {/* 3D Text Reveal replaces the static h2 — scroll down to see it */}
          <TextReveal3D
            lines={["Finance is fragmented.", "Control shouldn't be."]}
            className="font-serif text-5xl"
          />
          <p className="lead" style={{ marginTop: '1.5rem' }}>LedgerLens brings the scattered pieces of your financial operations into one calm, explainable control surface—with the context to understand what changed and the guardrails to act safely.</p>
          <div className="source-row">
            {sources.map((x, i) => <div key={x} className={`source-card ${i === 3 ? "source-focus" : ""}`}><span className="source-icon">{["↗","▬","↚","⊞","⌁","▤"][i]}</span><span>{x}</span><small>source {String(i + 1).padStart(2, "0")}</small></div>)}
          </div>
          <div className="controller-line">
            <div className="controller-copy"><span className="eyebrow">The LedgerLens method</span><h3 className="font-serif text-3xl">From reconciliation<br/>to financial control.</h3><p>Every module is connected by the same control line: a record, a decision, and the evidence behind it.</p></div>
            <div className="method-list">
              {method.map(([n, title, desc]) => <div className="method-item" key={n}><span>{n}</span><div><b>{title}</b><small>{desc}</small></div><ChevronRight size={17}/></div>)}
            </div>
          </div>
        </div>
      </section>

      <section id="workflow" className="workflow-section">
        <div className="workflow-heading"><span className="eyebrow">02 / A better operating rhythm</span><h2 className="font-serif text-5xl">Less hunting.<br/><em>More knowing.</em></h2><p>Move from a spreadsheet maze to a deliberate sequence that gives every role the right amount of context.</p></div>
        <div className="workflow-cards">
          <article><span>01</span><Radar size={22}/><h3 className="font-serif text-2xl">See the signal</h3><p>Monitor what moved outside the baseline across payment, settlement, refund, and bank sources.</p><a href="#evidence">Explore signals <ArrowUpRight size={14}/></a></article>
          <article className="workflow-featured"><span>02</span><GitBranch size={22}/><h3 className="font-serif text-2xl">Follow the thread</h3><p>Trace an exception through linked records and clusters until the underlying incident becomes legible.</p><a href="#evidence">Explore evidence <ArrowUpRight size={14}/></a></article>
          <article><span>03</span><Target size={22}/><h3 className="font-serif text-2xl">Act with confidence</h3><p>Prioritize exposure, assign a clear owner, and know when an automated answer should pause.</p><a href="#trust">Explore controls <ArrowUpRight size={14}/></a></article>
        </div>
      </section>

      <section id="evidence" className="evidence-section">
        <div className="evidence-head"><div><span className="eyebrow">03 / Evidence, not theatre</span><h2 className="font-serif text-5xl">Make the next<br/><em>right decision.</em></h2></div><p>Every signal is anchored to a financial record, separated from AI inference, and clear about what needs a human eye. No black boxes. No orphaned alerts.</p></div>
        <div className="evidence-grid">
          <div className="exception-preview"><div className="card-top"><span className="eyebrow">Exception / LL-0148</span><span className="severity">Critical</span></div><div className="exception-amount font-serif text-4xl">₹84,000</div><h3 className="font-serif text-2xl">Settlement discrepancy</h3><div className="mini-flow">{[["Payment", "Verified"], ["Settlement", "Verified"], ["Bank", "Mismatch"]].map(([a, b], i) => <div className={i === 2 ? "bad" : "good"} key={a}><span>{i === 2 ? <X size={13}/> : <Check size={13}/>}</span><small>{a}</small><b>{b}</b></div>)}</div><div className="evidence-footer"><span>Confidence <b>94%</b></span><span>Exposure <b>₹84,000</b></span></div></div>
          <div className="change-preview"><div className="card-top"><span className="eyebrow">What changed?</span><span className="trend-chip"><TrendingUp size={14}/> +347%</span></div><h3 className="font-serif text-2xl">Settlement exceptions</h3><div className="bar-chart">{[22, 30, 24, 36, 31, 48, 44, 59, 50, 67, 74, 92].map((h, i) => <i key={i} style={{ height: `${h}%` }} className={i > 9 ? "hot" : ""}/>)}</div><div className="change-bottom"><div><small>vs historical baseline</small><b>83 transactions affected</b></div><div><small>Primary contributor</small><b>Bank X</b></div></div></div>
          <div className="evidence-proof"><span className="eyebrow">Record anchor</span><div><FileCheck2 size={20}/><b className="font-serif text-xl">Every conclusion points somewhere.</b></div><p>Click from an exception to the exact transaction trail, source record, and confidence signal that shaped the recommendation.</p><Link href="/exceptions">Inspect a live exception <ArrowRight size={14}/></Link></div>
        </div>
      </section>

      <section id="trust" className="trust-section">
        <div className="trust-card">
          <div><span className="eyebrow">04 / The trust layer</span><h2 className="font-serif text-5xl">AI that knows<br/><em>when to pause.</em></h2><p>LedgerLens is designed around the reality of finance: not every answer should be automated, and every high-impact decision should be defensible.</p></div>
          <div className="trust-list">{[["Deterministic controls", "The system verifies what can be verified."], ["Evidence", "Every conclusion points back to a record."], ["Confidence", "Uncertainty is visible, never hidden."], ["Safe abstention", "The right answer can be 'review this.'"], ["Audit trail", "Decisions stay explainable after close."]].map(([a, b], i) => <div className="trust-item" key={a}><span>0{i + 1}</span><div><b className="font-serif">{a}</b><p>{b}</p></div><ArrowUpRight size={16}/></div>)}</div>
        </div>
      </section>

      <section id="resources" className="resource-section">
        <div><span className="eyebrow">05 / Built for the room</span><h2 className="font-serif text-5xl">Useful to the<br/><em>whole finance team.</em></h2></div>
        <div className="resource-links">
          <a href="#product"><span><UsersRound size={18}/><b className="font-serif text-xl">Finance leaders</b></span><small>Know if the close is actually ready.</small><ArrowRight size={15}/></a>
          <a href="#evidence"><span><BarChart3 size={18}/><b className="font-serif text-xl">Controllers</b></span><small>Move from variance to root cause.</small><ArrowRight size={15}/></a>
          <a href="#trust"><span><Layers3 size={18}/><b className="font-serif text-xl">Operators</b></span><small>Resolve the highest-impact work first.</small><ArrowRight size={15}/></a>
        </div>
      </section>

      <section id="pricing" className="pricing-section">
        <div className="pricing-heading"><div><span className="eyebrow">06 / Plans for the close</span><h2 className="font-serif text-5xl">Choose the level<br/><em>of control you need.</em></h2></div><p>Start with the visibility you need today, then add deeper investigation and operating rhythm as your finance system grows.</p></div>
        <div className="pricing-grid">
          <article className="price-card"><span className="price-label">Signal</span><h3 className="font-serif text-3xl">See what moved.</h3><div className="price-value font-serif">₹18,000 <small className="font-sans">/ month</small></div><p>For teams building a reliable view of payment and settlement movement.</p><button className="price-cta" onClick={() => setPlan("Signal")}>Compare plan <ArrowRight size={14}/></button><div className="price-features"><span><Check size={14}/> 6 source connections</span><span><Check size={14}/> Close-period overview</span><span><Check size={14}/> Signal log and baselines</span><span><Check size={14}/> CSV evidence export</span></div></article>
          <article className="price-card price-card-featured"><span className="price-label">Control <b>Most chosen</b></span><h3 className="font-serif text-3xl">Know what to fix.</h3><div className="price-value font-serif">₹42,000 <small className="font-sans">/ month</small></div><p>For controllers who need evidence, prioritization, and a clear review queue.</p><button className="price-cta" onClick={() => setPlan("Control")}>Compare plan <ArrowRight size={14}/></button><div className="price-features"><span><Check size={14}/> Everything in Signal</span><span><Check size={14}/> Exception investigation</span><span><Check size={14}/> Incident relationship graph</span><span><Check size={14}/> Owner and action queue</span></div></article>
          <article className="price-card"><span className="price-label">Command</span><h3 className="font-serif text-3xl">Run the close.</h3><div className="price-value font-serif">Custom <small className="font-sans">for your operating model</small></div><p>For finance organizations that need policy, audit, and cross-entity control at scale.</p><button className="price-cta" onClick={() => setPlan('Command')}>Talk through scope <ArrowRight size={14}/></button><div className="price-features"><span><Check size={14}/> Multi-entity control surface</span><span><Check size={14}/> Custom control library</span><span><Check size={14}/> Advanced audit workspace</span><span><Check size={14}/> Dedicated operating reviews</span></div></article>
        </div>
        <div className="comparison-table"><div className="comparison-row comparison-head"><span>Capability</span><b>Signal</b><b>Control</b><b>Command</b></div>{[["Source connections","6","12","Custom"],["Evidence anchors","Included","Included","Included"],["Exception investigation","—","Included","Included"],["Incident graph","—","Included","Advanced"],["Action queue","—","Included","Included"],["Close-readiness controls","Overview","Full","Policy-driven"]].map(([label,a,b,c]) => <div className="comparison-row" key={label}><span>{label}</span><b>{a}</b><b className={b === "Included" ? "verified-text" : ""}>{b}</b><b>{c}</b></div>)}</div>
      </section>

      <section className="closing-cta">
        <span className="eyebrow text-[#c56a3a]">A clearer close starts here</span>
        <h2 className="font-serif text-5xl">Know what needs<br/><em className="text-[#c56a3a] italic font-serif">your attention.</em></h2>
        <p>See the signals, follow the evidence, and enter your next close with a better operating rhythm.</p>
        <Link href="/dashboard" className="primary-cta font-bold tracking-[0.15em]">Enter Finance Control Center <ArrowRight size={17}/></Link>
      </section>

      <footer>
        <Link href="/" className="brand-lockup"><img className="brand-mark-image" src={mark} alt=""/><span className="font-serif">LEDGERLENS</span></Link>
        <div className="footer-links"><a href="#product">Product</a><a href="#workflow">Workflow</a><a href="#trust">Trust</a><a href="#resources">Resources</a></div>
        <span>© 2026 LedgerLens</span>
      </footer>

      {plan && (
        <div className="modal-backdrop fixed inset-0 bg-[#172b38]/60 backdrop-blur-sm z-50 flex items-center justify-center" onMouseDown={(event)=>{if(event.target===event.currentTarget)setPlan(null)}}>
          <div className="signup-modal bg-[#fbfaf7] p-10 rounded-xl shadow-[0_18px_50px_rgba(28,46,52,0.2)] max-w-lg w-full" role="dialog" aria-modal="true" aria-labelledby="signup-title">
            <div className="flex justify-between items-start mb-6">
              <div>
                <span className="eyebrow text-[#c56a3a]">LedgerLens / {plan} plan</span>
                <h2 id="signup-title" className="font-serif text-4xl text-[#172b38] mt-3 leading-[1.1]">Bring more clarity<br/><em className="text-[#c56a3a] italic font-serif">to your next close.</em></h2>
              </div>
              <button className="modal-close text-2xl text-[#81908a] hover:text-[#c56a3a]" onClick={()=>setPlan(null)} aria-label="Close"><X size={18}/></button>
            </div>
            <p className="text-[13px] text-[#71847b] mb-6">Tell us where your finance team is in the close cycle and we'll prepare a preview for the {plan} plan.</p>
            <label className="block mb-4">
              <span className="block text-[11px] font-bold text-[#172b38] mb-1">Work email</span>
              <input type="email" placeholder="you@company.com" autoFocus className="w-full p-3 bg-[#f5f4ef] border border-[#d9ddd7] rounded text-[11px]"/>
            </label>
            <label className="block mb-8">
              <span className="block text-[11px] font-bold text-[#172b38] mb-1">Team size</span>
              <select defaultValue="" className="w-full p-3 bg-[#f5f4ef] border border-[#d9ddd7] rounded text-[11px]">
                <option value="" disabled>Select team size</option>
                <option>1–10</option>
                <option>11–50</option>
                <option>51–250</option>
                <option>251+</option>
              </select>
            </label>
            <button className="primary-cta font-bold tracking-[0.15em] w-full flex items-center justify-center gap-3 bg-[#172b38] text-white p-4 rounded text-[11px] uppercase hover:bg-[#274653] transition-colors" onClick={()=>setPlan(null)}>
              Continue to workspace setup <ArrowRight size={15}/>
            </button>
            <small className="block text-center mt-4 text-[10px] text-[#81908a]">Preview only · no account or payment is created.</small>
          </div>
        </div>
      )}
    </div>
  );
}
