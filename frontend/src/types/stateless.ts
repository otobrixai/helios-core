// frontend/src/types/stateless.ts

/**
 * Helios Core — Stateless Analysis Types
 */

export type AnalysisMode = 'Exploration' | 'Reference';
export type ModelType = 'OneDiode' | 'TwoDiode';
export type AnalysisStatus = 'VALID' | 'INVALID' | 'FAILED';

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
}

import { FullDiagnosticReport } from './diagnostics';

export interface AnalysisSessionData {
  id: string;
  measurementId: string;
  status: AnalysisStatus;
  mode: AnalysisMode;
  modelType: ModelType;
  results?: AnalysisResult;
  resultHash?: string;
  errorMessage?: string;
  timestamp: string;
  diagnostics?: FullDiagnosticReport | null;
}

export interface HeliosSessionExport {
  version: 'helios_v1.0';
  exportTimestamp: string;
  measurements: MeasurementSessionData[];
  analyses: AnalysisSessionData[];
}
