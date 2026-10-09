import React from "react";
import { Sparkles, AlertTriangle, EyeOff } from "lucide-react";

interface CandidateFitPanelProps {
  summary: string;
  narrative?: string;
  warnings: string[];
  redactionCounts: Record<string, number>;
  redactionApplied: boolean;
}

export function CandidateFitPanel({
  summary,
  narrative,
  warnings,
  redactionCounts,
  redactionApplied,
}: CandidateFitPanelProps) {
  const removed = Object.entries(redactionCounts);
  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm h-full flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary" aria-hidden />
        <h3 className="text-xl font-bold">Summary for the reviewer</h3>
      </div>
      <p className="text-foreground text-sm leading-relaxed bg-muted/50 p-4 rounded-xl">{summary}</p>
      {narrative && (
        <p className="text-sm leading-relaxed border rounded-xl p-4">
          <span className="block text-xs font-semibold text-muted-foreground mb-1">
            AI-written rephrasing of the evidence above
          </span>
          {narrative}
        </p>
      )}
      <div className="text-sm">
        <h4 className="font-semibold flex items-center gap-2 mb-1">
          <EyeOff className="w-4 h-4" aria-hidden /> Blind screening
        </h4>
        {redactionApplied ? (
          removed.length ? (
            <p className="text-muted-foreground">
              Removed before scoring: {removed.map(([k, v]) => `${v} ${k.replace("_", " ")}`).join(", ")}.
            </p>
          ) : (
            <p className="text-muted-foreground">Nothing needed removing.</p>
          )
        ) : (
          <p className="text-yellow-700 dark:text-yellow-400">Redaction was switched off for this analysis.</p>
        )}
      </div>
      {warnings.length > 0 && (
        <ul className="space-y-1">
          {warnings.map((w) => (
            <li key={w} className="flex gap-2 text-sm text-yellow-700 dark:text-yellow-400">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden /> {w}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
