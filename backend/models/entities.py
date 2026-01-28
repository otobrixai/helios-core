"""
Helios Core — Entity Models

Pydantic schemas for ImportRecord, Measurement, and Analysis.
Per SOP_PERSISTENCE: All entities are immutable after creation in Reference Mode.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class HardwareProfile(str, Enum):
    """Supported hardware profiles per SOP_DATA_INGESTION."""
    KEITHLEY = "Keithley"
    KEYSIGHT = "Keysight"
    OSSILA = "Ossila"
    GENERIC = "Generic"


class AnalysisMode(str, Enum):
    """Analysis modes per FRD §3."""
    EXPLORATION = "Exploration"
    REFERENCE = "Reference"


class ModelType(str, Enum):
    """Physics models per SOP_PHYSICS_ENGINE."""
    ONE_DIODE = "OneDiode"
    TWO_DIODE = "TwoDiode"


class AnalysisStatus(str, Enum):
    """Analysis validity status."""
    VALID = "VALID"
    INVALID = "INVALID"
    PENDING = "PENDING"


class MeasurementType(str, Enum):
    """Types of measurements for physical analysis."""
    LIGHT = "light"
    DARK = "dark"
    SUNS_VOC = "suns_voc"


# =============================================================================
# COLUMN MAPPING
# =============================================================================

class ColumnMap(BaseModel):
    """Maps raw file columns to standard IV data."""
    voltage_column: str
    current_column: str
    time_column: Optional[str] = None
    voltage_unit: str = "V"
    current_unit: str = "A"
    unit_conversions_applied: list[str] = Field(default_factory=list)


# =============================================================================
# IMPORT RECORD
# =============================================================================

class ImportRecord(BaseModel):
    """
    Tracks ingestion of a raw file.
    Per SOP_PERSISTENCE: Created once per unique file hash, immutable after creation.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    source_filename: str
    file_hash: str  # SHA-256
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    hardware_profile: HardwareProfile
    column_map: ColumnMap
    encoding_detected: str = "utf-8"
    low_confidence_flag: bool = False


# =============================================================================
# MEASUREMENT
# =============================================================================

class MeasurementMetadata(BaseModel):
    """Metadata for a single IV measurement."""
    cell_area_cm2: float = 1.0
    temperature_c: float = 25.0
    irradiance_suns: float = 1.0
    measurement_type: MeasurementType = MeasurementType.LIGHT


class Measurement(BaseModel):
    """
    A single IV curve for one pixel/cell.
    Per SOP_PERSISTENCE: References ImportRecord, no raw data mutation.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    import_record_id: UUID
    device_label: str
    raw_data_path: str  # Read-only filesystem path
    metadata: MeasurementMetadata = Field(default_factory=MeasurementMetadata)
    column_map: Optional[ColumnMap] = None  # Override for multi-pixel files


# =============================================================================
# ANALYSIS RESULTS
# =============================================================================

class SolverConfig(BaseModel):
    """Snapshot of solver configuration for reproducibility."""
    model_type: ModelType
    solver_seed: int = 42
    de_strategy: str = "best1bin"
    de_mutation: tuple[float, float] = (0.5, 1.0)
    de_recombination: float = 0.7
    de_popsize: int = 15
    lm_xtol: float = 1e-10
    lm_ftol: float = 1e-10
    lm_gtol: float = 1e-10


class ExtractedParameters(BaseModel):
    """Extracted IV parameters."""
    j_sc: float  # mA/cm²
    v_oc: float  # V
    ff: float    # dimensionless (0-1)
    pce: float   # % efficiency
    r_s: float   # Ω·cm²
    r_sh: float  # Ω·cm²
    n_ideality: float
    # Two-diode additions (optional)
    n2_ideality: Optional[float] = None
    i_ph: Optional[float] = None
    i_0: Optional[float] = None
    # Fundamental Physics additions
    n_dark: Optional[float] = None
    n_light: Optional[float] = None
    i_0_dark: Optional[float] = None
    r_sh_dark: Optional[float] = None
    r_s_dark: Optional[float] = None
    delta_n: Optional[float] = None  # n_light - n_dark
    # Quality metrics
    residual_rms: Optional[float] = None


class Analysis(BaseModel):
    """
    Result of physics analysis on a Measurement.
    Per SOP_PERSISTENCE: Immutable once finalized in Reference Mode.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    measurement_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mode: AnalysisMode
    status: AnalysisStatus = AnalysisStatus.PENDING
    solver_config: SolverConfig
    parameters: Optional[ExtractedParameters] = None
    result_hash: Optional[str] = None  # SHA-256 of results for determinism check
    masks_applied: list[dict] = Field(default_factory=list)
    error_message: Optional[str] = None


# =============================================================================
# DATABASE TABLE SCHEMAS (for SQLite)
# =============================================================================

IMPORT_RECORD_TABLE = """
CREATE TABLE IF NOT EXISTS import_records (
    id TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    ingestion_timestamp TEXT NOT NULL,
    hardware_profile TEXT NOT NULL,
    column_map TEXT NOT NULL,
    encoding_detected TEXT NOT NULL,
    low_confidence_flag INTEGER NOT NULL DEFAULT 0
);
"""

MEASUREMENT_TABLE = """
CREATE TABLE IF NOT EXISTS measurements (
    id TEXT PRIMARY KEY,
    import_record_id TEXT NOT NULL,
    device_label TEXT NOT NULL,
    raw_data_path TEXT NOT NULL,
    metadata TEXT NOT NULL,
    column_map TEXT,
    FOREIGN KEY (import_record_id) REFERENCES import_records(id)
);
"""

ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    measurement_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    solver_config TEXT NOT NULL,
    parameters TEXT,
    result_hash TEXT,
    masks_applied TEXT NOT NULL,
    error_message TEXT,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id)
);
"""
