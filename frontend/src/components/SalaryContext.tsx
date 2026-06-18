"use client";
import React, { useState, useEffect, useMemo } from "react";

interface SalaryContextProps {
  salaryLow: number; // LPA
  salaryHigh: number; // LPA
}

interface SalaryDistribution {
  placement_rate: number;
  salary_stats: {
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    min: number;
    max: number;
    mean: number;
  };
}

/* ── Percentile bracket logic ── */
interface PercentileBadge {
  label: string;
  sub: string;
  bg: string;
  text: string;
  border: string;
  glow: string;
}

const getBadge = (
  midpoint: number,
  stats: SalaryDistribution["salary_stats"],
): PercentileBadge => {
  if (midpoint >= stats.p90)
    return {
      label: "Top 10%",
      sub: "Elite salary bracket",
      bg: "bg-amber-100/80 dark:bg-amber-900/30",
      text: "text-amber-700 dark:text-amber-300",
      border: "border-amber-400/50",
      glow: "shadow-amber-400/20",
    };
  if (midpoint >= stats.p75)
    return {
      label: "Top 25%",
      sub: "Above most placed students",
      bg: "bg-emerald-100/80 dark:bg-emerald-900/30",
      text: "text-emerald-700 dark:text-emerald-300",
      border: "border-emerald-400/50",
      glow: "shadow-emerald-400/20",
    };
  if (midpoint >= stats.p50)
    return {
      label: "Top 50%",
      sub: "Above median salary",
      bg: "bg-blue-100/80 dark:bg-blue-900/30",
      text: "text-blue-700 dark:text-blue-300",
      border: "border-blue-400/50",
      glow: "shadow-blue-400/20",
    };
  if (midpoint >= stats.p25)
    return {
      label: "Above Average",
      sub: "Competitive salary range",
      bg: "bg-slate-100/80 dark:bg-slate-800/50",
      text: "text-slate-600 dark:text-slate-300",
      border: "border-slate-300/50 dark:border-slate-600/50",
      glow: "",
    };
  return {
    label: "Below Average",
    sub: "Room for improvement",
    bg: "bg-gray-100/80 dark:bg-gray-800/50",
    text: "text-gray-500 dark:text-gray-400",
    border: "border-gray-300/50 dark:border-gray-600/50",
    glow: "",
  };
};

/* ── Skeleton loader ── */
function Skeleton() {
  return (
    <div className="animate-pulse space-y-3 w-full">
      <div className="flex items-center gap-3">
        <div className="h-7 w-20 rounded-full bg-muted" />
        <div className="h-4 w-36 rounded bg-muted" />
      </div>
      <div className="h-8 w-full rounded-lg bg-muted" />
    </div>
  );
}

/* ── Main component ── */
export function SalaryContext({ salaryLow, salaryHigh }: SalaryContextProps) {
  const [distribution, setDistribution] = useState<SalaryDistribution | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    fetch("http://localhost:8000/salary-distribution")
      .then((res) => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then((data: SalaryDistribution) => {
        if (!cancelled) {
          setDistribution(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const midpoint = (salaryLow + salaryHigh) / 2;

  const badge = useMemo(
    () => (distribution ? getBadge(midpoint, distribution.salary_stats) : null),
    [distribution, midpoint],
  );

  // Hide gracefully on error
  if (error) return null;

  if (loading || !distribution || !badge) {
    return (
      <div className="w-full max-w-md mx-auto">
        <Skeleton />
      </div>
    );
  }

  const { salary_stats: stats } = distribution;

  // Scale helpers – map LPA value to 0‑100% on the bar
  const rangeMin = stats.min;
  const rangeMax = stats.max;
  const span = rangeMax - rangeMin || 1;
  const toPercent = (v: number) =>
    Math.max(0, Math.min(100, ((v - rangeMin) / span) * 100));

  const userLeft = toPercent(salaryLow);
  const userRight = toPercent(salaryHigh);

  const percentileTicks: { value: number; label: string }[] = [
    { value: stats.p25, label: "P25" },
    { value: stats.p50, label: "P50" },
    { value: stats.p75, label: "P75" },
  ];

  return (
    <div className="w-full space-y-3">
      {/* ── Badge row ── */}
      <div className="flex items-center gap-3 flex-wrap">
        <span
          className={`
            inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold
            border backdrop-blur-sm transition-all duration-300
            ${badge.bg} ${badge.text} ${badge.border}
            ${badge.glow ? `shadow-md ${badge.glow}` : ""}
          `}
        >
          {/* Decorative dot */}
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full ${badge.text.replace("text-", "bg-")}`}
          />
          {badge.label}
        </span>
        <span className="text-xs text-muted-foreground font-medium">
          {badge.sub}
        </span>
      </div>

      {/* ── Distribution bar ── */}
      <div className="relative w-full select-none">
        {/* Track background */}
        <div
          className="relative h-6 w-full rounded-lg overflow-hidden border border-border/50"
          style={{
            background:
              "linear-gradient(to right, #ef4444, #f97316 30%, #eab308 55%, #22c55e 100%)",
          }}
        >
          {/* Semi‑transparent overlay to soften the gradient */}
          <div className="absolute inset-0 bg-background/30 dark:bg-background/50" />

          {/* User predicted range highlight */}
          <div
            className="absolute top-0 h-full rounded transition-all duration-700 ease-out"
            style={{
              left: `${userLeft}%`,
              width: `${Math.max(userRight - userLeft, 1)}%`,
              background:
                "linear-gradient(to bottom, rgba(255,255,255,0.45), rgba(255,255,255,0.15))",
              border: "2px solid rgba(255,255,255,0.8)",
              boxShadow:
                "0 0 10px rgba(255,255,255,0.3), inset 0 1px 2px rgba(255,255,255,0.3)",
            }}
          />

          {/* Percentile tick marks */}
          {percentileTicks.map(({ value, label }) => {
            const pct = toPercent(value);
            return (
              <div
                key={label}
                className="absolute top-0 h-full flex flex-col items-center"
                style={{ left: `${pct}%`, transform: "translateX(-50%)" }}
              >
                <div className="w-px h-full bg-foreground/30 dark:bg-foreground/20" />
              </div>
            );
          })}
        </div>

        {/* Labels below the bar */}
        <div className="relative h-12 mt-0.5">
          {/* Min / Max */}
          <span className="absolute left-0 text-[10px] text-muted-foreground font-medium">
            {rangeMin.toFixed(1)}
          </span>
          <span className="absolute right-0 text-[10px] text-muted-foreground font-medium">
            {rangeMax.toFixed(1)}
          </span>

          {/* Percentile labels */}
          {percentileTicks.map(({ value, label }, index) => {
            const pct = toPercent(value);
            // Alternate the Y position to prevent overlap
            const yOffset = index % 2 === 0 ? "top-[10px]" : "top-[24px]";
            return (
              <div
                key={label}
                className={`absolute ${yOffset} flex flex-col items-center`}
                style={{ left: `${pct}%`, transform: "translateX(-50%)" }}
              >
                {/* Small tick connector */}
                <div className={`w-px ${index % 2 === 0 ? 'h-1' : 'h-3'} bg-border/60 -mt-1`} />
                <span className="text-[10px] text-muted-foreground font-semibold whitespace-nowrap mt-0.5">
                  {label}
                  <span className="ml-1 font-normal opacity-70">
                    {value.toFixed(1)}
                  </span>
                </span>
              </div>
            );
          })}

          {/* User midpoint indicator */}
          <span
            className="absolute -top-[22px] text-[9px] font-bold text-white bg-foreground/80 dark:bg-foreground/90 px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap"
            style={{
              left: `${toPercent(midpoint)}%`,
              transform: "translateX(-50%)",
            }}
          >
            You: {midpoint.toFixed(1)} LPA
          </span>
        </div>
      </div>
    </div>
  );
}
