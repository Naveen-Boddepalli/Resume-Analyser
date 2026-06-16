import React from "react";
import { Target, DollarSign } from "lucide-react";

interface SummaryRowProps {
  probability: number;
  salaryRange: string;
}

export function SummaryRow({ probability, salaryRange }: SummaryRowProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto">
      <div className="bg-card border border-border rounded-xl p-6 flex items-center shadow-sm hover:shadow-md transition-shadow">
        <div className="bg-green-100 p-4 rounded-full mr-5">
          <Target className="w-8 h-8 text-green-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Placement Probability
          </p>
          <p className="text-3xl font-bold text-foreground">{probability}%</p>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 flex items-center shadow-sm hover:shadow-md transition-shadow">
        <div className="bg-blue-100 p-4 rounded-full mr-5">
          <DollarSign className="w-8 h-8 text-blue-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Estimated Salary Range
          </p>
          <p className="text-3xl font-bold text-foreground">{salaryRange}</p>
        </div>
      </div>
    </div>
  );
}
