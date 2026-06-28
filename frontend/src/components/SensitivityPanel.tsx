"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { ArrowUpRight, ArrowDownRight, Sparkles, TrendingUp } from "lucide-react";

interface Sensitivity {
  feature: string;
  current_value: number;
  new_value: number;
  delta_label: string; // e.g., "+0.5", "+1", "+10"
  probability_change: number; // e.g., 8.2 means +8.2%
}

interface SensitivityPanelProps {
  currentFeatures: Record<string, any>;
  baseProbability: number; // current probability (0-100)
}

export function SensitivityPanel({ currentFeatures, baseProbability }: SensitivityPanelProps) {
  const [data, setData] = useState<Sensitivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const prevFeaturesRef = useRef<string>("");

  const fetchSensitivity = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);

      const payload: Record<string, any> = {
        cgpa: currentFeatures.cgpa ?? 0,
        projects_count: currentFeatures.projects_count ?? 0,
        internships_count: currentFeatures.internships_count ?? 0,
        certifications_count: currentFeatures.certifications_count ?? 0,
        skills_list: currentFeatures.skills_list ?? [],
        college_tier: currentFeatures.college_tier ?? "Tier 2",
        branch: currentFeatures.branch ?? "CSE",
        coding_score: currentFeatures.coding_score ?? 50,
        communication_score: currentFeatures.communication_score ?? 50,
        leadership_score: currentFeatures.leadership_score ?? 50,
      };

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/sensitivity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to fetch sensitivity data");

      const result = await res.json();
      const sensitivities: Sensitivity[] = result.sensitivities ?? [];
      sensitivities.sort((a, b) => b.probability_change - a.probability_change);
      setData(sensitivities);
      setIsVisible(false);
      // Trigger animation after data loads
      requestAnimationFrame(() => {
        requestAnimationFrame(() => setIsVisible(true));
      });
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [currentFeatures]);

  useEffect(() => {
    const featuresKey = JSON.stringify(currentFeatures);
    if (featuresKey !== prevFeaturesRef.current) {
      prevFeaturesRef.current = featuresKey;
      fetchSensitivity();
    }
  }, [currentFeatures, fetchSensitivity]);

  // Don't render anything on error
  if (error) return null;

  const maxChange = Math.max(...data.map((d) => Math.abs(d.probability_change)), 1);

  return (
    <div className="bg-card border rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 relative overflow-hidden group h-full flex flex-col">
      {/* Green accent top border */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 to-emerald-500 group-hover:h-1.5 transition-all" />

      {/* Header */}
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 bg-green-500/10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-foreground">What Would Help Most</h3>
            <p className="text-sm text-muted-foreground">
              See how small improvements in each area could boost your chances
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pb-6 flex-1 overflow-y-auto" style={{ maxHeight: '600px' }}>
        {loading ? (
          /* Skeleton loading state */
          <div className="space-y-3 pt-4">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 p-4 rounded-xl bg-muted/40 animate-pulse"
              >
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded-lg w-1/3" />
                  <div className="h-3 bg-muted rounded-lg w-1/2" />
                  <div className="h-2 bg-muted rounded-full w-full mt-2" />
                </div>
                <div className="w-16 h-8 bg-muted rounded-lg" />
              </div>
            ))}
          </div>
        ) : data.length === 0 ? (
          /* Empty / optimized state */
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 bg-green-500/10 rounded-full mb-4">
              <Sparkles className="w-8 h-8 text-green-500" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-1">
              Your profile is already optimized!
            </h4>
            <p className="text-sm text-muted-foreground max-w-xs">
              There are no significant improvements to suggest — you&apos;re in great shape.
            </p>
          </div>
        ) : (
          /* Data rows */
          <div className="space-y-2 pt-3">
            {data.map((item, idx) => {
              const isPositive = item.probability_change >= 0;
              const barWidthPct =
                (Math.abs(item.probability_change) / maxChange) * 100;

              return (
                <div
                  key={`${item.feature}-${idx}`}
                  className="relative p-4 rounded-xl border border-transparent hover:border-border hover:bg-muted/30 transition-all duration-200 cursor-default group/row"
                  style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible
                      ? "translateY(0)"
                      : "translateY(16px)",
                    transition: `opacity 0.45s ease ${idx * 0.07}s, transform 0.45s ease ${idx * 0.07}s`,
                  }}
                >
                  <div className="flex items-center gap-4">
                    {/* Info column */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-bold text-foreground">
                          {formatFeatureName(item.feature)}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">
                        Increase by{" "}
                        <span className="font-medium text-foreground">
                          {item.delta_label}
                        </span>
                      </p>

                      {/* Progress bar */}
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-700 ease-out"
                          style={{
                            width: isVisible ? `${barWidthPct}%` : "0%",
                            transitionDelay: `${idx * 0.07 + 0.2}s`,
                            background: isPositive
                              ? "linear-gradient(90deg, #22c55e, #16a34a)"
                              : "linear-gradient(90deg, #ef4444, #dc2626)",
                          }}
                        />
                      </div>

                      {/* Current → New */}
                      <p className="text-[11px] text-muted-foreground mt-1.5">
                        {formatValue(item.current_value)} →{" "}
                        <span className="font-medium text-foreground">
                          {formatValue(item.new_value)}
                        </span>
                      </p>
                    </div>

                    {/* Change indicator */}
                    <div className="flex-shrink-0 flex flex-col items-center">
                      <div
                        className={`flex items-center gap-0.5 px-3 py-1.5 rounded-lg font-bold text-lg tabular-nums ${
                          isPositive
                            ? "text-green-600 bg-green-500/10"
                            : "text-red-500 bg-red-500/10"
                        }`}
                      >
                        {isPositive ? (
                          <ArrowUpRight className="w-4 h-4" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4" />
                        )}
                        <span>
                          {isPositive ? "+" : ""}
                          {item.probability_change.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Subtle hover glow */}
                  <div
                    className={`absolute inset-0 rounded-xl opacity-0 group-hover/row:opacity-100 transition-opacity duration-300 pointer-events-none ${
                      isPositive
                        ? "shadow-[inset_0_0_0_1px_rgba(34,197,94,0.15)]"
                        : "shadow-[inset_0_0_0_1px_rgba(239,68,68,0.15)]"
                    }`}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Bottom note */}
        {!loading && data.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/40 text-center">
            <p className="text-[11px] text-muted-foreground">
              Based on current prediction of{" "}
              <span className="font-semibold text-primary">
                {baseProbability.toFixed(1)}%
              </span>{" "}
              — sensitivity may vary with different profiles
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/** Pretty-print feature names (snake_case → Title Case) */
function formatFeatureName(name: string): string {
  const map: Record<string, string> = {
    cgpa: "CGPA",
    projects_count: "Projects",
    internships_count: "Internships",
    certifications_count: "Certifications",
    coding_score: "Coding Score",
    communication_score: "Communication Score",
    leadership_score: "Leadership Score",
    skills_list: "Skills",
    college_tier: "College Tier",
    branch: "Branch",
  };
  return (
    map[name] ??
    name
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

/** Format numeric values nicely */
function formatValue(val: number): string {
  if (Number.isInteger(val)) return val.toString();
  return val.toFixed(1);
}
