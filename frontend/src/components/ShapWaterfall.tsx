"use client";

import React, { useState, useEffect } from "react";
import { Droplets } from "lucide-react";

export interface WaterfallFeature {
  name: string;
  impact: number; // positive = pushes up, negative = pushes down
  value: string; // actual feature value for display
}

interface ShapWaterfallProps {
  features: WaterfallFeature[];
  baseValue: number; // base prediction (e.g., 0.5 = 50%)
  finalValue: number; // final prediction (e.g., 0.85 = 85%)
}

interface RowData {
  label: string;
  value: string;
  impact: number;
  barStart: number; // percentage 0–100
  barWidth: number; // percentage 0–100
  cumulative: number; // running total percentage
  type: "base" | "positive" | "negative" | "final";
}

export function ShapWaterfall({ features, baseValue, finalValue }: ShapWaterfallProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Build rows
  const rows: RowData[] = [];
  const basePct = baseValue * 100;

  // Base value row
  rows.push({
    label: "Base value",
    value: `${basePct.toFixed(1)}%`,
    impact: 0,
    barStart: 0,
    barWidth: Math.min(Math.max(basePct, 0), 100),
    cumulative: basePct,
    type: "base",
  });

  // Feature rows
  let runningTotal = basePct;
  for (const feat of features) {
    const impactPct = feat.impact * 100;
    const start = impactPct >= 0 ? runningTotal : runningTotal + impactPct;
    const width = Math.abs(impactPct);
    runningTotal += impactPct;

    rows.push({
      label: feat.name,
      value: feat.value,
      impact: impactPct,
      barStart: Math.max(start, 0),
      barWidth: Math.min(width, 100 - Math.max(start, 0)),
      cumulative: runningTotal,
      type: impactPct >= 0 ? "positive" : "negative",
    });
  }

  // Final prediction row
  const finalPct = finalValue * 100;
  rows.push({
    label: "Final prediction",
    value: `${finalPct.toFixed(1)}%`,
    impact: 0,
    barStart: 0,
    barWidth: Math.min(Math.max(finalPct, 0), 100),
    cumulative: finalPct,
    type: "final",
  });

  const gridlines = [0, 25, 50, 75, 100];

  return (
    <div id="tour-waterfall" className="bg-card border rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 relative overflow-hidden group">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 w-full h-1 bg-primary group-hover:h-1.5 transition-all" />

      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Droplets className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-foreground">Impact Waterfall</h3>
          <p className="text-sm text-muted-foreground">
            How each feature shifts the prediction
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="relative">
        {/* Gridlines header */}
        <div className="flex items-end mb-1 ml-[120px] mr-[60px] relative h-5">
          {gridlines.map((pct) => (
            <div
              key={pct}
              className="absolute text-[10px] text-muted-foreground font-medium"
              style={{ left: `${pct}%`, transform: "translateX(-50%)" }}
            >
              {pct}%
            </div>
          ))}
        </div>

        {/* Rows */}
        <div className="space-y-0">
          {rows.map((row, idx) => {
            const isFirst = idx === 0;
            const isLast = idx === rows.length - 1;
            const prevRow = idx > 0 ? rows[idx - 1] : null;
            const isHovered = hoveredIndex === idx;

            // Connector from previous bar end to this bar start
            const showConnector =
              !isFirst && !isLast && prevRow;
            const connectorLeft = prevRow
              ? prevRow.type === "base" || prevRow.type === "final"
                ? prevRow.barStart + prevRow.barWidth
                : prevRow.cumulative
              : 0;

            return (
              <div key={idx} className="relative">
                {/* Connector line */}
                {showConnector && (
                  <div
                    className="absolute top-0 w-px border-l border-dashed border-muted-foreground/30 z-10"
                    style={{
                      left: `calc(120px + (100% - 120px - 60px) * ${Math.max(Math.min(connectorLeft, 100), 0)} / 100)`,
                      height: "100%",
                    }}
                  />
                )}

                <div
                  className={`flex items-center py-2.5 px-2 rounded-lg cursor-default transition-all duration-200 ${
                    isHovered
                      ? "bg-muted/80 shadow-sm"
                      : "hover:bg-muted/40"
                  } ${isFirst || isLast ? "font-semibold" : ""}`}
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? "translateX(0)" : "translateX(-12px)",
                    transition: `opacity 0.4s ease ${idx * 0.08}s, transform 0.4s ease ${idx * 0.08}s`,
                  }}
                >
                  {/* Feature label */}
                  <div className="w-[120px] flex-shrink-0 pr-2">
                    <div className="text-sm text-foreground truncate">
                      {row.label}
                      {!isFirst && !isLast && (
                        <span className="text-muted-foreground font-normal ml-1">
                          ({row.value})
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Bar area */}
                  <div className="flex-1 relative h-8">
                    {/* Gridlines */}
                    {gridlines.map((pct) => (
                      <div
                        key={pct}
                        className="absolute top-0 bottom-0 w-px bg-border/40"
                        style={{ left: `${pct}%` }}
                      />
                    ))}

                    {/* Bar */}
                    <div
                      className="absolute top-1 bottom-1 rounded-md flex items-center justify-center overflow-hidden"
                      style={{
                        left: `${row.barStart}%`,
                        width: isVisible ? `${row.barWidth}%` : "0%",
                        transition: `width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${idx * 0.08 + 0.15}s`,
                        background:
                          row.type === "positive"
                            ? "linear-gradient(90deg, #22c55e, #16a34a)"
                            : row.type === "negative"
                            ? "linear-gradient(90deg, #ef4444, #dc2626)"
                            : "linear-gradient(90deg, var(--primary), #2563eb)",
                        boxShadow: isHovered
                          ? row.type === "positive"
                            ? "0 2px 12px rgba(34,197,94,0.35)"
                            : row.type === "negative"
                            ? "0 2px 12px rgba(239,68,68,0.35)"
                            : "0 2px 12px rgba(59,130,246,0.35)"
                          : "none",
                      }}
                    >
                      {/* Impact label on bar */}
                      {row.barWidth > 4 && (
                        <span className="text-[11px] font-bold text-white drop-shadow-sm whitespace-nowrap px-1">
                          {row.type === "base" || row.type === "final"
                            ? `${row.cumulative.toFixed(1)}%`
                            : row.impact >= 0
                            ? `+${row.impact.toFixed(1)}%`
                            : `−${Math.abs(row.impact).toFixed(1)}%`}
                        </span>
                      )}
                    </div>

                    {/* Impact label outside bar if bar too small */}
                    {row.barWidth <= 4 && !isFirst && !isLast && (
                      <span
                        className={`absolute top-1/2 -translate-y-1/2 text-[11px] font-bold whitespace-nowrap ${
                          row.type === "positive"
                            ? "text-green-600"
                            : "text-red-500"
                        }`}
                        style={{
                          left: `${row.barStart + row.barWidth + 1}%`,
                        }}
                      >
                        {row.impact >= 0
                          ? `+${row.impact.toFixed(1)}%`
                          : `−${Math.abs(row.impact).toFixed(1)}%`}
                      </span>
                    )}
                  </div>

                  {/* Cumulative total */}
                  <div className="w-[60px] flex-shrink-0 text-right">
                    <span
                      className={`text-xs font-semibold tabular-nums ${
                        isFirst || isLast
                          ? "text-primary"
                          : row.type === "positive"
                          ? "text-green-600"
                          : "text-red-500"
                      }`}
                    >
                      {row.cumulative.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Hover tooltip */}
                {isHovered && !isFirst && !isLast && (
                  <div
                    className="absolute z-20 bg-foreground text-background text-xs rounded-lg px-3 py-2 shadow-xl pointer-events-none"
                    style={{
                      left: `calc(120px + (100% - 120px - 60px) * ${row.barStart + row.barWidth / 2} / 100)`,
                      top: "-8px",
                      transform: "translate(-50%, -100%)",
                    }}
                  >
                    <div className="font-bold mb-0.5">
                      {row.label}: {row.value}
                    </div>
                    <div>
                      Impact:{" "}
                      <span
                        className={
                          row.type === "positive"
                            ? "text-green-400"
                            : "text-red-400"
                        }
                      >
                        {row.impact >= 0
                          ? `+${row.impact.toFixed(2)}%`
                          : `−${Math.abs(row.impact).toFixed(2)}%`}
                      </span>
                    </div>
                    <div className="text-[10px] opacity-75">
                      Running total: {row.cumulative.toFixed(1)}%
                    </div>
                    {/* Arrow */}
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-0 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-foreground" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom axis */}
        <div className="flex items-start mt-2 ml-[120px] mr-[60px] relative h-3 border-t border-border/60">
          {gridlines.map((pct) => (
            <div
              key={pct}
              className="absolute top-0 w-px h-2 bg-border"
              style={{ left: `${pct}%` }}
            />
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-5 pt-4 border-t border-border/40">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-[#22c55e] to-[#16a34a]" />
          <span className="text-xs text-muted-foreground">Positive impact</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-[#ef4444] to-[#dc2626]" />
          <span className="text-xs text-muted-foreground">Negative impact</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-primary" />
          <span className="text-xs text-muted-foreground">Base / Final</span>
        </div>
      </div>
    </div>
  );
}
