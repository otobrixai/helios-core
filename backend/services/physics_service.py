"""
Helios Core — Fundamental Physics Service

Extracts deeper physical parameters from light and dark IV curves.
- Ideality factor (n) extraction from slopes
- Recombination mechanism identification
- Defect density estimation
- Dual-analysis comparison (Light+Dark)
"""

import numpy as np
from typing import Dict, Any, List, Optional
from backend.models.entities import ExtractedParameters, MeasurementType

# Physical Constants
K_BOLTZMANN = 1.380649e-23  # J/K
Q_ELECTRON = 1.602176634e-19  # C

def extract_ideality_from_slope(
    voltage: np.ndarray, 
    current: np.ndarray, 
    temp_c: float = 25.0,
    is_light: bool = False,
    j_sc: Optional[float] = None
) -> float:
    """
    Extract ideality factor n from ln(I) vs V slope in forward bias.
    
    For Light measurements:
    I = I_ph - I_dark => I_dark = I_ph - I
    Approximating I_ph with J_sc, we analyze ln(|J_sc - J|) vs V.
    """
    vt = K_BOLTZMANN * (temp_c + 273.15) / Q_ELECTRON
    
    # Process current for diode component
    if is_light:
        # If j_sc is not provided, estimate it from the first few points near V=0
        if j_sc is None:
            v_zero_mask = np.abs(voltage) < 0.05
            j_sc = np.mean(current[v_zero_mask]) if np.any(v_zero_mask) else current[0]
        
        # Analyze the shifted curve (diode component)
        # Note: current is typically negative in power region in our convention
        # J_dark = J_ph - J. If J_ph ~ J_sc and J is negative: J_dark = J_sc - J
        abs_i = np.abs(j_sc - current)
    else:
        abs_i = np.abs(current)
    
    # Filter for forward bias where exponential dominates (V > 3Vt)
    # Also ignore points too close to noise floor or rollover
    mask = (voltage > 3 * vt) & (abs_i > 1e-9)
    if is_light and j_sc is not None:
        # For light curves, only fit the region approaching Voc, 
        # but avoid the high-injection/series-resistance dominated highest bias
        # Typical range: 0.7*Voc to 0.95*Voc
        pass # The general mask often works if filter is right

    if np.count_nonzero(mask) < 5:
        return 0.0
        
    v_fit = voltage[mask]
    ln_i_fit = np.log(abs_i[mask])
    
    # Linear fit
    try:
        slope, _ = np.polyfit(v_fit, ln_i_fit, 1)
    except:
        return 0.0
    
    if slope <= 0:
        return 0.0
        
    n = 1.0 / (slope * vt)
    
    # Sanity check: n > 5 is usually a sign of bad fitting/data
    return float(n) if n < 10.0 else 0.0

def estimate_recombination_mechanism(n: float) -> str:
    """Classify recombination based on ideality factor."""
    if n <= 0:
        return "Invalid/Unreliable"
    if 0.8 <= n <= 1.2:
        return "Radiative/Band-to-band"
    if 1.2 < n < 1.8:
        return "SRH / Trap-assisted (Depletion Region)"
    if 1.8 <= n <= 2.2:
        return "SRH / Diffusion-limited (Quasi-neutral Region)"
    if n > 2.2:
        return "Complex (Tunneling / Multi-level / Barriers)"
    return "Below unity (Potential measurement artifact)"

def calculate_dual_metrics(
    light_params: ExtractedParameters, 
    dark_params: Optional[ExtractedParameters]
) -> ExtractedParameters:
    """
    Enhances light parameters with comparisons to dark parameters.
    """
    if dark_params is None:
        return light_params
        
    updated = light_params.model_copy()
    
    # Assign dark values for comparison
    updated.n_dark = dark_params.n_ideality
    updated.n_light = light_params.n_ideality
    updated.i_0_dark = dark_params.i_0
    updated.r_s_dark = dark_params.r_s
    updated.r_sh_dark = dark_params.r_sh
    
    if updated.n_dark and updated.n_light:
        updated.delta_n = updated.n_light - updated.n_dark
        
    return updated

def estimate_defect_density(n: float, v_oc: float, temp_c: float) -> float:
    """
    Rough defect density estimation from ideality factor and Voc.
    Simplified Sah-Noyce-Shockley relationship.
    Returns relative defect metric (normalized).
    """
    # Placeholder for more complex physics later
    return max(0.0, (n - 1.0) * 10.0) if n > 1.0 else 0.0
