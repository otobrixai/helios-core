"use client";

import { useMemo } from "react";
import { 
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ScatterChart,
  Scatter,
} from "recharts";
import { useScientificPlotData, PlotIntegrityBadge } from "@/hooks/useScientificPlotData";
import { GPUChartContainer } from "./GPUChartContainer";
import { ScientificSkeleton } from "./ScientificSkeleton";
import { 
  AnalysisMode, 
  MeasurementSessionData, 
  AnalysisSessionData 
} from "@/types/stateless";

interface AnalysisHubProps {
  measurement: MeasurementSessionData | null;
  result: AnalysisSessionData | null;
  mode: AnalysisMode;
  constants: { bandgap: number; temperature: number; area: number };
  onAnalyze: (area: number, temp: number) => void;
  isLoading?: boolean;
}



export function AnalysisHub({
  measurement,
  result,
  mode,
  constants,
  onAnalyze,
  isLoading = false,
}: AnalysisHubProps) {
  const isReference = mode === "Reference";
  const accentColor = isReference ? "#ffc107" : "#00d9ff";

  // Prepare plot data from measurement in memory
  const voltage = measurement?.voltage;
  const current = measurement?.current;
  const plotData = useMemo(() => {
    if (!voltage || !current) return [];

    const area = constants.area || 1.0;

    return voltage.map((v, i) => {
      const j_measured = (current[i] / area) * 1000;
      const fit_j = result?.fit_current ? (result.fit_current[i] / area) * 1000 : undefined;
      
      const safe_j = isFinite(j_measured) ? j_measured : 0;
      const safe_fit_j = fit_j !== undefined && isFinite(fit_j) ? fit_j : undefined;

      return {
        voltage: isFinite(v) ? v : 0,
        current: safe_j,
        fit_current: safe_fit_j,
        power: isFinite(v * safe_j) ? v * safe_j : 0,
        residual: (safe_j !== undefined && safe_fit_j !== undefined) ? safe_j - safe_fit_j : undefined,
      };
    });
  }, [voltage, current, result, constants.area]);

  // Apply Scientific Data Decimation
  const { displayData, metadata } = useScientificPlotData(plotData, {
    maxPoints: 400,
    preserveExtrema: true,
    smoothTolerance: 0.001
  });

  if (!measurement) {
    return (
      <div className="flex-1 flex items-center justify-center bg-(--bg-primary)">
        <div className="text-center opacity-50">
          <div className="w-20 h-20 border-2 border-dashed border-(--text-muted) rounded-xl mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2-2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-(--text-secondary) font-medium">No Measurement Selected</p>
          <p className="text-(--text-muted) text-sm mt-1">Select a pixel from the Inventory to begin</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-(--bg-primary)">
      {/* Visual Hub Header */}
      <div className="h-14 border-b border-(--border-default) flex items-center justify-between px-6 bg-(--bg-secondary)">
        <div>
          <h2 className="text-sm font-semibold text-(--text-primary)">
            {measurement.deviceLabel}
          </h2>
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isReference ? "bg-(--accent-gold)" : "bg-(--accent-cyan)"}`} />
            <span className="text-xs text-(--text-muted)">
              {isReference ? "Reference Mode (Audit Locked)" : "Exploration Mode (Interactive)"}
            </span>
          </div>
        </div>

        <button
          onClick={() => onAnalyze(constants.area, constants.temperature)}
          disabled={isLoading}
          className={`
            px-4 py-1.5 text-xs font-semibold rounded uppercase tracking-wide transition-all duration-200
            ${isLoading ? "opacity-50 cursor-wait" : ""}
            ${
              isReference
                ? "bg-(--accent-gold) text-black hover:bg-(--accent-amber)"
                : "bg-(--accent-cyan) text-black hover:bg-[#00b8d4]"
            }
          `}
        >
          {isLoading ? "Processing..." : result ? "Re-Analyze" : "Run Analysis"}
        </button>
      </div>

      <div className="flex-1 p-4 lg:p-6 flex flex-col gap-4 overflow-y-auto">
        {/* Master IV Plot */}
        <div className="flex-2 glass-card p-4 min-h-[450px] relative">
          <h3 className="absolute top-3 left-4 text-[10px] font-semibold text-(--text-secondary) uppercase tracking-wider z-10">
            Current Density vs Voltage
          </h3>
          
          <div className="w-full h-full min-h-[400px]">
            <ScientificSkeleton type="chart" mode={mode} hasData={!isLoading || displayData.length > 0} />
            <PlotIntegrityBadge metadata={metadata} />
            
            <GPUChartContainer id="iv-master" priority="high">
              <ResponsiveContainer width="100%" height="100%" minHeight={300}>
                <LineChart data={displayData} margin={{ top: 30, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-muted)" vertical={false} />
                <XAxis 
                  dataKey="voltage" 
                  type="number"
                  domain={['auto', 'auto']}
                  tick={{ fill: "var(--text-muted)", fontSize: 9 }}
                  axisLine={{ stroke: "var(--border-default)" }}
                  label={{ value: "Voltage (V)", position: "bottom", offset: 0, fill: "var(--text-secondary)", fontSize: 10 }}
                />
                <YAxis 
                  yAxisId="current"
                  tick={{ fill: "var(--text-muted)", fontSize: 9 }}
                  axisLine={{ stroke: "var(--border-default)" }}
                  label={{ value: "J (mA/cm²)", angle: -90, position: "insideLeft", fill: "var(--text-secondary)", fontSize: 10 }}
                />
                <YAxis 
                  yAxisId="power" 
                  orientation="right"
                  tick={{ fill: "var(--text-muted)", fontSize: 9 }}
                  axisLine={{ stroke: "var(--border-default)" }}
                  label={{ value: "P (mW/cm²)", angle: 90, position: "insideRight", fill: "var(--text-secondary)", fontSize: 10 }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-default)", fontSize: "11px" }}
                  itemStyle={{ color: "var(--text-primary)" }}
                />
                
                {/* Raw Data (Dots) */}
                <Line 
                  yAxisId="current" type="monotone" dataKey="current" 
                  stroke={accentColor} strokeWidth={0} dot={{ r: 1.5, fill: accentColor }} 
                  activeDot={{ r: 3, stroke: "none", fill: accentColor }}
                  name="Measured J"
                  connectNulls
                />
                
                {/* Fit Data placeholder - fit is complex in stateless session */}
                {result?.results && (
                  <Line 
                    yAxisId="current" type="monotone" dataKey="fit_current" 
                    stroke="var(--accent-green)" strokeWidth={2} dot={false}
                    name="Physics Fit"
                    connectNulls
                  />
                )}

                <Line 
                  yAxisId="power" type="monotone" dataKey="power" 
                  stroke="var(--text-muted)" strokeWidth={1} dot={false} strokeDasharray="3 3"
                  opacity={0.3}
                  name="Measured Power"
                />
                
                {result?.results && (
                  <ReferenceLine 
                    yAxisId="current" x={(result.results.v_oc || 0) * 0.8} 
                    stroke="var(--text-muted)" strokeDasharray="3 3" 
                    label={{ value: "MPP", fill: "var(--text-muted)", fontSize: 9, position: "top" }} 
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
            </GPUChartContainer>
          </div>
        </div>

        <div className="flex-1 min-h-[220px] glass-card p-4 relative">
          <h3 className="absolute top-2 left-4 text-[10px] font-semibold text-(--text-secondary) uppercase tracking-wider z-10">
            Fit Residuals (ΔJ)
          </h3>
          <div className="w-full h-full min-h-[180px]">
            {result ? (
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 30, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-muted)" vertical={false} />
                  <XAxis 
                    dataKey="voltage" 
                    type="number" 
                    domain={['auto', 'auto']}
                    hide 
                  />
                  <YAxis 
                    type="number"
                    tick={{ fill: "var(--text-muted)", fontSize: 8 }}
                    axisLine={{ stroke: "var(--border-default)" }}
                    domain={['auto', 'auto']}
                    label={{ value: "ΔJ (mA/cm²)", angle: -90, position: "insideLeft", fill: "var(--text-secondary)", fontSize: 8 }}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-default)", fontSize: "10px" }}
                    itemStyle={{ color: accentColor }}
                  />
                  <ReferenceLine y={0} stroke="var(--text-muted)" strokeWidth={1} strokeDasharray="3 3" />
                  <Scatter 
                    name="Fit Residual"
                    data={displayData} 
                    fill={accentColor} 
                    line={false}
                    shape="circle"
                    dataKey="residual"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex items-center justify-center opacity-30 text-[10px] uppercase tracking-widest font-bold">
                Run Analysis for Residuals
              </div>
            )}
          </div>
        </div>

        <div className={`
          h-12 border-t border-(--border-default) flex items-center px-4 gap-4
          ${isReference ? "opacity-50 pointer-events-none grayscale" : ""}
        `}>
          <div className="flex-1 h-1.5 bg-(--bg-tertiary) rounded-full overflow-hidden">
            <div className="w-full h-full bg-(--text-muted) opacity-20" />
          </div>
          <span className="text-[10px] text-(--text-muted) font-mono uppercase">
            {isReference ? "SCRUB LOCKED" : "FULL RANGE"}
          </span>
        </div>
      </div>
    </div>
  );
}
