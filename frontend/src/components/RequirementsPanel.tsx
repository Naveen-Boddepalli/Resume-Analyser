import React from "react";
import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import type { RequirementEvidence } from "@/lib/api";

const STATUS = {
  met: { label: "Evidenced", Icon: CheckCircle2, cls: "text-green-600 dark:text-green-400" },
  partial: { label: "Partial", Icon: CircleDashed, cls: "text-yellow-600 dark:text-yellow-400" },
  unmet: { label: "No evidence", Icon: XCircle, cls: "text-red-600 dark:text-red-400" },
} as const;

interface Props {
  requirements: RequirementEvidence[];
  counts: { met: number; partial: number; unmet: number };
}

export function RequirementsPanel({ requirements, counts }: Props) {
  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-1">
        <h3 className="text-xl font-bold">Requirement-by-requirement evidence</h3>
        <p className="text-sm text-muted-foreground">
          {counts.met} evidenced · {counts.partial} partial · {counts.unmet} without evidence
        </p>
      </div>
      <p className="text-xs text-muted-foreground mb-4">
        Each job requirement is linked to the most similar sentence in the (redacted) resume. Similarity is
        embedding cosine; it indicates relevance, not proof of competence.
      </p>
      <ul className="space-y-3">
        {requirements.map((r, i) => {
          const s = STATUS[r.status];
          return (
            <li key={i} className="rounded-xl border p-3">
              <div className="flex items-start gap-2">
                <s.Icon className={`w-5 h-5 mt-0.5 shrink-0 ${s.cls}`} aria-hidden />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{r.requirement}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    <span className={s.cls}>{s.label}</span> · {r.kind} · similarity {r.similarity.toFixed(2)}
                  </p>
                  {r.evidence && (
                    <p className="text-sm text-foreground/80 mt-2 border-l-2 border-primary/40 pl-3 italic">
                      {r.evidence}
                    </p>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
