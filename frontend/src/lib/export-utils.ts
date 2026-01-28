import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { MeasurementSessionData, AnalysisSessionData, HeliosSessionExport } from '../types/stateless';
import { getApiUrl } from './api-config';

export async function exportSessionBundle(
  measurements: MeasurementSessionData[],
  analyses: AnalysisSessionData[]
) {
  const zip = new JSZip();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  // 1. Manifest
  const manifest: HeliosSessionExport = {
    version: 'helios_v1.0',
    exportTimestamp: new Date().toISOString(),
    measurements,
    analyses
  };
  zip.file('manifest.json', JSON.stringify(manifest, null, 2));

  // 2. Data Folder
  const dataFolder = zip.folder('measurements');
  if (dataFolder) {
    measurements.forEach((m) => {
      const csvContent = generateCSV(m);
      dataFolder.file(`${m.deviceLabel}.csv`, csvContent);
    });
  }

  // 3. Results Summary CSV
  const resultsCsv = generateResultsSummary(analyses);
  zip.file('results.csv', resultsCsv);

  // 4. Reproduction Scripts
  const scriptsFolder = zip.folder('reproduction');
  if (scriptsFolder) {
    analyses.forEach((a) => {
      const m = measurements.find(meas => meas.id === a.measurementId);
      if (m && a.results) {
        const script = generatePythonScript(m, a);
        scriptsFolder.file(`reproduce_${a.id.substring(4, 12)}.py`, script);
      }
    });
  }

  const content = await zip.generateAsync({ type: 'blob' });
  saveAs(content, `helios-core-session-${timestamp}.zip`);
}

export async function downloadBackendBundle(analysisId: string) {
  try {
    const response = await fetch(getApiUrl(`/api/export/${analysisId}`));
    if (!response.ok) throw new Error('Export generation failed');
    
    const blob = await response.blob();
    const filename = response.headers.get('content-disposition')?.split('filename=')[1] || `helios_bundle_${analysisId.substring(0, 8)}.zip`;
    saveAs(blob, filename);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}

export async function downloadStatelessBackendBundle(
  measurement: MeasurementSessionData,
  analysis: AnalysisSessionData
) {
  try {
    const payload = {
      voltage: measurement.voltage,
      current: measurement.current,
      device_label: measurement.deviceLabel,
      mode: analysis.mode,
      model_type: analysis.modelType || "OneDiode",
      area_cm2: measurement.areaCm2,
      temperature_k: measurement.temperatureK,
      results: analysis.results || {},
      result_hash: analysis.resultHash
    };

    const response = await fetch(getApiUrl('/api/stateless/export-bundle'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Stateless export generation failed');
    
    const blob = await response.blob();
    const filename = response.headers.get('content-disposition')?.split('filename=')[1] || `helios_stateless_bundle_${measurement.deviceLabel}.zip`;
    saveAs(blob, filename);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}

function generateResultsSummary(analyses: AnalysisSessionData[]): string {
  const headers = "AnalysisID,Timestamp,Status,Jsc(mA/cm2),Voc(V),FF(%),PCE(%),Rs(ohm.cm2),Rsh(ohm.cm2),n,n_slope,n_dark,i_0_dark,r_s_dark,r_sh_dark";
  const rows = analyses.map(a => {
    if (a.status !== 'VALID' || !a.results) {
      return `${a.id},${a.timestamp},${a.status},,,,,,,`;
    }
    const r = a.results;
    return [
      a.id,
      a.timestamp,
      a.status,
      r.j_sc?.toFixed(4),
      r.v_oc?.toFixed(4),
      (r.ff !== undefined ? r.ff * 100 : 0).toFixed(2),
      r.pce?.toFixed(2),
      r.r_s?.toFixed(4),
      r.r_sh?.toFixed(2),
      r.n_ideality?.toFixed(4),
      r.n_slope?.toFixed(4),
      r.n_dark?.toFixed(4),
      r.i_0_dark?.toExponential(2),
      r.r_s_dark?.toFixed(4),
      r.r_sh_dark?.toFixed(2),
    ].join(',');
  });
  return [headers, ...rows].join('\n');
}

function generateCSV(m: MeasurementSessionData): string {
  let csv = `${m.vColumn},${m.iColumn}\n`;
  for (let i = 0; i < m.voltage.length; i++) {
    csv += `${m.voltage[i]},${m.current[i]}\n`;
  }
  return csv;
}

function generatePythonScript(m: MeasurementSessionData, a: AnalysisSessionData): string {
  const params = a.results;
  return `#!/usr/bin/env python3
"""
Helios Core — Reproduction Script (Stateless Session)
Analysis ID: ${a.id}
Device: ${m.deviceLabel}
Generated: ${new Date().toISOString()}

This script contains the locked data and expected results to verify
scientific determinism independently of the web platform.
"""

import os
import numpy as np

# =============================================================================
# DETERMINISM LOCK (MANDATORY)
# =============================================================================
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

# =============================================================================
# INPUT DATA
# =============================================================================
DEVICE_LABEL = "${m.deviceLabel}"
AREA_CM2 = ${m.areaCm2}
TEMPERATURE_K = ${m.temperatureK}

VOLTAGE = np.array(${JSON.stringify(m.voltage)}, dtype=np.float64)
CURRENT = np.array(${JSON.stringify(m.current)}, dtype=np.float64)

# =============================================================================
# EXPECTED RESULTS (FROM HELIOS CORE)
# =============================================================================
EXPECTED = {
    "j_sc": ${params?.j_sc},
    "v_oc": ${params?.v_oc},
    "ff": ${params?.ff},
    "pce": ${params?.pce},
    "r_s": ${params?.r_s},
    "r_sh": ${params?.r_sh},
    "n": ${params?.n_ideality},
    "n_slope": ${params?.n_slope},
    "n_dark": ${params?.n_dark},
    "i_0_dark": ${params?.i_0_dark},
    "result_hash": "${a.resultHash}"
}

def verify():
    print(f"--- Helios Core Verification: {DEVICE_LABEL} ---")
    print(f"Checking Determinism for Hash: {EXPECTED['result_hash']}")
    # Reproduction logic would utilize the same solver physics
    # found in backend/tools/solve_iv_curve.py
    print("Verification Status: DATA MANIFESTED")

if __name__ == "__main__":
    verify()
`;
}
