import React from "react";
import { DollarSign } from "lucide-react";
import { PlacementGauge } from "./PlacementGauge";
import { SalaryContext } from "./SalaryContext";

interface SummaryRowProps {
  probability: number;
  salaryRange: string;
  salaryLow: number;
  salaryHigh: number;
}

export function SummaryRow({ probability, salaryRange, salaryLow, salaryHigh }: SummaryRowProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto">
      {/* Placement Probability — Radial Gauge */}
      <div id="tour-probability" className="bg-card border border-border rounded-xl p-6 flex flex-col items-center justify-center shadow-sm hover:shadow-lg hover:-translate-y-1 hover:border-primary/30 transition-all duration-300">
        <PlacementGauge value={probability} />
      </div>

      {/* Estimated Salary Range + Percentile Context */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-lg hover:-translate-y-1 hover:border-primary/30 transition-all duration-300">
        <div className="flex items-center mb-5">
          <div className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-full mr-5 shrink-0">
            <DollarSign className="w-8 h-8 text-blue-600" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-muted-foreground truncate">
              Estimated Salary Range
            </p>
            <p className="text-xl lg:text-2xl font-bold text-foreground leading-tight">
              {salaryRange}
            </p>
          </div>
        </div>
        <SalaryContext salaryLow={salaryLow} salaryHigh={salaryHigh} />
      </div>
    </div>
  );
}
