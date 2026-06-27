import React from "react";
import { Calendar, Target } from "lucide-react";

export interface RoadmapItem {
  timeframe: string;
  action: string;
}

interface RecommendationsPanelProps {
  roadmap: RoadmapItem[];
}

export function RecommendationsPanel({
  roadmap,
}: RecommendationsPanelProps) {
  // Fallback if roadmap isn't available
  const safeRoadmap = roadmap || [];

  return (
    <div id="tour-roadmap" className="bg-card border border-border rounded-2xl p-6 w-full h-full flex flex-col shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Calendar className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-foreground">
            Improvement Roadmap
          </h3>
          <p className="text-sm text-muted-foreground">Your step-by-step action plan</p>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2" style={{ maxHeight: '600px' }}>
        {safeRoadmap.length > 0 ? (
          <div className="space-y-4">
            {safeRoadmap.map((item, index) => (
              <div
                key={index}
                className="group relative flex flex-col p-5 rounded-xl bg-muted/30 border border-muted hover:bg-muted/50 hover:border-primary/40 transition-all duration-300 shadow-sm overflow-hidden"
              >
                {/* Left Accent line */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary/20 group-hover:bg-primary transition-colors duration-300" />
                
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-primary" />
                  <span className="font-bold text-sm text-primary tracking-wide uppercase">
                    {item.timeframe}
                  </span>
                </div>
                
                <p className="text-foreground leading-relaxed text-sm pl-1">
                  {item.action}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <p>No roadmap available.</p>
          </div>
        )}
      </div>
    </div>
  );
}
