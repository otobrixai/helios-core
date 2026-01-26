"""
Helios Core — Configuration & Determinism Lock

This module MUST be imported at application startup before any numerical computation.
It enforces the determinism contract defined in SOP_PHYSICS_ENGINE and the Solver Spec.

MANDATORY: All five BLAS/threading environment variables must be set to "1".
Failure to enforce this invalidates all determinism guarantees.
"""

import os
import sys
import warnings

# =============================================================================
# DETERMINISM CONTRACT — NON-NEGOTIABLE
# =============================================================================

DETERMINISM_ENV_VARS = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}

GLOBAL_RNG_SEED = 42


def enforce_determinism() -> None:
    """
    Enforce determinism contract at process start.
    
    Must be called BEFORE importing numpy, scipy, or pvlib.
    Sets environment variables and validates the numerical environment.
    
    Raises:
        RuntimeError: If determinism cannot be guaranteed.
    """
    # Set environment variables
    for var, value in DETERMINISM_ENV_VARS.items():
        os.environ[var] = value
    
    # Validate they are set correctly
    missing = []
    for var, expected in DETERMINISM_ENV_VARS.items():
        actual = os.environ.get(var)
        if actual != expected:
            missing.append(f"{var}={actual} (expected {expected})")
    
    if missing:
        raise RuntimeError(
            f"Determinism contract violated. Invalid env vars: {missing}"
        )


def get_rng_seed() -> int:
    """Return the global RNG seed (42) for all stochastic operations."""
    return GLOBAL_RNG_SEED


# =============================================================================
# SOLVER CONFIGURATION — LOCKED PARAMETERS
# =============================================================================

DIFFERENTIAL_EVOLUTION_CONFIG = {
    "strategy": "best1bin",
    "mutation": (0.5, 1.0),
    "recombination": 0.7,
    "popsize": 15,
    "seed": GLOBAL_RNG_SEED,
    "updating": "deferred",
    "workers": 1,
    "polish": False,  # We do our own L-M refinement
}

# High-speed variant for Exploration mode
EXPLORATION_DE_CONFIG = {
    **DIFFERENTIAL_EVOLUTION_CONFIG,
    "popsize": 5,      # Smaller population for speed
    "maxiter": 100,    # Cap iterations
    "tol": 0.05,       # Relax tolerance
}

LEVENBERG_MARQUARDT_CONFIG = {
    "method": "lm",
    "xtol": 1e-10,
    "ftol": 1e-10,
    "gtol": 1e-10,
    "max_nfev": 10000,
}


# =============================================================================
# NUMERICAL TOLERANCES — CROSS-PLATFORM
# =============================================================================

NUMERICAL_TOLERANCES = {
    "Jsc": 0.001,   # ±0.1%
    "Voc": 0.0005,  # ±0.05%
    "FF": 0.001,    # ±0.1%
    "PCE": 0.0015,  # ±0.15%
}


# =============================================================================
# APPLICATION PATHS
# =============================================================================

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
EXPORTS_DIR = DATA_DIR / "exports"
DATABASE_PATH = DATA_DIR / "helios_core.db"


def ensure_directories() -> None:
    """Create required directories if they don't exist. Ignore errors on read-only filesystems."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        RAW_DATA_DIR.mkdir(exist_ok=True)
        EXPORTS_DIR.mkdir(exist_ok=True)
    except Exception as e:
        # On Vercel, the filesystem might be read-only (except /tmp)
        # We allow this to fail silently as stateless API doesn't need these
        import os
        if "VERCEL" not in os.environ:
            print(f"[Helios Core] Warning: Could not create directories: {e}")


# =============================================================================
# STARTUP HOOK
# =============================================================================

def initialize() -> None:
    """
    Initialize Helios Core environment.
    
    Call this at application startup before any imports of numerical libraries.
    """
    enforce_determinism()
    
    # Only try to ensure directories if we're not running in a strictly stateless/serverless mode
    # Or at least handle the failure gracefully
    ensure_directories()
    
    # Now safe to configure numpy
    import numpy as np
    np.set_printoptions(precision=15)
    
    # Emit startup confirmation
    print(f"[Helios Core] Determinism lock engaged. Seed={GLOBAL_RNG_SEED}")
