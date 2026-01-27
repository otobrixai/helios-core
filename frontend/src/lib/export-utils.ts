import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { MeasurementSessionData, AnalysisSessionData, HeliosSessionExport } from '../types/stateless';

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

  // 3. Reproduction Scrips
  const scriptsFolder = zip.folder('reproduction');
  if (scriptsFolder) {
    analyses.forEach((a) => {
      const m = measurements.find(meas => meas.id === a.measurementId);
      if (m && a.results) {
        const script = generatePythonScript(m, a);
        scriptsFolder.file(`reproduce_${a.id.substring(0, 8)}.py`, script);
      }
    });
  }

  const content = await zip.generateAsync({ type: 'blob' });
  saveAs(content, `helios-core-session-${timestamp}.zip`);
}

function generateCSV(m: MeasurementSessionData): string {
  let csv = `${m.vColumn},${m.iColumn}\n`;
  for (let i = 0; i < m.voltage.length; i++) {
    csv += `${m.voltage[i]},${m.current[i]}\n`;
  }
  return csv;
}

function generatePythonScript(m: MeasurementSessionData, a: AnalysisSessionData): string {
  return `
# Helios Core Reproduction Script
# Analysis ID: ${a.id}
# Mode: ${a.mode}
# Model: ${a.modelType}

import numpy as np
import json

# Results for comparison
# Jsc: ${a.results?.j_sc} mA/cm2
# Voc: ${a.results?.v_oc} V
# FF: ${a.results?.ff}
# PCE: ${a.results?.pce} %

# Input Data
voltage = np.array(${JSON.stringify(m.voltage)}, dtype=np.float64)
current = np.array(${JSON.stringify(m.current)}, dtype=np.float64)
area_cm2 = ${m.areaCm2}

print(f"Reproducing analysis for {m.deviceLabel}...")
# Physics engine reproduction logic would go here
`;
}
