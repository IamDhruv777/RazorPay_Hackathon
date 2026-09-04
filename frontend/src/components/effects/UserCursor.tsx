'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

const SUPPRESS_SELECTORS = 'input, textarea, select, button, a, table, td, th, [role="button"], [role="textbox"], [role="grid"]';

export default function UserCursor({ label = 'Finance' }: { label?: string }) {
  const [active, setActive] = useState(false);
  const [suppressed, setSuppressed] = useState(false);

  const rawX = useMotionValue(0);
  const rawY = useMotionValue(0);
  const x = useSpring(rawX, { stiffness: 200, damping: 24, mass: 0.5 });
  const y = useSpring(rawY, { stiffness: 200, damping: 24, mass: 0.5 });

  // prefers-reduced-motion
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const fn = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', fn);
    return () => mq.removeEventListener('change', fn);
  }, []);

  useEffect(() => {
    if (reduced) return;

    const move = (e: MouseEvent) => {
      rawX.set(e.clientX);
      rawY.set(e.clientY);
      setActive(true);
      // Check if cursor is over a suppressed element
      const el = document.elementFromPoint(e.clientX, e.clientY);
      if (el) {
        setSuppressed(!!el.closest(SUPPRESS_SELECTORS));
      }
    };

    const leave = () => setActive(false);

    window.addEventListener('mousemove', move);
    document.addEventListener('mouseleave', leave);
    return () => {
      window.removeEventListener('mousemove', move);
      document.removeEventListener('mouseleave', leave);
    };
  }, [rawX, rawY, reduced]);

  if (reduced) return null;

  return (
    <motion.div
      aria-hidden="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        x,
        y,
        translateX: 16,
        translateY: -8,
        zIndex: 99999,
        pointerEvents: 'none',
      }}
      animate={{ opacity: active && !suppressed ? 1 : 0, scale: active && !suppressed ? 1 : 0.85 }}
      transition={{ duration: 0.15 }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '3px 9px',
        borderRadius: 4,
        background: 'rgba(10,18,36,0.92)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(96,165,250,0.3)',
        boxShadow: '0 2px 12px rgba(0,0,0,0.35)',
        whiteSpace: 'nowrap',
        userSelect: 'none',
      }}>
        <span style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: '#60a5fa',
          boxShadow: '0 0 6px #60a5fa88',
          flexShrink: 0,
          display: 'inline-block',
        }} />
        <span style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          color: '#e2e8f0',
          textTransform: 'uppercase',
          fontFamily: 'system-ui, sans-serif',
        }}>
          {label}
        </span>
      </div>
    </motion.div>
  );
}
