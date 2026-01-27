"use client";

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Activity, 
  Shield, 
  BarChart3,
  TrendingUp,
  AlertCircle,
  Download,
  Lock,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { FullDiagnosticReport } from '../types/diagnostics';

interface DiagnosticSidebarProps {
  diagnosticReport: FullDiagnosticReport | null;
  mode: 'Exploration' | 'Reference';
  onViewReport?: () => void;
  onDownloadAudit?: () => void;
  isLoading?: boolean;
}

export const DiagnosticSidebar: React.FC<DiagnosticSidebarProps> = ({ 
  diagnosticReport, 
  mode,
  onViewReport,
  onDownloadAudit,
  isLoading
}) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  
  if (isLoading) {
    return (
      <div className="w-80 h-full bg-(--bg-secondary) border-l border-(--border-default) p-6 flex flex-col items-center justify-center text-(--text-muted)">
        <div className="w-8 h-8 rounded-full border-2 border-(--accent-cyan)/20 border-t-(--accent-cyan) animate-spin mb-4" />
        <p className="text-sm font-medium">Analyzing Physics...</p>
      </div>
    );
  }

  if (!diagnosticReport) {
    return (
      <div className="w-80 h-full bg-(--bg-secondary) border-l border-(--border-default) p-6 flex flex-col items-center justify-center text-(--text-muted)">
        <div className="p-4 rounded-full bg-(--bg-primary) mb-4 border border-(--border-default)">
          <BarChart3 size={32} className="opacity-40" />
        </div>
        <p className="text-center text-sm font-semibold">Diagnostic Engine Ready</p>
        <p className="text-[10px] text-center mt-2 uppercase tracking-widest opacity-60">Run analysis to generate audit</p>
      </div>
    );
  }
  
  const getSeverityColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-(--accent-red) bg-(--accent-red)/5 border-(--accent-red)/20';
      case 'HIGH': return 'text-(--accent-amber) bg-(--accent-amber)/5 border-(--accent-amber)/20';
      case 'MEDIUM': return 'text-(--accent-gold) bg-(--accent-gold)/5 border-(--accent-gold)/20';
      case 'LOW': return 'text-(--accent-green) bg-(--accent-green)/5 border-(--accent-green)/20';
      default: return 'text-(--text-muted) bg-(--bg-tertiary) border-(--border-default)';
    }
  };
  
  const getSeverityIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'HIGH': return <AlertTriangle size={14} />;
      case 'MEDIUM': return <AlertCircle size={14} />;
      case 'LOW': return <CheckCircle size={14} />;
      default: return <Info size={14} />;
    }
  };
  
  const renderResidualCard = () => {
    const res = diagnosticReport.residuals;
    if (!res) return null;
    
    return (
      <div className={`p-4 rounded-lg border mb-4 transition-all duration-300 ${getSeverityColor(res.warning)}`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity size={16} className="shrink-0" />
            <span className="font-bold text-[11px] uppercase tracking-wider">Residual Analysis</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-current/20 bg-black/20">
            {getSeverityIcon(res.warning)}
            <span className="text-[9px] font-black tracking-tighter">{res.warning}</span>
          </div>
        </div>
        
        <p className="text-xs mb-4 font-medium leading-relaxed opacity-90">{res.message}</p>
        
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-black/20 p-2 rounded border border-white/5">
            <div className="text-[9px] text-current/60 uppercase font-bold tracking-tighter">RMS</div>
            <div className="font-mono text-[10px] tabular-nums">{res.rms.toExponential(2)}</div>
          </div>
          <div className="bg-black/20 p-2 rounded border border-white/5">
            <div className="text-[9px] text-current/60 uppercase font-bold tracking-tighter">R² Fit</div>
            <div className="font-mono text-[10px] tabular-nums">{res.r_squared.toFixed(3)}</div>
          </div>
        </div>
        
        {res.pattern === 's_shaped' && (
          <div className="mt-4 p-2 bg-(--accent-red)/10 border border-(--accent-red)/30 rounded text-[10px]">
            <div className="flex items-center gap-2 text-(--accent-red) mb-1 font-bold">
              <AlertTriangle size={12} />
              <span>S-SHAPE ANOMALY</span>
            </div>
            <p className="opacity-80 leading-tight">
              Evidence of extraction barriers. Check contact interface quality.
            </p>
          </div>
        )}
      </div>
    );
  };
  
  const renderNoiseStabilityCard = () => {
    const ns = diagnosticReport.noise_stability;
    if (!ns) return null;
    
    const isStable = ns.stability_score >= 80;
    
    return (
      <div className="bg-(--bg-tertiary) rounded-lg p-4 mb-4 border border-(--border-default) group">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-(--text-primary)">
            <Shield size={16} className={isStable ? 'text-(--accent-cyan)' : 'text-(--accent-red)'} />
            <h3 className="text-[11px] font-bold uppercase tracking-wider">Stability Scan</h3>
          </div>
          <div className={`text-[9px] px-2 py-0.5 rounded font-black tracking-widest ${isStable ? 'bg-(--accent-green)/10 text-(--accent-green)' : 'bg-(--accent-red)/10 text-(--accent-red)'}`}>
            {isStable ? 'STABLE' : 'VOLATILE'}
          </div>
        </div>
        
        <div className="mb-4">
          <div className="flex justify-between text-[10px] mb-2 font-bold uppercase tracking-tighter text-(--text-secondary)">
            <span>Robustness Coefficient</span>
            <span className="font-mono">{ns.stability_score.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-(--bg-primary) h-1.5 rounded-full overflow-hidden border border-(--border-default)">
            <div 
              className={`h-full transition-all duration-1000 ${isStable ? 'bg-(--accent-green)' : 'bg-(--accent-red)'}`}
              style={{ width: `${ns.stability_score}%` }}
            />
          </div>
        </div>
        
        <button 
          onClick={() => setExpandedSection(expandedSection === 'noise' ? null : 'noise')}
          className="w-full flex items-center justify-between text-[9px] text-(--text-muted) hover:text-(--text-secondary) font-bold uppercase tracking-widest transition-colors py-1"
        >
          <span>Parameter Drift Matrices</span>
          {expandedSection === 'noise' ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
        
        {expandedSection === 'noise' && ns.parameter_drifts && (
          <div className="mt-3 grid grid-cols-2 gap-2 animate-in fade-in slide-in-from-top-1">
            {Object.entries(ns.parameter_drifts).map(([param, drift]) => (
              <div key={param} className="bg-(--bg-primary) p-2 rounded border border-(--border-default)">
                <div className="text-[8px] text-(--text-muted) font-black uppercase tracking-tighter mb-1">{param}</div>
                <div className="font-mono text-[9px] tabular-nums text-(--text-primary)">
                  ±{(drift.mean * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };
  
  const renderBoundaryStressCard = () => {
    const bs = diagnosticReport.boundary_stress;
    if (!bs) return null;
    
    const hasErrors = bs.boundary_hits.some(h => h.severity === 'ERROR');
    const hasWarnings = bs.boundary_hits.some(h => h.severity === 'WARNING');
    
    return (
      <div className={`rounded-lg p-4 mb-4 border transition-colors ${
        hasErrors ? 'border-(--accent-red)/50 bg-(--accent-red)/5' : 
        hasWarnings ? 'border-(--accent-gold)/50 bg-(--accent-gold)/5' : 
        'border-(--border-default) bg-(--bg-tertiary)'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className={hasErrors ? 'text-(--accent-red)' : hasWarnings ? 'text-(--accent-gold)' : 'text-(--text-secondary)'} />
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-(--text-primary)">Boundary Engine</h3>
          </div>
          <div className={`text-[9px] px-2 py-0.5 rounded font-black tracking-widest ${
            hasErrors ? 'bg-(--accent-red)/20 text-(--accent-red)' : 
            hasWarnings ? 'bg-(--accent-gold)/20 text-(--accent-gold)' : 
            'bg-(--text-muted)/10 text-(--text-muted)'
          }`}>
            {bs.n_hits} HIT{bs.n_hits !== 1 ? 'S' : ''}
          </div>
        </div>
        
        {bs.boundary_hits.length > 0 ? (
          <div className="space-y-2">
            {bs.boundary_hits.map((hit, idx) => (
              <div key={idx} className="bg-black/20 border border-white/5 p-2 rounded">
                <div className="flex justify-between items-baseline mb-1">
                  <span className="text-[10px] font-bold text-white uppercase tracking-tighter">{hit.parameter}</span>
                  <span className="font-mono text-[10px] tabular-nums text-white/90">{hit.value.toExponential(2)}</span>
                </div>
                <div className="text-[8px] uppercase font-black tracking-wider opacity-60 flex justify-between">
                  <span>{hit.direction} bound reached</span>
                  <span>({hit.bound})</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[10px] text-(--text-muted) italic text-center py-2">Physics constraints held within nominal range</p>
        )}
      </div>
    );
  };

  const riskScore = diagnosticReport.overall_risk_score;
  const hasRiskData = riskScore !== undefined && riskScore !== null;
  const displayRisk = hasRiskData ? riskScore : 0;
  
  const isHighRisk = hasRiskData && displayRisk >= 70;
  const isMedRisk = hasRiskData && displayRisk >= 30 && displayRisk < 70;
  
  return (
    <div className="w-80 h-full bg-(--bg-secondary) border-l border-(--border-default) flex flex-col relative z-30">
      {/* Header */}
      <div className="p-6 border-b border-(--border-default) bg-(--bg-tertiary)/50 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-(--bg-primary) border border-(--border-default) text-(--accent-cyan) shadow-inner-lg">
            <Shield size={20} />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-widest text-(--text-primary)">Physics Audit</h2>
            <div className="flex items-center gap-2 mt-1">
              <div className={`text-[9px] px-2 py-0.5 rounded-full font-black tracking-widest uppercase border ${
                mode === 'Reference' ? 'bg-(--accent-gold)/10 text-(--accent-gold) border-(--accent-gold)/30' : 'bg-(--accent-cyan)/10 text-(--accent-cyan) border-(--accent-cyan)/30'
              }`}>
                {mode === 'Reference' && <Lock size={8} className="inline mr-1 mb-0.5" />}
                {mode}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Scrollable Metrics */}
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        
        {/* Risk Score Hub */}
        <div className="mb-8 text-center bg-(--bg-primary) p-6 rounded-2xl border border-(--border-default) shadow-2xl relative overflow-hidden group">
          <div className={`absolute top-0 left-0 w-full h-1 ${!hasRiskData ? 'bg-(--text-muted)' : isHighRisk ? 'bg-(--accent-red)' : isMedRisk ? 'bg-(--accent-gold)' : 'bg-(--accent-green)'}`} />
          
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-(--text-muted) mb-3 block">Overall Confidence</span>
          
          <div className="relative inline-block">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48" cy="48" r="42"
                stroke="currentColor"
                strokeWidth="4"
                fill="transparent"
                className="text-(--bg-tertiary)"
              />
              <circle
                cx="48" cy="48" r="42"
                stroke="currentColor"
                strokeWidth="4"
                fill="transparent"
                strokeDasharray={264}
                strokeDashoffset={264 - (264 * (100 - displayRisk)) / 100}
                className={`transition-all duration-1000 ease-out ${!hasRiskData ? 'text-(--text-muted) opacity-20' : isHighRisk ? 'text-(--accent-red)' : isMedRisk ? 'text-(--accent-gold)' : 'text-(--accent-green)'}`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl font-black tabular-nums tracking-tighter text-(--text-primary)">
                {hasRiskData ? Math.round(100 - displayRisk) : '—'}
                {hasRiskData && <span className="text-xs opacity-50 ml-0.5">%</span>}
              </span>
            </div>
          </div>
          
          <div className={`mt-4 text-[10px] font-bold uppercase tracking-wider ${!hasRiskData ? 'text-(--text-muted)' : isHighRisk ? 'text-(--accent-red)' : isMedRisk ? 'text-(--accent-gold)' : 'text-(--accent-green)'}`}>
             {!hasRiskData ? 'Audit Pending (Stateless)' : isHighRisk ? 'Critical Review Required' : isMedRisk ? 'Manual Validation Suggested' : 'Publication Ready Data'}
          </div>
        </div>

        {renderResidualCard()}
        {renderNoiseStabilityCard()}
        {renderBoundaryStressCard()}
        
        {/* Recommendations */}
        {diagnosticReport.recommendations?.length > 0 && (
          <div className="bg-(--bg-tertiary) rounded-xl p-4 border border-(--border-default) mt-2 shadow-sm">
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-(--text-muted) mb-4 flex items-center gap-2">
              <Info size={12} className="text-(--accent-cyan)" />
              Next Scientific Steps
            </h3>
            <ul className="space-y-4">
              {diagnosticReport.recommendations.map((rec, idx) => (
                <li key={idx} className="text-[11px] leading-relaxed text-(--text-secondary) flex gap-3 group">
                  <div className="w-1.5 h-1.5 rounded-full bg-(--accent-cyan)/40 mt-1 shrink-0 group-hover:bg-(--accent-cyan) transition-colors" />
                  <span className="opacity-90">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Action Footer */}
      <div className="p-6 border-t border-(--border-default) bg-(--bg-tertiary)/30 space-y-3">
        <button
          onClick={onViewReport}
          className="w-full flex items-center justify-center gap-2 py-3 bg-(--bg-primary) hover:bg-(--bg-tertiary) border border-(--border-default) text-(--text-primary) text-[11px] font-bold uppercase tracking-widest rounded-lg transition-all active:scale-95 shadow-sm"
        >
          <Activity size={14} />
          View Full Audit Log
        </button>
        
        <button
          onClick={onDownloadAudit}
          className={`w-full flex items-center justify-center gap-2 py-3 text-[11px] font-black uppercase tracking-widest rounded-lg transition-all active:scale-95 border shadow-lg ${
            isHighRisk 
              ? 'bg-(--accent-red)/10 text-(--accent-red) border-(--accent-red)/30 hover:bg-(--accent-red)/20' 
              : 'bg-(--accent-cyan)/10 text-(--accent-cyan) border-(--accent-cyan)/30 hover:bg-(--accent-cyan)/20'
          }`}
        >
          <Download size={14} />
          Export Artifacts
        </button>
        
        {mode === 'Reference' && diagnosticReport.hash && (
          <div className="pt-4 mt-2 border-t border-(--border-default)/50">
            <div className="flex items-center justify-between text-[8px] font-black uppercase tracking-widest text-(--text-muted) mb-2">
              <span>Integrity Hash</span>
              <Lock size={8} />
            </div>
            <div className="font-mono text-[9px] text-(--text-muted) bg-(--bg-primary) p-2 rounded truncate border border-(--border-default)/30 opacity-60">
              {diagnosticReport.hash}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
