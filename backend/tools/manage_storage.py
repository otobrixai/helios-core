"""
Helios Core — Storage Manager

SQLite CRUD operations with immutability and hash integrity enforcement.
Per SOP_PERSISTENCE:
- Raw data is immutable
- Derived data is versioned
- Nothing is overwritten
- All relationships are traceable
"""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from backend.config import DATABASE_PATH, RAW_DATA_DIR
from backend.models.entities import (
    Analysis,
    AnalysisStatus,
    ImportRecord,
    Measurement,
    IMPORT_RECORD_TABLE,
    MEASUREMENT_TABLE,
    ANALYSIS_TABLE,
)


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_path() -> Path:
    """Get database path, ensuring parent directory exists."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DATABASE_PATH


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """Create database tables if they don't exist and handle migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(IMPORT_RECORD_TABLE)
        cursor.execute(MEASUREMENT_TABLE)
        cursor.execute(ANALYSIS_TABLE)
        
        # Migration: Add column_map to measurements if missing
        try:
            cursor.execute("ALTER TABLE measurements ADD COLUMN column_map TEXT")
        except sqlite3.OperationalError:
            # Column already exists
            pass


# =============================================================================
# HASHING — Per SOP_PERSISTENCE §6
# =============================================================================

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(content).hexdigest()


def compute_result_hash(parameters: dict, config: dict) -> str:
    """
    Compute determinism verification hash.
    Excludes timestamps, paths, and machine identifiers per specs/determinism.md §6.
    """
    # Sort keys for deterministic JSON serialization
    hashable = {
        "parameters": parameters,
        "config": config,
    }
    json_str = json.dumps(hashable, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


# =============================================================================
# IMPORT RECORD CRUD
# =============================================================================

def create_import_record(record: ImportRecord) -> ImportRecord:
    """
    Insert ImportRecord into database.
    Fails if file_hash already exists (per SOP: same file → same record).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check for existing hash
        cursor.execute(
            "SELECT id FROM import_records WHERE file_hash = ?",
            (record.file_hash,)
        )
        existing = cursor.fetchone()
        if existing:
            raise ValueError(
                f"ImportRecord with hash {record.file_hash[:16]}... already exists: {existing['id']}"
            )
        
        cursor.execute(
            """
            INSERT INTO import_records 
            (id, source_filename, file_hash, ingestion_timestamp, 
             hardware_profile, column_map, encoding_detected, low_confidence_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                record.source_filename,
                record.file_hash,
                record.ingestion_timestamp.isoformat(),
                record.hardware_profile.value,
                record.column_map.model_dump_json(),
                record.encoding_detected,
                int(record.low_confidence_flag),
            )
        )
    return record


def get_import_record(record_id: UUID) -> Optional[ImportRecord]:
    """Fetch ImportRecord by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM import_records WHERE id = ?",
            (str(record_id),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_import_record(row)


def get_import_record_by_hash(file_hash: str) -> Optional[ImportRecord]:
    """Fetch ImportRecord by file hash."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM import_records WHERE file_hash = ?",
            (file_hash,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_import_record(row)


def list_import_records() -> list[ImportRecord]:
    """List all ImportRecords."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_records ORDER BY ingestion_timestamp DESC")
        return [_row_to_import_record(row) for row in cursor.fetchall()]


def _row_to_import_record(row: sqlite3.Row) -> ImportRecord:
    """Convert database row to ImportRecord."""
    from backend.models.entities import ColumnMap, HardwareProfile
    return ImportRecord(
        id=UUID(row["id"]),
        source_filename=row["source_filename"],
        file_hash=row["file_hash"],
        ingestion_timestamp=datetime.fromisoformat(row["ingestion_timestamp"]),
        hardware_profile=HardwareProfile(row["hardware_profile"]),
        column_map=ColumnMap.model_validate_json(row["column_map"]),
        encoding_detected=row["encoding_detected"],
        low_confidence_flag=bool(row["low_confidence_flag"]),
    )


# =============================================================================
# MEASUREMENT CRUD
# =============================================================================

def create_measurement(measurement: Measurement) -> Measurement:
    """Insert Measurement into database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO measurements 
            (id, import_record_id, device_label, raw_data_path, metadata, column_map)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(measurement.id),
                str(measurement.import_record_id),
                measurement.device_label,
                measurement.raw_data_path,
                measurement.metadata.model_dump_json(),
                measurement.column_map.model_dump_json() if measurement.column_map else None,
            )
        )
    return measurement


def get_measurement(measurement_id: UUID) -> Optional[Measurement]:
    """Fetch Measurement by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM measurements WHERE id = ?",
            (str(measurement_id),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_measurement(row)


def list_measurements_for_import(import_record_id: UUID) -> list[Measurement]:
    """List all Measurements for an ImportRecord."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM measurements WHERE import_record_id = ?",
            (str(import_record_id),)
        )
        return [_row_to_measurement(row) for row in cursor.fetchall()]


def _row_to_measurement(row: sqlite3.Row) -> Measurement:
    """Convert database row to Measurement."""
    from backend.models.entities import MeasurementMetadata, ColumnMap
    return Measurement(
        id=UUID(row["id"]),
        import_record_id=UUID(row["import_record_id"]),
        device_label=row["device_label"],
        raw_data_path=row["raw_data_path"],
        metadata=MeasurementMetadata.model_validate_json(row["metadata"]),
        column_map=ColumnMap.model_validate_json(row["column_map"]) if row["column_map"] else None,
    )


# =============================================================================
# ANALYSIS CRUD
# =============================================================================

def create_analysis(analysis: Analysis) -> Analysis:
    """
    Insert Analysis into database.
    Per SOP_PERSISTENCE: Creates new versioned record, never updates existing.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analyses 
            (id, measurement_id, timestamp, mode, status, 
             solver_config, parameters, result_hash, masks_applied, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(analysis.id),
                str(analysis.measurement_id),
                analysis.timestamp.isoformat(),
                analysis.mode.value,
                analysis.status.value,
                analysis.solver_config.model_dump_json(),
                analysis.parameters.model_dump_json() if analysis.parameters else None,
                analysis.result_hash,
                json.dumps(analysis.masks_applied),
                analysis.error_message,
            )
        )
    return analysis


def get_analysis(analysis_id: UUID) -> Optional[Analysis]:
    """Fetch Analysis by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (str(analysis_id),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_analysis(row)


def list_analyses_for_measurement(measurement_id: UUID) -> list[Analysis]:
    """List all Analyses for a Measurement."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM analyses WHERE measurement_id = ? ORDER BY timestamp DESC",
            (str(measurement_id),)
        )
        return [_row_to_analysis(row) for row in cursor.fetchall()]


def _row_to_analysis(row: sqlite3.Row) -> Analysis:
    """Convert database row to Analysis."""
    from backend.models.entities import (
        AnalysisMode, AnalysisStatus, ExtractedParameters, SolverConfig
    )
    return Analysis(
        id=UUID(row["id"]),
        measurement_id=UUID(row["measurement_id"]),
        timestamp=datetime.fromisoformat(row["timestamp"]),
        mode=AnalysisMode(row["mode"]),
        status=AnalysisStatus(row["status"]),
        solver_config=SolverConfig.model_validate_json(row["solver_config"]),
        parameters=ExtractedParameters.model_validate_json(row["parameters"]) if row["parameters"] else None,
        result_hash=row["result_hash"],
        masks_applied=json.loads(row["masks_applied"]),
        error_message=row["error_message"],
    )


# =============================================================================
# RAW FILE STORAGE — Per SOP_PERSISTENCE §7
# =============================================================================

def store_raw_file(content: bytes, filename: str) -> tuple[Path, str]:
    """
    Store raw file in read-only location.
    Returns (path, hash).
    
    Per SOP_PERSISTENCE: Raw data is never deleted or overwritten.
    """
    file_hash = compute_content_hash(content)
    
    # Use hash-based directory structure to avoid collisions
    hash_prefix = file_hash[:2]
    target_dir = RAW_DATA_DIR / hash_prefix
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = target_dir / f"{file_hash}_{filename}"
    
    # Only write if doesn't exist (idempotent)
    if not target_path.exists():
        target_path.write_bytes(content)
    
    return target_path, file_hash


def get_raw_file_path(file_hash: str, filename: str) -> Optional[Path]:
    """Get path to stored raw file by hash."""
    hash_prefix = file_hash[:2]
    target_path = RAW_DATA_DIR / hash_prefix / f"{file_hash}_{filename}"
    if target_path.exists():
        return target_path
    return None
