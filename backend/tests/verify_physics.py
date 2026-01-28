import numpy as np
from backend.services.physics_service import extract_ideality_from_slope
from backend.models.entities import MeasurementType
from backend.tools.solve_iv_curve import solve_iv_curve, one_diode_equation
from backend.models.entities import AnalysisMode, ModelType

def simulate_dark_iv(v, i0=1e-10, n=1.5, rs=0.1, rsh=1e6, temp_k=298.15):
    """
    Simulate dark IV with very low Rs for pure ideality verification.
    """
    return one_diode_equation(v, 0.0, i0, n, rs, rsh, temp_k)

def simulate_light_iv(v, iph=0.02, i0=1e-10, n=1.5, rs=0.1, rsh=1e6, temp_k=298.15):
    """
    Simulate light IV.
    """
    return one_diode_equation(v, iph, i0, n, rs, rsh, temp_k)

def test_ideality_extraction():
    print("Testing Ideality Factor Extraction...")
    v = np.linspace(0.4, 0.6, 50) # Use lower voltage range to avoid saturation
    target_n = 1.6
    temp_c = 25.0
    
    # Generate data (should be negative for V > 0 in one_diode_equation)
    j = simulate_dark_iv(v, n=target_n, temp_k=temp_c+273.15)
    noise = np.random.normal(0, np.abs(j) * 0.01)
    j_noisy = j + noise
    
    extracted_n = extract_ideality_from_slope(v, j_noisy, temp_c)
    print(f"Target n: {target_n}")
    print(f"Extracted n: {extracted_n:.4f}")
    
    assert abs(extracted_n - target_n) < 0.1, f"Extracted n {extracted_n} too far from {target_n}"
    print("Ideality extraction test PASSED.\n")

def test_dark_solver():
    print("Testing Dark J-V Solver...")
    v = np.linspace(-0.2, 0.8, 100) # Include forward bias range
    target_i0 = 2e-9
    target_n = 1.4
    target_rs = 2.0
    target_rsh = 5000.0
    temp_c = 25.0
    
    # Simulating data using the exact model the solver uses
    j = simulate_dark_iv(v, i0=target_i0, n=target_n, rs=target_rs, rsh=target_rsh, temp_k=temp_c+273.15)
    
    params, config, _ = solve_iv_curve(
        V=v,
        I=j,
        cell_area_cm2=1.0,
        temperature_c=temp_c,
        mode=AnalysisMode.EXPLORATION,
        model_type=ModelType.ONE_DIODE,
        measurement_type=MeasurementType.DARK
    )
    
    print(f"Target n: {target_n}, Solved n: {params.n_dark:.4f}")
    print(f"Target i0: {target_i0}, Solved i0: {params.i_0_dark:.2e}")
    
    assert abs(params.n_dark - target_n) < 0.1, f"Solved n {params.n_dark} too far from {target_n}"
    assert abs(np.log10(params.i_0_dark) - np.log10(target_i0)) < 0.5, f"Solved i0 {params.i_0_dark} too far from {target_i0}"
    print("Dark solver test PASSED.\n")

def test_light_ideality_extraction():
    print("Testing Illuminated Ideality Extraction (with compensation)...")
    v = np.linspace(0.4, 0.6, 50)
    target_n = 1.3
    temp_c = 25.0
    iph = 0.025 # 25mA
    
    # Generate light data
    j = simulate_light_iv(v, iph=iph, i0=1e-9, n=target_n, temp_k=temp_c+273.15)
    
    # Extract with IS_LIGHT=TRUE
    extracted_n = extract_ideality_from_slope(v, j, temp_c, is_light=True, j_sc=iph)
    print(f"Target n: {target_n}, Extracted n (with Jsc={iph}): {extracted_n:.4f}")
    
    assert abs(extracted_n - target_n) < 0.1, f"Extracted n {extracted_n} too far from {target_n}"
    print("Illuminated ideality extraction test PASSED.\n")

if __name__ == "__main__":
    try:
        test_ideality_extraction()
        test_light_ideality_extraction()
        test_dark_solver()
        print("ALL PHYSICS VERIFICATION TESTS PASSED.")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        exit(1)
