"""
Helios Core — Data Access API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from uuid import UUID
import numpy as np

from backend.tools.manage_storage import get_measurement, get_analysis
from backend.tools.ingest_file import extract_iv_data
from backend.tools.solve_iv_curve import one_diode_equation, two_diode_equation
from backend.models.entities import ModelType

router = APIRouter()

@router.get("/measurements/{measurement_id}/data")
async def get_measurement_data(measurement_id: str, area_cm2: float = None, temperature_k: float = None):
    """Get raw data points for a measurement."""
    measurement = get_measurement(UUID(measurement_id))
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # We need the parent import record's column map if not overridden
    from backend.tools.manage_storage import get_import_record
    import_record = get_import_record(measurement.import_record_id)
    target_map = measurement.column_map or import_record.column_map
    
    # Apply overrides
    area = area_cm2 if area_cm2 is not None else measurement.metadata.cell_area_cm2
    
    try:
        V, I = extract_iv_data(measurement, target_map)
        # Convert to current density J (mA/cm2) for consistent display
        J = I / area * 1000
        
        points = []
        for v, j in zip(V, J):
            points.append({
                "voltage": float(v),
                "current": float(j),
                "power": float(v * j)
            })
        return points
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses/{analysis_id}/fit")
async def get_analysis_fit(analysis_id: str, area_cm2: float = None, temperature_k: float = None):
    """Get fitted curve points for an analysis."""
    analysis = get_analysis(UUID(analysis_id))
    if not analysis or not analysis.parameters:
        raise HTTPException(status_code=404, detail="Analysis or parameters not found")
    
    measurement = get_measurement(analysis.measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    # Use parent import record's map to get voltage range
    from backend.tools.manage_storage import get_import_record
    import_record = get_import_record(measurement.import_record_id)
    target_map = measurement.column_map or import_record.column_map
    V_raw, _ = extract_iv_data(measurement, target_map)
    
    # Create high-resolution V range for smooth plot
    V_fit = np.linspace(np.min(V_raw), np.max(V_raw), 200)
    
    # Apply overrides
    area = area_cm2 if area_cm2 is not None else measurement.metadata.cell_area_cm2
    temp_k = temperature_k if temperature_k is not None else (measurement.metadata.temperature_c + 273.15)
    
    p = analysis.parameters
    
    try:
        if analysis.solver_config.model_type == ModelType.ONE_DIODE:
            I_fit = one_diode_equation(V_fit, p.i_ph, p.i_0, p.n_ideality, p.r_s / area, p.r_sh / area, temp_k)
        else:
            # Fallback to one-diode if parameters missing
            I_fit = one_diode_equation(V_fit, p.i_ph, p.i_0, p.n_ideality, p.r_s / area, p.r_sh / area, temp_k)

        # Convert to J (mA/cm2)
        J_fit = I_fit / area * 1000
        
        points = []
        for v, j in zip(V_fit, J_fit):
            points.append({
                "voltage": float(v),
                "fit_current": float(j),
                "fit_power": float(v * j)
            })
        return points
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
