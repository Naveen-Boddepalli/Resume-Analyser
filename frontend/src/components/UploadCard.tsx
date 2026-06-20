"use client";

import React, { useState } from "react";
import { UploadCloud, CheckCircle, Loader2 } from "lucide-react";

interface UploadCardProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
  title?: string;
}

export function UploadCard({ onUpload, isLoading = false, title }: UploadCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      onUpload(file);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      onUpload(file);
    }
  };

  return (
    <div className="w-full flex flex-col items-center">
      {title && <h3 className="text-lg font-bold text-foreground mb-3">{title}</h3>}
      <div
        className={`relative w-full max-w-xl mx-auto rounded-xl border-2 border-dashed p-10 transition-all duration-300 ${
          isDragging
            ? "border-primary bg-primary/5 scale-[1.02] shadow-md"
            : "border-border bg-card hover:border-primary/50 hover:scale-[1.02] hover:shadow-lg hover:bg-muted/30"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
      <div className="flex flex-col items-center justify-center text-center space-y-4">
        {isLoading ? (
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
        ) : selectedFile ? (
          <CheckCircle className="w-12 h-12 text-green-500" />
        ) : (
          <UploadCloud className="w-12 h-12 text-muted-foreground" />
        )}

        <div>
          <p className="text-lg font-medium text-foreground">
            {selectedFile ? selectedFile.name : "Drag & drop your resume"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {selectedFile
              ? "File ready to be analyzed"
              : "PDF, DOCX, or TXT up to 5MB"}
          </p>
        </div>

        {!isLoading && (
          <label className="relative cursor-pointer bg-primary text-primary-foreground px-6 py-2 rounded-md font-medium hover:bg-primary/90 transition-colors">
            <span>Browse Files</span>
            <input
              type="file"
              className="sr-only"
              accept=".pdf,.docx,.txt"
              onChange={handleChange}
            />
          </label>
        )}
      </div>
    </div>
    </div>
  );
}
