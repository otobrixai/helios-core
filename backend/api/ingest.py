"""
Helios Core — Ingestion API Routes

POST /ingest endpoint for file upload.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from backend.tools.ingest_file import ingest_file
from backend.tools.manage_storage import initialize_database
from backend.models.entities import HardwareProfile, MeasurementMetadata


router = APIRouter()

# Ensure database is initialized
initialize_database()


class IngestResponse(BaseModel):
    """Response from ingestion endpoint."""
    import_record_id: str
    source_filename: str
    hardware_profile: str
    low_confidence: bool
    measurement_count: int
    measurement_ids: list[str]


class IngestMetadata(BaseModel):
    """Optional metadata for ingestion."""
    cell_area_cm2: float = 1.0
    temperature_c: float = 25.0
    irradiance_suns: float = 1.0


@router.post("/ingest", response_model=IngestResponse)
async def ingest_file_endpoint(
    file: UploadFile = File(...),
    cell_area_cm2: float = 1.0,
    temperature_c: float = 25.0,
):
    """
    Ingest a raw IV measurement file.
    
    Supported formats: .csv, .txt, .xls, .xlsx
    """
    try:
        content = await file.read()
        
        metadata = MeasurementMetadata(
            cell_area_cm2=cell_area_cm2,
            temperature_c=temperature_c,
        )
        
        import_record, measurements = ingest_file(
            file_content=content,
            filename=file.filename or "unknown.csv",
            metadata=metadata,
        )
        
        return IngestResponse(
            import_record_id=str(import_record.id),
            source_filename=import_record.source_filename,
            hardware_profile=import_record.hardware_profile.value,
            low_confidence=import_record.low_confidence_flag,
            measurement_count=len(measurements),
            measurement_ids=[str(m.id) for m in measurements],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
