"""
Helios Core — IV Curve Solver

Physics-based parameter extraction using One-Diode and Two-Diode models.
Per SOP_PHYSICS_ENGINE:
- No black-box math
- Determinism over speed in Reference Mode
- Standards-first (pvlib, scipy, numpy only)
- Explicit configuration
"""

import hashlib
import json
from typing import Optional

import numpy as np
from scipy.optimize import differential_evolution, least_squares

from backend.config import (
    DIFFERENTIAL_EVOLUTION_CONFIG,
    EXPLORATION_DE_CONFIG,
    LEVENBERG_MARQUARDT_CONFIG,
    GLOBAL_RNG_SEED,
)
from backend.models.entities import (
    Analysis,
    AnalysisMode,
    AnalysisStatus,
    ExtractedParameters,
    Measurement,
    MeasurementType,
    ModelType,
    SolverConfig,
)
from backend.tools.manage_storage import compute_result_hash, create_analysis


# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================

K_BOLTZMANN = 1.380649e-23  # J/K
Q_ELECTRON = 1.602176634e-19  # C
T_STC = 298.15  # K (25°C)
V_THERMAL = K_BOLTZMANN * T_STC / Q_ELECTRON  # ~0.0257 V


# =============================================================================
# DIODE MODELS — Per specs/solver_math.md
# =============================================================================

def one_diode_equation(
    V: np.ndarray,
    I_ph: float,
    I_0: float,
    n: float,
    R_s: float,
    R_sh: float,
    T_k: float = 298.15,
) -> np.ndarray:
    """
    One-diode model: I = I_ph - I_0 * [exp((V + I*Rs)/(n*Vt)) - 1] - (V + I*Rs)/Rsh
    """
    Vt = K_BOLTZMANN * T_k / Q_ELECTRON
    I = np.zeros_like(V, dtype=np.float64)
    
    for iteration in range(50):
        exponential_term = np.clip((V + I * R_s) / (n * Vt), -50, 50)
        exp_val = np.exp(exponential_term)
        f = I_ph - I_0 * (exp_val - 1) - (V + I * R_s) / R_sh - I
        df = -I_0 * exp_val * R_s / (n * Vt) - R_s / R_sh - 1
        I_new = I - f / df
        if np.max(np.abs(I_new - I)) < 1e-12:
            break
        I = I_new
    return I


def two_diode_equation(
    V: np.ndarray,
    I_ph: float,
    I_01: float,
    n1: float,
    I_02: float,
    n2: float,
    R_s: float,
    R_sh: float,
    T_k: float = 298.15,
) -> np.ndarray:
    """Two-diode model with dual recombination pathways."""
    Vt = K_BOLTZMANN * T_k / Q_ELECTRON
    I = np.zeros_like(V, dtype=np.float64)
    
    for iteration in range(50):
        V_j = V + I * R_s
        exp1 = np.exp(np.clip(V_j / (n1 * Vt), -50, 50))
        exp2 = np.exp(np.clip(V_j / (n2 * Vt), -50, 50))
        f = I_ph - I_01 * (exp1 - 1) - I_02 * (exp2 - 1) - V_j / R_sh - I
        df = (-I_01 * exp1 * R_s / (n1 * Vt) - I_02 * exp2 * R_s / (n2 * Vt) - R_s / R_sh - 1)
        I_new = I - f / df
        if np.max(np.abs(I_new - I)) < 1e-12:
            break
        I = I_new
    return I


# =============================================================================
# PARAMETER BOUNDS — Per specs/solver_math.md §2.2
# =============================================================================

ONE_DIODE_BOUNDS = [
    (1e-6, 2.0),       # I_ph: Photocurrent (A)
    (1e-18, 1e-3),    # I_0: Saturation current (A)
    (0.5, 5.0),       # n: Ideality factor
    (0.0, 1000.0),    # R_s: Series resistance (Ω)
    (1.0, 1e9),       # R_sh: Shunt resistance (Ω)
]

DARK_DIODE_BOUNDS = [
    (1e-20, 1e-3),    # I_0: Saturation current (A)
    (0.5, 5.0),       # n: Ideality factor
    (0.0, 1000.0),    # R_s: Series resistance (Ω)
    (1.0, 1e9),       # R_sh: Shunt resistance (Ω)
]

TWO_DIODE_BOUNDS = [
    (0.0, 2.0),       # I_ph
    (1e-18, 1e-3),    # I_01
    (0.5, 3.0),       # n1
    (1e-18, 1e-3),    # I_02
    (1.0, 7.0),       # n2
    (0.0, 1000.0),    # R_s
    (1.0, 1e9),       # R_sh
]


# =============================================================================
# OBJECTIVE FUNCTIONS
# =============================================================================

def _one_diode_residuals(params: np.ndarray, V: np.ndarray, I_measured: np.ndarray, sm: float = 1.0) -> np.ndarray:
    """Residuals for one-diode model fitting with sign multiplier."""
    I_ph, I_0, n, R_s, R_sh = params
    I_model = one_diode_equation(V, I_ph, I_0, n, R_s, R_sh)
    return I_measured - (sm * I_model)


def _two_diode_residuals(params: np.ndarray, V: np.ndarray, I_measured: np.ndarray, sm: float = 1.0) -> np.ndarray:
    """Residuals for two-diode model fitting with sign multiplier."""
    I_ph, I_01, n1, I_02, n2, R_s, R_sh = params
    I_model = two_diode_equation(V, I_ph, I_01, n1, I_02, n2, R_s, R_sh)
    return I_measured - (sm * I_model)


def _one_diode_cost(params: np.ndarray, V: np.ndarray, I_measured: np.ndarray, sm: float = 1.0) -> float:
    """Sum of squared residuals for DE optimization."""
    residuals = _one_diode_residuals(params, V, I_measured, sm)
    return float(np.sum(residuals**2))


def _two_diode_cost(params: np.ndarray, V: np.ndarray, I_measured: np.ndarray, sm: float = 1.0) -> float:
    """Sum of squared residuals for DE optimization."""
    residuals = _two_diode_residuals(params, V, I_measured, sm)
    return float(np.sum(residuals**2))


# =============================================================================
# MAIN SOLVER — Per SOP_PHYSICS_ENGINE §5
# =============================================================================

def solve_iv_curve(
    V: np.ndarray,
    I: np.ndarray,
    cell_area_cm2: float,
    temperature_c: float,
    mode: AnalysisMode,
    model_type: ModelType = ModelType.ONE_DIODE,
    measurement_type: MeasurementType = MeasurementType.LIGHT,
    measurement_id: Optional[str] = None,
) -> tuple[ExtractedParameters, SolverConfig, str]:
    """
    Solve IV curve using physics-based model.
    """
    # MANDATORY: Ensure float64 per Solver Spec §1.2
    V = np.asarray(V, dtype=np.float64)
    I = np.asarray(I, dtype=np.float64)
    T_k = temperature_c + 273.15
    
    # Per Solver Spec: NaN/Inf → hard failure
    if np.any(np.isnan(V)) or np.any(np.isinf(V)):
        raise ValueError("Voltage contains NaN or Inf")
    if np.any(np.isnan(I)) or np.any(np.isinf(I)):
        raise ValueError("Current contains NaN or Inf")
    
    # Build solver config
    solver_config = SolverConfig(
        model_type=model_type,
        solver_seed=GLOBAL_RNG_SEED,
        **{k: v for k, v in DIFFERENTIAL_EVOLUTION_CONFIG.items() 
           if k in ["de_strategy", "de_mutation", "de_recombination", "de_popsize"]},
        **{k: v for k, v in LEVENBERG_MARQUARDT_CONFIG.items()
           if k in ["lm_xtol", "lm_ftol", "lm_gtol"]},
    )
    
    # Select model and optimization speed
    de_config = EXPLORATION_DE_CONFIG if mode == AnalysisMode.EXPLORATION else DIFFERENTIAL_EVOLUTION_CONFIG
    
    # Per SOP_PHYSICS_ENGINE: Detect sign convention.
    # Solar cell current in the power region (V > 0) is often negative in "sink" convention.
    potential_power_mask = (V > 0) & (V < 0.9 * np.max(V))
    if np.any(potential_power_mask) and np.median(I[potential_power_mask]) < 0:
        print(f"  [DEBUG] Negative current convention detected. Flipping for fitting.", flush=True)
        I_fit = -I
        sm = -1.0
    else:
        I_fit = I
        sm = 1.0

    if measurement_type == MeasurementType.DARK:
        # Specialized Dark Curve Fitting: Force I_ph = 0
        # Use log10(I_0) for better numerical search (spans 15 orders of magnitude)
        bounds = [
            (-20.0, -2.0),    # log10(I_0)
            (0.5, 5.0),       # n: Ideality factor
            (0.0, 1000.0),    # R_s: Series resistance (Ω)
            (1.0, 1e9),       # R_sh: Shunt resistance (Ω)
        ]
        
        def dark_res(p, v, i, tk, s):
            log_i0, n, rs, rsh = p
            im = one_diode_equation(v, 0.0, 10**log_i0, n, rs, rsh, tk)
            # Scale residuals to uA to keep them in O(1) for the solver
            return (i - (s * im)) * 1e6

        cost_func = lambda p, v, i: np.sum(dark_res(p, v, i, T_k, sm)**2)
        residual_func = lambda p, v, i: dark_res(p, v, i, T_k, sm)
    elif model_type == ModelType.ONE_DIODE:
        bounds = ONE_DIODE_BOUNDS
        cost_func = lambda p, v, i: _one_diode_cost(p, v, i, sm)
        residual_func = lambda p, v, i: _one_diode_residuals(p, v, i, sm)
    else:
        bounds = TWO_DIODE_BOUNDS
        cost_func = lambda p, v, i: _two_diode_cost(p, v, i, sm)
        residual_func = lambda p, v, i: _two_diode_residuals(p, v, i, sm)

    de_result = differential_evolution(
        cost_func,
        bounds=bounds,
        args=(V, I_fit),
        **de_config,
    )
    print(f"  [DEBUG] Global Opt Done. Success: {de_result.success}", flush=True)
    
    # Stage B: Local Refinement
    lb = [b[0] for b in bounds]
    ub = [b[1] for b in bounds]
    
    print(f"  [DEBUG] Starting Local Refinement...", flush=True)
    lm_result = least_squares(
        residual_func,
        x0=de_result.x,
        args=(V, I_fit),
        bounds=(lb, ub),
        method="trf",
        **{k.replace("lm_", ""): v for k, v in LEVENBERG_MARQUARDT_CONFIG.items() 
           if k in ["lm_xtol", "lm_ftol", "lm_gtol", "lm_max_nfev"]},
    )
    print(f"  [DEBUG] Local Refinement Done. Success: {lm_result.success}", flush=True)
    
    params = lm_result.x
    if measurement_type == MeasurementType.DARK:
        # Un-log the I_0
        I_ph, I_0, n, R_s, R_sh = 0.0, 10**params[0], params[1], params[2], params[3]
        n2 = None
    elif model_type == ModelType.ONE_DIODE:
        I_ph, I_0, n, R_s, R_sh = params[0], params[1], params[2], params[3], params[4]
        n2 = None
    else:
        # TWO_DIODE_BOUNDS = (I_ph, I_01, n1, I_02, n2, R_s, R_sh)
        I_ph, I_0, n = params[0], params[1], params[2]
        I_02, n2 = params[3], params[4]
        R_s, R_sh = params[5], params[6]
    
    # Derived Parameters
    # Standardize current density (J)
    J = I / cell_area_cm2 * 1000  # mA/cm²
    
    # Jsc: Current at V closest to 0
    v_zero_idx = np.argmin(np.abs(V))
    j_sc = abs(float(J[v_zero_idx]))
    
    # Voc: Voltage where current crosses 0
    # Use absolute interpolation to find crossing
    try:
        sign_changes = np.where(np.diff(np.sign(I)))[0]
        if len(sign_changes) > 0:
            idx = sign_changes[0]
            # Linear interpolation for zero crossing
            v_oc = abs(float(V[idx] - I[idx] * (V[idx + 1] - V[idx]) / (I[idx + 1] - I[idx])))
        else:
            v_oc = abs(float(V[-1]))
    except Exception:
        v_oc = abs(float(V[-1]))
    
    # Power max (MPP): MUST be in the power-producing quadrant (V > 0)
    # Different systems use different signs for current (+ or - at V=0 is common)
    v_zero_idx = np.argmin(np.abs(V))
    jsc_sign = np.sign(I[v_zero_idx]) if abs(I[v_zero_idx]) > 0 else 1.0
    
    # Power region: V is between 0 and Voc, and I has same sign as Jsc
    mask = (V >= 0) & (V <= v_oc * 1.05) & (np.sign(I) == jsc_sign)
    
    if np.any(mask):
        P_vals = np.abs(V[mask] * I[mask])
        p_mpp = float(np.max(P_vals))
    else:
        # Fallback to absolute max if no power region found
        p_mpp = float(np.max(np.abs(V * I)))
    
    # Fill Factor Calculation (Pmax / (Voc * Isc))
    # Isc = Jsc * Area / 1000
    i_sc_converted = j_sc * cell_area_cm2 / 1000.0
    if v_oc > 0 and i_sc_converted > 0:
        ff = p_mpp / (v_oc * i_sc_converted)
    else:
        ff = 0.0
        
    # Power Conversion Efficiency (assuming 1 sun = 100 mW/cm²)
    p_in_total_w = (100.0 * cell_area_cm2) / 1000.0  # 100mW/cm² * Area -> mW -> W
    pce = (p_mpp / p_in_total_w) * 100.0 if p_in_total_w > 0 else 0.0
    
    extracted = ExtractedParameters(
        j_sc=j_sc,
        v_oc=v_oc,
        ff=ff,
        pce=pce,
        r_s=R_s * cell_area_cm2,
        r_sh=R_sh * cell_area_cm2,
        n_ideality=n,
        n2_ideality=n2,
        i_ph=I_ph,
        i_0=I_0,
        n_dark=n if measurement_type == MeasurementType.DARK else None,
        i_0_dark=I_0 if measurement_type == MeasurementType.DARK else None,
        r_s_dark=R_s * cell_area_cm2 if measurement_type == MeasurementType.DARK else None,
        r_sh_dark=R_sh * cell_area_cm2 if measurement_type == MeasurementType.DARK else None,
        residual_rms=float(np.sqrt(np.mean(lm_result.fun**2))),
    )
    
    result_hash = compute_result_hash(extracted.model_dump(), solver_config.model_dump())
    return extracted, solver_config, result_hash


def _one_diode_residuals(params, V, I_measured, T_k):
    I_ph, I_0, n, R_s, R_sh = params
    I_model = one_diode_equation(V, I_ph, I_0, n, R_s, R_sh, T_k)
    return I_measured - I_model


def _two_diode_residuals(params, V, I_measured, T_k):
    I_ph, I_01, n1, I_02, n2, R_s, R_sh = params
    I_model = two_diode_equation(V, I_ph, I_01, n1, I_02, n2, R_s, R_sh, T_k)
    return I_measured - I_model


def analyze_measurement(
    measurement: Measurement,
    V: np.ndarray,
    I: np.ndarray,
    mode: AnalysisMode,
    model_type: ModelType = ModelType.ONE_DIODE,
) -> Analysis:
    """Run full analysis and persist."""
    try:
        params, config, result_hash = solve_iv_curve(
            V=V,
            I=I,
            cell_area_cm2=measurement.metadata.cell_area_cm2,
            temperature_c=measurement.metadata.temperature_c,
            mode=mode,
            model_type=model_type,
            measurement_type=measurement.metadata.measurement_type,
            measurement_id=str(measurement.id),
        )
        status = AnalysisStatus.VALID
        err = None
    except Exception as e:
        params = None
        config = SolverConfig(model_type=model_type)
        result_hash = None
        status = AnalysisStatus.INVALID
        err = str(e)
        
    analysis = Analysis(
        measurement_id=measurement.id,
        mode=mode,
        status=status,
        solver_config=config,
        parameters=params,
        result_hash=result_hash,
        error_message=err,
    )
    return create_analysis(analysis)
