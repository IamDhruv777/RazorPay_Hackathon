'use client';

import { useEffect, useRef, useCallback } from 'react';

const COLS = 26;
const ROWS = 16;
const INFLUENCE = 130;
const BASE_SIZE = 1.6;
const BURST_MS = 550;

interface Dot {
  x: number; y: number;
  bx: number; by: number;
  size: number;
  op: number;
  vx: number; vy: number;
}

interface Burst {
  x: number; y: number;
  r: number; alpha: number; born: number;
}

export default function CursorWaveGrid() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dots = useRef<Dot[]>([]);
  const bursts = useRef<Burst[]>([]);
  const mouse = useRef({ x: -9999, y: -9999 });
  const raf = useRef<number>(0);
  const reducedMotion = useRef(false);

  const buildGrid = useCallback((w: number, h: number) => {
    const sx = w / (COLS + 1);
    const sy = h / (ROWS + 1);
    const list: Dot[] = [];
    for (let r = 1; r <= ROWS; r++) {
      for (let c = 1; c <= COLS; c++) {
        const bx = sx * c;
        const by = sy * r;
        list.push({ x: bx, y: by, bx, by, size: BASE_SIZE + Math.random() * 0.7, op: 0.15 + Math.random() * 0.12, vx: 0, vy: 0 });
      }
    }
    dots.current = list;
  }, []);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotion.current = mq.matches;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    let w = 0, h = 0;
    let canvasLeft = 0, canvasTop = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width; h = rect.height;
      canvasLeft = rect.left; canvasTop = rect.top;
      canvas.width = w * devicePixelRatio;
      canvas.height = h * devicePixelRatio;
      canvas.style.width = w + 'px';
      canvas.style.height = h + 'px';
      ctx.scale(devicePixelRatio, devicePixelRatio);
      buildGrid(w, h);
    };

    // Track mouse at WINDOW level so canvas pointer-events:none doesn't block it
    const onMouseMove = (e: MouseEvent) => {
      mouse.current = { x: e.clientX - canvasLeft, y: e.clientY - canvasTop };
    };

    const onClick = (e: MouseEvent) => {
      if (reducedMotion.current) return;
      bursts.current.push({ x: e.clientX - canvasLeft, y: e.clientY - canvasTop, r: 0, alpha: 0.7, born: performance.now() });
      if (bursts.current.length > 5) bursts.current.shift();
    };

    const draw = (now: number) => {
      ctx.clearRect(0, 0, w, h);
      const mx = mouse.current.x;
      const my = mouse.current.y;

      for (const d of dots.current) {
        if (!reducedMotion.current) {
          const dx = mx - d.bx;
          const dy = my - d.by;
          const dist = Math.hypot(dx, dy);
          if (dist < INFLUENCE) {
            const s = 1 - dist / INFLUENCE;
            d.vx += (-dx * s * 0.3 - (d.x - d.bx)) * 0.14;
            d.vy += (-dy * s * 0.3 - (d.y - d.by)) * 0.14;
          } else {
            d.vx += (d.bx - d.x) * 0.09;
            d.vy += (d.by - d.y) * 0.09;
          }
          d.vx *= 0.72; d.vy *= 0.72;
          d.x += d.vx; d.y += d.vy;
        }

        const dist2 = Math.hypot(mx - d.x, my - d.y);
        const near = reducedMotion.current ? 0 : Math.max(0, 1 - dist2 / INFLUENCE);
        const bright = near > 0.4;
        const size = (d.size + near * 1.2) * (1 + near * 0.8);
        const opacity = d.op + near * 0.5;

        ctx.beginPath();
        ctx.arc(d.x, d.y, size, 0, Math.PI * 2);
        ctx.fillStyle = bright
          ? `rgba(96,165,250,${opacity})`
          : `rgba(148,163,184,${opacity})`;
        ctx.fill();
      }

      bursts.current = bursts.current.filter(b => {
        const age = now - b.born;
        const t = age / BURST_MS;
        if (t >= 1) return false;
        b.r = 90 * t;
        b.alpha = 0.7 * (1 - t);
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(96,165,250,${b.alpha})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        return true;
      });

      raf.current = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener('resize', resize);
    // Track on window so content above canvas still lets us see cursor
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('click', onClick);
    raf.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf.current);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('click', onClick);
    };
  }, [buildGrid]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        // CRITICAL: pointer-events none so canvas doesn't block clicks on links/buttons
        pointerEvents: 'none',
        zIndex: 0,
      }}
      aria-hidden="true"
    />
  );
}
