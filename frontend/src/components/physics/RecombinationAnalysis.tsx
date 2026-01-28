"use client";

import { AnalysisSessionData } from "@/types/stateless";

interface RecombinationAnalysisProps {
  result: AnalysisSessionData | null;
}

export function RecombinationAnalysis({ result }: RecombinationAnalysisProps) {
  const n = result?.results?.n_ideality || 0;

  const getMechanism = (val: number) => {
    if (val === 0) return { label: "No Data", color: "var(--text-muted)", desc: "Run analysis to determine mechanism." };
    if (val < 0.8) return { label: "Measurement Artifact", color: "#ff4444", desc: "Non-physical n < 1. Check for leakage or noise." };
    if (val <= 1.2) return { label: "Radiative / Bimolecular", color: "var(--accent-cyan)", desc: "Ideal band-to-band recombination dominates." };
    if (val < 1.8) return { label: "SRH (Trap-Assisted)", color: "var(--accent-green)", desc: "Shockley-Read-Hall recombination in the depletion region." };
    if (val <= 2.2) return { label: "Diffusion Limited", color: "var(--accent-gold)", desc: "SRH recombination in quasi-neutral regions." };
    return { label: "Complex Transport", color: "var(--accent-gold)", desc: "Tunneling, multi-level traps, or extraction barriers." };
  };

  const mech = getMechanism(n);

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-xs font-bold text-(--text-secondary) uppercase tracking-widest px-1">
        Recombination Diagnostics
      </h3>

      <div className="glass-card p-4 flex flex-col items-center text-center gap-3">
        <div 
          className="w-16 h-16 rounded-full border-4 flex items-center justify-center transition-all duration-500"
          style={{ borderColor: mech.color, boxShadow: `0 0 20px ${mech.color}33` }}
        >
          <span className="text-lg font-bold" style={{ color: mech.color }}>
            n={n > 0 ? n.toFixed(2) : "?"}
          </span>
        </div>
        
        <div className="space-y-1">
          <p className="text-sm font-bold text-(--text-primary) uppercase tracking-wide">
            {mech.label}
          </p>
          <p className="text-[11px] text-(--text-muted) leading-relaxed">
            {mech.desc}
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-[10px] text-(--text-muted) uppercase font-bold px-1">
          <span>Mechanism Map</span>
          <span>SRH Intensity</span>
        </div>
        <div className="h-2 w-full bg-(--bg-tertiary) rounded-full flex overflow-hidden">
          <div className="h-full bg-(--accent-cyan)/40 w-[30%]" title="Radiative" />
          <div className="h-full bg-(--accent-green)/40 w-[30%]" title="SRH Depletion" />
          <div className="h-full bg-(--accent-gold)/40 w-[20%]" title="SRH Quasi-neutral" />
          <div className="h-full bg-red-500/40 w-[20%]" title="Tunneling" />
        </div>
        <div className="flex justify-between text-[9px] text-(--text-muted) px-1">
          <span>n=1</span>
          <span>n=1.5</span>
          <span>n=2.0</span>
          <span>n{'>'}2</span>
        </div>
      </div>
    </div>
  );
}
