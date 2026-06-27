"use client";

import React, { useState, useRef } from "react";
import { UploadCard } from "@/components/UploadCard";
import { SummaryRow } from "@/components/SummaryRow";
import { ShapPanel, ShapFeature } from "@/components/ShapPanel";
import { RecommendationsPanel } from "@/components/RecommendationsPanel";
import { SensitivityPanel } from "@/components/SensitivityPanel";
import { CompareResultsPanel, AnalysisResult } from "@/components/CompareResultsPanel";
import { Play, CheckCircle, Download, BookOpen, FileDiff } from "lucide-react";
import { WhatIfSliders, FeatureSet } from "@/components/WhatIfSliders";
import { AssessmentModal, AssessmentType } from "@/components/AssessmentModal";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import { ThemeToggle } from "@/components/ThemeToggle";
import { OnboardingTour } from "@/components/OnboardingTour";

const runAnalysis = async (file: File): Promise<{ features: FeatureSet, results: AnalysisResult }> => {
  const formData = new FormData();
  formData.append("file", file);

  const uploadRes = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body: formData,
  });
  if (!uploadRes.ok) throw new Error("Upload failed for " + file.name);
  
  const { job_id } = await uploadRes.json();

  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await fetch(`http://localhost:8000/result/${job_id}`);
        const statusData = await statusRes.json();
        
        if (statusData.status === "completed") {
          clearInterval(pollInterval);
          
          const backendRes = statusData.result;
          const features = backendRes.features || {};
          const analysis = backendRes.analysis || { strengths: [], weaknesses: [], waterfall: [], base_value: 0.5 };
          
          const shapFeatures = analysis.waterfall && analysis.waterfall.length > 0
            ? analysis.waterfall
            : [...(analysis.strengths || []), ...(analysis.weaknesses || [])];

          resolve({
            features,
            results: {
              probability: features.placement_probability || 0,
              salaryRange: `${features.salary_low || 0} LPA - ${features.salary_high || 0} LPA`,
              salaryLow: features.salary_low || 0,
              salaryHigh: features.salary_high || 0,
              shapFeatures: shapFeatures,
              baseValue: analysis.base_value ?? 0.5,
              roadmap: backendRes.roadmap || []
            }
          });
        } else if (statusData.status === "failed") {
          clearInterval(pollInterval);
          reject(new Error(statusData.result?.error || "Analysis failed"));
        }
      } catch (e) {
        clearInterval(pollInterval);
        reject(e);
      }
    }, 2000);
  });
};

export default function Home() {
  const [mode, setMode] = useState<"single" | "compare">("single");
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  
  const [currentFeatures, setCurrentFeatures] = useState<FeatureSet | null>(null);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assessmentState, setAssessmentState] = useState<{isOpen: boolean, type: AssessmentType}>({ isOpen: false, type: "coding" });
  const reportRef = useRef<HTMLDivElement>(null);

  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [results2, setResults2] = useState<AnalysisResult | null>(null);

  const handleModeSwitch = (newMode: "single" | "compare") => {
    setMode(newMode);
    setResults(null);
    setResults2(null);
    setCurrentFeatures(null);
    setHasAnalyzed(false);
    setError(null);
  };

  const handleUpload = (f: File) => {
    setFile(f);
    setResults(null);
    setResults2(null);
    setCurrentFeatures(null);
    setHasAnalyzed(false);
    setError(null);
  };

  const handleUpload2 = (f: File) => {
    setFile2(f);
    setResults(null);
    setResults2(null);
    setCurrentFeatures(null);
    setHasAnalyzed(false);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (mode === "single" && !file) return;
    if (mode === "compare" && (!file || !file2)) return;
    
    setIsLoading(true);
    setError(null);
    try {
      if (mode === "compare") {
        const [res1, res2] = await Promise.all([runAnalysis(file!), runAnalysis(file2!)]);
        setCurrentFeatures(res1.features);
        setResults(res1.results);
        setResults2(res2.results);
      } else {
        const res1 = await runAnalysis(file!);
        setCurrentFeatures(res1.features);
        setResults(res1.results);
      }
      setHasAnalyzed(true);
    } catch (err: any) {
      console.error("Analysis process failed:", err);
      setError(err.message || "Analysis failed due to an unknown error.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunDemo = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          cgpa: 8.5,
          projects_count: 3,
          internships_count: 1,
          certifications_count: 2,
          skills_list: ["React", "Python", "AWS"],
          college_tier: "Tier 2",
          branch: "CSE"
        })
      });
      
      if (!response.ok) {
        throw new Error("Demo request failed");
      }
      
      const data = await response.json();
      const analysis = data.analysis || { strengths: [], weaknesses: [], waterfall: [], base_value: 0.5 };
      const shapFeatures: ShapFeature[] = analysis.waterfall && analysis.waterfall.length > 0
        ? analysis.waterfall
        : [...(analysis.strengths || []), ...(analysis.weaknesses || [])];
      
      setCurrentFeatures(data.features);
      const res1 = {
        probability: data.features.placement_probability || 0,
        salaryRange: `${data.features.salary_low || 0} LPA - ${data.features.salary_high || 0} LPA`,
        salaryLow: data.features.salary_low || 0,
        salaryHigh: data.features.salary_high || 0,
        shapFeatures: shapFeatures,
        baseValue: analysis.base_value ?? 0.5,
        roadmap: data.roadmap || []
      };
      setResults(res1);

      if (mode === "compare") {
        // Generate a fake slightly better second result for demo
        const res2 = {
          ...res1,
          probability: Math.min(100, res1.probability + 12),
          salaryRange: `${(data.features.salary_low + 2).toFixed(1)} LPA - ${(data.features.salary_high + 3).toFixed(1)} LPA`,
          salaryLow: data.features.salary_low + 2,
          salaryHigh: data.features.salary_high + 3,
          shapFeatures: [
            ...res1.shapFeatures,
            { name: "Added React Skill", impact: 0.08, value: "Yes" }
          ],
          roadmap: [
            { timeframe: "Week 1-2", action: "Keep up the great work! Your new skills already boosted your score." },
            { timeframe: "Week 3-4", action: "Apply to 10+ mid-senior roles." }
          ]
        };
        setResults2(res2);
      }
    } catch (error) {
      console.error("Demo failed:", error);
      // Fallback
      const dummyFeatures = {
        cgpa: 8.5,
        projects_count: 3,
        internships_count: 1,
        certifications_count: 2,
        skills_list: ["React", "Python"],
        college_tier: "Tier 2",
        branch: "CSE",
        coding_score: 75,
        placement_probability: 85,
        salary_low: 9.5,
        salary_high: 12.0
      };
      setCurrentFeatures(dummyFeatures);
      const fake1 = {
        probability: 85,
        salaryRange: "9.5 LPA - 12.0 LPA",
        salaryLow: 9.5,
        salaryHigh: 12.0,
        shapFeatures: [
          { name: "React Experience", impact: 0.8, value: "Yes" },
          { name: "Missing Python Skills", impact: -0.6, value: "No" },
        ],
        baseValue: 0.5,
        roadmap: [
          { timeframe: "Week 1-2", action: "Learn Python basics and syntax." },
          { timeframe: "Week 3-4", action: "Build 2 small Python projects." },
          { timeframe: "Week 5-6", action: "Practice Data Structures." },
          { timeframe: "Week 7-8", action: "Start mock interviews." }
        ],
      };
      setResults(fake1);
      
      if (mode === "compare") {
        setResults2({
          ...fake1,
          probability: 95,
          salaryRange: "11.5 LPA - 14.0 LPA",
          salaryLow: 11.5,
          salaryHigh: 14.0,
        });
      }
    }
    setIsLoading(false);
  };

  const handleRecalculate = async (features: FeatureSet) => {
    setIsLoading(true);
    try {
      const payload = { ...features };
      if (!payload.skills_list) payload.skills_list = [];

      const response = await fetch("http://localhost:8000/demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) throw new Error("Recalculation failed");
      const data = await response.json();
      
      setCurrentFeatures(data.features);
      const analysis = data.analysis || { strengths: [], weaknesses: [], waterfall: [], base_value: 0.5 };
      const shapFeatures: ShapFeature[] = analysis.waterfall && analysis.waterfall.length > 0
        ? analysis.waterfall
        : [...(analysis.strengths || []), ...(analysis.weaknesses || [])];
      
      setResults({
        probability: data.features.placement_probability || 0,
        salaryRange: `${data.features.salary_low || 0} LPA - ${data.features.salary_high || 0} LPA`,
        salaryLow: data.features.salary_low || 0,
        salaryHigh: data.features.salary_high || 0,
        shapFeatures: shapFeatures,
        baseValue: analysis.base_value ?? 0.5,
        roadmap: data.roadmap || []
      });
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssessmentComplete = (score: number, type: AssessmentType) => {
    if (currentFeatures) {
      const updatedFeatures = { ...currentFeatures };
      if (type === "coding") updatedFeatures.coding_score = score;
      if (type === "communication") updatedFeatures.communication_score = score;
      handleRecalculate(updatedFeatures);
    }
  };

  const handleExportPDF = async () => {
    if (!reportRef.current) return;
    
    // Temporarily hide buttons for export
    const actionButtons = document.getElementById("pdf-action-buttons");
    if (actionButtons) actionButtons.style.display = 'none';

    try {
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("Placement_Readiness_Report.pdf");
    } catch (err) {
      console.error("PDF Export failed", err);
    } finally {
      // Restore buttons
      if (actionButtons) actionButtons.style.display = 'flex';
    }
  };

  return (
    <main className="min-h-screen p-8 md:p-24 space-y-12 bg-gradient-to-br from-background to-muted/30 dark:from-background dark:to-muted/10 transition-colors duration-300">
      <OnboardingTour hasAnalyzed={hasAnalyzed} />
      <div className="absolute top-4 right-4 md:top-8 md:right-8">
        <ThemeToggle />
      </div>
      <div className="max-w-6xl mx-auto space-y-12">
        
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

        {/* Mode Toggle */}
        <div className="flex justify-center">
          <div className="bg-card border p-1 rounded-xl shadow-sm inline-flex items-center">
            <button
              onClick={() => handleModeSwitch("single")}
              className={`px-6 py-2 rounded-lg font-medium transition-all text-sm ${
                mode === "single" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-muted"
              }`}
            >
              Analyze Single Resume
            </button>
            <button
              onClick={() => handleModeSwitch("compare")}
              className={`px-6 py-2 rounded-lg font-medium transition-all text-sm flex items-center gap-2 ${
                mode === "compare" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-muted"
              }`}
            >
              <FileDiff className="w-4 h-4" />
              Compare Two Resumes
            </button>
          </div>
        </div>

        {/* Upload Section */}
        <section className="flex flex-col items-center space-y-6">
          {mode === "single" ? (
            <UploadCard onUpload={handleUpload} isLoading={isLoading} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full">
              <UploadCard onUpload={handleUpload} isLoading={isLoading} title="Original Resume" />
              <UploadCard onUpload={handleUpload2} isLoading={isLoading} title="Updated Resume" />
            </div>
          )}
          
          {error && (
            <div className="w-full max-w-md bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm text-center">
              {error}
            </div>
          )}

          <div className="flex items-center gap-4">
            <button
              id="tour-analyze"
              onClick={handleAnalyze}
              disabled={isLoading || (mode === "single" && !file) || (mode === "compare" && (!file || !file2))}
              className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-full font-semibold hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <CheckCircle className="w-5 h-5" />
              )}
              {mode === "compare" ? "Analyze Resumes" : "Analyze Resume"}
            </button>
            <button
              id="tour-demo"
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
        {mode === "compare" ? (
          /* Compare Mode Results */
          results && results2 && (
            <div ref={reportRef} className="animate-in fade-in slide-in-from-bottom-4 duration-700 space-y-8">
              <div id="pdf-action-buttons" className="flex justify-between items-center bg-card p-4 rounded-2xl border shadow-sm">
                <h3 className="font-bold text-lg">Comparison Report</h3>
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors text-sm"
                >
                  <Download className="w-4 h-4" />
                  Download PDF
                </button>
              </div>
              <CompareResultsPanel results1={results} results2={results2} />
            </div>
          )
        ) : (
          /* Single Mode Results */
          results && currentFeatures && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
              {/* Left Column: Sliders */}
              <div className="lg:col-span-1">
                <div className="sticky top-6 space-y-6">
                <WhatIfSliders 
                  initialFeatures={currentFeatures} 
                  onRecalculate={handleRecalculate} 
                  isLoading={isLoading} 
                />
                
                <div className="bg-card border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <BookOpen className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold">Skill Assessment</h3>
                      <p className="text-sm text-muted-foreground">Prove your skills to boost your score</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <button
                      onClick={() => setAssessmentState({ isOpen: true, type: "coding" })}
                      className="w-full py-2 border-2 border-primary text-primary font-medium rounded-lg hover:bg-primary hover:text-primary-foreground transition-all duration-300"
                    >
                      Take Coding Assessment
                    </button>
                    <button
                      onClick={() => setAssessmentState({ isOpen: true, type: "communication" })}
                      className="w-full py-2 border-2 border-foreground text-foreground font-medium rounded-lg hover:bg-foreground hover:text-background transition-all duration-300"
                    >
                      Take Communication Assessment
                    </button>
                  </div>
                </div>
              </div>
            </div>

              {/* Right Column: Report */}
              <div className="lg:col-span-2 flex flex-col gap-8" ref={reportRef}>
                <div id="pdf-action-buttons" className="flex justify-between items-center bg-card p-4 rounded-2xl border shadow-sm">
                  <h3 className="font-bold text-lg">Analysis Report</h3>
                  <button
                    onClick={handleExportPDF}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                </div>

                <SummaryRow
                  probability={results.probability}
                  salaryRange={results.salaryRange}
                  salaryLow={results.salaryLow}
                  salaryHigh={results.salaryHigh}
                />
                
                <ShapPanel
                  features={results.shapFeatures}
                  baseValue={results.baseValue}
                  finalValue={results.probability / 100}
                />

                {/* Bento Box: Side-by-side panels */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="h-full">
                    <SensitivityPanel
                      currentFeatures={currentFeatures}
                      baseProbability={results.probability}
                    />
                  </div>
                  <div className="h-full">
                    <RecommendationsPanel roadmap={results.roadmap} />
                  </div>
                </div>
              </div>
            </div>
          )
        )}
      </div>

      <AssessmentModal 
        isOpen={assessmentState.isOpen} 
        type={assessmentState.type}
        onClose={() => setAssessmentState(prev => ({ ...prev, isOpen: false }))} 
        onComplete={handleAssessmentComplete} 
      />
    </main>
  );
}
