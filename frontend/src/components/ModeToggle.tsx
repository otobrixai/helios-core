"use client";

import { AnalysisMode } from "@/types/stateless";

interface ModeToggleProps {
  mode: AnalysisMode;
  onModeChange: (mode: AnalysisMode) => void;
}

export function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
  const isReference = mode === "Reference";

  return (
    <div className="flex items-center gap-3">
      <span
        className={`text-sm font-medium transition-colors ${
          !isReference ? "text-(--accent-cyan)" : "text-(--text-muted)"
        }`}
      >
        Exploration
      </span>

      {/* Physical Toggle Switch */}
      <button
        onClick={() => onModeChange(isReference ? "Exploration" : "Reference")}
        className={`relative w-16 h-8 rounded-full transition-all duration-300 ${
          isReference
            ? "bg-linear-to-r from-(--accent-gold) to-(--accent-amber) neon-glow-gold"
            : "bg-(--bg-tertiary) border border-(--border-default)"
        }`}
        aria-label={`Switch to ${isReference ? "Exploration" : "Reference"} mode`}
      >
        {/* Toggle Knob */}
        <span
          className={`absolute top-1 w-6 h-6 rounded-full shadow-lg transition-all duration-300 ${
            isReference
              ? "left-9 bg-white"
              : "left-1 bg-(--accent-cyan)"
          }`}
        >
          {/* Inner Light */}
          <span
            className={`absolute inset-1 rounded-full ${
              isReference
                ? "bg-(--accent-gold)"
                : "bg-(--accent-cyan) opacity-50"
            }`}
          />
        </span>

        {/* Lock Icon for Reference Mode */}
        {isReference && (
          <svg
            className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/80"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        )}
      </button>

      <span
        className={`text-sm font-medium transition-colors ${
          isReference ? "text-(--accent-gold)" : "text-(--text-muted)"
        }`}
      >
        Reference
      </span>
    </div>
  );
}
