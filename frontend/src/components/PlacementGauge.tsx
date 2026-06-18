"use client";
import React, { useState, useEffect, useMemo } from "react";

interface PlacementGaugeProps {
  value: number; // 0-100
}

/* ── Helpers ── */

/** Convert degrees → radians */
const deg2rad = (deg: number) => (deg * Math.PI) / 180;

/** Point on a circle at angle θ (degrees) */
const polarToCartesian = (cx: number, cy: number, r: number, angleDeg: number) => ({
  x: cx + r * Math.cos(deg2rad(angleDeg)),
  y: cy + r * Math.sin(deg2rad(angleDeg)),
});

/** SVG arc path for a given angular range (large‑arc handled automatically) */
const describeArc = (
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number,
) => {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
};

/** Linearly interpolate between two hex colours */
const lerpColor = (a: string, b: string, t: number): string => {
  const parse = (hex: string) => [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
  const ca = parse(a);
  const cb = parse(b);
  const r = Math.round(ca[0] + (cb[0] - ca[0]) * t);
  const g = Math.round(ca[1] + (cb[1] - ca[1]) * t);
  const bl = Math.round(ca[2] + (cb[2] - ca[2]) * t);
  return `#${((1 << 24) | (r << 16) | (g << 8) | bl).toString(16).slice(1)}`;
};

/** Get the arc colour for a 0‑100 value */
const getColor = (v: number): string => {
  if (v <= 40) return lerpColor("#ef4444", "#f97316", v / 40);
  if (v <= 70) return lerpColor("#f97316", "#eab308", (v - 40) / 30);
  return lerpColor("#eab308", "#22c55e", (v - 70) / 30);
};

/* ── Constants ── */
const CX = 100;
const CY = 100;
const R = 80;
const START_ANGLE = 135; // bottom‑left
const END_ANGLE = 405; // bottom‑right (135 + 270)
const SWEEP = 270;
const ARC_LENGTH = 2 * Math.PI * R * (SWEEP / 360); // ≈ 376.99
const STROKE_WIDTH = 14;
const TICK_POSITIONS = [0, 25, 50, 75, 100];

export function PlacementGauge({ value }: PlacementGaugeProps) {
  const clampedTarget = Math.max(0, Math.min(100, value));
  const [animatedValue, setAnimatedValue] = useState(0);
  const [mounted, setMounted] = useState(false);

  // Trigger CSS‑transition‑based animation on mount
  useEffect(() => {
    // Small delay so the initial state (0) is painted first
    const raf = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  // Animate the number counter independently for the centre text
  useEffect(() => {
    if (!mounted) return;
    const duration = 1500; // ms
    const start = performance.now();
    let frame: number;

    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease‑out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedValue(Math.round(eased * clampedTarget));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [mounted, clampedTarget]);

  const displayColor = useMemo(() => getColor(animatedValue), [animatedValue]);
  const targetColor = useMemo(() => getColor(clampedTarget), [clampedTarget]);

  // stroke‑dashoffset for the foreground arc
  const currentOffset = mounted
    ? ARC_LENGTH * (1 - clampedTarget / 100)
    : ARC_LENGTH;

  // Build the background arc path
  const bgArcPath = describeArc(CX, CY, R, START_ANGLE, END_ANGLE);

  // Ticks & labels
  const ticks = TICK_POSITIONS.map((pct) => {
    const angle = START_ANGLE + (SWEEP * pct) / 100;
    const innerR = R - STROKE_WIDTH / 2 - 2;
    const outerR = R - STROKE_WIDTH / 2 - 10;
    const labelR = R - STROKE_WIDTH / 2 - 18;
    const inner = polarToCartesian(CX, CY, innerR, angle);
    const outer = polarToCartesian(CX, CY, outerR, angle);
    const label = polarToCartesian(CX, CY, labelR, angle);
    return { pct, inner, outer, label };
  });

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        viewBox="0 0 200 200"
        width="200"
        height="200"
        className="drop-shadow-sm"
        role="img"
        aria-label={`Placement probability gauge showing ${clampedTarget}%`}
      >
        {/* ── Glow filter ── */}
        <defs>
          <filter id="gauge-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Gradient for the arc (start‑colour → end‑colour) */}
          <linearGradient id="arc-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="40%" stopColor="#f97316" />
            <stop offset="65%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>
        </defs>

        {/* ── Background track ── */}
        <path
          d={bgArcPath}
          fill="none"
          stroke="var(--border, #e5e7eb)"
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          opacity={0.5}
        />

        {/* ── Foreground arc (animated) ── */}
        <path
          d={bgArcPath}
          fill="none"
          stroke={targetColor}
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          strokeDasharray={ARC_LENGTH}
          strokeDashoffset={currentOffset}
          filter="url(#gauge-glow)"
          style={{
            transition: mounted
              ? "stroke-dashoffset 1.5s cubic-bezier(0.22, 1, 0.36, 1), stroke 0.4s ease"
              : "none",
          }}
        />

        {/* ── Tick marks ── */}
        {ticks.map(({ pct, inner, outer }) => (
          <line
            key={`tick-${pct}`}
            x1={inner.x}
            y1={inner.y}
            x2={outer.x}
            y2={outer.y}
            stroke="var(--muted-foreground, #9ca3af)"
            strokeWidth={1.5}
            strokeLinecap="round"
            opacity={0.6}
          />
        ))}

        {/* ── Tick labels ── */}
        {ticks.map(({ pct, label }) => (
          <text
            key={`label-${pct}`}
            x={label.x}
            y={label.y}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize="8"
            fontWeight="500"
            fill="var(--muted-foreground, #9ca3af)"
          >
            {pct}
          </text>
        ))}

        {/* ── Centre display ── */}
        <text
          x={CX}
          y={CY - 6}
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--foreground, #111827)"
          fontSize="38"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
        >
          {animatedValue}
          <tspan fontSize="16" fontWeight="600" dy="-8">
            %
          </tspan>
        </text>

        <text
          x={CX}
          y={CY + 24}
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--muted-foreground, #9ca3af)"
          fontSize="9"
          fontWeight="500"
          letterSpacing="0.02em"
        >
          Placement Probability
        </text>
      </svg>

      {/* Outer ambient glow ring (CSS‑driven) */}
      <div
        className="pointer-events-none absolute inset-0 rounded-full opacity-20 blur-xl transition-colors duration-1000"
        style={{ backgroundColor: displayColor }}
      />
    </div>
  );
}
