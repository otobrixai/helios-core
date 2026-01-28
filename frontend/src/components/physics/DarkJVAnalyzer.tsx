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
  Legend
} from "recharts";
import { AnalysisSessionData, MeasurementSessionData } from "@/types/stateless";

interface DarkJVAnalyzerProps {
  measurement: MeasurementSessionData;
  result: AnalysisSessionData | null;
}

export function DarkJVAnalyzer({ measurement, result }: DarkJVAnalyzerProps) {
  const { voltage, current, areaCm2 } = measurement;
  const fit_current = result?.fit_current;

  const plotData = useMemo(() => {
    if (!voltage || !current) return [];
    
    return voltage.map((v, i) => {
      const j_abs = Math.abs((current[i] / (areaCm2 || 1.0)) * 1000);
      const fit_j_abs = fit_current 
        ? Math.abs((fit_current[i] / (areaCm2 || 1.0)) * 1000) 
        : null;
        
      return {
        voltage: v,
        j_abs: j_abs > 1e-6 ? j_abs : 1e-6, // Floor for log scale
        fit_j_abs: fit_j_abs && fit_j_abs > 1e-6 ? fit_j_abs : null,
      };
    });
  }, [voltage, current, areaCm2, fit_current]);

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex items-center justify-between px-2">
        <h3 className="text-xs font-bold text-(--text-secondary) uppercase tracking-widest">
          Dark J-V Analysis (Log Scale)
        </h3>
        <div className="flex gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-(--text-muted) uppercase">Rsh (Dark)</span>
            <span className="text-sm font-mono text-(--accent-cyan)">
              {result?.results?.r_sh_dark?.toFixed(2) || "---"} Ω·cm²
            </span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-(--text-muted) uppercase">I₀ (Dark)</span>
            <span className="text-sm font-mono text-(--accent-gold)">
              {result?.results?.i_0_dark?.toExponential(2) || "---"} A
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-[300px] glass-card p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={plotData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-muted)" vertical={false} />
            <XAxis 
              dataKey="voltage" 
              type="number"
              domain={['auto', 'auto']}
              label={{ value: "Voltage (V)", position: "bottom", offset: 0, fill: "var(--text-secondary)", fontSize: 10 }}
              tick={{ fill: "var(--text-muted)", fontSize: 9 }}
            />
            <YAxis 
              type="number"
              scale="log"
              domain={[1e-4, 'auto']}
              label={{ value: "|J| (mA/cm²)", angle: -90, position: "insideLeft", fill: "var(--text-secondary)", fontSize: 10 }}
              tick={{ fill: "var(--text-muted)", fontSize: 9 }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-default)", fontSize: "11px" }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '10px' }} />
            <Line 
              type="monotone" 
              dataKey="j_abs" 
              stroke="var(--accent-cyan)" 
              dot={{ r: 2 }} 
              strokeWidth={0} 
              name="Measured |J|"
            />
            {result?.results && (
              <Line 
                type="monotone" 
                dataKey="fit_j_abs" 
                stroke="var(--accent-green)" 
                dot={false} 
                strokeWidth={2} 
                name="Diode Fit"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="p-3 bg-(--bg-tertiary) rounded border border-(--border-default) text-[11px] text-(--text-secondary)">
        <p className="font-semibold text-(--accent-cyan) mb-1">Researcher Note:</p>
        <p>
          Dark J-V reveals shunts at low bias and series resistance at high bias. 
          The exponential slope in the range 0.4V - 0.7V is used to extract the 
          fundamental ideality factor without photogeneration masking.
        </p>
      </div>
    </div>
  );
}
