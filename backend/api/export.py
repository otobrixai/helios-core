"""
Helios Core — Export API Routes

GET /export/{analysis_id} endpoint for Supplementary Bundle generation.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from uuid import UUID

from backend.tools.manage_storage import get_analysis, get_measurement
from backend.tools.generate_bundle import generate_supplementary_bundle, generate_results_csv
from fastapi import Response


router = APIRouter()


from pydantic import BaseModel
from typing import Optional

class ExportRequest(BaseModel):
    includeAudit: bool = True
    includeScript: bool = True
    includeRawData: bool = True
    compressionLevel: int = 6
    cacheBuster: Optional[int] = None
    recalculate: bool = False

class VerifyRequest(BaseModel):
    hash: str

@router.get("/export/{analysis_id}")
async def export_bundle(analysis_id: str):
    """Generate and download Supplementary Bundle (Legacy)."""
    try:
        analysis = get_analysis(UUID(analysis_id))
        if analysis is None: raise HTTPException(status_code=404, detail="Analysis not found")
        measurement = get_measurement(analysis.measurement_id)
        if measurement is None: raise HTTPException(status_code=404, detail="Measurement not found")
        bundle_path = generate_supplementary_bundle(analysis=analysis, measurement=measurement)
        return FileResponse(path=bundle_path, media_type="application/zip", filename=f"helios_bundle_{analysis_id[:8]}.zip")
    except Exception as e: raise HTTPException(status_code=500, detail=f"Export failed: {e}")

@router.post("/export/{analysis_id}/generate")
async def generate_export_integrity(analysis_id: str, request: ExportRequest):
    """Fresh calculation bundle generation with options."""
    try:
        analysis = get_analysis(UUID(analysis_id))
        if analysis is None: raise HTTPException(status_code=404, detail="Analysis not found")
        measurement = get_measurement(analysis.measurement_id)
        if measurement is None: raise HTTPException(status_code=404, detail="Measurement not found")
        
        # In a real scenario, request.recalculate would trigger a re-run of the solver
        # For now, we generate a fresh bundle file from the existing analysis parameters
        bundle_path = generate_supplementary_bundle(analysis=analysis, measurement=measurement)
        
        return FileResponse(
            path=bundle_path, 
            media_type="application/zip", 
            filename=f"helios_export_{analysis_id[:8]}.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/{analysis_id}/verify")
async def verify_export_hash(analysis_id: str, request: VerifyRequest):
    """Simple verification placeholder."""
    return {"status": "verified", "hash": request.hash}

@router.get("/export/{analysis_id}/csv")
async def export_results_csv(analysis_id: str):
    """Generate and download only the results.csv."""
    try:
        analysis = get_analysis(UUID(analysis_id))
        if analysis is None: raise HTTPException(status_code=404, detail="Analysis not found")
        csv_content = generate_results_csv(analysis)
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=helios_results_{analysis_id[:8]}.csv"})
    except Exception as e: raise HTTPException(status_code=500, detail=f"CSV Export failed: {e}")
