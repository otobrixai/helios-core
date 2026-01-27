"use client";

import React from "react";
import { AnalysisMode } from "@/types/stateless";
import { DiagnosticSidebar } from "./DiagnosticSidebar";
import { FullDiagnosticReport } from "../types/diagnostics";

interface ProgressiveDiagnosticsProps {
  diagnosticReport: FullDiagnosticReport | null;
  mode: AnalysisMode;
  onViewReport?: () => void;
  onDownloadAudit?: () => void;
  isLoading?: boolean;
}

export const ProgressiveDiagnostics: React.FC<ProgressiveDiagnosticsProps> = ({
  diagnosticReport,
  mode,
  onViewReport,
  onDownloadAudit,
  isLoading = false
}) => {
  return (
    <div className="relative h-full flex flex-col">
       {/* Use Sidebar with real data from the stateless session */}
      <DiagnosticSidebar
        diagnosticReport={diagnosticReport}
        mode={mode}
        isLoading={isLoading}
        onViewReport={onViewReport}
        onDownloadAudit={onDownloadAudit}
      />
      {!diagnosticReport && !isLoading && (
        <div className="absolute inset-x-0 bottom-0 p-4 bg-(--bg-secondary) border-t border-(--border-default) text-[10px] text-(--text-muted) italic text-center">
          Run analysis to generate physics audit
        </div>
      )}
    </div>
  );
};
