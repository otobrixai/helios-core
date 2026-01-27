import numpy as np
import pandas as pd
from pathlib import Path

def generate_iv_curve(v, i_ph, i_0, n, r_s, r_sh, temp_k=298.15):
    k_b = 1.380649e-23
    q = 1.602176634e-19
    v_t = k_b * temp_k / q
    i = np.zeros_like(v)
    for _ in range(50):
        v_j = v + i * r_s
        exp_term = np.exp(np.clip(v_j / (n * v_t), -50, 50))
        f = i_ph - i_0 * (exp_term - 1) - v_j / r_sh - i
        df = -i_0 * exp_term * r_s / (n * v_t) - r_s / r_sh - 1
        i = i - f / df
    return i

v = np.linspace(-0.2, 0.8, 100)
p1_i = generate_iv_curve(v, 0.022, 1e-12, 1.5, 2.0, 1000.0) + np.random.normal(0, 1e-5, len(v))
p2_v = v + 0.01 
p2_i = generate_iv_curve(p2_v, 0.021, 5e-11, 1.8, 15.0, 50.0) + np.random.normal(0, 2e-4, len(v))

df = pd.DataFrame({
    'Voltage (V)': v,
    'Current_Density_1 (A/cm2)': p1_i,
    'Voltage_2 (V)': p2_v,
    'Current_Density_2 (A/cm2)': p2_i
})

output_path = Path('sample_scientific_data.csv')
df.to_csv(output_path, index=False)
print(f"Sample data generated at: {output_path.absolute()}")
