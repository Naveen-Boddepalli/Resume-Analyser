import React from "react";
import { CheckCircle, XCircle } from "lucide-react";
import type { SkillEvidence } from "@/lib/api";

interface SkillMatchPanelProps {
  matchingSkills: SkillEvidence[];
  missingSkills: string[];
}

export function SkillMatchPanel({ matchingSkills, missingSkills }: SkillMatchPanelProps) {
  return (
    <div className="w-full bg-card border rounded-2xl p-6 shadow-sm h-full">
      <h3 className="text-xl font-bold mb-6">Skills</h3>
      <div className="grid grid-cols-1 gap-8">
        <div>
          <h4 className="text-lg font-semibold text-green-600 dark:text-green-400 flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5" aria-hidden /> Evidenced in the resume
          </h4>
          {matchingSkills.length > 0 ? (
            <ul className="space-y-2">
              {matchingSkills.map((s) => (
                <li
                  key={s.skill}
                  className="text-sm text-foreground bg-green-50 dark:bg-green-900/20 p-2 rounded-md border border-green-200 dark:border-green-900/50"
                >
                  <span className="font-medium">{s.skill}</span>
                  <span className="block text-xs text-muted-foreground mt-1 italic">{s.evidence}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No listed skills were found in the resume.</p>
          )}
        </div>
        <div>
          <h4 className="text-lg font-semibold text-red-600 dark:text-red-400 flex items-center gap-2 mb-3">
            <XCircle className="w-5 h-5" aria-hidden /> Asked for, no evidence found
          </h4>
          {missingSkills.length > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {missingSkills.map((s) => (
                <li
                  key={s}
                  className="text-sm text-foreground bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded-md border border-red-200 dark:border-red-900/50"
                >
                  {s}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Every skill named in the posting has evidence.</p>
          )}
        </div>
      </div>
    </div>
  );
}
