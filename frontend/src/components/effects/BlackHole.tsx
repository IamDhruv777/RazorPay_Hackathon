'use client';

import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const PARTICLE_COUNT = 3200;
const INNER_RADIUS = 0.08;
const OUTER_RADIUS = 2.8;

function BlackHoleParticles() {
  const meshRef = useRef<THREE.Points>(null);
  const reducedMotion = useRef(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotion.current = mq.matches;
  }, []);

  const { positions, speeds, angles, radii, colors } = useMemo(() => {
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const speeds = new Float32Array(PARTICLE_COUNT);
    const angles = new Float32Array(PARTICLE_COUNT);
    const radii = new Float32Array(PARTICLE_COUNT);
    const colors = new Float32Array(PARTICLE_COUNT * 3);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Disk distribution biased toward center for black hole accretion effect
      const t = Math.pow(Math.random(), 1.6); // bias toward center
      const r = INNER_RADIUS + t * (OUTER_RADIUS - INNER_RADIUS);
      const angle = Math.random() * Math.PI * 2;
      const spread = (1 - t) * 0.12; // more z spread far out
      const z = (Math.random() - 0.5) * spread;

      positions[i * 3] = Math.cos(angle) * r;
      positions[i * 3 + 1] = Math.sin(angle) * r;
      positions[i * 3 + 2] = z;

      angles[i] = angle;
      radii[i] = r;
      // Keplerian: inner particles orbit faster
      speeds[i] = (0.004 + Math.random() * 0.006) / Math.max(r * 0.5, 0.1);

      // Color: deep blue-gray -> electric blue near center
      const intensity = Math.pow(1 - t, 1.4);
      colors[i * 3] = 0.3 + intensity * 0.5;     // R
      colors[i * 3 + 1] = 0.4 + intensity * 0.55; // G
      colors[i * 3 + 2] = 0.55 + intensity * 0.45; // B
    }

    return { positions, speeds, angles, radii, colors };
  }, []);

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions.slice(), 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    return geo;
  }, [positions, colors]);

  const material = useMemo(() => new THREE.PointsMaterial({
    size: 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.75,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  }), []);

  useFrame((_, delta) => {
    if (reducedMotion.current || !meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position;
    const t = performance.now() * 0.001;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      angles[i] += speeds[i];
      // Gentle pulsing radial drift toward center
      const r = radii[i] * (1 - Math.sin(t * 0.15 + i * 0.3) * 0.005);
      posAttr.setXY(
        i,
        Math.cos(angles[i]) * r,
        Math.sin(angles[i]) * r
      );
    }
    posAttr.needsUpdate = true;
    meshRef.current.rotation.z += delta * 0.04;
  });

  return (
    <points ref={meshRef} geometry={geometry} material={material} />
  );
}

function CoreGlow() {
  const meshRef = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.z += delta * 0.12;
    }
  });

  return (
    <mesh ref={meshRef}>
      <circleGeometry args={[0.07, 32]} />
      <meshBasicMaterial color="#1e3a5f" transparent opacity={0.92} />
    </mesh>
  );
}

export default function BlackHole() {
  return (
    <div
      className="absolute inset-0 w-full h-full pointer-events-none select-none"
      aria-hidden="true"
    >
      <Canvas
        camera={{ position: [0, 0, 4.5], fov: 55 }}
        dpr={[1, 1.5]}
        style={{ background: 'transparent' }}
        gl={{ alpha: true, antialias: false, powerPreference: 'low-power' }}
      >
        <BlackHoleParticles />
        <CoreGlow />
      </Canvas>
    </div>
  );
}
