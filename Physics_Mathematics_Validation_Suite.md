# 🧪 **Helios Core: Comprehensive Physics & Mathematics Validation Suite**

## 🎯 **Test Objective**

Validate the mathematical correctness, numerical stability, and physical plausibility of all physics calculations in Helios Core across diverse solar cell technologies and edge cases.

## 📋 **Test Categories**

### **1. Core Diode Equation Validation**

```
Test: Verify single-diode equation solutions across parameter space
Method: Generate synthetic IV curves with known parameters, solve, compare
Tolerance: Parameters within 0.1% of ground truth
Edge Cases:
  - High series resistance (Rs > 100 Ω·cm²)
  - Low shunt resistance (Rsh < 10 Ω·cm²)
  - Non-ideal diodes (n = 0.8, 1.5, 2.5)
  - Low-light conditions (Jsc < 1 mA/cm²)
  - High Voc devices (Voc > 1.2V)
```

### **2. Numerical Determinism Verification**

```
Test: Confirm bitwise identical results across repeated runs
Method: 1000 identical inputs, SHA-256 hash of outputs
Requirements:
  - All 1000 hashes identical
  - No floating-point nondeterminism
  - Thread-safe execution
  - Platform-independent within IEEE 754
```

### **3. Solver Convergence Analysis**

```
Test: Validate solver converges to global minimum
Method: Multiple starting points, compare final parameters
Metrics:
  - Parameter spread < 0.01%
  - Residual RMS consistency
  - Convergence time distribution
  - No boundary sticking (parameters not at bounds)
```

### **4. Physical Bounds Enforcement**

```
Test: Ensure all extracted parameters are physically plausible
Bounds:
  - Jsc > 0 (positive photocurrent)
  - Voc > 0 (positive open-circuit voltage)
  - 0.3 < FF < 0.85 (reasonable fill factor)
  - 0.8 ≤ n ≤ 2.5 (ideality factor range)
  - Rs ≥ 0 (non-negative series resistance)
  - Rsh ≥ 0 (non-negative shunt resistance)
```

### **5. Derivative Parameter Consistency**

```
Test: Verify derived parameters match fundamental equations
Equations to Test:
  1. PCE = (Jsc × Voc × FF) / Pin × 100%
  2. Jmp × Vmp = Jsc × Voc × FF
  3. dV/dJ at Voc ≈ -Rsh (for ideal diode)
  4. dV/dJ at Jsc ≈ -Rs (for ideal diode)
  5. FF ≈ (v_oc - ln(v_oc + 0.72))/(v_oc + 1) (empirical, v_oc = qVoc/nkT)
```

### **6. Temperature Dependence Validation**

```
Test: Confirm temperature coefficients calculated correctly
Method: Simulate IV curves at 273K, 298K, 323K
Verify:
  - dVoc/dT ≈ -2.3 mV/K for silicon
  - dJsc/dT ≈ +0.1%/K for silicon
  - dFF/dT ≈ -0.2%/K for silicon
  - STC normalization accuracy
```

### **7. Noise Robustness Testing**

```
Test: Parameter stability under measurement noise
Method: Add Gaussian noise (0.1%, 0.5%, 1%, 2%, 5%)
Requirements:
  - Parameter drift < noise amplitude × 2
  - No catastrophic failure (solver still converges)
  - Residual RMS scales with noise level
```

### **8. Model Selection Validation**

```
Test: One-diode vs two-diode model comparison
Method: Generate data from both models, test both fits
Criteria:
  - Correct model should have lower AIC/BIC
  - Residuals should be random for correct model
  - Parameter count penalty applied correctly
  - Overfitting detection working
```

### **9. Edge Case Stress Testing**

```
Test Cases:
  1. S-shaped JV curves (injection barriers)
  2. Double-diode behavior (n1 ≈ 1, n2 ≈ 2)
  3. Reverse breakdown (sharp current increase)
  4. Light-soaking effects (Voc increase with time)
  5. Hysteresis (forward vs reverse scan differences)
  6. Partial shading (multiple steps in IV curve)
```

### **10. Computational Performance**

```
Test: Solver performance across curve complexity
Metrics:
  - Time per curve (Exploration vs Reference mode)
  - Memory usage scaling with data points
  - Convergence rate vs parameter count
  - Cache effectiveness for similar curves
```

## 🧮 **Mathematical Validation Tests**

### **Test 1: Diode Equation Root Finding**

```python
def test_diode_equation_root():
    """
    For given parameters {Iph, I0, n, Rs, Rsh},
    solve I = Iph - I0[exp((V+IRs)/(nVt))-1] - (V+IRs)/Rsh
    Verify residual < 1e-12 for all V in [-0.1, Voc+0.1]
    """
```

### **Test 2: Parameter Sensitivity Analysis**

```python
def test_parameter_jacobian():
    """
    Compute ∂J/∂p for each parameter p at MPP
    Verify:
      - ∂PCE/∂Rs < 0 (series resistance hurts efficiency)
      - ∂PCE/∂Rsh > 0 (shunt resistance helps efficiency)
      - ∂Voc/∂I0 < 0 (higher saturation current lowers Voc)
      - ∂Jsc/∂Rsh ≈ 0 (shunt doesn't affect Jsc much)
    """
```

### **Test 3: Energy Conservation**

```python
def test_energy_conservation():
    """
    For synthesized IV curve:
    ∫(J × V)dV from 0 to Voc ≈ Jsc × Voc × FF
    Power under curve matches calculated MPP
    """
```

### **Test 4: Reciprocity Theorem**

```python
def test_reciprocity():
    """
    For linear regime (near Voc):
    dJ/dV at light ≈ dJ/dV at dark + qJsc/(nkT)
    (Superposition principle for solar cells)
    """
```

## 📊 **Validation Dataset**

### **Synthetic Data Generation:**

```python
def generate_validation_dataset():
    """
    Create 1000 synthetic IV curves covering:
    - 5 material types (Si, GaAs, Perovskite, Organic, CIGS)
    - 4 illumination levels (0.1, 0.5, 1.0, 1.5 suns)
    - 3 temperature points (275K, 300K, 325K)
    - 2 noise levels (0%, 1%)
    - Known ground truth parameters
    """
```

### **Real Data Benchmarks:**

```
Include NREL reference datasets:
1. Silicon champion cells (NREL efficiency records)
2. Perovskite stability study data
3. Multi-junction NASA datasets
4. Degradation time-series
```

## 🔬 **Physics-Specific Tests**

### **For Silicon Cells:**

```python
def test_silicon_specific():
    """
    Silicon-specific validations:
    1. n ≈ 1.0-1.2 for high-quality cells
    2. Temperature coefficients match literature
    3. Rs < 1 Ω·cm² for good cells
    4. Rsh > 1000 Ω·cm² for good cells
    """
```

### **For Perovskite Cells:**

```python
def test_perovskite_specific():
    """
    Perovskite-specific validations:
    1. n often 1.5-2.0 (trap-assisted recombination)
    2. Hysteresis index calculation
    3. Light-soaking Voc increase
    4. S-shaped curve detection
    """
```

### **For Organic PV:**

```python
def test_organic_specific():
    """
    Organic PV validations:
    1. Low FF (<0.65) typical
    2. High series resistance common
    3. Non-geminate recombination models
    4. Field-dependent charge generation
    """
```

## 🧪 **Experimental Validation Protocol**

### **Step 1: Unit Tests**

```bash
pytest tests/physics/test_diode_equations.py -v
pytest tests/physics/test_parameter_extraction.py -v
pytest tests/physics/test_derived_parameters.py -v
```

### **Step 2: Integration Tests**

```bash
python tests/integration/test_full_pipeline.py
# Tests: Upload → Parse → Solve → Export → Reproduce
```

### **Step 3: Determinism Tests**

```bash
python tests/determinism/test_bitwise_reproducibility.py
# Run same analysis 100x, verify identical hashes
```

### **Step 4: Cross-Platform Validation**

```bash
# Test on: Windows, Linux, macOS
# Different Python versions: 3.9, 3.10, 3.11
# Different BLAS backends: OpenBLAS, MKL, Accelerate
```

### **Step 5: Benchmark Against Established Tools**

```python
def benchmark_against_reference():
    """
    Compare with:
    1. PVLighthouse's PVDP
    2. SCAPS-1D simulations
    3. Sentaurus TCAD
    4. Manual expert analysis
    """
```

## 📈 **Acceptance Criteria**

### **Numerical Accuracy:**

- Parameters within 0.1% of ground truth for synthetic data
- Residual RMS < 0.1% of Jsc for good fits
- No NaN or Inf in any calculation
- All derivatives numerically stable

### **Physical Plausibility:**

- 100% of parameters within physical bounds
- No unphysical correlations (e.g., higher Rs giving higher FF)
- Temperature trends match semiconductor physics
- Ideality factors match expected ranges for materials

### **Determinism:**

- 100% hash match across 1000 identical runs
- Platform differences < specified tolerances
- Random seeds working correctly in both modes

### **Performance:**

- Exploration mode < 10 seconds per curve
- Reference mode < 120 seconds per curve
- Memory usage < 500MB for 100-curve batch
- Linear scaling with data points

## 🚨 **Failure Modes to Detect**

### **Mathematical Failures:**

1. Solver converging to local minima
2. Numerical instability in derivatives
3. Poor conditioning in parameter space
4. Overflow/underflow in exponential terms

### **Physical Failures:**

1. Negative resistances
2. Ideality factor outside [0.8, 2.5]
3. FF > 0.9 (physically impossible)
4. Temperature coefficients wrong sign

### **Implementation Failures:**

1. Memory leaks in large batches
2. Thread safety issues
3. Platform-specific numerical differences
4. Cache invalidation errors

## 📋 **Validation Report Template**

```markdown
# Helios Core Physics Validation Report

## Date: [Date]

## Version: [Version]

### Executive Summary

- [ ] All mathematical tests passed
- [ ] Physical bounds respected
- [ ] Determinism verified
- [ ] Performance targets met

### Detailed Results

1. Core Equations: X/X tests passed
2. Parameter Extraction: Y/Y tests passed
3. Derived Parameters: Z/Z tests passed
4. Edge Cases: A/A handled correctly

### Issues Found

1. [Critical/High/Medium/Low] Issue description
2. [Critical/High/Medium/Low] Issue description

### Recommendations

1. Fix [issue] before release
2. Monitor [parameter] in production
3. Add test for [scenario]

### Sign-off

[ ] Mathematics validated
[ ] Physics validated  
[ ] Determinism verified
[ ] Ready for production
```

## 🎯 **Final Verification Command**

```bash
# Run complete validation suite
./scripts/validate_physics.sh --all --report --verbose

# Expected output:
# ✅ 152/152 mathematical tests passed
# ✅ 89/89 physical validation tests passed
# ✅ Determinism: 1000/1000 identical hashes
# ✅ Performance: Exploration 8.2s, Reference 58.3s
# ✅ Ready for scientific publication use
```

## 💡 **Prompt for Testing:**

**"Run the comprehensive physics and mathematics validation suite for Helios Core. Generate synthetic IV curves covering the full parameter space of realistic solar cells (silicon, perovskite, CIGS, organic PV) with known ground truth parameters. Test: 1) Single-diode equation solutions accuracy to 0.1%, 2) Parameter extraction deterministic across 1000 runs, 3) Physical bounds enforcement, 4) Derived parameter consistency with fundamental equations, 5) Temperature dependence correctness, 6) Noise robustness up to 5% Gaussian noise, 7) Edge case handling (S-curves, hysteresis, breakdown), and 8) Computational performance within targets. Output a detailed validation report with pass/fail status for each test category, identified issues ranked by severity, and recommendations for fixes before production deployment."**
