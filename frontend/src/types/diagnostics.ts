// frontend/src/types/diagnostics.ts

export interface ResidualDiagnostic {
  pattern: 'random' | 'linear_trend' | 'systematic_curvature' | 's_shaped';
  warning: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  rms: number;
  slope: number;
  r_squared: number;
  quadratic_strength: number;
  classification_confidence: number;
}

export interface ParameterDrift {
  mean: number;
  std: number;
  max: number;
}

export interface NoiseStabilityDiagnostic {
  stability_score: number; // 0-100%
  parameter_drifts: {
    [key: string]: ParameterDrift;
  };
  worst_case_drift: number;
  noise_level_tested: number; // e.g., 0.02 for 2%
}

export interface BoundaryHit {
  parameter: string;
  value: number;
  bound: number;
  direction: 'upper' | 'lower';
  distance_percent: number;
  severity: 'WARNING' | 'ERROR';
}

export interface BoundaryStressDiagnostic {
  boundary_hits: BoundaryHit[];
  n_hits: number;
  recommendations: string[];
}

export interface FullDiagnosticReport {
  timestamp: string;
  analysis_id: string;
  mode: 'Exploration' | 'Reference';
  residuals: ResidualDiagnostic | null;
  noise_stability: NoiseStabilityDiagnostic | null;
  boundary_stress: BoundaryStressDiagnostic | null;
  overall_risk_score: number; // 0-100, lower is better
  recommendations: string[];
  validation_passed: boolean;
  hash: string; // SHA-256 of diagnostic data
}
