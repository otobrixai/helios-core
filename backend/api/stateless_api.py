"""
Helios Core — Stateless API Routes
For session-based, zero-DB deployments.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
import os
import shutil
import hashlib
import json
import numpy as np
import re
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from backend.tools.generate_bundle import generate_supplementary_bundle

from backend.tools.ingest_file import (
    _detect_encoding, 
    _parse_to_dataframe, 
    detect_hardware_profile, 
    detect_column_mapping,
    detect_multi_pixel_columns,
    detect_time_column,
    _extract_unit
)
from backend.tools.solve_iv_curve import (
    analyze_measurement, 
    one_diode_equation, 
    two_diode_equation
)
from backend.services.diagnostic_service import DiagnosticReport
from backend.models.entities import (
    AnalysisMode, 
    ModelType, 
    AnalysisStatus, 
    Measurement, 
    ImportRecord, 
    MeasurementMetadata,
    ColumnMap,
    HardwareProfile,
    MeasurementType,
    SolverConfig,
    ExtractedParameters,
    Analysis
)
from backend.services.physics_service import extract_ideality_from_slope
from backend.services.citation_service import generate_physics_audit_id, generate_bibtex

router = APIRouter()

class StatelessExportRequest(BaseModel):
    voltage: List[float]
    current: List[float]
    device_label: str
    mode: str
    model_type: str = "OneDiode"
    area_cm2: float
    temperature_k: float
    results: dict  # derived parameters
    result_hash: str

def extract_area_from_header(content_str: str) -> Optional[float]:
    """
    Attempt to extract device area from file header content.
    """
    try:
        # Look for common area patterns in the first 4000 chars
        area_patterns = [
            r"device\s*area\s*[:=\t,]\s*([\d\.]+)",
            r"area\s*\(?cm2\)?\s*[:=\t,]\s*([\d\.]+)",
            r"area\s*\(?cm\^2\)?\s*[:=\t,]\s*([\d\.]+)",
        ]
        for pattern in area_patterns:
            match = re.search(pattern, content_str[:4000], re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        # Special case for tabular metadata
        lines = content_str.split('\n')
        if len(lines) > 2:
            for i in range(min(5, len(lines))):
                headers = [h.strip().lower() for h in re.split(r'[\t,]', lines[i])]
                if "device area" in headers:
                    idx = headers.index("device area")
                    if i + 1 < len(lines):
                        values = re.split(r'[\t,]', lines[i+1])
                        if len(values) > idx:
                            try:
                                return float(values[idx].strip())
                            except ValueError:
                                pass
    except Exception as e:
        print(f"[Stateless] Warning: Failed to extract area locally: {e}")
    return None

class StatelessProcessResponse(BaseModel):
    filename: str
    file_hash: str
    hardware_profile: str
    encoding: str
    low_confidence: bool
    measurements: List[dict]
    detected_area: Optional[float] = None

class StatelessAnalyzeRequest(BaseModel):
    voltage: List[float]
    current: List[float]
    device_label: str
    mode: str = "Exploration"
    model_type: str = "OneDiode"
    area_cm2: float = 1.0
    temperature_k: float = 298.15
    measurement_type: str = "light"

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
        detected_area = None  # Initialize before conditional branches
        
        if multi_pixels:
            for i, (v_col, i_col) in enumerate(multi_pixels):
                V = df[v_col].astype(float).values
                I = df[i_col].astype(float).values
                
                # Unit conversion to standard A
                i_unit = _extract_unit(i_col, "A").lower()
                if "ma" in i_unit:
                    I = I / 1000.0
                elif "ua" in i_unit or "µa" in i_unit:
                    I = I / 1e6
                
                measurements_data.append({
                    "device_label": f"{file.filename}_Pixel_{i+1}",
                    "voltage": V.tolist(),
                    "current": I.tolist(),
                    "v_column": v_col,
                    "i_column": i_col
                })
        else:
            # Detect Area from header
            detected_area = extract_area_from_header(content_str)
            area_to_use = detected_area if detected_area is not None else 1.0

            cmap = detect_column_mapping(df)
            V = df[cmap.voltage_column].astype(float).values
            I = df[cmap.current_column].astype(float).values
            
            # Unit conversion to standard A
            i_unit = cmap.current_unit.lower()
            is_density = "/cm" in i_unit or "cm^2" in i_unit

            if "ma" in i_unit:
                I = I / 1000.0
            elif "ua" in i_unit or "µa" in i_unit:
                I = I / 1e6
            
            # Density handling
            if is_density:
                I = I * area_to_use
                
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
            measurements=measurements_data,
            detected_area=detected_area
        )

    except Exception as e:
        import traceback
        print(f"[Stateless] Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")

@router.post("/analyze")
async def analyze_stateless(request: StatelessAnalyzeRequest):
    """
    Analyze IV data and return results with full diagnostics.
    No database records created.
    """
    try:
        V = np.array(request.voltage, dtype=np.float64)
        I_measured = np.array(request.current, dtype=np.float64)
        
        
        # Measurement needs an ID, we'll use a random one as it's not persisted
        measurement = Measurement(
            id=uuid4(),
            import_record_id=uuid4(),
            device_label=request.device_label,
            raw_data_path="stateless",
            metadata=MeasurementMetadata(
                cell_area_cm2=request.area_cm2,
                temperature_c=request.temperature_k - 273.15,
                measurement_type=MeasurementType(request.measurement_type)
            )
        )
        
        # Run physics engine
        analysis = analyze_measurement(
            measurement=measurement,
            V=V,
            I=I_measured,
            mode=AnalysisMode(request.mode),
            model_type=ModelType(request.model_type),
        )
        
        # Generate Diagnostics
        diagnostic_report = None
        I_fitted = None
        if analysis.status == AnalysisStatus.VALID and analysis.parameters:
            p = analysis.parameters
            try:
                # Reconstruct fitted curve for residuals based on model type
                if analysis.solver_config.model_type == ModelType.TWO_DIODE:
                    I_fitted = two_diode_equation(
                        V=V,
                        I_ph=p.i_ph or 0.0,
                        I_01=p.i_0 or 1e-12,
                        n1=p.n_ideality or 1.0,
                        I_02=getattr(p, 'i_02', 1e-12),
                        n2=getattr(p, 'n2_ideality', 2.0),
                        R_s=p.r_s / request.area_cm2,
                        R_sh=p.r_sh / request.area_cm2,
                        T_k=request.temperature_k
                    )
                else:
                    I_fitted = one_diode_equation(
                        V=V,
                        I_ph=p.i_ph or 0.0,
                        I_0=p.i_0 or 1e-12,
                        n=p.n_ideality or 1.0,
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
            except Exception as e:
                print(f"Diagnostic generation failed: {e}")
                # We still want to return the results even if diagnostics fail

        # Prepare response
        res = {
            "status": analysis.status.value,
            "mode": analysis.mode.value,
            "result_hash": analysis.result_hash,
            "error_message": analysis.error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": diagnostic_report,
            "audit_id": generate_physics_audit_id(analysis.solver_config),
            "bibtex": generate_bibtex(
                generate_physics_audit_id(analysis.solver_config), 
                analysis.mode, 
                str(analysis.id)
            )
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
                "i_ph": analysis.parameters.i_ph,
                "i_0": analysis.parameters.i_0,
                # Physics additions with light-bias compensation
                "n_slope": extract_ideality_from_slope(
                    V, I_measured, 
                    temp_c=request.temperature_k - 273.15,
                    is_light=request.measurement_type == "light",
                    j_sc=analysis.parameters.j_sc
                ),
                "n_dark": analysis.parameters.n_dark,
                "i_0_dark": analysis.parameters.i_0_dark,
                "r_s_dark": analysis.parameters.r_s_dark,
                "r_sh_dark": analysis.parameters.r_sh_dark,
                "fit_current": I_fitted.tolist() if I_fitted is not None else None
            })
            
        return res

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/export-bundle")
async def download_bundle_stateless(request: StatelessExportRequest, background_tasks: BackgroundTasks):
    """
    Generate a full export bundle (PDF/SVG/LaTeX) from stateless session data.
    Creates a temporary raw file to satisfy the bundle generator's contract.
    """
    try:
        # 1. Create Transient Entities
        meas_id = uuid4()
        ana_id = uuid4()
        
        # Write temp raw file
        temp_dir = Path("temp_stateless_export")
        temp_dir.mkdir(exist_ok=True)
        raw_path = temp_dir / f"{request.device_label}_{meas_id}.csv"
        
        # Reconstruct CSV content
        df = pd.DataFrame({"V": request.voltage, "I": request.current})
        df.to_csv(raw_path, index=False)
        
        # Cleanup task
        def cleanup_files():
            try:
                if raw_path.exists(): os.remove(raw_path)
                # Cleanup zip if needed (handled by FileResponse usually?)
            except Exception:
                pass
        background_tasks.add_task(cleanup_files)

        measurement = Measurement(
            id=meas_id,
            import_record_id=uuid4(),
            device_label=request.device_label,
            raw_data_path=str(raw_path),
            metadata=MeasurementMetadata(
                cell_area_cm2=request.area_cm2,
                temperature_c=request.temperature_k - 273.15,
                measurement_type=MeasurementType.LIGHT
            ),
            column_map=ColumnMap(
                voltage_column="V", 
                current_column="I",
                voltage_unit="V", 
                current_unit="A"
            )
        )
        
        solver_config = SolverConfig(
            model_type=ModelType(request.model_type),
            solver_seed=42  # Standard lock
        )
        
        # Reconstruct parameters
        r = request.results
        params = ExtractedParameters(
            j_sc=r.get("j_sc") or 0.0,
            v_oc=r.get("v_oc") or 0.0,
            ff=r.get("ff") or 0.0,
            pce=r.get("pce") or 0.0,
            r_s=r.get("r_s") or 0.0,
            r_sh=r.get("r_sh") or 0.0,
            n_ideality=r.get("n_ideality") or 1.0,
            i_ph=r.get("i_ph"),
            i_0=r.get("i_0"),
            n_dark=r.get("n_dark"),
            i_0_dark=r.get("i_0_dark"),
            r_s_dark=r.get("r_s_dark"),
            r_sh_dark=r.get("r_sh_dark"),
            delta_n=r.get("n_slope")  # Mapping n_slope to delta_n for report context
        )

        analysis = Analysis(
            id=ana_id,
            measurement_id=meas_id,
            timestamp=datetime.utcnow(),
            mode=AnalysisMode(request.mode),
            status=AnalysisStatus.VALID,
            solver_config=solver_config,
            parameters=params,
            result_hash=request.result_hash
        )

        # 2. Generate Bundle
        bundle_path = generate_supplementary_bundle(analysis, measurement)
        
        # Add bundle path to cleanup
        def cleanup_bundle():
            try:
                if bundle_path.exists(): os.remove(bundle_path)
            except: pass
        background_tasks.add_task(cleanup_bundle)

        return FileResponse(
            path=bundle_path,
            media_type="application/zip",
            filename=f"helios_stateless_bundle_{request.device_label}.zip"
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
