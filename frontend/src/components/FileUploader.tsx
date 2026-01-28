"use client";

import { useState, useCallback } from "react";
import { MeasurementType } from "@/types/stateless";

interface FileUploaderProps {
  onUpload: (file: File, type: MeasurementType) => void;
  isUploading: boolean;
}

export function FileUploader({ onUpload, isUploading }: FileUploaderProps) {
  const [type, setType] = useState<MeasurementType>("light");

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) onUpload(file, type);
    },
    [onUpload, type]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file, type);
    },
    [onUpload, type]
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
        accept=".csv,.txt,.xls,.xlsx,.data,.dat,.asc,text/*"
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
            CSV, TXT, XLS, DAT, DATA, ASC supported
          </span>
        </div>
      )}

      {/* Type Selector */}
      <div className="absolute bottom-0 left-0 right-0 h-8 flex items-center justify-center gap-4 bg-(--bg-secondary)/80 backdrop-blur-sm border-t border-(--border-default) rounded-b-lg pointer-events-auto">
        {(['light', 'dark', 'suns_voc'] as const).map((t) => (
          <label key={t} className="flex items-center gap-1.5 cursor-pointer z-10" onClick={(e) => e.stopPropagation()}>
            <input 
              type="radio" 
              name="meas-type" 
              checked={type === t} 
              onChange={() => setType(t)}
              className="w-3 h-3 accent-(--accent-cyan)"
            />
            <span className={`text-[10px] font-bold uppercase tracking-wider ${type === t ? 'text-(--accent-cyan)' : 'text-(--text-muted)'}`}>
              {t.replace('_', '-')}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
