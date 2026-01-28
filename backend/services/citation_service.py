"""
Helios Core — Citation & Provenance Service

Generates "Physics Kernel ID" (Audit ID) and BibTeX citations.
Ensures every analysis is cryptographically tied to the exact runtime environment
and solver configuration used.
"""

import hashlib
import scipy
import numpy
import pvlib
from datetime import datetime
from backend.models.entities import SolverConfig, AnalysisMode

def generate_runtime_signature() -> str:
    """
    Captures the exact version of the scientific stack.
    If the underlying math libraries change, the audit ID must change.
    """
    return f"scipy:{scipy.__version__}|numpy:{numpy.__version__}|pvlib:{pvlib.__version__}"

def generate_physics_audit_id(solver_config: SolverConfig) -> str:
    """
    Creates a unique fingerprint for the scientific environment.
    Combines library versions + solver settings.
    """
    env_string = generate_runtime_signature()
    
    # Sort settings for determinism
    settings_dict = solver_config.model_dump()
    settings_str = str(sorted(settings_dict.items()))
    
    combined = f"{env_string}::{settings_str}"
    
    # Return first 12 chars of SHA-256
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:12]

def generate_bibtex(audit_id: str, mode: AnalysisMode, analysis_id: str) -> str:
    """
    Generates a publication-ready BibTeX entry.
    """
    from backend.config import FRONTEND_BASE_URL
    year = datetime.now().year
    
    return f"""@manual{{helios_core_{audit_id},
  title = {{Helios Core Scientific Analysis (Kernel: {audit_id})}},
  author = {{Helios Core Research Suite}},
  year = {{{year}}},
  note = {{Analysis Mode: {mode.value}, Deterministic Fit Engine}},
  url = {{{FRONTEND_BASE_URL}/verify/{audit_id}}}
}}"""
