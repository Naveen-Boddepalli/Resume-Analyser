import React from "react";
import { Target, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { PlacementGauge } from "./PlacementGauge";

interface SummaryRowProps {
  matchScore: number;
  decision: string;
}

export function SummaryRow({ matchScore, decision }: SummaryRowProps) {
  let DecisionIcon = AlertTriangle;
  let decisionColor = "text-yellow-500";
  let bgDark = "dark:bg-yellow-900/30";
  let bgLight = "bg-yellow-100";

  if (decision === "Shortlist") {
    DecisionIcon = CheckCircle2;
    decisionColor = "text-green-500";
    bgDark = "dark:bg-green-900/30";
    bgLight = "bg-green-100";
  } else if (decision === "Reject") {
    DecisionIcon = XCircle;
    decisionColor = "text-red-500";
    bgDark = "dark:bg-red-900/30";
    bgLight = "bg-red-100";
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mx-auto">
      {/* Match Score — Radial Gauge */}
      <div className="bg-card border border-border rounded-xl p-6 flex flex-col items-center justify-center shadow-sm hover:shadow-lg hover:-translate-y-1 hover:border-primary/30 transition-all duration-300">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Fit score (0-100)</h3>
        <PlacementGauge value={matchScore} />
      </div>

      {/* Decision */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-lg hover:-translate-y-1 hover:border-primary/30 transition-all duration-300 flex flex-col justify-center">
        <div className="flex items-center">
          <div className={`${bgLight} ${bgDark} p-4 rounded-full mr-5 shrink-0`}>
            <DecisionIcon className={`w-8 h-8 ${decisionColor}`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-muted-foreground truncate">
              Suggested outcome (human review required)
            </p>
            <p className="text-2xl lg:text-3xl font-bold text-foreground leading-tight">
              {decision}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
