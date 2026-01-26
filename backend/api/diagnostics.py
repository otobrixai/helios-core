"""
Helios Core — Diagnostics API Routes
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID
import numpy as np

from backend.tools.manage_storage import get_analysis, get_measurement, get_import_record
from backend.tools.ingest_file import extract_iv_data
from backend.services.diagnostic_service import DiagnosticReport
from backend.tools.solve_iv_curve import one_diode_equation, two_diode_equation
from backend.models.entities import ModelType

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

async def _get_base_diagnostic_data(analysis_id: str):
    """Helper to fetch common data for diagnostics."""
    # 1. Fetch Analysis
    analysis = get_analysis(UUID(analysis_id))
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.parameters:
        raise HTTPException(status_code=400, detail="Analysis has no parameters (Status: INVALID)")
        
    # 2. Fetch Measurement & Data
    measurement = get_measurement(analysis.measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
        
    import_record = get_import_record(measurement.import_record_id)
    target_map = measurement.column_map or import_record.column_map
    
    V, I_measured = extract_iv_data(measurement, target_map)
    
    # 3. Reconstruct Fitted Curve
    p = analysis.parameters
    T_k = measurement.metadata.temperature_c + 273.15
    area = measurement.metadata.cell_area_cm2
    
    if analysis.solver_config.model_type == ModelType.ONE_DIODE:
        I_fitted = one_diode_equation(
            V=V,
            I_ph=p.i_ph,
            I_0=p.i_0,
            n=p.n_ideality,
            R_s=p.r_s / area,
            R_sh=p.r_sh / area,
            T_k=T_k
        )
    else:
        I_fitted = two_diode_equation(
            V=V,
            I_ph=p.i_ph,
            I_01=p.i_0,
            n1=p.n_ideality,
            I_02=0.0,
            n2=p.n2_ideality or 2.0,
            R_s=p.r_s / area,
            R_sh=p.r_sh / area,
            T_k=T_k
        )
    
    return analysis, measurement, V, I_measured, I_fitted

@router.get("/{analysis_id}")
async def get_diagnostics(analysis_id: str):
    """Get comprehensive diagnostics (Legacy/Fallback)."""
    try:
        analysis, measurement, V, I_measured, I_fitted = await _get_base_diagnostic_data(analysis_id)
        
        report = DiagnosticReport(analysis_id=str(analysis.id), mode=analysis.mode.value)
        report.analyze_residuals(voltage=V, measured=I_measured, fitted=I_fitted)
        
        diag_params = {'n': analysis.parameters.n_ideality, 'Rs': analysis.parameters.r_s, 'Rsh': analysis.parameters.r_sh}
        bounds = {'n': (0.8, 2.5), 'Rs': (0, 1000), 'Rsh': (1.0, 1e9)}
        report.analyze_boundary_stress(diag_params, bounds)
        
        return report.generate_report()
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}/quick")
async def get_quick_diagnostics(analysis_id: str):
    """Quick stage: Residuals only."""
    try:
        analysis, measurement, V, I_measured, I_fitted = await _get_base_diagnostic_data(analysis_id)
        report = DiagnosticReport(analysis_id=str(analysis.id), mode=analysis.mode.value)
        report.analyze_residuals(voltage=V, measured=I_measured, fitted=I_fitted)
        return report.generate_report()
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}/full")
async def get_full_diagnostics(analysis_id: str):
    """Full stage: Residuals + Boundary Stress + Audit."""
    try:
        analysis, measurement, V, I_measured, I_fitted = await _get_base_diagnostic_data(analysis_id)
        report = DiagnosticReport(analysis_id=str(analysis.id), mode=analysis.mode.value)
        report.analyze_residuals(voltage=V, measured=I_measured, fitted=I_fitted)
        
        diag_params = {'n': analysis.parameters.n_ideality, 'Rs': analysis.parameters.r_s, 'Rsh': analysis.parameters.r_sh}
        bounds = {'n': (0.8, 2.5), 'Rs': (0, 1000), 'Rsh': (1.0, 1e9)}
        report.analyze_boundary_stress(diag_params, bounds)
        
        return report.generate_report()
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
