"""
Helios Core — File Ingestion Engine

Universal parser for IV measurement files.
Per SOP_DATA_INGESTION:
- Raw data is sacred — never modified
- Parsing must be explainable — every inference logged
- Ambiguity must be surfaced, not guessed silently
- Same file → same ImportRecord (hash-based)
"""

import hashlib
import re
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

import numpy as np
import pandas as pd

from backend.models.entities import (
    ColumnMap,
    HardwareProfile,
    ImportRecord,
    Measurement,
    MeasurementMetadata,
)
from backend.tools.manage_storage import (
    create_import_record,
    create_measurement,
    get_import_record_by_hash,
    store_raw_file,
)


# =============================================================================
# COLUMN DETECTION PATTERNS — Per SOP_DATA_INGESTION §5-6
# =============================================================================

VOLTAGE_PATTERNS = [
    r"^voltage\s*\(?v\)?$",
    r"^v\s*\(?v\)?$",
    r"^voltage_v$",
    r"^v_v$",
    r"^v_?oc$",
    r"^bias$",
    r"^voltage$",
    r"^v$",
]

CURRENT_PATTERNS = [
    r"^current_density\s*\(?a/cm2\)?$",
    r"^j\s*\(?a/cm2\)?$",
    r"^current_density\s*\(?ma/cm2\)?$",
    r"^j\s*\(?ma/cm2\)?$",
    r"^current_density$",
    r"^j$",
    r"^current\s*\(?a\)?$",
    r"^i\s*\(?a\)?$",
    r"^current\s*\(?ma\)?$",
    r"^i\s*\(?ma\)?$",
    r"^current_a$",
    r"^current_ma$",
    r"^i_a$",
    r"^i_ma$",
    r"^current$",
    r"^i$",
]

TIME_PATTERNS = [
    r"^time\s*\(?s\)?$",
    r"^t\s*\(?s\)?$",
    r"^time_s$",
    r"^timestamp$",
    r"^time$",
    r"^t$",
]

# Hardware-specific header patterns
HARDWARE_SIGNATURES = {
    HardwareProfile.KEITHLEY: [
        r"keithley",
        r"model\s*24",
        r"model\s*26",
    ],
    HardwareProfile.KEYSIGHT: [
        r"keysight",
        r"agilent",
        r"b29\d{2}",
    ],
    HardwareProfile.OSSILA: [
        r"ossila",
        r"solar\s*cell\s*tester",
    ],
}


# =============================================================================
# HARDWARE DETECTION — Per SOP_DATA_INGESTION §5
# =============================================================================

def detect_hardware_profile(
    content: str, 
    filename: str
) -> tuple[HardwareProfile, bool]:
    """
    Detect hardware profile from file content and filename.
    
    Returns:
        (profile, low_confidence): The detected profile and whether it's low confidence.
    
    Per SOP: Priority order is explicit headers > column patterns > user override.
    """
    combined = (content[:2000] + filename).lower()
    
    for profile, patterns in HARDWARE_SIGNATURES.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return profile, False
    
    # No match — default to Generic with low confidence flag
    return HardwareProfile.GENERIC, True


# =============================================================================
# COLUMN MAPPING — Per SOP_DATA_INGESTION §6
# =============================================================================

def clean_column_name(name: str) -> str:
    """Standardize column names for pattern matching."""
    return name.lower().strip().replace(" ", "_").replace("(", "").replace(")", "")


def detect_time_column(df: pd.DataFrame) -> Optional[str]:
    """Helper to find time column."""
    for pattern in TIME_PATTERNS:
        for col in df.columns:
            if re.match(pattern, clean_column_name(col)):
                return col
    return None


def detect_column_mapping(df: pd.DataFrame) -> ColumnMap:
    """
    Detect voltage and current columns from DataFrame.
    
    Per SOP:
    - Units inferred only from headers or metadata
    - Unit conversion must be logged
    - No inferred unit guessing
    
    Raises:
        ValueError: If voltage or current columns cannot be detected.
    """
    columns = [c.lower().strip() for c in df.columns]
    original_columns = list(df.columns)
    
    voltage_col = None
    current_col = None
    time_col = None
    
    # Detect voltage
    for idx, col in enumerate(columns):
        for pattern in VOLTAGE_PATTERNS:
            if re.search(pattern, col, re.IGNORECASE):
                voltage_col = original_columns[idx]
                break
        if voltage_col:
            break
    
    # Detect current
    for idx, col in enumerate(columns):
        for pattern in CURRENT_PATTERNS:
            if re.search(pattern, col, re.IGNORECASE):
                current_col = original_columns[idx]
                break
        if current_col:
            break
    
    # Detect time (optional)
    for idx, col in enumerate(columns):
        for pattern in TIME_PATTERNS:
            if re.search(pattern, col, re.IGNORECASE):
                time_col = original_columns[idx]
                break
        if time_col:
            break
    
    # Per SOP §8: Fail loudly if mandatory columns missing
    if voltage_col is None:
        raise ValueError(
            f"Voltage column not detected. Available columns: {original_columns}"
        )
    if current_col is None:
        raise ValueError(
            f"Current column not detected. Available columns: {original_columns}"
        )
    
    # Detect units from column names
    voltage_unit = _extract_unit(voltage_col, default="V")
    current_unit = _extract_unit(current_col, default="A")
    
    conversions = []
    
    # Log unit conversions
    if current_unit.lower() == "ma":
        conversions.append("Current: mA → A (÷1000)")
    if current_unit.lower() == "ua":
        conversions.append("Current: µA → A (÷1e6)")
    
    return ColumnMap(
        voltage_column=voltage_col,
        current_column=current_col,
        time_column=time_col,
        voltage_unit=voltage_unit,
        current_unit=current_unit,
        unit_conversions_applied=conversions,
    )


def _extract_unit(column_name: str, default: str) -> str:
    """Extract unit from column name (e.g., 'Current (mA)' → 'mA')."""
    match = re.search(r"\(([^)]+)\)", column_name)
    if match:
        return match.group(1)
    return default


# =============================================================================
# MULTI-PIXEL SEGMENTATION — Per SOP_DATA_INGESTION §7
# =============================================================================

def detect_multi_pixel_columns(df: pd.DataFrame) -> list[tuple[str, str]]:
    """
    Detect multiple IV curves in a single file.
    
    Returns:
        List of (voltage_col, current_col) tuples for each pixel.
    
    Per SOP: Each pixel becomes a separate Measurement with shared metadata.
    """
    columns = list(df.columns)
    
    # Common patterns for multi-pixel files
    pixel_patterns = [
        (r"v_?(\d+|[a-z])", r"i_?(\d+|[a-z])"),
        (r"voltage_?(\d+|[a-z])", r"current_?(\d+|[a-z])"),
        (r"voltage_?(\d+|[a-z])", r"current_density_?(\d+|[a-z])"),
        (r"pixel_?(\d+|[a-z])_v", r"pixel_?(\d+|[a-z])_i"),
        (r"pixel_?(\d+|[a-z])_voltage", r"pixel_?(\d+|[a-z])_current"),
        (r"pixel_?(\d+|[a-z])_voltage", r"pixel_?(\d+|[a-z])_current_density"),
    ]
    
    pixels = []
    
    for v_pattern, i_pattern in pixel_patterns:
        v_cols = {}
        i_cols = {}
        
        for col in columns:
            col_lower = col.lower()
            v_match = re.match(v_pattern, col_lower, re.IGNORECASE)
            i_match = re.match(i_pattern, col_lower, re.IGNORECASE)
            
            if v_match:
                v_cols[v_match.group(1)] = col
            elif i_match:
                i_cols[i_match.group(1)] = col
        
    # Match V/I pairs
    for key in v_cols:
        if key in i_cols:
            pixels.append((v_cols[key], i_cols[key]))
    
    if pixels:
        return pixels

    # Strategy 2: Shared Voltage (Voltage, I_A, I_B...)
    # Check for Master Voltage first
    master_voltage = None
    for pattern in VOLTAGE_PATTERNS:
        for col in columns:
            if re.match(pattern, clean_column_name(col)):
                master_voltage = col
                break
        if master_voltage:
            break
            
    if master_voltage:
        # Find all columns that look like pixel currents
        # Heuristic: Contains "current" or "i" and is NOT the master voltage
        # and has some suffix
        potential_currents = []
        for col in columns:
            if col == master_voltage:
                continue
            clean = clean_column_name(col)
            # Match current patterns but exclude generic master current if it would cause ambiguity
            # However, if we found no pairs, any current-like column besides master_voltage is a candidate
            if any(re.search(p, clean) for p in CURRENT_PATTERNS) or "pixel" in clean:
                potential_currents.append(col)
        
        # If we have multiple currents, map them all to master_voltage
        if len(potential_currents) >= 1:
            for i_col in potential_currents:
                pixels.append((master_voltage, i_col))
            
    return pixels


# =============================================================================
# MAIN INGESTION — Per SOP_DATA_INGESTION §4
# =============================================================================

def ingest_file(
    file_content: bytes,
    filename: str,
    metadata: Optional[MeasurementMetadata] = None,
) -> tuple[ImportRecord, list[Measurement]]:
    """
    Ingest a raw IV measurement file.
    
    Per SOP §4 Workflow:
    1. Receive raw file
    2. Compute SHA256 hash
    3. Store raw file as read-only
    4. Create ImportRecord
    5. Detect hardware profile
    6. Detect column mappings
    7. Emit Measurement records
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        metadata: Optional measurement metadata
    
    Returns:
        (ImportRecord, list[Measurement])
    
    Raises:
        ValueError: If parsing fails (missing columns, encoding issues)
    """
    if metadata is None:
        metadata = MeasurementMetadata()
    
    # Step 3: Store raw file (Self-healing: always ensure file exists on disk)
    raw_path, _ = store_raw_file(file_content, filename)
    
    # Step 2: Compute hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Check for existing import (Idempotency)
    existing = get_import_record_by_hash(file_hash)
    if existing is not None:
        from backend.tools.manage_storage import list_measurements_for_import
        print(f"[Ingest] File already exists (hash {file_hash[:8]}). Returning existing records.")
        measurements = list_measurements_for_import(existing.id)
        return existing, measurements
    
    # Detect encoding
    encoding = _detect_encoding(file_content)
    
    # Parse file content
    try:
        content_str = file_content.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode file with {encoding}: {e}") from e
    
    # Step 5: Detect hardware
    hardware_profile, low_confidence = detect_hardware_profile(content_str, filename)
    
    # Parse into DataFrame
    df = _parse_to_dataframe(file_content, filename, encoding)
    
    # Step 6: Detect columns
    # We first try standard detection. If it fails, we check for multi-pixel.
    column_map = None
    multi_pixels = None
    
    try:
        column_map = detect_column_mapping(df)
    except ValueError:
        # Standard detection failed. Let's see if it's a multi-pixel file.
        pass
        
    multi_pixels = detect_multi_pixel_columns(df)
    
    if not column_map and not multi_pixels:
        # Both failed -> hard failure
        raise ValueError(f"Could not detect valid Voltage/Current columns. Available: {list(df.columns)}")
        
    # If we have multi-pixels but no master map, we use the first pixel to satisfy ImportRecord schema
    if not column_map and multi_pixels:
        v0, i0 = multi_pixels[0]
        column_map = ColumnMap(
            voltage_column=v0,
            current_column=i0,
            time_column=detect_time_column(df),
            voltage_unit="V",
            current_unit="A",
        )
    
    # Step 4: Create ImportRecord
    import_record = ImportRecord(
        source_filename=filename,
        file_hash=file_hash,
        hardware_profile=hardware_profile,
        column_map=column_map,
        encoding_detected=encoding,
        low_confidence_flag=low_confidence,
    )
    create_import_record(import_record)
    
    # Step 7: Emit Measurements
    measurements = []
    
    if multi_pixels:
        # Multi-pixel file
        for i, (v_col, i_col) in enumerate(multi_pixels):
            pixel_label = f"{Path(filename).stem}_Pixel_{i+1}"
            
            # Create per-pixel column map override
            pixel_map = ColumnMap(
                voltage_column=v_col,
                current_column=i_col,
                time_column=column_map.time_column,
                voltage_unit=column_map.voltage_unit,
                current_unit=column_map.current_unit,
            )
            
            measurement = Measurement(
                import_record_id=import_record.id,
                device_label=pixel_label,
                raw_data_path=str(raw_path),
                metadata=metadata,
                column_map=pixel_map,
            )
            create_measurement(measurement)
            measurements.append(measurement)
    else:
        # Single measurement
        measurement = Measurement(
            import_record_id=import_record.id,
            device_label=Path(filename).stem,
            raw_data_path=str(raw_path),
            metadata=metadata,
        )
        create_measurement(measurement)
        measurements.append(measurement)
    
    return import_record, measurements


def _detect_encoding(content: bytes) -> str:
    """Detect file encoding. Defaults to UTF-8."""
    # Try UTF-8 first
    try:
        content.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    
    # Try Latin-1 (covers most Western files)
    try:
        content.decode("latin-1")
        return "latin-1"
    except UnicodeDecodeError:
        pass
    
    return "utf-8"  # Default fallback


def _parse_to_dataframe(
    content: bytes, 
    filename: str, 
    encoding: str
) -> pd.DataFrame:
    """Parse file content to DataFrame based on extension."""
    ext = Path(filename).suffix.lower()
    
    if ext in (".csv", ".txt"):
        # Try common delimiters
        for sep in [",", "\t", ";", " "]:
            try:
                df = pd.read_csv(
                    BytesIO(content),
                    sep=sep,
                    encoding=encoding,
                    skipinitialspace=True,
                )
                if len(df.columns) >= 2:
                    return df
            except Exception:
                continue
        
        raise ValueError(f"Could not parse {filename} as CSV/TXT")
    
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(BytesIO(content))
        return df
    
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


# =============================================================================
# DATA EXTRACTION — Per SOP_DATA_INGESTION §10
# =============================================================================

def extract_iv_data(
    measurement: Measurement,
    column_map: ColumnMap,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract voltage and current arrays from stored raw data.
    
    Per SOP §10 Non-Negotiables:
    - No silent corrections
    - No data smoothing
    - No filtering at ingestion stage
    
    Per Solver Spec §2.3: Arrays cast to float64 at this boundary.
    
    Returns:
        (V, I) as numpy arrays with dtype=float64
    """
    raw_path = Path(measurement.raw_data_path)
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    # Detect encoding from parent import record (would need lookup)
    content = raw_path.read_bytes()
    encoding = _detect_encoding(content)
    
    df = _parse_to_dataframe(content, raw_path.name, encoding)
    
    # Extract columns
    V = df[column_map.voltage_column].values
    I = df[column_map.current_column].values
    
    # MANDATORY: Cast to float64 per Solver Spec §1.2, §2.3
    V = np.asarray(V, dtype=np.float64)
    I = np.asarray(I, dtype=np.float64)
    
    # Per Solver Spec: NaN/Inf → hard failure
    if np.any(np.isnan(V)) or np.any(np.isinf(V)):
        raise ValueError("Voltage data contains NaN or Inf values")
    if np.any(np.isnan(I)) or np.any(np.isinf(I)):
        raise ValueError("Current data contains NaN or Inf values")
    
    # Apply unit conversions if needed
    current_unit = column_map.current_unit.lower()
    if current_unit == "ma":
        I = I / 1000.0
    elif current_unit == "ua":
        I = I / 1e6
    
    return V, I
