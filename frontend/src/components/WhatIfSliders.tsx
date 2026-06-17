import React, { useState, useEffect } from "react";
import { Sliders } from "lucide-react";

export interface FeatureSet {
  cgpa: number;
  projects_count: number;
  internships_count: number;
  certifications_count: number;
  skills_list: string[];
  coding_score?: number;
  communication_score?: number;
  leadership_score?: number;
  [key: string]: any;
}

interface WhatIfSlidersProps {
  initialFeatures: FeatureSet;
  onRecalculate: (features: FeatureSet) => void;
  isLoading: boolean;
}

export function WhatIfSliders({ initialFeatures, onRecalculate, isLoading }: WhatIfSlidersProps) {
  const [features, setFeatures] = useState<FeatureSet>(initialFeatures);

  useEffect(() => {
    setFeatures(initialFeatures);
  }, [initialFeatures]);

  const handleChange = (key: keyof FeatureSet, value: number) => {
    setFeatures(prev => ({ ...prev, [key]: value }));
  };

  const handleApply = () => {
    onRecalculate(features);
  };

  return (
    <div className="bg-card border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3 mb-6 border-b pb-4">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Sliders className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-foreground">What-If Analysis</h3>
          <p className="text-sm text-muted-foreground">Tweak your stats to see how it affects your chances</p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-foreground">CGPA</label>
            <span className="text-sm text-muted-foreground">{features.cgpa?.toFixed(1) || "0.0"} / 10</span>
          </div>
          <input
            type="range"
            min="0"
            max="10"
            step="0.1"
            value={features.cgpa || 0}
            onChange={(e) => handleChange("cgpa", parseFloat(e.target.value))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-foreground">Internships</label>
            <span className="text-sm text-muted-foreground">{features.internships_count || 0}</span>
          </div>
          <input
            type="range"
            min="0"
            max="10"
            step="1"
            value={features.internships_count || 0}
            onChange={(e) => handleChange("internships_count", parseInt(e.target.value, 10))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-foreground">Projects</label>
            <span className="text-sm text-muted-foreground">{features.projects_count || 0}</span>
          </div>
          <input
            type="range"
            min="0"
            max="20"
            step="1"
            value={features.projects_count || 0}
            onChange={(e) => handleChange("projects_count", parseInt(e.target.value, 10))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-foreground">Certifications</label>
            <span className="text-sm text-muted-foreground">{features.certifications_count || 0}</span>
          </div>
          <input
            type="range"
            min="0"
            max="20"
            step="1"
            value={features.certifications_count || 0}
            onChange={(e) => handleChange("certifications_count", parseInt(e.target.value, 10))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>

        <button
          onClick={handleApply}
          disabled={isLoading}
          className="w-full py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isLoading ? "Recalculating..." : "Update Prediction"}
        </button>
      </div>
    </div>
  );
}
