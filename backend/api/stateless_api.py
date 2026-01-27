"""
Helios Core — Stateless API Routes
For session-based, zero-DB deployments.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
import hashlib
import json
import numpy as np
from datetime import datetime
from uuid import uuid4

from backend.tools.ingest_file import (
    _detect_encoding, 
    _parse_to_dataframe, 
    detect_hardware_profile, 
    detect_column_mapping,
    detect_multi_pixel_columns,
    detect_time_column,
    _extract_unit
)
from backend.tools.solve_iv_curve import analyze_measurement
from backend.models.entities import (
    AnalysisMode, 
    ModelType, 
    AnalysisStatus, 
    Measurement, 
    ImportRecord, 
    MeasurementMetadata,
    ColumnMap,
    HardwareProfile
)

router = APIRouter()

class StatelessProcessResponse(BaseModel):
    filename: str
    file_hash: str
    hardware_profile: str
    encoding: str
    low_confidence: bool
    measurements: List[dict]

class StatelessAnalyzeRequest(BaseModel):
    voltage: List[float]
    current: List[float]
    device_label: str
    mode: str = "Exploration"
    model_type: str = "OneDiode"
    area_cm2: float = 1.0
    temperature_k: float = 298.15

@router.post("/process", response_model=StatelessProcessResponse)
async def process_file_stateless(file: UploadFile = File(...)):
    """
    Process an uploaded file and return all data immediately.
    No database or disk storage used.
    """
    try:
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        encoding = _detect_encoding(content)
        
        try:
            content_str = content.decode(encoding)
        except UnicodeDecodeError:
            content_str = content.decode("latin-1")
            encoding = "latin-1"

        hardware_profile, low_confidence = detect_hardware_profile(content_str, file.filename)
        df = _parse_to_dataframe(content, file.filename, encoding)
        
        # Detect columns
        multi_pixels = detect_multi_pixel_columns(df)
        
        measurements_data = []
        
        if multi_pixels:
            for i, (v_col, i_col) in enumerate(multi_pixels):
                V = df[v_col].astype(float).values
                I = df[i_col].astype(float).values
                
                # Unit conversion (mA -> A)
                v_unit = _extract_unit(v_col, "V")
                i_unit = _extract_unit(i_col, "A")
                if i_unit.lower() == "ma":
                    I = I / 1000.0
                
                measurements_data.append({
                    "device_label": f"{file.filename}_Pixel_{i+1}",
                    "voltage": V.tolist(),
                    "current": I.tolist(),
                    "v_column": v_col,
                    "i_column": i_col
                })
        else:
            cmap = detect_column_mapping(df)
            V = df[cmap.voltage_column].astype(float).values
            I = df[cmap.current_column].astype(float).values
            
            if cmap.current_unit.lower() == "ma":
                I = I / 1000.0
                
            measurements_data.append({
                "device_label": file.filename.split('.')[0],
                "voltage": V.tolist(),
                "current": I.tolist(),
                "v_column": cmap.voltage_column,
                "i_column": cmap.current_column
            })

        return StatelessProcessResponse(
            filename=file.filename,
            file_hash=file_hash,
            hardware_profile=hardware_profile.value,
            encoding=encoding,
            low_confidence=low_confidence,
            measurements=measurements_data
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")

from backend.services.diagnostic_service import DiagnosticReport
from backend.tools.solve_iv_curve import analyze_measurement, one_diode_equation

@router.post("/analyze")
async def analyze_stateless(request: StatelessAnalyzeRequest):
    """
    Analyze IV data and return results with full diagnostics.
    No database records created.
    """
    try:
        V = np.array(request.voltage, dtype=np.float64)
        I_measured = np.array(request.current, dtype=np.float64)
        
        # Create a mock measurement object for the solver
        metadata = MeasurementMetadata(
            cell_area_cm2=request.area_cm2,
            temperature_c=request.temperature_k - 273.15
        )
        
        # Measurement needs an ID, we'll use a random one as it's not persisted
        measurement = Measurement(
            id=uuid4(),
            import_record_id=uuid4(),
            device_label=request.device_label,
            raw_data_path="stateless",
            metadata=metadata
        )
        
        # Run physics engine
        analysis = analyze_measurement(
            measurement=measurement,
            V=V,
            I=I_measured,
            mode=AnalysisMode(request.mode),
            model_type=ModelType(request.model_type)
        )
        
        # Generate Diagnostics
        diagnostic_report = None
        if analysis.status == AnalysisStatus.VALID and analysis.parameters:
            p = analysis.parameters
            # Reconstruct fitted curve for residuals
            I_fitted = one_diode_equation(
                V=V,
                I_ph=p.i_ph,
                I_0=p.i_0,
                n=p.n_ideality,
                R_s=p.r_s / request.area_cm2,
                R_sh=p.r_sh / request.area_cm2,
                T_k=request.temperature_k
            )
            
            report = DiagnosticReport(analysis_id="stateless", mode=request.mode)
            report.analyze_residuals(voltage=V, measured=I_measured, fitted=I_fitted)
            
            diag_params = {
                'n': p.n_ideality, 
                'Rs': p.r_s, 
                'Rsh': p.r_sh
            }
            bounds = {
                'n': (0.8, 2.5), 
                'Rs': (0, 1000), 
                'Rsh': (1.0, 1e9)
            }
            report.analyze_boundary_stress(diag_params, bounds)
            diagnostic_report = report.generate_report()

        # Prepare response
        res = {
            "status": analysis.status.value,
            "mode": analysis.mode.value,
            "result_hash": analysis.result_hash,
            "error_message": analysis.error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": diagnostic_report
        }
        
        if analysis.parameters:
            res.update({
                "j_sc": analysis.parameters.j_sc,
                "v_oc": analysis.parameters.v_oc,
                "ff": analysis.parameters.ff,
                "pce": analysis.parameters.pce,
                "r_s": analysis.parameters.r_s,
                "r_sh": analysis.parameters.r_sh,
                "n_ideality": analysis.parameters.n_ideality,
                "fit_current": I_fitted.tolist() if 'I_fitted' in locals() else None
            })
            
        return res

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
