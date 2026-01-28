import numpy as np
import pytest
from backend.services.physics_service import extract_ideality_from_slope, calculate_dual_metrics, estimate_recombination_mechanism
from backend.tools.solve_iv_curve import solve_iv_curve, one_diode_equation
from backend.models.entities import AnalysisMode, ModelType, MeasurementType, ExtractedParameters

class TestDarkConditionAnalysis:
    
    def test_dark_ideality_extraction(self):
        """Test ideality factor from dark forward bias using real physics_service"""
        V = np.linspace(0.1, 0.7, 100)
        I0 = 1e-10
        n = 1.5
        temp_c = 25.0
        # Diode characteristic: J = J0 * (exp(V/nVt) - 1)
        # Our solver uses vt = kT/q
        vt = 1.380649e-23 * (temp_c + 273.15) / 1.602176634e-19
        
        # Current should be negative for forward bias in our convention (power sink)
        I = -I0 * (np.exp(V / (n * vt)) - 1)
        
        extracted_n = extract_ideality_from_slope(V, I, temp_c=temp_c, is_light=False)
        
        # Check within 5% (noise/slope extraction sensitivity)
        assert abs(extracted_n - n) / n < 0.05, f"n mismatch: {extracted_n} vs {target_n}"
    
    def test_dark_vs_light_comparison(self):
        """Test light/dark parameter comparison using calculate_dual_metrics"""
        # Create mock parameter objects
        dark_params = ExtractedParameters(
            j_sc=0.0, v_oc=0.0, ff=0.0, pce=0.0, r_s=2.0, r_sh=1000.0, n_ideality=1.5, i_0=1e-10
        )
        light_params = ExtractedParameters(
            j_sc=35.0, v_oc=0.6, ff=0.7, pce=15.0, r_s=2.2, r_sh=800.0, n_ideality=1.8
        )
        
        comparison = calculate_dual_metrics(light_params, dark_params)
        
        # n should increase under illumination (delta_n = light - dark)
        assert comparison.delta_n is not None
        assert comparison.delta_n > 0, "n should increase with light in this test case"
        assert abs(comparison.delta_n - 0.3) < 1e-6
        
        # Dark-specific fields should be populated
        assert comparison.n_dark == 1.5
        assert comparison.r_sh_dark == 1000.0
    
    def test_dark_saturation_current_solver(self):
        """Test I0 extraction using the full solver (Dark J-V mode)"""
        # Limit V to 0.7V to avoid huge currents that skew fitting or hit numerical bounds
        V = np.linspace(-0.2, 0.7, 100)
        target_i0 = 2e-10
        target_n = 1.3
        target_rs = 0.8
        target_rsh = 10000.0
        temp_c = 25.0
        
        # Simulate data using standard diode equation
        I = one_diode_equation(V, 0.0, target_i0, target_n, target_rs, target_rsh, temp_c + 273.15)
        
        params, _, _ = solve_iv_curve(
            V=V, I=I, cell_area_cm2=1.0, temperature_c=temp_c,
            mode=AnalysisMode.EXPLORATION, model_type=ModelType.ONE_DIODE,
            measurement_type=MeasurementType.DARK
        )
        
        assert abs(params.n_dark - target_n) < 0.1
        # Log10 check for I0 since it spans orders of magnitude
        assert abs(np.log10(params.i_0_dark) - np.log10(target_i0)) < 0.5
    
    def test_physical_bounds_dark(self):
        """Test dark parameters are within reasonable scientific bounds"""
        V = np.linspace(0.1, 1.0, 100)
        # Extreme case: n=2.8
        I = -1e-9 * (np.exp(V / (2.8 * 0.0259)) - 1)
        
        params, _, _ = solve_iv_curve(
            V=V, I=I, cell_area_cm2=1.0, temperature_c=25.0,
            mode=AnalysisMode.EXPLORATION, model_type=ModelType.ONE_DIODE,
            measurement_type=MeasurementType.DARK
        )
        
        assert 0.8 <= params.n_dark <= 3.5
        assert params.i_0_dark > 0
        
    def test_determinism_dark(self):
        """Dark analysis must be deterministic (same results for same input)"""
        V = np.linspace(-0.5, 0.7, 200)
        # Use a fixed seed for jitter if we had any, but the core solver is deterministic with fixed seed
        I = one_diode_equation(V, 0.0, 1e-10, 1.5, 1.0, 10000.0, 298.15)
        
        params1, _, _ = solve_iv_curve(
            V=V, I=I, cell_area_cm2=1.0, temperature_c=25.0,
            mode=AnalysisMode.EXPLORATION, model_type=ModelType.ONE_DIODE,
            measurement_type=MeasurementType.DARK
        )
        
        params2, _, _ = solve_iv_curve(
            V=V, I=I, cell_area_cm2=1.0, temperature_c=25.0,
            mode=AnalysisMode.EXPLORATION, model_type=ModelType.ONE_DIODE,
            measurement_type=MeasurementType.DARK
        )
        
        assert params1.n_dark == params2.n_dark
        assert params1.i_0_dark == params2.i_0_dark
        assert params1.r_s_dark == params2.r_s_dark

@pytest.mark.quick
def test_quick_dark_analysis_smoke():
    """Quick smoke test for basic connectivity"""
    # Simple dark curve
    V = np.array([-0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7])
    I = np.array([-1e-10, -1e-10, -1e-10, 1e-9, 1e-7, 1e-5, 1e-3])
    # Flip current for our solver convention (needs to be negative for forward bias)
    I_solver = -np.abs(I) 
    
    params, _, _ = solve_iv_curve(
        V=V, I=I_solver, cell_area_cm2=1.0, temperature_c=25.0,
        mode=AnalysisMode.EXPLORATION, model_type=ModelType.ONE_DIODE,
        measurement_type=MeasurementType.DARK
    )
    
    assert params.n_dark > 0
    assert params.i_0_dark > 0
    
    mechanism = estimate_recombination_mechanism(params.n_dark)
    assert mechanism is not None
