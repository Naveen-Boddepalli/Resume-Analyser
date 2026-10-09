export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Decision = "Shortlist" | "Review" | "Reject";

export interface RequirementEvidence {
  requirement: string;
  kind: "required" | "preferred" | "duty" | "other";
  status: "met" | "partial" | "unmet";
  similarity: number;
  evidence: string | null;
}

export interface SkillEvidence {
  skill: string;
  evidence: string;
}

export interface Driver {
  feature: string;
  group: string;
  effect: number;
}

export interface AnalysisResult {
  fit_score: number;
  decision: Decision;
  probabilities: Record<string, number>;
  requirements: RequirementEvidence[];
  requirement_counts: { met: number; partial: number; unmet: number };
  matching_skills: SkillEvidence[];
  missing_skills: string[];
  experience: { candidate_years: number; required_years: number; meets: boolean };
  education: { candidate_level: number; required_level: number; meets: boolean };
  drivers: Driver[];
  group_effects: Record<string, number>;
  redaction: { applied: boolean; counts: Record<string, number> };
  summary: string;
  narrative?: string;
  warnings: string[];
  filename?: string;
}

export interface AuditResult {
  redaction_applied: boolean;
  baseline_score: number;
  name_cell_scores: Record<string, number>;
  name_spread: number;
  proxy_cues: { cue: string; reference: string; score_change: number; decision_changed: boolean }[];
  decision_at_baseline: Decision;
  interpretation: string;
}

function headers(): HeadersInit {
  const key = process.env.NEXT_PUBLIC_API_KEY;
  return key ? { "X-API-Key": key } : {};
}

async function post<T>(path: string, file: File, jobDescription: string, redact: boolean): Promise<T> {
  const body = new FormData();
  body.append("file", file);
  body.append("job_description", jobDescription);
  body.append("redact", String(redact));
  const res = await fetch(`${API_URL}${path}`, { method: "POST", headers: headers(), body });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = typeof err.detail === "string" ? err.detail : `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const analyze = (file: File, jd: string, redact: boolean) =>
  post<AnalysisResult>("/analyze", file, jd, redact);

export const audit = (file: File, jd: string, redact: boolean) =>
  post<AuditResult>("/audit", file, jd, redact);
