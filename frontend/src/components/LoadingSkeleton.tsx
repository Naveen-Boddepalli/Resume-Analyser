"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STEPS = [
  "Waking up backend server (Render free tier)",
  "Parsing your resume",
  "Analyzing your experience",
  "Extracting your skills",
  "Generating recommendations"
];

export function LoadingSkeleton() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // If backend is local, it's fast (~2s total). If on Render, it takes ~25-50s due to cold start.
    const isLocal = API_URL.includes("localhost") || API_URL.includes("127.0.0.1");
    const intervals = isLocal ? [200, 200, 200, 200] : [8000, 5000, 6000, 5000];
    
    let timerId: NodeJS.Timeout;
    
    const advanceStep = (stepIndex: number) => {
      if (stepIndex >= intervals.length) return;
      timerId = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
        advanceStep(stepIndex + 1);
      }, intervals[stepIndex]);
    };

    advanceStep(0);

    return () => clearTimeout(timerId);
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700 w-full mt-8">
      {/* Left Column: Skeleton Score Card */}
      <div className="lg:col-span-1">
        <div className="bg-card border shadow-lg rounded-2xl p-6 space-y-6 flex flex-col h-full relative overflow-hidden">
          <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-foreground/5 to-transparent z-10" />
          
          <h2 className="text-xl font-bold text-center text-foreground">Placement Score</h2>
          
          <div className="flex flex-col items-center justify-center space-y-4 py-4">
            {/* Fake Gauge */}
            <div className="w-32 h-16 bg-slate-200 dark:bg-slate-700 rounded-t-full relative overflow-hidden">
              <div className="absolute bottom-0 w-full h-[1px] bg-muted-foreground/30" />
              <div className="absolute bottom-0 left-1/2 w-2 h-2 bg-muted-foreground rounded-full -translate-x-1/2 translate-y-1/2" />
            </div>
            
            <div className="space-y-2 flex flex-col items-center">
              <div className="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded-full" />
              <div className="h-3 w-20 bg-slate-200 dark:bg-slate-700 rounded-full" />
            </div>
          </div>
          
          <div className="space-y-4 pt-4 border-t border-border">
            {["CGPA", "PROJECTS", "INTERNSHIPS", "CERTIFICATIONS"].map((item, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-xs font-semibold text-muted-foreground">{item}</span>
                <div className="w-8 h-4 bg-slate-200 dark:bg-slate-700 rounded-full" />
              </div>
            ))}
          </div>

          <div className="mt-auto pt-6 border-t border-border">
            <div className="w-full h-10 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
              <span className="text-sm font-semibold text-muted-foreground">Generating Report...</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Loading Steps */}
      <div className="lg:col-span-2">
        <div className="bg-slate-50/50 dark:bg-slate-800/30 border border-border shadow-sm rounded-2xl p-8 lg:p-12 h-full flex flex-col justify-center space-y-8">
          <div className="space-y-8 max-w-md mx-auto w-full">
            {STEPS.map((step, index) => {
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;
              const isPending = index > currentStep;

              return (
                <div 
                  key={index} 
                  className={`flex items-center gap-4 transition-all duration-500 ${
                    isPending ? 'opacity-40' : 'opacity-100'
                  } ${isActive ? 'scale-105' : 'scale-100'}`}
                >
                  <div className="flex-shrink-0">
                    {isCompleted ? (
                      <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center">
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      </div>
                    ) : isActive ? (
                      <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.5)]">
                        <Loader2 className="w-5 h-5 text-white animate-spin" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full border-2 border-muted flex items-center justify-center" />
                    )}
                  </div>
                  <span className={`text-lg font-medium ${isActive ? 'text-foreground' : isCompleted ? 'text-foreground/80' : 'text-muted-foreground'}`}>
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
