import React from "react";
import { Sparkles } from "lucide-react";

interface CandidateFitPanelProps {
  summary: string;
}

export function CandidateFitPanel({ summary }: CandidateFitPanelProps) {
  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-primary" />
        <h3 className="text-xl font-bold">Recruiter Summary</h3>
      </div>
      <div className="text-foreground text-sm leading-relaxed whitespace-pre-wrap bg-muted/50 p-4 rounded-xl flex-grow">
        {summary || "No summary provided by the AI."}
      </div>
    </div>
  );
}
