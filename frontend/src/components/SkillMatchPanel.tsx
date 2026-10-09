import React from "react";
import { CheckCircle, XCircle } from "lucide-react";

interface SkillMatchPanelProps {
  matchingSkills: string[];
  missingSkills: string[];
}

export function SkillMatchPanel({ matchingSkills, missingSkills }: SkillMatchPanelProps) {
  return (
    <div className="w-full max-w-4xl mx-auto bg-card border rounded-2xl p-6 shadow-sm">
      <h3 className="text-xl font-bold mb-6">Skills Analysis</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h4 className="text-lg font-semibold text-green-600 dark:text-green-400 flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5" /> Matching Skills
          </h4>
          {matchingSkills.length > 0 ? (
            <ul className="space-y-2">
              {matchingSkills.map((skill, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-foreground bg-green-50 dark:bg-green-900/20 p-2 rounded-md border border-green-200 dark:border-green-900/50">
                  <span className="w-2 h-2 rounded-full bg-green-500 shrink-0"></span>
                  {skill}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No matching skills found.</p>
          )}
        </div>

        <div>
          <h4 className="text-lg font-semibold text-red-600 dark:text-red-400 flex items-center gap-2 mb-4">
            <XCircle className="w-5 h-5" /> Missing Skills
          </h4>
          {missingSkills.length > 0 ? (
            <ul className="space-y-2">
              {missingSkills.map((skill, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-foreground bg-red-50 dark:bg-red-900/20 p-2 rounded-md border border-red-200 dark:border-red-900/50">
                  <span className="w-2 h-2 rounded-full bg-red-500 shrink-0"></span>
                  {skill}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No missing critical skills found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
