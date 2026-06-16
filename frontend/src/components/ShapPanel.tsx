import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

export interface ShapFeature {
  name: string;
  impact: number; // positive for strength, negative for weakness
}

interface ShapPanelProps {
  features: ShapFeature[];
}

export function ShapPanel({ features }: ShapPanelProps) {
  const strengths = features.filter(f => f.impact > 0).sort((a, b) => b.impact - a.impact);
  const weaknesses = features.filter(f => f.impact < 0).sort((a, b) => a.impact - b.impact);

  const maxImpact = Math.max(...features.map(f => Math.abs(f.impact)), 0.01);

  return (
    <div className="grid md:grid-cols-2 gap-6 w-full max-w-5xl mx-auto">
      {/* Strengths Card */}
      <div className="bg-card border border-green-500/20 rounded-2xl p-6 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-green-500" />
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-green-500/10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Top Strengths</h3>
        </div>
        
        <div className="space-y-5">
          {strengths.length > 0 ? strengths.map((f, i) => (
            <div key={i} className="space-y-2">
              <div className="flex justify-between text-sm font-medium">
                <span>{f.name}</span>
                <span className="text-green-600">+{Math.abs(f.impact).toFixed(2)}</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-green-500 h-full rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${(Math.abs(f.impact) / maxImpact) * 100}%` }}
                />
              </div>
            </div>
          )) : (
            <div className="text-sm text-muted-foreground italic py-4">No major strengths identified.</div>
          )}
        </div>
      </div>

      {/* Weaknesses Card */}
      <div className="bg-card border border-red-500/20 rounded-2xl p-6 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-red-500" />
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-red-500/10 rounded-lg">
            <TrendingDown className="w-5 h-5 text-red-600" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Areas for Improvement</h3>
        </div>
        
        <div className="space-y-5">
          {weaknesses.length > 0 ? weaknesses.map((f, i) => (
            <div key={i} className="space-y-2">
              <div className="flex justify-between text-sm font-medium">
                <span>{f.name}</span>
                <span className="text-red-600">-{Math.abs(f.impact).toFixed(2)}</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden flex justify-end">
                <div 
                  className="bg-red-500 h-full rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${(Math.abs(f.impact) / maxImpact) * 100}%` }}
                />
              </div>
            </div>
          )) : (
            <div className="text-sm text-muted-foreground italic py-4">No major weaknesses identified.</div>
          )}
        </div>
      </div>
    </div>
  );
}
