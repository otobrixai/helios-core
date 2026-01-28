# Helios Core — Physics Reference

This document outlines the mathematical models, physical constants, and conversion logic used by the Helios Core solver for parameter extraction and data analysis.

---

## 1. Physical Constants

The solver uses standard CODATA fundamental constants for all thermal voltage calculations.

| Constant              | Symbol    | Value                      | Unit     |
| :-------------------- | :-------- | :------------------------- | :------- |
| Boltzmann Constant    | $k_B$     | $1.380649 \times 10^{-23}$ | J/K      |
| Elementary Charge     | $q$       | $1.602176 \times 10^{-19}$ | C        |
| Standard Temperature  | $T_{STC}$ | $298.15$                   | K (25°C) |
| Thermal Voltage (STC) | $V_t$     | $\approx 0.0257$           | V        |

**Thermal Voltage Equation:**
$$V_t = \frac{k_B T}{q}$$

---

## 2. Diode Models

Helios Core utilizes global optimization (Differential Evolution) followed by local refinement (Levenberg-Marquardt) to fit raw $I-V$ data to these models.

### 2.1 One-Diode Model

The standard model for most solar cell technologies (Si, Perovskite, Organic).

$$I = I_{ph} - I_0 \left[ \exp\left(\frac{V + I R_s}{n V_t}\right) - 1 \right] - \frac{V + I R_s}{R_{sh}}$$

- **$I_{ph}$**: Photocurrent (A)
- **$I_0$**: Dark saturation current (A)
- **$n$**: Ideality factor (typically 1.0–2.0)
- **$R_s$**: Series resistance ($\Omega$)
- **$R_{sh}$**: Shunt resistance ($\Omega$)

### 2.2 Two-Diode Model

Used for cells with significant recombination at the space-charge region or grain boundaries.

$$I = I_{ph} - I_{01}\left(\exp\left(\frac{V_j}{n_1 V_t}\right) - 1\right) - I_{02}\left(\exp\left(\frac{V_j}{n_2 V_t}\right) - 1\right) - \frac{V_j}{R_{sh}}$$
_Where $V_j = V + I R_s$_

---

## 3. Performance Metrics

These values are extracted either directly from the data (using interpolation) or derived from the fitted model parameters.

### 3.1 Short-Circuit Current ($J_{sc}$)

The current density when $V = 0$.
$$J_{sc} \text{ [mA/cm}^2\text{]} = \frac{|I(V=0)|}{\text{Area}} \times 1000$$

### 3.2 Open-Circuit Voltage ($V_{oc}$)

The voltage when $I = 0$. Found using linear interpolation between the two points surrounding the zero-crossing.
$$V_{oc} = |V(I=0)|$$

### 3.3 Fill Factor ($FF$)

The ratio of maximum power to the theoretical maximum.
$$FF = \frac{P_{max}}{V_{oc} \cdot I_{sc}}$$
_Note: Helios Core ensures $P_{max}$ is calculated within the power-producing quadrant._

### 3.4 Power Conversion Efficiency ($\eta$)

$$P_{in} = 100 \text{ mW/cm}^2 \text{ (1 Sun)}$$
$$\eta \text{ [\%]} = \frac{P_{max}}{\text{Area} \cdot P_{in}} \times 100$$

---

## 4. Normalization and Scaling

Helios Core converts all absolute values ($\Omega$, A) to normalized values ($\Omega \cdot cm^2$, $mA/cm^2$) for standardized reporting.

### 4.1 Resistance Normalization

To compare cells of different sizes, resistances must be normalized by area:
$$R_{\text{normalized}} \text{ [}\Omega \cdot cm^2\text{]} = R_{\text{absolute}} \text{ [}\Omega\text{]} \times \text{Area [}cm^2\text{]}$$

### 4.2 Current Normalization

$$J \text{ [mA/cm}^2\text{]} = \frac{I \text{ [A]} \times 1000}{\text{Area [}cm^2\text{]}}$$

---

## 5. Automated Data Handling

### 5.1 Sign Convention

Helios Core automatically detects the data's sign convention. If current at $V > 0$ is negative (sink convention), the engine automatically flips it for fitting against the generator-based diode equations.

### 5.2 Unit Detection

The engine automatically scales current based on detected column headers:

- **mA/cm² or mA**: Scale by $10^{-3}$
- **µA/cm² or µA**: Scale by $10^{-6}$
- **A**: No scaling
