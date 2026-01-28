"use client";

import { useState } from "react";
import { useHeliosStore } from "@/lib/helios-store";
import { exportSessionBundle } from "@/lib/export-utils";
import { 
  AnalysisMode as StatelessMode, 
  MeasurementSessionData,
  AnalysisSessionData,
  MeasurementType
} from "@/types/stateless";

import { BatchManager } from "@/components/BatchManager";
import { AnalysisHub } from "@/components/AnalysisHub";
import { ParameterInspector } from "@/components/ParameterInspector";
import { ModeToggle } from "@/components/ModeToggle";
import { FileUploader } from "@/components/FileUploader";
import { AuditLogModal } from "@/components/AuditLogModal";

import { ProgressiveDiagnostics } from "@/components/ProgressiveDiagnostics";
import { PerformanceShield } from "@/components/PerformanceShield";
import { getApiUrl } from "@/lib/api-config";



export default function Home() {
  const {
    measurements,
    analyses,
    currentMeasurementId,
    currentAnalysisId,
    setCurrentMeasurement,
    addMeasurement,
    addAnalysis,
    isLoading,
    setLoading,
    setError
  } = useHeliosStore();

  const [mode, setMode] = useState<StatelessMode>("Exploration");
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  // Constants State (Locked in Reference Mode)
  const [constants, setConstants] = useState({
    bandgap: 1.4,
    temperature: 298.15,
    area: 1.0,
  });

  const selectedMeasurement = measurements.find(m => m.id === currentMeasurementId) || null;
  const analysisResult = analyses.find(a => a.id === currentAnalysisId) || null;



  const handleFileUpload = async (file: File, type: MeasurementType = "light") => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(getApiUrl("/api/stateless/process"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      
      // Update global session constants if area detected in file
      if (data.detected_area) {
        setConstants(prev => ({ ...prev, area: data.detected_area }));
      }

      data.measurements.forEach((m: {
        device_label: string;
        voltage: number[];
        current: number[];
        v_column: string;
        i_column: string;
      }) => {
        const measurement: MeasurementSessionData = {
          id: `meas_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          filename: data.filename,
          fileHash: data.file_hash,
          deviceLabel: m.device_label,
          voltage: m.voltage,
          current: m.current,
          vColumn: m.v_column,
          iColumn: m.i_column,
          areaCm2: data.detected_area ?? constants.area,
          temperatureK: constants.temperature,
          measurementType: type,
          timestamp: new Date().toISOString()
        };
        addMeasurement(measurement);
      });
      
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      console.error("Upload error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (area?: number, temp?: number) => {
    if (!selectedMeasurement) return;

    setLoading(true);
    try {
      const response = await fetch(getApiUrl("/api/stateless/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voltage: selectedMeasurement.voltage,
          current: selectedMeasurement.current,
          device_label: selectedMeasurement.deviceLabel,
          mode: mode,
          model_type: "OneDiode",
          area_cm2: area ?? constants.area,
          temperature_k: temp ?? constants.temperature,
          measurement_type: selectedMeasurement.measurementType
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Analysis failed");
      }

      const data = await response.json();
      
      const analysis: AnalysisSessionData = {
        id: `ana_${Date.now()}`,
        measurementId: selectedMeasurement.id,
        status: data.status,
        mode: data.mode as StatelessMode,
        modelType: 'OneDiode',
        results: data.status === 'VALID' ? {
          j_sc: data.j_sc,
          v_oc: data.v_oc,
          ff: data.ff,
          pce: data.pce,
          r_s: data.r_s,
          r_sh: data.r_sh,
          n_ideality: data.n_ideality,
          n_slope: data.n_slope,
          n_dark: data.n_dark,
          i_0_dark: data.i_0_dark,
          r_s_dark: data.r_s_dark,
          r_sh_dark: data.r_sh_dark,
        } : undefined,
        resultHash: data.result_hash,
        fit_current: data.fit_current,
        errorMessage: data.error_message,
        timestamp: data.timestamp,
        diagnostics: data.diagnostics
      };
      
      addAnalysis(analysis);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      console.error("Analysis error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportBundle = async () => {
    if (measurements.length === 0) return;
    await exportSessionBundle(measurements, analyses);
  };

  return (
    <main className="h-screen w-full flex flex-col bg-(--bg-primary) overflow-hidden">
      {/* Global Header */}
      <header className="h-14 border-b border-(--border-default) px-6 flex items-center justify-between bg-(--bg-secondary) shrink-0 z-20">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-(--accent-cyan)">Helios</span>
            <span className="text-(--text-primary)">Core</span>
          </h1>
          <span className="text-[10px] text-(--accent-cyan) border border-(--accent-cyan)/30 bg-(--accent-cyan)/10 px-2 py-0.5 rounded uppercase tracking-wider">
            Instrument v1.0
          </span>
        </div>

        <div className="flex items-center gap-6">
          <ModeToggle mode={mode} onModeChange={setMode} />
          
          <button
            onClick={() => setShowDiagnostics(!showDiagnostics)}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition-all
              ${showDiagnostics 
                ? "bg-(--accent-cyan)/20 text-(--accent-cyan) border border-(--accent-cyan)/40" 
                : "bg-(--bg-tertiary) text-(--text-secondary) border border-(--border-default) hover:border-(--text-muted)"
              }
            `}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Physics Audit
          </button>

          {mode === "Reference" && (
            <div className="flex items-center gap-2 px-3 py-1 bg-(--accent-gold)/10 border border-(--accent-gold)/30 rounded-full animate-pulse-slow">
              <span className="w-2 h-2 rounded-full bg-(--accent-gold)" />
              <span className="text-xs font-semibold text-(--accent-gold) uppercase tracking-wide">
                Reference Listed
              </span>
            </div>
          )}
        </div>
      </header>

      {/* 3-Column Command Center Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Column 1: Inventory & Provenance */}
        <aside className="w-64 bg-(--bg-secondary) border-r border-(--border-default) flex flex-col shrink-0">
          <div className="p-3 border-b border-(--border-default)">
            <h2 className="text-[10px] font-semibold text-(--text-muted) uppercase tracking-wider mb-2 px-1">
              Input Source
            </h2>
            <FileUploader onUpload={handleFileUpload} isUploading={isLoading} />
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <BatchManager
              measurements={measurements}
              selectedId={currentMeasurementId}
              onSelect={setCurrentMeasurement}
              mode={mode}
            />
          </div>

          {/* Session Constants Panel */}
          <div className="p-3 border-t border-(--border-default) bg-(--bg-tertiary)">
            <h3 className="text-[10px] font-semibold text-(--text-muted) uppercase tracking-wider mb-2 flex justify-between px-1">
              Session Constants
              {mode === "Reference" && (
                <span className="text-(--accent-gold)">🔒</span>
              )}
            </h3>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="flex flex-col gap-1">
                <label className="text-(--text-secondary)">Area (cm²)</label>
                <input 
                  type="number" 
                  value={constants.area}
                  onChange={(e) => setConstants({ ...constants, area: parseFloat(e.target.value) || 0 })}
                  disabled={mode === "Reference"}
                  className="bg-(--bg-card) border border-(--border-default) rounded px-1.5 py-1 text-(--text-primary) disabled:opacity-50"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-(--text-secondary)">Temp (K)</label>
                <input 
                  type="number" 
                  value={constants.temperature}
                  onChange={(e) => setConstants({ ...constants, temperature: parseFloat(e.target.value) || 0 })}
                  disabled={mode === "Reference"}
                  className="bg-(--bg-card) border border-(--border-default) rounded px-1.5 py-1 text-(--text-primary) disabled:opacity-50"
                />
              </div>
            </div>
          </div>
        </aside>

        {/* Column 2: Visual Analysis Hub */}
        <main className="flex-1 min-w-[350px] bg-(--bg-primary) border-r border-(--border-default) relative z-0 overflow-y-auto">
          <AnalysisHub
            measurement={selectedMeasurement}
            result={analysisResult}
            mode={mode}
            constants={constants}
            onAnalyze={handleAnalyze}
          />
        </main>

        {/* Column 3: Parameter Inspector */}
        <aside className="w-72 xl:w-80 bg-(--bg-secondary) shrink-0 z-10 shadow-xl overflow-hidden flex flex-col">
          <ParameterInspector
            result={analysisResult}
            mode={mode}
            onExport={handleExportBundle}
          >
            <PerformanceShield 
              visible={true} 
              dataPointCount={measurements.length} 
            />
          </ParameterInspector>
        </aside>

        {/* Column 4: Diagnostic Sidebar (Physics Audit) */}
        <div className={`
          overflow-hidden transition-all duration-300 ease-in-out border-l border-(--border-default)
          ${showDiagnostics ? "w-80 opacity-100" : "w-0 opacity-0 border-none"}
        `}>
          <div className="w-80">
            <ProgressiveDiagnostics 
              diagnosticReport={analysisResult?.diagnostics || null}
              mode={mode}
              isLoading={isLoading}
              onViewReport={() => setIsAuditModalOpen(true)}
              onDownloadAudit={handleExportBundle}
            />
          </div>
        </div>

        {/* Audit Log Modal Overlay */}
        <AuditLogModal
          isOpen={isAuditModalOpen}
          onClose={() => setIsAuditModalOpen(false)}
          report={analysisResult?.diagnostics || null}
        />

      </div>
    </main>
  );
}
