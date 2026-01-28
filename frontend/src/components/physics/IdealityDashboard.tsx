"use client";

import { AnalysisSessionData } from "@/types/stateless";

interface IdealityDashboardProps {
  result: AnalysisSessionData | null;
}

export function IdealityDashboard({ result }: IdealityDashboardProps) {
  const n_fit = result?.results?.n_ideality;
  const n_slope = result?.results?.n_slope;
  const n_dark = result?.results?.n_dark;

  const methods = [
    { 
      name: "Global Fit (One-Diode)", 
      value: n_fit, 
      accuracy: "High", 
      desc: "Extracted using full-curve optimization" 
    },
    { 
      name: "Local Slope (ln J vs V)", 
      value: n_slope, 
      accuracy: "Medium", 
      desc: "Calculated from forward bias derivative" 
    },
    { 
      name: "Dark JV Extraction", 
      value: n_dark, 
      accuracy: "Very High", 
      desc: "Pure diode behavior without illumination" 
    }
  ];

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-xs font-bold text-(--text-secondary) uppercase tracking-widest px-1">
        Ideality Factor Dashboard
      </h3>

      <div className="grid grid-cols-1 gap-3">
        {methods.map((m) => (
          <div key={m.name} className="glass-card p-3 flex flex-col gap-1 border-l-2" 
               style={{ borderLeftColor: m.value ? (m.value > 2 ? 'var(--accent-gold)' : 'var(--accent-cyan)') : 'var(--border-default)' }}>
            <div className="flex justify-between items-center">
              <span className="text-[11px] font-bold text-(--text-primary)">{m.name}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                m.accuracy === 'Very High' ? 'bg-(--accent-green)/20 text-(--accent-green)' :
                m.accuracy === 'High' ? 'bg-(--accent-cyan)/20 text-(--accent-cyan)' :
                'bg-(--text-muted)/20 text-(--text-muted)'
              }`}>
                {m.accuracy}
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-mono font-bold">
                {m.value ? m.value.toFixed(3) : "---"}
              </span>
              <span className="text-[10px] text-(--text-muted)">dimensionless</span>
            </div>
            <p className="text-[10px] text-(--text-muted) italic">{m.desc}</p>
          </div>
        ))}
      </div>

      {n_fit && n_dark && (
        <div className="p-3 bg-(--accent-cyan)/5 border border-(--accent-cyan)/20 rounded">
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-(--text-secondary)">Illumination Shift (Δn)</span>
            <span className="font-mono font-bold text-(--accent-cyan)">
              {(n_fit - n_dark).toFixed(3)}
            </span>
          </div>
          <p className="text-[10px] text-(--text-muted)">
            Positive Δn suggests illumination-dependent recombination centers.
          </p>
        </div>
      )}
    </div>
  );
}
