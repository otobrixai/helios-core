"""
POST /analyze endpoint for IV curve analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from backend.tools.manage_storage import (
    get_measurement,
    get_import_record,
    list_analyses_for_measurement,
)
from backend.tools.ingest_file import extract_iv_data
from backend.tools.solve_iv_curve import analyze_measurement
from backend.models.entities import AnalysisMode, ModelType, AnalysisStatus, MeasurementType
from backend.services.physics_service import extract_ideality_from_slope


router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for analysis."""
    measurement_id: str
    mode: str = "Exploration"  # "Exploration" or "Reference"
    model_type: str = "OneDiode"  # "OneDiode" or "TwoDiode"
    area_cm2: Optional[float] = None
    temperature_k: Optional[float] = None


class AnalyzeResponse(BaseModel):
    """Response from analysis endpoint."""
    analysis_id: str
    status: str
    mode: str
    j_sc: Optional[float] = None
    v_oc: Optional[float] = None
    ff: Optional[float] = None
    pce: Optional[float] = None
    r_s: Optional[float] = None
    r_sh: Optional[float] = None
    n_ideality: Optional[float] = None
    # Fundamental Physics
    n_slope: Optional[float] = None
    n_dark: Optional[float] = None
    i_0_dark: Optional[float] = None
    r_s_dark: Optional[float] = None
    r_sh_dark: Optional[float] = None
    result_hash: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    """Analyze an IV curve measurement."""
    try:
        # Get measurement
        measurement = get_measurement(UUID(request.measurement_id))
        if measurement is None:
            print(f"[Analyze Error] Measurement not found: {request.measurement_id}")
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        # Get import record
        import_record = get_import_record(measurement.import_record_id)
        if import_record is None:
            print(f"[Analyze Error] Import record not found: {measurement.import_record_id}")
            raise HTTPException(status_code=404, detail="Import record not found")
        
        # Extract IV data
        target_map = measurement.column_map or import_record.column_map
        try:
            V, I = extract_iv_data(measurement, target_map)
        except Exception as e:
            print(f"[Analyze Error] Data extraction failed: {e}")
            raise ValueError(f"Data extraction failed: {e}")
            
        print(f"[Analyze Trace] Input data shape: {V.shape}, Mapping: {target_map.voltage_column}/{target_map.current_column}")
        
        # Parse settings
        mode = AnalysisMode(request.mode)
        model_type = ModelType(request.model_type)
        
        # Apply metadata overrides if provided
        if request.area_cm2 is not None:
            measurement = measurement.model_copy(update={
                "metadata": measurement.metadata.model_copy(update={"cell_area_cm2": request.area_cm2})
            })
        if request.temperature_k is not None:
            measurement = measurement.model_copy(update={
                "metadata": measurement.metadata.model_copy(update={"temperature_c": request.temperature_k - 273.15})
            })
        
        # Run analysis
        analysis = analyze_measurement(
            measurement=measurement,
            V=V,
            I=I,
            mode=mode,
            model_type=model_type,
        )
        
        if analysis.status == AnalysisStatus.INVALID:
            print(f"[Analyze Warning] Physics engine returned invalid status: {analysis.error_message}")
        
        # Build response
        response = AnalyzeResponse(
            analysis_id=str(analysis.id),
            status=analysis.status.value,
            mode=analysis.mode.value,
            result_hash=analysis.result_hash,
            error_message=analysis.error_message,
        )
        
        if analysis.parameters:
            response.j_sc = analysis.parameters.j_sc
            response.v_oc = analysis.parameters.v_oc
            response.ff = analysis.parameters.ff
            response.pce = analysis.parameters.pce
            response.r_s = analysis.parameters.r_s
            response.r_sh = analysis.parameters.r_sh
            response.n_ideality = analysis.parameters.n_ideality
            
            # Extract additional physics with light-bias compensation if applicable
            is_light = measurement.metadata.measurement_type == MeasurementType.LIGHT
            response.n_slope = extract_ideality_from_slope(
                V, I, 
                temp_c=measurement.metadata.temperature_c,
                is_light=is_light,
                j_sc=analysis.parameters.j_sc
            )
            response.n_dark = analysis.parameters.n_dark
            response.i_0_dark = analysis.parameters.i_0_dark
            response.r_s_dark = analysis.parameters.r_s_dark
            response.r_sh_dark = analysis.parameters.r_sh_dark
        
        return response
        
    except ValueError as e:
        print(f"[Analyze 400] {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Analyze 500] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.get("/analyses/{measurement_id}")
async def list_analyses(measurement_id: str):
    """List all analyses for a measurement."""
    try:
        analyses = list_analyses_for_measurement(UUID(measurement_id))
        return [
            {
                "id": str(a.id),
                "timestamp": a.timestamp.isoformat(),
                "mode": a.mode.value,
                "status": a.status.value,
                "result_hash": a.result_hash,
            }
            for a in analyses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
