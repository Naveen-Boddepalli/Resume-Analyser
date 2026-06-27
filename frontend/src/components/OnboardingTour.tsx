"use client";

import React, { useEffect, useState } from "react";
import { Joyride, Step, STATUS } from "react-joyride";

interface OnboardingTourProps {
  hasAnalyzed: boolean;
}

export function OnboardingTour({ hasAnalyzed }: OnboardingTourProps) {
  const [runPre, setRunPre] = useState(false);
  const [runPost, setRunPost] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;

    // Check if we should run the pre-analysis tour
    const seenPre = localStorage.getItem("hasSeenUploadTour");
    if (!seenPre && !hasAnalyzed) {
      setRunPre(true);
    } else if (hasAnalyzed) {
      setRunPre(false); // Stop pre tour if they analyze early
    }

    // Check if we should run the post-analysis tour
    if (hasAnalyzed) {
      const seenPost = localStorage.getItem("hasSeenResultsTour");
      if (!seenPost) {
        // slight delay to let DOM render
        const timer = setTimeout(() => setRunPost(true), 800);
        return () => clearTimeout(timer);
      }
    }
  }, [hasAnalyzed, isMounted]);

  const preAnalysisSteps: Step[] = [
    {
      target: "#tour-upload",
      content: "Welcome! Start by uploading your resume here. We accept PDF, DOCX, and TXT files.",
      skipBeacon: true,
    },
    {
      target: "#tour-analyze",
      content: "Once uploaded, click here to get your AI-powered readiness score.",
      skipBeacon: true,
    },
    {
      target: "#tour-demo",
      content: "Or, if you don't have a resume handy, run our live demo to see how it works!",
      skipBeacon: true,
    }
  ];

  const postAnalysisSteps: Step[] = [
    {
      target: "#tour-probability",
      content: "This is your estimated placement probability and expected salary range based on current market data.",
      skipBeacon: true,
    },
    {
      target: "#tour-waterfall",
      content: "The Impact Waterfall shows exactly how your specific skills pushed your score up or down.",
      skipBeacon: true,
    },
    {
      target: "#tour-whatif",
      content: "Play with these sliders to instantly see how learning new skills or doing more projects changes your score.",
      skipBeacon: true,
    },
    {
      target: "#tour-roadmap",
      content: "Finally, follow this week-by-week AI generated action plan to land your dream job!",
      skipBeacon: true,
    }
  ];

  const handlePreJoyrideCallback = (data: any) => {
    const { status } = data;
    if (([STATUS.FINISHED, STATUS.SKIPPED] as string[]).includes(status)) {
      localStorage.setItem("hasSeenUploadTour", "true");
      setRunPre(false);
    }
  };

  const handlePostJoyrideCallback = (data: any) => {
    const { status } = data;
    if (([STATUS.FINISHED, STATUS.SKIPPED] as string[]).includes(status)) {
      localStorage.setItem("hasSeenResultsTour", "true");
      setRunPost(false);
    }
  };

  const commonStyles = {
    options: {
      primaryColor: "#2563eb", // blue-600
      zIndex: 10000,
    },
    tooltipContainer: {
      textAlign: "left" as const,
      borderRadius: "0.75rem",
    },
    buttonNext: {
      borderRadius: "0.5rem",
      fontWeight: 600,
    },
    buttonBack: {
      marginRight: "0.5rem",
    },
  };

  const commonLocale = { back: '<', next: '>', skip: 'Skip', last: 'Finish' };

  if (!isMounted) return null;

  return (
    <>
      <Joyride
        steps={preAnalysisSteps}
        run={runPre}
        continuous
        onEvent={handlePreJoyrideCallback}
        styles={commonStyles}
        locale={commonLocale}
      />
      <Joyride
        steps={postAnalysisSteps}
        run={runPost}
        continuous
        onEvent={handlePostJoyrideCallback}
        styles={commonStyles}
        locale={commonLocale}
      />
    </>
  );
}
