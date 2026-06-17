import React, { useState, useEffect } from "react";
import { X, Code, MessageSquare, CheckCircle } from "lucide-react";

export type AssessmentType = "coding" | "communication";

interface AssessmentModalProps {
  isOpen: boolean;
  type: AssessmentType;
  onClose: () => void;
  onComplete: (score: number, type: AssessmentType) => void;
}

const CODING_QUESTIONS = [
  {
    question: "What is the time complexity of searching for an element in a balanced Binary Search Tree?",
    options: ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
    answerIndex: 2
  },
  {
    question: "Which of the following sorting algorithms has the best average-case time complexity?",
    options: ["Bubble Sort", "Insertion Sort", "Selection Sort", "Merge Sort"],
    answerIndex: 3
  },
  {
    question: "In object-oriented programming, what does polymorphism refer to?",
    options: [
      "Hiding the internal state and requiring all interaction to be performed through an object's methods",
      "The ability of different classes to respond to the same method call in their own way",
      "Creating a new class based on an existing class",
      "The process of creating an instance of a class"
    ],
    answerIndex: 1
  },
  {
    question: "What is a primary advantage of using a RESTful API architecture?",
    options: [
      "It maintains a persistent connection between client and server",
      "It is stateful, meaning the server remembers client state between requests",
      "It uses standard HTTP methods, making it stateless and scalable",
      "It requires XML for data formatting"
    ],
    answerIndex: 2
  },
  {
    question: "Which data structure uses LIFO (Last In, First Out) principle?",
    options: ["Queue", "Stack", "Linked List", "Tree"],
    answerIndex: 1
  }
];

const COMMUNICATION_QUESTIONS = [
  {
    question: "When explaining a complex technical concept to a non-technical stakeholder, what is the best approach?",
    options: [
      "Use precise technical jargon to ensure accuracy.",
      "Use analogies and focus on the business impact or high-level function.",
      "Send them a link to the API documentation.",
      "Avoid explaining the details and just say it works."
    ],
    answerIndex: 1
  },
  {
    question: "During a code review, you notice a significant flaw in a colleague's code. How should you address it?",
    options: [
      "Fix it yourself without telling them to save time.",
      "Leave a comment pointing out the flaw and constructively suggesting an alternative approach.",
      "Approve the PR but send them a private message telling them their code is bad.",
      "Reject the PR immediately with a comment 'Fix this'."
    ],
    answerIndex: 1
  },
  {
    question: "You realize you will not be able to meet a sprint deadline. When should you communicate this?",
    options: [
      "On the day of the deadline, so you have maximum time to try and finish.",
      "As soon as you realize the deadline is at risk.",
      "Wait for the project manager to ask about your progress.",
      "During the sprint retrospective after the deadline has passed."
    ],
    answerIndex: 1
  },
  {
    question: "What is active listening?",
    options: [
      "Listening while simultaneously working on your code.",
      "Waiting for your turn to speak and planning your response.",
      "Fully concentrating, understanding, responding, and remembering what is being said.",
      "Interrupting the speaker to show you understand their point."
    ],
    answerIndex: 2
  },
  {
    question: "How should you prepare for a daily stand-up meeting?",
    options: [
      "You don't need to prepare, just say what comes to mind.",
      "Prepare a detailed 10-minute presentation of your work.",
      "Briefly review what you did yesterday, what you plan to do today, and identify any blockers.",
      "Focus only on discussing the problems of other team members."
    ],
    answerIndex: 2
  }
];

export function AssessmentModal({ isOpen, type, onClose, onComplete }: AssessmentModalProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const questions = type === "coding" ? CODING_QUESTIONS : COMMUNICATION_QUESTIONS;
  const title = type === "coding" ? "Coding Assessment" : "Communication Assessment";
  const Icon = type === "coding" ? Code : MessageSquare;

  // Initialize or reset answers when the modal opens or type changes
  useEffect(() => {
    if (isOpen) {
      setAnswers(Array(questions.length).fill(-1));
      setCurrentQuestionIndex(0);
      setIsSubmitted(false);
    }
  }, [isOpen, type, questions.length]);

  if (!isOpen) return null;

  const handleOptionSelect = (index: number) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = index;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = () => {
    let correctCount = 0;
    answers.forEach((ans, i) => {
      if (ans === questions[i].answerIndex) {
        correctCount++;
      }
    });
    const score = Math.round((correctCount / questions.length) * 100);
    setIsSubmitted(true);
    
    // Give user a moment to see their score before closing
    setTimeout(() => {
      onComplete(score, type);
      onClose();
    }, 2000);
  };

  const currentQuestion = questions[currentQuestionIndex];
  
  // Calculate a temporary score if submitted to show the user
  const currentScore = answers.reduce((acc, ans, i) => acc + (ans === questions[i]?.answerIndex ? 1 : 0), 0);
  const finalPercentage = Math.round((currentScore / questions.length) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-card w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <h2 className="text-xl font-bold">{title}</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-muted rounded-full transition-colors">
            <X className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>

        <div className="p-6">
          {isSubmitted ? (
            <div className="flex flex-col items-center justify-center py-10 space-y-4">
              <CheckCircle className="w-16 h-16 text-green-500 mb-2" />
              <h3 className="text-2xl font-bold">Assessment Complete!</h3>
              <p className="text-muted-foreground text-center">
                You scored {finalPercentage}%. Your new score is being applied to the AI analysis...
              </p>
            </div>
          ) : (
            <>
              <div className="flex justify-between text-sm font-medium text-muted-foreground mb-4">
                <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
                <span>{Math.round((answers.filter(a => a !== -1).length / questions.length) * 100)}% Answered</span>
              </div>
              
              <div className="w-full bg-muted h-2 rounded-full mb-8">
                <div 
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
                />
              </div>

              {currentQuestion && (
                <>
                  <h3 className="text-lg font-semibold mb-6">{currentQuestion.question}</h3>

                  <div className="space-y-3 mb-8">
                    {currentQuestion.options.map((opt, i) => (
                      <button
                        key={i}
                        onClick={() => handleOptionSelect(i)}
                        className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                          answers[currentQuestionIndex] === i 
                            ? "border-primary bg-primary/5 text-primary font-medium" 
                            : "border-muted hover:border-primary/50 text-foreground"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </>
              )}

              <div className="flex justify-between pt-4 border-t">
                <button
                  onClick={handlePrevious}
                  disabled={currentQuestionIndex === 0}
                  className="px-6 py-2 rounded-lg font-medium hover:bg-muted disabled:opacity-50 transition-colors text-foreground"
                >
                  Previous
                </button>
                
                {currentQuestionIndex === questions.length - 1 ? (
                  <button
                    onClick={handleSubmit}
                    disabled={answers.includes(-1)}
                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    Submit Assessment
                  </button>
                ) : (
                  <button
                    onClick={handleNext}
                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                  >
                    Next
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
