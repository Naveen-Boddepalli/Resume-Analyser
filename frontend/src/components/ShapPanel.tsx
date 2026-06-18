import React from "react";
import { ShapWaterfall, WaterfallFeature } from "./ShapWaterfall";

export interface ShapFeature {
  name: string;
  impact: number; // positive for strength, negative for weakness
  value?: string;
}

interface ShapPanelProps {
  features: ShapFeature[];
  baseValue?: number;  // SHAP expected value (0-1 scale)
  finalValue?: number; // final prediction (0-1 scale)
}

export function ShapPanel({ features, baseValue, finalValue }: ShapPanelProps) {
  // If we have waterfall data, render the interactive waterfall chart
  if (baseValue !== undefined && finalValue !== undefined && features.length > 0) {
    const waterfallFeatures: WaterfallFeature[] = features.map(f => ({
      name: f.name,
      impact: f.impact,
      value: f.value ?? "",
    }));

    return (
      <ShapWaterfall
        features={waterfallFeatures}
        baseValue={baseValue}
        finalValue={finalValue}
      />
    );
  }

  // Fallback: no waterfall data available — show nothing or a placeholder
  return null;
}
