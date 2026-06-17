"use client";

import React, { useState, useRef } from "react";
import { UploadCard } from "@/components/UploadCard";
import { SummaryRow } from "@/components/SummaryRow";
import { ShapPanel, ShapFeature } from "@/components/ShapPanel";
import { RecommendationsPanel } from "@/components/RecommendationsPanel";
import { Play, CheckCircle, Download, BookOpen } from "lucide-react";
import { WhatIfSliders, FeatureSet } from "@/components/WhatIfSliders";
import { AssessmentModal, AssessmentType } from "@/components/AssessmentModal";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [currentFeatures, setCurrentFeatures] = useState<FeatureSet | null>(null);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assessmentState, setAssessmentState] = useState<{isOpen: boolean, type: AssessmentType}>({ isOpen: false, type: "coding" });
  const reportRef = useRef<HTMLDivElement>(null);

  const [results, setResults] = useState<{
    probability: number;
    salaryRange: string;
    shapFeatures: ShapFeature[];
    recommendations: string[];
  } | null>(null);

  const handleUpload = (file: File) => {
    setFile(file);
    setResults(null);
    setCurrentFeatures(null);
    setHasAnalyzed(false);
    setError(null);
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

            setCurrentFeatures(features);
            setResults({
              probability: features.placement_probability || 0,
              salaryRange: `${features.salary_low || 0} LPA - ${features.salary_high || 0} LPA`,
              shapFeatures: shapFeatures,
              recommendations: backendRes.recommendations || []
            });
            setIsLoading(false);
            setHasAnalyzed(true);
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            console.error("Analysis failed:", statusData.result?.error);
            setError(statusData.result?.error || "Analysis failed due to an unknown error.");
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
      setCurrentFeatures(data.features);
      setResults({
        probability: data.features.placement_probability || 0,
        salaryRange: `${data.features.salary_low || 0} LPA - ${data.features.salary_high || 0} LPA`,
        shapFeatures: [...(data.analysis.strengths || []), ...(data.analysis.weaknesses || [])],
        recommendations: data.recommendations || []
      });
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
      setResults({
        probability: 85,
        salaryRange: "9.5 LPA - 12.0 LPA",
        shapFeatures: [
          { name: "React Experience", impact: 0.8 },
          { name: "Missing Python Skills", impact: -0.6 },
        ],
        recommendations: ["Learn Python"],
      });
    }
    setIsLoading(false);
  };

  const handleRecalculate = async (features: FeatureSet) => {
    setIsLoading(true);
    try {
      // Create request payload. Make sure it conforms to DemoRequest schema
      const payload = { ...features };
      // ensure skills_list is present
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
      const analysis = data.analysis || { strengths: [], weaknesses: [] };
      const shapFeatures = [
        ...(analysis.strengths || []),
        ...(analysis.weaknesses || [])
      ];
      
      setResults({
        probability: data.features.placement_probability || 0,
        salaryRange: `${data.features.salary_low || 0} LPA - ${data.features.salary_high || 0} LPA`,
        shapFeatures: shapFeatures,
        recommendations: data.recommendations || []
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

        {/* Upload Section */}
        <section className="flex flex-col items-center space-y-6">
          <UploadCard onUpload={handleUpload} isLoading={isLoading} />
          
          {error && (
            <div className="w-full max-w-md bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm text-center">
              {error}
            </div>
          )}

          <div className="flex items-center gap-4">
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !file || hasAnalyzed}
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
        {results && currentFeatures && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Left Column: Sliders */}
            <div className="lg:col-span-1 space-y-6">
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

            {/* Right Column: Report */}
            <div className="lg:col-span-2 space-y-10" ref={reportRef}>
              <div id="pdf-action-buttons" className="flex justify-end">
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg font-medium hover:bg-secondary/80 transition-colors text-sm"
                >
                  <Download className="w-4 h-4" />
                  Download PDF Report
                </button>
              </div>

              <SummaryRow
                probability={results.probability}
                salaryRange={results.salaryRange}
              />
              
              <ShapPanel features={results.shapFeatures} />
              
              <RecommendationsPanel recommendations={results.recommendations} />
            </div>
          </div>
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

