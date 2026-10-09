import React from "react";
import type { Driver } from "@/lib/api";

interface Props {
  groupEffects: Record<string, number>;
  drivers: Driver[];
}

const GROUP_LABEL: Record<string, string> = {
  lexical: "Keyword overlap",
  semantic: "Semantic coverage",
  skills: "Skill coverage",
  experience: "Experience & education",
};

function Bar({ value, max }: { value: number; max: number }) {
  const pct = Math.min(100, (Math.abs(value) / (max || 1)) * 100);
  const positive = value >= 0;
  return (
    <div className="flex items-center h-3 w-full">
      <div className="w-1/2 flex justify-end">
        {!positive && <div className="h-2 rounded-l bg-red-500/80" style={{ width: `${pct}%` }} />}
      </div>
      <div className="w-px h-4 bg-border" />
      <div className="w-1/2">
        {positive && <div className="h-2 rounded-r bg-primary" style={{ width: `${pct}%` }} />}
      </div>
    </div>
  );
}

export function DriversPanel({ groupEffects, drivers }: Props) {
  const groups = Object.entries(groupEffects);
  const max = Math.max(1, ...groups.map(([, v]) => Math.abs(v)), ...drivers.map((d) => Math.abs(d.effect)));
  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm h-full">
      <h3 className="text-xl font-bold mb-1">What moved the score</h3>
      <p className="text-xs text-muted-foreground mb-4">
        Change in the 0-100 fit score when a signal is replaced by its training average (occlusion). Right of the
        line raised the score; left lowered it.
      </p>
      <div className="space-y-2 mb-6">
        {groups.map(([g, v]) => (
          <div key={g} className="grid grid-cols-[9rem_1fr_3.5rem] items-center gap-2 text-sm">
            <span className="text-foreground">{GROUP_LABEL[g] || g}</span>
            <Bar value={v} max={max} />
            <span className="text-right tabular-nums text-muted-foreground">{v >= 0 ? "+" : ""}{v.toFixed(1)}</span>
          </div>
        ))}
      </div>
      <h4 className="text-sm font-semibold mb-2">Largest individual signals</h4>
      <ul className="space-y-1">
        {drivers.slice(0, 6).map((d) => (
          <li key={d.feature} className="grid grid-cols-[9rem_1fr_3.5rem] items-center gap-2 text-xs">
            <span className="font-mono truncate" title={d.feature}>{d.feature}</span>
            <Bar value={d.effect} max={max} />
            <span className="text-right tabular-nums text-muted-foreground">{d.effect >= 0 ? "+" : ""}{d.effect.toFixed(1)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
