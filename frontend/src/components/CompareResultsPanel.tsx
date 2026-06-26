import React from "react";
import { SummaryRow } from "./SummaryRow";
import { ShapPanel, ShapFeature } from "./ShapPanel";
import { RecommendationsPanel } from "./RecommendationsPanel";
import { ArrowUp, ArrowDown, TrendingUp } from "lucide-react";

export interface AnalysisResult {
  probability: number;
  salaryRange: string;
  salaryLow: number;
  salaryHigh: number;
  shapFeatures: ShapFeature[];
  baseValue: number;
  roadmap: { timeframe: string; action: string; }[];
}

interface CompareResultsPanelProps {
  results1: AnalysisResult;
  results2: AnalysisResult;
}

export function CompareResultsPanel({ results1, results2 }: CompareResultsPanelProps) {
  const probDiff = results2.probability - results1.probability;
  const isPositive = probDiff >= 0;

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Diff Banner */}
      <div className="bg-card border rounded-2xl shadow-sm p-6 text-center">
        <h2 className="text-xl font-bold text-foreground mb-4">Improvement Summary</h2>
        <div className="flex flex-col md:flex-row items-center justify-center gap-8">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Probability Shift</p>
            <div
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-2xl ${
                isPositive ? "text-green-600 bg-green-500/10" : "text-red-500 bg-red-500/10"
              }`}
            >
              {isPositive ? <ArrowUp className="w-6 h-6" /> : <ArrowDown className="w-6 h-6" />}
              {isPositive ? "+" : ""}{probDiff.toFixed(1)}%
            </div>
          </div>

          <div className="hidden md:block w-px h-16 bg-border"></div>

          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Original Salary Range</p>
            <p className="text-xl font-semibold text-foreground">{results1.salaryRange}</p>
          </div>

          <div className="hidden md:block w-px h-16 bg-border"></div>

          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">New Salary Range</p>
            <p className="text-xl font-semibold text-foreground">{results2.salaryRange}</p>
          </div>
        </div>
      </div>

      {/* Side-by-side Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Column 1: Original */}
        <div className="flex flex-col h-full space-y-8 p-6 bg-card/50 border rounded-2xl border-dashed">
          <div className="text-center mb-6 flex items-center justify-center h-10">
            <h3 className="text-2xl font-bold text-muted-foreground">Original Resume</h3>
          </div>
          <SummaryRow
            probability={results1.probability}
            salaryRange={results1.salaryRange}
            salaryLow={results1.salaryLow}
            salaryHigh={results1.salaryHigh}
          />
          <ShapPanel
            features={results1.shapFeatures}
            baseValue={results1.baseValue}
            finalValue={results1.probability / 100}
          />
          <div className="flex-1">
            <RecommendationsPanel roadmap={results1.roadmap} />
          </div>
        </div>

        {/* Column 2: Updated */}
        <div className="flex flex-col h-full space-y-8 p-6 bg-card border rounded-2xl shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-primary to-blue-500" />
          <div className="text-center mb-6 flex items-center justify-center h-10">
            <h3 className="text-2xl font-bold text-foreground flex items-center justify-center gap-2">
              <TrendingUp className="w-6 h-6 text-primary" />
              Updated Resume
            </h3>
          </div>
          <SummaryRow
            probability={results2.probability}
            salaryRange={results2.salaryRange}
            salaryLow={results2.salaryLow}
            salaryHigh={results2.salaryHigh}
          />
          <ShapPanel
            features={results2.shapFeatures}
            baseValue={results2.baseValue}
            finalValue={results2.probability / 100}
          />
          <div className="flex-1">
            <RecommendationsPanel roadmap={results2.roadmap} />
          </div>
        </div>
      </div>
    </div>
  );
}
