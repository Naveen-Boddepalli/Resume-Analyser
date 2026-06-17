import React from "react";

interface RecommendationsPanelProps {
  recommendations: string[];
}

export function RecommendationsPanel({
  recommendations,
}: RecommendationsPanelProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-6 w-full max-w-4xl mx-auto shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-xl font-bold mb-6 text-foreground">
        AI Recommendations
      </h3>
      <ul className="space-y-4">
        {recommendations.map((rec, index) => (
          <li
            key={index}
            className="flex items-start p-4 rounded-lg bg-muted/50 border border-muted hover:bg-muted transition-colors duration-300 hover:border-primary/30 hover:shadow-sm"
          >
            <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary text-primary-foreground font-bold mr-4">
              {index + 1}
            </div>
            <p className="text-foreground leading-relaxed pt-1">{rec}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
