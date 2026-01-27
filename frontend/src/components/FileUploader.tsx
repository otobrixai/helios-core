"use client";

import { useCallback } from "react";

interface FileUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export function FileUploader({ onUpload, isUploading }: FileUploaderProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) onUpload(file);
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
    },
    [onUpload]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className={`
        relative border-2 border-dashed rounded-lg p-6 text-center
        transition-all duration-200 cursor-pointer
        ${
          isUploading
            ? "border-(--accent-cyan) bg-(--accent-cyan)/5"
            : "border-(--border-default) hover:border-(--accent-cyan) hover:bg-(--bg-tertiary)"
        }
      `}
    >
      <input
        type="file"
        accept=".csv,.txt,.xls,.xlsx"
        onChange={handleChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={isUploading}
      />

      {isUploading ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-(--accent-cyan) border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-(--accent-cyan)">Processing...</span>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          {/* Upload Icon */}
          <svg
            className="w-8 h-8 text-(--text-muted)"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <span className="text-sm text-(--text-secondary)">
            Drop IV file or <span className="text-(--accent-cyan)">browse</span>
          </span>
          <span className="text-xs text-(--text-muted)">
            CSV, TXT, XLS supported
          </span>
        </div>
      )}
    </div>
  );
}
