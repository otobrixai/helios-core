// frontend/src/types/stateless.ts

/**
 * Helios Core — Stateless Analysis Types
 */

export type AnalysisMode = 'Exploration' | 'Reference';
export type ModelType = 'OneDiode' | 'TwoDiode';
export type AnalysisStatus = 'VALID' | 'INVALID' | 'FAILED';
export type MeasurementType = 'light' | 'dark' | 'suns_voc';

export interface MeasurementSessionData {
  id: string;
  filename: string;
  fileHash: string;
  deviceLabel: string;
  voltage: number[];
  current: number[];
  vColumn: string;
  iColumn: string;
  areaCm2: number;
  temperatureK: number;
  measurementType: MeasurementType;
  timestamp: string;
}

export interface AnalysisResult {
  j_sc: number;
  v_oc: number;
  ff: number;
  pce: number;
  r_s: number;
  r_sh: number;
  n_ideality: number;
  i_ph?: number;
  i_0?: number;
  // Fundamental Physics
  n_slope?: number;
  n_dark?: number;
  i_0_dark?: number;
  r_s_dark?: number;
  r_sh_dark?: number;
}

import { FullDiagnosticReport } from './diagnostics';

export interface AnalysisSessionData {
  id: string;
  measurementId: string;
  status: AnalysisStatus;
  mode: AnalysisMode;
  modelType: ModelType;
  results?: AnalysisResult;
  fit_current?: number[];
  resultHash?: string;
  errorMessage?: string;
  timestamp: string;
  errorMessage?: string;
  timestamp: string;
  diagnostics?: FullDiagnosticReport | null;
  auditId?: string;
  bibtex?: string;
}

export interface HeliosSessionExport {
  version: 'helios_v1.0';
  exportTimestamp: string;
  measurements: MeasurementSessionData[];
  analyses: AnalysisSessionData[];
}
