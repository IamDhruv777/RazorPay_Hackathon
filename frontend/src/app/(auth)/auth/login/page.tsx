"use client";
import { useState, lazy, Suspense } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, LockKeyhole } from "lucide-react";

const BlackHole = lazy(() => import("@/components/effects/BlackHole"));

export default function Login() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleDemoLogin = () => {
    setLoading(true);
    localStorage.setItem("demo_token", "demo-hackathon-token-123");
    setTimeout(() => router.push("/dashboard"), 700);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: '#060b14' }}
    >
      {/* Black Hole background — sits behind everything */}
      <Suspense fallback={null}>
        <BlackHole />
      </Suspense>

      {/* Vignette gradient so the form area is readable */}
      <div
        className="absolute inset-0 pointer-events-none z-[1]"
        style={{
          background: 'radial-gradient(ellipse 55% 65% at 50% 50%, rgba(6,11,20,0.65) 30%, rgba(6,11,20,0.92) 100%)',
        }}
        aria-hidden="true"
      />

      {/* Auth card */}
      <div
        className="relative z-10 w-full max-w-sm mx-4"
        style={{
          background: 'rgba(10,16,28,0.82)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(96,165,250,0.12)',
          borderRadius: '14px',
          padding: '2.5rem 2rem',
          boxShadow: '0 0 80px rgba(30,60,100,0.35), 0 2px 40px rgba(0,0,0,0.6)',
        }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center mb-5"
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: 'rgba(96,165,250,0.1)',
              border: '1px solid rgba(96,165,250,0.25)',
              boxShadow: '0 0 24px rgba(96,165,250,0.15)',
            }}
          >
            <LockKeyhole size={20} color="#60a5fa" />
          </div>
          <h1 style={{ color: '#e2e8f0', fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.05em', fontFamily: 'serif' }}>
            LEDGERLENS
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.35rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Enter the Control Center
          </p>
        </div>

        {/* Form */}
        <div className="flex flex-col gap-3 mb-5">
          <div>
            <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.7rem', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@company.com"
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(96,165,250,0.18)',
                borderRadius: '7px',
                color: '#e2e8f0',
                fontSize: '0.8rem',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={e => (e.target.style.borderColor = 'rgba(96,165,250,0.5)')}
              onBlur={e => (e.target.style.borderColor = 'rgba(96,165,250,0.18)')}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.7rem', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(96,165,250,0.18)',
                borderRadius: '7px',
                color: '#e2e8f0',
                fontSize: '0.8rem',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={e => (e.target.style.borderColor = 'rgba(96,165,250,0.5)')}
              onBlur={e => (e.target.style.borderColor = 'rgba(96,165,250,0.18)')}
            />
          </div>
        </div>

        {/* Sign in button */}
        <button
          onClick={handleDemoLogin}
          disabled={loading}
          style={{
            width: '100%',
            padding: '0.75rem 1rem',
            background: loading ? 'rgba(37,99,235,0.5)' : 'rgba(37,99,235,0.85)',
            border: '1px solid rgba(96,165,250,0.35)',
            borderRadius: '7px',
            color: '#e2e8f0',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'background 0.2s, transform 0.15s',
            boxShadow: '0 0 20px rgba(37,99,235,0.3)',
          }}
          onMouseEnter={e => { if (!loading) (e.currentTarget.style.background = 'rgba(37,99,235,0.95)'); }}
          onMouseLeave={e => { if (!loading) (e.currentTarget.style.background = 'rgba(37,99,235,0.85)'); }}
        >
          {loading ? 'Authenticating...' : (<>Sign In <ArrowRight size={14}/></>)}
        </button>

        <div className="my-5" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
          <span style={{ color: '#475569', fontSize: '0.65rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>or</span>
          <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
        </div>

        {/* Demo account */}
        <button
          onClick={handleDemoLogin}
          disabled={loading}
          style={{
            width: '100%',
            padding: '0.7rem 1rem',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '7px',
            color: '#94a3b8',
            fontSize: '0.73rem',
            fontWeight: 600,
            letterSpacing: '0.05em',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.2s, color 0.2s',
          }}
          onMouseEnter={e => { (e.currentTarget.style.borderColor = 'rgba(96,165,250,0.25)'); (e.currentTarget.style.color = '#e2e8f0'); }}
          onMouseLeave={e => { (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'); (e.currentTarget.style.color = '#94a3b8'); }}
        >
          {loading ? 'Loading demo...' : 'Use Demo Account'}
        </button>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#334155', fontSize: '0.68rem' }}>
          No account?{' '}
          <Link href="/auth/signup" style={{ color: '#60a5fa', textDecoration: 'none' }}>
            Request access
          </Link>
        </p>
      </div>

      {/* Bottom brand strip */}
      <div
        className="absolute bottom-6 w-full text-center pointer-events-none z-10"
        style={{ color: '#1e293b', fontSize: '0.65rem', letterSpacing: '0.12em', textTransform: 'uppercase' }}
      >
        LedgerLens · Financial Control System
      </div>
    </div>
  );
}
