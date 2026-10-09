"use client";

import React, { useState } from "react";
import { ShieldCheck, Loader2 } from "lucide-react";
import { audit, type AuditResult } from "@/lib/api";

interface Props {
  file: File;
  jobDescription: string;
  redact: boolean;
}

export function AuditPanel({ file, jobDescription, redact }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await audit(file, jobDescription, redact));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-bold flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" aria-hidden /> Bias check
          </h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-xl">
            Re-scores this resume with only irrelevant cues changed (names from ten demographic groups, group-coded
            affiliations, hobbies and a career break) and reports how far the score moves.
          </p>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Run bias check"}
        </button>
      </div>
      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
      {result && (
        <div className="mt-5 space-y-4 text-sm">
          <p>
            Baseline score <b>{result.baseline_score.toFixed(1)}</b>. Largest gap between name groups:{" "}
            <b>{result.name_spread.toFixed(2)}</b> points
            {result.redaction_applied ? " (redaction on)." : " (redaction OFF: names were visible to the scorer)."}
          </p>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {result.proxy_cues.map((p) => (
              <li key={p.cue} className="flex justify-between rounded-lg border px-3 py-2">
                <span className="font-mono text-xs">{p.cue.replace("_", " ")}</span>
                <span className="tabular-nums">
                  {p.score_change >= 0 ? "+" : ""}
                  {p.score_change.toFixed(2)}
                  {p.decision_changed ? " · decision changed" : ""}
                </span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground">{result.interpretation}</p>
        </div>
      )}
    </div>
  );
}
