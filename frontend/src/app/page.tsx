"use client";

import React, { useState, useRef } from "react";
import { UploadCard } from "@/components/UploadCard";
import { SummaryRow } from "@/components/SummaryRow";
import { SkillMatchPanel } from "@/components/SkillMatchPanel";
import { CandidateFitPanel } from "@/components/CandidateFitPanel";
import { Play, CheckCircle, Download } from "lucide-react";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AnalysisResult {
  matchScore: number;
  decision: string;
  matchingSkills: string[];
  missingSkills: string[];
  summary: string;
}

const runAnalysis = async (file: File, jobDescription: string): Promise<AnalysisResult> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("job_description", jobDescription);

  const uploadRes = await fetch(`${API_URL}/upload`, {
    method: "POST",
    headers: {
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
    },
    body: formData,
  });
  if (!uploadRes.ok) {
    const errorData = await uploadRes.json().catch(() => ({}));
    const errorMsg = errorData.error || (typeof errorData.detail === 'string' ? errorData.detail : "Upload failed for " + file.name);
    throw new Error(errorMsg);
  }
  
  const { job_id } = await uploadRes.json();

  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API_URL}/result/${job_id}`, {
          headers: {
            "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
          }
        });
        const statusData = await statusRes.json();
        
        if (statusData.status === "completed") {
          clearInterval(pollInterval);
          
          const backendRes = statusData.result;

          resolve({
            matchScore: backendRes.match_score || 0,
            decision: backendRes.decision || "Review",
            matchingSkills: backendRes.matching_skills || [],
            missingSkills: backendRes.missing_skills || [],
            summary: backendRes.summary || "Analysis complete."
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
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState<string>("");
  
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  const [results, setResults] = useState<AnalysisResult | null>(null);

  const handleUpload = (f: File, jd: string) => {
    setFile(f);
    setJobDescription(jd);
    setResults(null);
    setHasAnalyzed(false);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file || !jobDescription) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const res = await runAnalysis(file, jobDescription);
      setResults(res);
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
      const response = await fetch(`${API_URL}/demo`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
        },
        body: JSON.stringify({
          job_description: "We are looking for a software engineer with strong React and Python skills, who has a high GPA and good project experience.",
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
      
      setResults({
        matchScore: data.match_score || 0,
        decision: data.decision || "Review",
        matchingSkills: data.matching_skills || [],
        missingSkills: data.missing_skills || [],
        summary: data.summary || "Analysis complete."
      });
      setHasAnalyzed(true);

    } catch (error) {
      console.error("Demo failed:", error);
      // Fallback
      setResults({
        matchScore: 85,
        decision: "Shortlist",
        matchingSkills: ["React", "Python"],
        missingSkills: ["Docker", "Kubernetes"],
        summary: "The candidate shows strong foundation in React and Python, which aligns well with the core requirements. However, they lack DevOps experience."
      });
      setHasAnalyzed(true);
    }
    setIsLoading(false);
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
      pdf.save("Candidate_Screening_Report.pdf");
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
            AI Resume Screening & Job-Matching
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Paste a job description and upload a resume to get an AI-powered analysis of the candidate's fit, matching skills, and a shortlist recommendation.
          </p>
        </div>

        {/* Conditionally render Loading Skeleton or Upload Section */}
        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <>
            {/* Upload Section */}
            <section className="flex flex-col items-center space-y-6 mt-6">
              <UploadCard onUpload={handleUpload} isLoading={isLoading} />
              
              {error && (
                <div className="w-full max-w-md bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm text-center">
                  {error}
                </div>
              )}

              <div className="flex items-center gap-4">
                <button
                  id="tour-analyze"
                  onClick={handleAnalyze}
                  disabled={isLoading || hasAnalyzed || !file || !jobDescription}
                  className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-full font-semibold hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                >
                  <CheckCircle className="w-5 h-5" />
                  Analyze Resume
                </button>
                <button
                  id="tour-demo"
                  onClick={handleRunDemo}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-full font-semibold hover:bg-foreground/90 transition-all shadow-lg hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                >
                  <Play className="w-5 h-5" />
                  Run Demo
                </button>
              </div>
            </section>
          </>
        )}

        {/* Results Section */}
        {results && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700" ref={reportRef}>
            <div id="pdf-action-buttons" className="flex justify-between items-center bg-card p-4 rounded-2xl border shadow-sm">
              <h3 className="font-bold text-lg">Screening Report</h3>
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors text-sm"
              >
                <Download className="w-4 h-4" />
                Download PDF
              </button>
            </div>

            <SummaryRow
              matchScore={results.matchScore}
              decision={results.decision}
            />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="h-full">
                <SkillMatchPanel
                  matchingSkills={results.matchingSkills}
                  missingSkills={results.missingSkills}
                />
              </div>
              <div className="h-full">
                <CandidateFitPanel summary={results.summary} />
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
