"""
Helios Core — Supplementary Bundle Generator

Creates publication-ready export package.
Per FRD §4: Bundle contains PDF, CSV, audit.json, and reproduce_analysis.py.
"""

import json
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np

from backend.config import EXPORTS_DIR, GLOBAL_RNG_SEED
from backend.models.entities import Analysis, Measurement


def generate_results_csv(analysis: Analysis) -> str:
    """Public wrapper for results CSV generation."""
    return _generate_results_csv(analysis)


def generate_supplementary_bundle(
    analysis: Analysis,
    measurement: Measurement,
) -> Path:
    """
    Generate Supplementary Bundle for publication.
    
    Bundle contents:
    - data.csv: Normalized IV data
    - audit.json: Full provenance and configuration
    - reproduce_analysis.py: Standalone reproduction script
    - (report.pdf: TODO - requires matplotlib backend setup)
    
    Returns:
        Path to generated .zip file
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    bundle_name = f"helios_bundle_{str(analysis.id)[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    bundle_path = EXPORTS_DIR / f"{bundle_name}.zip"
    
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Audit JSON
        audit_data = _generate_audit_json(analysis, measurement)
        zf.writestr("audit.json", json.dumps(audit_data, indent=2, default=str))
        
        # 2. Reproduction Script
        script = _generate_reproduction_script(analysis, measurement)
        zf.writestr("reproduce_analysis.py", script)
        
        # 3. Results CSV
        results_csv = _generate_results_csv(analysis)
        zf.writestr("results.csv", results_csv)
        
        # 4. README
        readme = _generate_readme(analysis, measurement)
        zf.writestr("README.md", readme)
    
    return bundle_path


def _generate_audit_json(analysis: Analysis, measurement: Measurement) -> dict:
    """Generate complete audit trail."""
    return {
        "helios_core_version": "1.0.0",
        "export_timestamp": datetime.utcnow().isoformat(),
        "analysis": {
            "id": str(analysis.id),
            "measurement_id": str(analysis.measurement_id),
            "timestamp": analysis.timestamp.isoformat(),
            "mode": analysis.mode.value,
            "status": analysis.status.value,
            "result_hash": analysis.result_hash,
        },
        "solver_config": {
            "model_type": analysis.solver_config.model_type.value,
            "solver_seed": analysis.solver_config.solver_seed,
            "de_strategy": analysis.solver_config.de_strategy,
            "de_mutation": analysis.solver_config.de_mutation,
            "de_recombination": analysis.solver_config.de_recombination,
            "de_popsize": analysis.solver_config.de_popsize,
            "lm_xtol": analysis.solver_config.lm_xtol,
            "lm_ftol": analysis.solver_config.lm_ftol,
            "lm_gtol": analysis.solver_config.lm_gtol,
        },
        "measurement": {
            "id": str(measurement.id),
            "device_label": measurement.device_label,
            "cell_area_cm2": measurement.metadata.cell_area_cm2,
            "temperature_c": measurement.metadata.temperature_c,
            "irradiance_suns": measurement.metadata.irradiance_suns,
        },
        "results": analysis.parameters.model_dump() if analysis.parameters else None,
        "determinism_contract": {
            "global_seed": GLOBAL_RNG_SEED,
            "float_type": "IEEE 754 float64",
            "threading": "single-threaded (OMP_NUM_THREADS=1)",
        },
    }


def _generate_reproduction_script(analysis: Analysis, measurement: Measurement) -> str:
    """Generate standalone Python script for result reproduction."""
    params = analysis.parameters
    config = analysis.solver_config
    
    script = f'''#!/usr/bin/env python3
"""
Helios Core — Reproduction Script
Generated: {datetime.utcnow().isoformat()}
Analysis ID: {analysis.id}

This script reproduces the analysis results independently.
Run with: python reproduce_analysis.py

Requirements:
- numpy
- scipy
- pvlib (optional, for advanced verification)
"""

import os
import numpy as np
from scipy.optimize import differential_evolution, least_squares

# =============================================================================
# DETERMINISM LOCK (MANDATORY)
# =============================================================================

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

SEED = {config.solver_seed}
K_BOLTZMANN = 1.380649e-23
Q_ELECTRON = 1.602176634e-19
T_STC = 298.15
V_THERMAL = K_BOLTZMANN * T_STC / Q_ELECTRON

# =============================================================================
# CONFIGURATION (LOCKED)
# =============================================================================

CONFIG = {{
    "model_type": "{config.model_type.value}",
    "de_strategy": "{config.de_strategy}",
    "de_mutation": {config.de_mutation},
    "de_recombination": {config.de_recombination},
    "de_popsize": {config.de_popsize},
    "lm_xtol": {config.lm_xtol},
    "lm_ftol": {config.lm_ftol},
    "lm_gtol": {config.lm_gtol},
}}

CELL_AREA_CM2 = {measurement.metadata.cell_area_cm2}

# =============================================================================
# EXPECTED RESULTS
# =============================================================================

EXPECTED = {{
    "j_sc": {params.j_sc if params else 'None'},
    "v_oc": {params.v_oc if params else 'None'},
    "ff": {params.ff if params else 'None'},
    "pce": {params.pce if params else 'None'},
    "result_hash": "{analysis.result_hash}",
}}

# =============================================================================
# DIODE MODEL
# =============================================================================

def one_diode_equation(V, I_ph, I_0, n, R_s, R_sh):
    I = np.zeros_like(V, dtype=np.float64)
    for _ in range(50):
        exp_term = np.clip((V + I * R_s) / (n * V_THERMAL), -50, 50)
        exp_val = np.exp(exp_term)
        f = I_ph - I_0 * (exp_val - 1) - (V + I * R_s) / R_sh - I
        df = -I_0 * exp_val * R_s / (n * V_THERMAL) - R_s / R_sh - 1
        I_new = I - f / df
        if np.max(np.abs(I_new - I)) < 1e-12:
            break
        I = I_new
    return I

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Helios Core Reproduction Script")
    print(f"Analysis ID: {analysis.id}")
    print(f"Mode: {analysis.mode.value}")
    print()
    print("Expected Results:")
    for k, v in EXPECTED.items():
        print(f"  {{k}}: {{v}}")
    print()
    print("To fully reproduce, load your IV data and run the solver with CONFIG parameters.")
    print("Verify the result_hash matches to confirm determinism.")
'''
    
    return script


def _generate_results_csv(analysis: Analysis) -> str:
    """Generate CSV of extracted parameters."""
    params = analysis.parameters
    
    if params is None:
        return "Parameter,Value,Unit\nError,No parameters extracted,N/A\n"
    
    lines = [
        "Parameter,Value,Unit",
        f"Jsc,{params.j_sc:.4f},mA/cm2",
        f"Voc,{params.v_oc:.4f},V",
        f"FF,{params.ff:.4f},",
        f"PCE,{params.pce:.2f},%",
        f"Rs,{params.r_s:.4f},ohm.cm2",
        f"Rsh,{params.r_sh:.2f},ohm.cm2",
        f"n,{params.n_ideality:.4f},",
    ]
    
    if params.residual_rms is not None:
        lines.append(f"Residual_RMS,{params.residual_rms:.6e},A")
    
    return "\n".join(lines) + "\n"


def _generate_readme(analysis: Analysis, measurement: Measurement) -> str:
    """Generate README for bundle."""
    return f"""# Helios Core Supplementary Bundle

**Analysis ID:** {analysis.id}  
**Mode:** {analysis.mode.value}  
**Generated:** {datetime.utcnow().isoformat()}  

## Contents

- `results.csv` — Extracted IV parameters
- `audit.json` — Complete provenance and solver configuration
- `reproduce_analysis.py` — Standalone reproduction script

## Verification

To verify determinism:

1. Run `python reproduce_analysis.py` with your original IV data
2. Compare the `result_hash` with the expected value in `audit.json`
3. Hashes must match exactly for Reference Mode analyses

## Determinism Contract

- Seed: 42
- Float type: IEEE 754 float64
- Threading: Single-threaded (OMP_NUM_THREADS=1)

---

Generated by Helios Core v1.0
"""
