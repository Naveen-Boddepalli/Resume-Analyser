"use client";

import React, { useState } from "react";
import { UploadCard } from "@/components/UploadCard";
import { SummaryRow } from "@/components/SummaryRow";
import { ShapPanel, ShapFeature } from "@/components/ShapPanel";
import { RecommendationsPanel } from "@/components/RecommendationsPanel";
import { Play, CheckCircle } from "lucide-react";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [results, setResults] = useState<{
    probability: number;
    salaryRange: string;
    shapFeatures: ShapFeature[];
    recommendations: string[];
  } | null>(null);

  const handleUpload = (file: File) => {
    setFile(file);
    setResults(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      if (!uploadRes.ok) throw new Error("Upload failed");
      
      const { job_id } = await uploadRes.json();

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/result/${job_id}`);
          const statusData = await statusRes.json();
          
          if (statusData.status === "completed") {
            clearInterval(pollInterval);
            
            const backendRes = statusData.result;
            const features = backendRes.features || {};
            const analysis = backendRes.analysis || { strengths: [], weaknesses: [] };
            
            const shapFeatures = [
              ...(analysis.strengths || []),
              ...(analysis.weaknesses || [])
            ];

            setResults({
              probability: features.placement_probability || 0,
              salaryRange: `${features.salary_low || 0} LPA - ${features.salary_high || 0} LPA`,
              shapFeatures: shapFeatures,
              recommendations: backendRes.recommendations || []
            });
            setIsLoading(false);
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            console.error("Analysis failed");
            setIsLoading(false);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);

    } catch (error) {
      console.error("Upload process failed:", error);
      setIsLoading(false);
    }
  };

  const handleRunDemo = async () => {
    setIsLoading(true);
    try {
      // Assuming backend is running locally at http://localhost:8000
      const response = await fetch("http://localhost:8000/demo", {
        method: "POST",
      });
      
      if (!response.ok) {
        throw new Error("Demo request failed");
      }
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Demo failed:", error);
      // Fallback dummy data for demo purposes if backend isn't available
      setTimeout(() => {
        setResults({
          probability: 85,
          salaryRange: "$95k - $120k",
          shapFeatures: [
            { name: "React Experience", impact: 0.8 },
            { name: "Cloud Deployment (AWS)", impact: -0.4 },
            { name: "System Design", impact: 0.5 },
            { name: "Missing Python Skills", impact: -0.6 },
          ],
          recommendations: [
            "Highlight your recent AWS deployment experience more prominently in the first page.",
            "Add a dedicated section for your Python side projects to offset the lack of professional Python experience.",
            "Quantify your achievements in the React dashboard project (e.g., 'improved load time by 40%').",
            "Consider obtaining an AWS Cloud Practitioner certification to bolster your cloud credentials.",
          ],
        });
        setIsLoading(false);
      }, 1500);
      return;
    }
    
    setIsLoading(false);
  };

  return (
    <main className="min-h-screen p-8 md:p-24 space-y-12 bg-gradient-to-br from-background to-muted/30">
      <div className="max-w-5xl mx-auto space-y-12">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
            AI Placement Readiness Platform
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload your resume to get an AI-powered analysis of your job placement probability, 
            expected salary range, and personalized improvement recommendations.
          </p>
        </div>

        {/* Upload Section */}
        <section className="flex flex-col items-center space-y-6">
          <UploadCard onUpload={handleUpload} isLoading={isLoading} />
          
          <div className="flex items-center gap-4">
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !file}
              className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-full font-semibold hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <CheckCircle className="w-5 h-5" />
              )}
              Analyze Resume
            </button>
            <button
              onClick={handleRunDemo}
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-full font-semibold hover:bg-foreground/90 transition-all shadow-lg hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-background border-t-transparent rounded-full animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              Run Demo
            </button>
          </div>
        </section>

        {/* Results Section */}
        {results && (
          <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <SummaryRow
              probability={results.probability}
              salaryRange={results.salaryRange}
            />
            
            <ShapPanel features={results.shapFeatures} />
            
            <RecommendationsPanel recommendations={results.recommendations} />
          </div>
        )}
      </div>
    </main>
  );
}
