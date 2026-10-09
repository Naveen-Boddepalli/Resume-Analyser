"use client";

import React, { useRef, useState } from "react";
import { CheckCircle, Download, Play } from "lucide-react";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import { UploadCard } from "@/components/UploadCard";
import { SummaryRow } from "@/components/SummaryRow";
import { SkillMatchPanel } from "@/components/SkillMatchPanel";
import { CandidateFitPanel } from "@/components/CandidateFitPanel";
import { RequirementsPanel } from "@/components/RequirementsPanel";
import { DriversPanel } from "@/components/DriversPanel";
import { AuditPanel } from "@/components/AuditPanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { analyze, type AnalysisResult } from "@/lib/api";

const DEMO_JD =
  "Backend Engineer. Requirements: 4+ years of experience building REST APIs in Python. Experience with Docker, " +
  "Kubernetes and AWS is required. Bachelor's degree in Computer Science. Preferred: PostgreSQL experience is a plus.";

const DEMO_RESUME = [
  "Alex Morgan",
  "alex.morgan@example.com | 555-123-4567",
  "Summary: Backend engineer with 6 years of experience building REST APIs in Python and FastAPI.",
  "Deployed services with Docker and Kubernetes on AWS; maintained PostgreSQL databases and CI/CD pipelines.",
  "Skills: Python, SQL, Docker, Kubernetes, AWS, PostgreSQL, Git",
  "Experience: 03/2018 to Present, Senior Software Engineer. Led a team of four engineers.",
  "Education: Bachelor of Science in Computer Science, Northfield State University.",
].join("\n");

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [redact, setRedact] = useState(true);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  const handleUpload = (f: File, jd: string) => {
    setFile(f);
    setJobDescription(jd);
    setResults(null);
    setError(null);
  };

  const run = async (f: File, jd: string) => {
    setIsLoading(true);
    setError(null);
    try {
      setResults(await analyze(f, jd, redact));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemo = () => {
    const demo = new File([DEMO_RESUME], "sample_resume.txt", { type: "text/plain" });
    setFile(demo);
    setJobDescription(DEMO_JD);
    void run(demo, DEMO_JD);
  };

  const handleExportPDF = async () => {
    if (!reportRef.current) return;
    const buttons = document.getElementById("pdf-action-buttons");
    if (buttons) buttons.style.display = "none";
    try {
      const canvas = await html2canvas(reportRef.current, { scale: 2, useCORS: true, backgroundColor: "#ffffff" });
      const pdf = new jsPDF("p", "mm", "a4");
      const w = pdf.internal.pageSize.getWidth();
      pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, w, (canvas.height * w) / canvas.width);
      pdf.save("EviMatch_Screening_Report.pdf");
    } finally {
      if (buttons) buttons.style.display = "flex";
    }
  };

  return (
    <main className="min-h-screen p-8 md:p-24 space-y-12 bg-gradient-to-br from-background to-muted/30 dark:from-background dark:to-muted/10 transition-colors duration-300">
      <div className="absolute top-4 right-4 md:top-8 md:right-8">
        <ThemeToggle />
      </div>
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">EviMatch</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Evidence-grounded resume screening. Every score comes with the resume sentences that support it, names
            and other identity cues are removed before scoring, and a bias check shows what redaction leaves behind.
          </p>
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <section className="flex flex-col items-center space-y-6 mt-6">
            <UploadCard onUpload={handleUpload} isLoading={isLoading} />
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input type="checkbox" checked={redact} onChange={(e) => setRedact(e.target.checked)} />
              Remove names, contact details, institutions and pronouns before scoring (recommended)
            </label>
            {error && (
              <div className="w-full max-w-md bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm text-center">
                {error}
              </div>
            )}
            <div className="flex items-center gap-4">
              <button
                onClick={() => file && void run(file, jobDescription)}
                disabled={!file || jobDescription.trim().split(/\s+/).length < 25}
                className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-full font-semibold hover:bg-primary/90 transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
              >
                <CheckCircle className="w-5 h-5" /> Analyze resume
              </button>
              <button
                onClick={handleDemo}
                className="flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-full font-semibold hover:bg-foreground/90 transition-all shadow-lg active:scale-95"
              >
                <Play className="w-5 h-5" /> Run sample
              </button>
            </div>
            <p className="text-xs text-muted-foreground max-w-xl text-center">
              Decision support only. Resumes are processed in memory and are not stored. A person must review the
              evidence before any hiring outcome.
            </p>
          </section>
        )}

        {results && file && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700" ref={reportRef}>
            <div id="pdf-action-buttons" className="flex justify-between items-center bg-card p-4 rounded-2xl border shadow-sm">
              <h3 className="font-bold text-lg">Screening report{results.filename ? ` - ${results.filename}` : ""}</h3>
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors text-sm"
              >
                <Download className="w-4 h-4" /> Download PDF
              </button>
            </div>

            <SummaryRow matchScore={results.fit_score} decision={results.decision} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <CandidateFitPanel
                summary={results.summary}
                narrative={results.narrative}
                warnings={results.warnings}
                redactionCounts={results.redaction.counts}
                redactionApplied={results.redaction.applied}
              />
              <DriversPanel groupEffects={results.group_effects} drivers={results.drivers} />
            </div>

            <RequirementsPanel requirements={results.requirements} counts={results.requirement_counts} />
            <SkillMatchPanel matchingSkills={results.matching_skills} missingSkills={results.missing_skills} />
            <AuditPanel file={file} jobDescription={jobDescription} redact={redact} />
          </div>
        )}
      </div>
    </main>
  );
}
