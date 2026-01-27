"use client";

import { AnalysisMode, AnalysisSessionData } from "@/types/stateless";
import { Info } from "lucide-react";

interface ParameterInspectorProps {
  result: AnalysisSessionData | null;
  mode: AnalysisMode;
  onExport: () => void;
  children?: React.ReactNode;
}

interface MetricCardProps {
  label: string;
  value: number | string | undefined;
  unit: string;
  warning?: boolean;
  isReference: boolean;
  tooltipEquation?: string;
}

function MetricCard({ label, value, unit, warning, isReference, tooltipEquation }: MetricCardProps) {
  let displayValue = "—";
  if (value !== undefined) {
    const val = typeof value === "number" ? value : parseFloat(value);
    if (isNaN(val)) {
      displayValue = "—";
    } else if (Math.abs(val) > 10000) {
      displayValue = val.toExponential(4);
    } else {
      displayValue = val.toFixed(4);
    }
  }
  return (
    <div className={`metric-card group relative ${warning ? "warning-amber" : ""}`}>
      {/* Math Overlay Tooltip */}
      {tooltipEquation && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/90 text-white text-xs p-2 rounded pointer-events-none whitespace-nowrap z-10 border border-white/10">
          {tooltipEquation}
        </div>
      )}
      
      <div className="flex items-baseline gap-1">
        <span
          className={`metric-value ${
            warning
              ? "text-(--accent-amber)"
              : isReference
              ? "text-(--accent-gold)"
              : "text-(--accent-cyan)"
          }`}
        >
          {displayValue}
        </span>
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-label flex items-center gap-1">
        {label}
        {tooltipEquation && <Info className="w-3 h-3 text-(--text-muted) opacity-50" />}
      </div>
    </div>
  );
}

export function ParameterInspector({
  result,
  mode,
  onExport,
  children,
}: ParameterInspectorProps) {
  const isReference = mode === "Reference";
  const metrics = result?.results;

  return (
    <div className="p-4 flex flex-col h-full border-l border-(--border-default) bg-(--bg-secondary) overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xs font-semibold text-(--text-muted) uppercase tracking-wider">
          Parameter Inspector
        </h2>
        {isReference && (
          <span className="text-[10px] bg-(--accent-gold)/10 text-(--accent-gold) px-2 py-0.5 rounded border border-(--accent-gold)/20">
            LOCKED
          </span>
        )}
      </div>

      {/* Primary Metrics */}
      <div className="space-y-3 mb-8">
        <h3 className="text-xs font-medium text-(--text-muted) flex items-center gap-2">
          Extracted Metrics
          <span className="h-px flex-1 bg-(--border-default)" />
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            label="Voc"
            value={metrics?.v_oc}
            unit="V"
            isReference={isReference}
            tooltipEquation="V_{oc} = \frac{nkT}{q} \ln(\frac{I_{ph}}{I_0} + 1)"
          />
          <MetricCard
            label="Jsc"
            value={metrics?.j_sc}
            unit="mA/cm²"
            isReference={isReference}
            tooltipEquation="J_{sc} \approx J_{ph}"
          />
          <MetricCard
            label="Fill Factor"
            value={metrics?.ff !== undefined ? metrics.ff * 100 : undefined}
            unit="%"
            isReference={isReference}
            tooltipEquation="FF = \frac{P_{mpp}}{V_{oc} J_{sc}}"
          />
          <MetricCard
            label="Efficiency"
            value={metrics?.pce}
            unit="%"
            isReference={isReference}
            tooltipEquation="\eta = \frac{P_{mpp}}{P_{in}}"
          />
          <MetricCard
            label="Series Res."
            value={metrics?.r_s}
            unit="Ω·cm²"
            isReference={isReference}
          />
          <MetricCard
            label="Shunt Res."
            value={metrics?.r_sh}
            unit="Ω·cm²"
            isReference={isReference}
          />
        </div>
      </div>

      {/* Physics Health Check Table */}
      <div className="space-y-3 mb-8">
        <h3 className="text-xs font-medium text-(--text-muted) flex items-center gap-2">
          Physics Health Check
          <span className="h-px flex-1 bg-(--border-default)" />
        </h3>
        
        <div className="rounded-lg border border-(--border-default) overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-(--bg-tertiary) text-(--text-secondary)">
              <tr>
                <th className="py-2 px-3 text-left font-medium text-xs">Param</th>
                <th className="py-2 px-3 text-right font-medium text-xs">Value</th>
                <th className="py-2 px-3 text-right font-medium text-xs">Check</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-(--border-default)">
              {/* Rs */}
              <tr className="bg-(--bg-card)">
                <td className="py-2 px-3 text-(--text-secondary)">Rs</td>
                <td className="py-2 px-3 text-right font-mono text-xs">
                  {metrics?.r_s !== undefined 
                    ? (metrics.r_s > 1000 ? metrics.r_s.toExponential(2) : metrics.r_s.toFixed(2)) 
                    : "—"}
                </td>
                <td className="py-2 px-3 text-right text-(--text-muted) text-[10px]">Ω·cm²</td>
              </tr>
              
              {/* Rsh */}
              <tr className="bg-(--bg-card)">
                <td className="py-2 px-3 text-(--text-secondary)">Rsh</td>
                <td className="py-2 px-3 text-right font-mono text-xs">
                  {metrics?.r_sh !== undefined 
                    ? (metrics.r_sh > 10000 ? metrics.r_sh.toExponential(2) : metrics.r_sh.toFixed(0)) 
                    : "—"}
                </td>
                <td className="py-2 px-3 text-right text-(--text-muted) text-[10px]">Ω·cm²</td>
              </tr>
              
              {/* Ideality Factor n */}
              <tr className={`bg-(--bg-card) ${metrics && metrics.n_ideality > 2.0 ? "bg-(--accent-amber)/5" : ""}`}>
                <td className="py-2 px-3 text-(--text-secondary)">n</td>
                <td className={`py-2 px-3 text-right font-mono ${metrics && metrics.n_ideality > 2.0 ? "text-(--accent-amber) font-bold" : ""}`}>
                  {metrics?.n_ideality !== undefined ? metrics.n_ideality.toFixed(3) : "—"}
                </td>
                <td className="py-2 px-3 text-right">
                  {metrics && metrics.n_ideality > 2.0 ? (
                    <span className="text-[10px] text-(--accent-amber) border border-(--accent-amber)/30 px-1 rounded">
                      ⚠ HIGH
                    </span>
                  ) : (
                    <span className="text-[10px] text-(--accent-green) px-1">OK</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Log / Hash */}
      {result?.resultHash && (
        <div className="mb-6">
          <h3 className="text-xs font-medium text-(--text-muted) mb-2">
            Determinism Hash
          </h3>
          <div className="bg-(--bg-tertiary) rounded-lg p-3 border border-(--border-default)">
            <code className="text-[10px] text-(--accent-green) font-mono break-all leading-tight block">
              {result.resultHash}
            </code>
          </div>
        </div>
      )}

      {/* Telemetry / Children */}
      {children}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Export Action */}
      <div className="pt-4 border-t border-(--border-default)">
        <button
          onClick={onExport}
          disabled={!result || mode !== "Reference"}
          className={`
            w-full py-3 rounded-lg font-bold text-xs uppercase tracking-widest transition-all duration-200
            flex items-center justify-center gap-2
            ${
              result && mode === "Reference"
                ? "bg-linear-to-r from-(--accent-gold) to-(--accent-amber) text-black cursor-pointer shadow-lg hover:brightness-110 active:scale-[0.98]"
                : "bg-(--bg-tertiary) text-(--text-muted) cursor-not-allowed border border-(--border-default)"
            }
          `}
        >
          {!result ? (
            "Run Analysis to Export"
          ) : mode !== "Reference" ? (
            "🔒 Switch to Reference Mode"
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Session Export (ZIP)
            </>
          )}
        </button>
      </div>
    </div>
  );
}
