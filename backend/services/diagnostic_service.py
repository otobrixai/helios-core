"""
Service that generates comprehensive diagnostic reports
Implements B.L.A.S.T. Protocol: Boundary, Linear, Adversarial, Stress, Transparency
"""

import numpy as np
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import hashlib
from datetime import datetime

@dataclass
class DiagnosticReport:
    """Comprehensive diagnostic report for a solar cell analysis"""
    
    def __init__(self, analysis_id: str, mode: str):
        self.analysis_id = analysis_id
        self.mode = mode
        self.timestamp = datetime.utcnow().isoformat()
        self.residuals: Optional[Dict[str, Any]] = None
        self.noise_stability: Optional[Dict[str, Any]] = None
        self.boundary_stress: Optional[Dict[str, Any]] = None
    
    def analyze_residuals(self, voltage: np.ndarray, 
                         measured: np.ndarray, 
                         fitted: np.ndarray) -> Dict[str, Any]:
        """Analyze residual patterns with scientific classification"""
        
        residuals = measured - fitted
        rms = np.sqrt(np.mean(residuals**2))
        
        # Avoid division by zero with safe PTP
        ptp_voltage = np.ptp(voltage) if len(voltage) > 1 else 1.0
        ptp_residuals = np.ptp(residuals) if len(residuals) > 1 else 0.0
        
        if len(voltage) > 1:
            # 1. Linear trend analysis
            slope, intercept = np.polyfit(voltage, residuals, 1)
            # Handle correlation coef
            corr_matrix = np.corrcoef(voltage, residuals)
            if corr_matrix.shape == (2, 2):
                r_squared = corr_matrix[0, 1]**2
            else:
                r_squared = 0.0
            
            # 2. Quadratic curvature analysis
            poly2 = np.polyfit(voltage, residuals, 2)
            quad_strength = abs(poly2[0]) * ptp_voltage**2
            
            # 3. S-shape detection (cubic analysis)
            poly3 = np.polyfit(voltage, residuals, 3)
            cubic_strength = abs(poly3[0]) * ptp_voltage**3
        else:
            slope, r_squared, quad_strength, cubic_strength = 0.0, 0.0, 0.0, 0.0
        
        # Classification logic
        if cubic_strength > 0.15 * rms:
            pattern = "s_shaped"
            warning = "CRITICAL"
            message = "S-shaped residuals indicate injection/extraction barriers"
        elif quad_strength > 0.1 * rms:
            pattern = "systematic_curvature"
            warning = "HIGH"
            message = "Systematic curvature suggests model mismatch"
        elif abs(slope) > 0.05 * (ptp_residuals / ptp_voltage if ptp_voltage > 0 else 1.0):
            pattern = "linear_trend"
            warning = "MEDIUM"
            message = "Linear trend indicates potential series resistance error"
        else:
            pattern = "random"
            warning = "LOW"
            message = "Residuals appear random (good fit)"
        
        self.residuals = {
            "pattern": pattern,
            "warning": warning,
            "message": message,
            "rms": float(rms),
            "slope": float(slope),
            "r_squared": float(r_squared),
            "quadratic_strength": float(quad_strength),
            "cubic_strength": float(cubic_strength),
            "classification_confidence": self._calculate_confidence(residuals)
        }
        
        return self.residuals
    
    def analyze_noise_stability(self, parameters: Dict[str, Any], 
                               clean_results: Dict[str, Any],
                               noisy_results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze parameter stability under noise perturbation"""
        
        drifts = {}
        for param in ['Jsc', 'Voc', 'FF', 'Rs', 'Rsh', 'n']:
            # Handle key variations if necessary (e.g., 'j_sc' vs 'Jsc')
            # For this service we expect normalized keys, or we utilize a mapper.
            # Assuming input keys match requirements or are handled by caller.
            clean_val = clean_results.get(param, 0.0)
            if clean_val == 0:
                continue
                
            # Calculate drift for each noise instance
            param_drifts = []
            for noisy_result in noisy_results_list:
                noisy_val = noisy_result.get(param, 0.0)
                drift = abs(noisy_val - clean_val) / clean_val
                param_drifts.append(drift)
            
            drifts[param] = {
                "mean": float(np.mean(param_drifts)),
                "std": float(np.std(param_drifts)),
                "max": float(np.max(param_drifts))
            }
        
        # Calculate overall stability score (0-100%)
        # Lower drift = higher score
        if drifts:
            max_drifts = [drifts[p]["max"] for p in drifts]
            avg_max_drift = np.mean(max_drifts)
            stability_score = max(0, 100 * (1 - 10 * avg_max_drift))  # Scale factor
            worst_case = float(np.max(max_drifts))
        else:
            stability_score = 0
            worst_case = 0
        
        self.noise_stability = {
            "stability_score": float(stability_score),
            "parameter_drifts": drifts,
            "worst_case_drift": worst_case,
            "noise_level_tested": 0.02,  # 2% Gaussian noise - standardized anchor
            "n_iterations": len(noisy_results_list)
        }
        
        return self.noise_stability
    
    def analyze_boundary_stress(self, parameters: Dict[str, Any], 
                               bounds: Dict[str, tuple]) -> Dict[str, Any]:
        """Check if parameters are hitting physical boundaries"""
        
        boundary_hits = []
        recommendations = []
        
        # Check each parameter against bounds
        for param, (lower, upper) in bounds.items():
            value = parameters.get(param)
            if value is None:
                continue
            
            # Calculate distance to boundaries (normalized)
            if lower is not None and value <= lower * 1.1:  # Within 10% of bound
                boundary_hits.append({
                    "parameter": param,
                    "value": float(value),
                    "bound": float(lower),
                    "direction": "lower",
                    "distance_percent": float(abs((value - lower) / lower) * 100) if lower != 0 else 0.0,
                    "severity": "ERROR" if value <= lower else "WARNING"
                })
                
                if param == 'n' and value <= 0.8:
                    recommendations.append(f"Non-ideal diode (n={value:.2f}). Consider recombination analysis.")
                elif param == 'Rsh' and value <= 10:
                    recommendations.append(f"Low shunt resistance ({value:.1f} Ω). Check for shunts or degradation.")
                    
            elif upper is not None and value >= upper * 0.9:  # Within 10% of bound
                boundary_hits.append({
                    "parameter": param,
                    "value": float(value),
                    "bound": float(upper),
                    "direction": "upper",
                    "distance_percent": float(abs((value - upper) / upper) * 100) if upper != 0 else 0.0,
                    "severity": "ERROR" if value >= upper else "WARNING"
                })
                
                if param == 'n' and value >= 2.5:
                    recommendations.append(f"High ideality factor (n={value:.2f}). Multiple recombination pathways likely.")
                elif param == 'Rs' and value >= 100:
                    recommendations.append(f"High series resistance ({value:.1f} Ω). Check contacts and grid design.")
        
        self.boundary_stress = {
            "boundary_hits": boundary_hits,
            "n_hits": len(boundary_hits),
            "recommendations": recommendations,
            "bounds_used": bounds
        }
        
        return self.boundary_stress
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        
        # Calculate overall risk score
        risk_factors = []
        
        if self.residuals:
            residual_risk = {
                "LOW": 10,
                "MEDIUM": 40,
                "HIGH": 70,
                "CRITICAL": 90
            }.get(self.residuals["warning"], 50)
            risk_factors.append(residual_risk)
        
        if self.noise_stability:
            noise_risk = 100 - self.noise_stability["stability_score"]
            risk_factors.append(noise_risk)
        
        if self.boundary_stress:
            boundary_risk = min(100, self.boundary_stress["n_hits"] * 20)
            risk_factors.append(boundary_risk)
        
        overall_risk = np.mean(risk_factors) if risk_factors else 0
        
        # Generate report
        report = {
            "timestamp": self.timestamp,
            "analysis_id": self.analysis_id,
            "mode": self.mode,
            "residuals": self.residuals,
            "noise_stability": self.noise_stability,
            "boundary_stress": self.boundary_stress,
            "overall_risk_score": float(overall_risk),
            "validation_passed": bool(overall_risk < 50),
            "recommendations": self._generate_recommendations(),
            "metadata": {
                "diagnostic_version": "1.0",
                "generator": "Helios Core Diagnostic Service"
            }
        }
        
        # Add hash for immutability
        try:
            report_str = json.dumps(report, sort_keys=True)
            report["hash"] = hashlib.sha256(report_str.encode()).hexdigest()
        except TypeError:
            # Fallback for non-serializable types if any creep in
            report["hash"] = "hashing_failed"
        
        return report
    
    def _calculate_confidence(self, residuals: np.ndarray) -> float:
        """Calculate confidence in residual classification"""
        # Based on how well residuals match expected patterns
        if len(residuals) < 5:
            return 0.0
            
        autocorr = np.correlate(residuals, residuals, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        if autocorr[0] == 0:
            return 0.0
            
        autocorr = autocorr / autocorr[0]
        
        # Random residuals have quick autocorrelation decay
        decay_rate = np.mean(np.abs(autocorr[1:5]))
        confidence = 100 * (1 - decay_rate)
        
        return float(np.clip(confidence, 0, 100))
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on diagnostics"""
        recommendations = []
        
        if self.residuals:
            if self.residuals["pattern"] == "s_shaped":
                recommendations.append("S-shaped residuals detected. Consider: 1) Check for voltage-dependent photogeneration, 2) Analyze injection barriers, 3) Test two-diode model")
            elif self.residuals["pattern"] == "systematic_curvature":
                recommendations.append("Systematic curvature in residuals. Try: 1) Two-diode model, 2) Check for series resistance variation, 3) Verify illumination uniformity")
        
        if self.noise_stability and self.noise_stability.get("stability_score", 100) < 80:
            recommendations.append(f"Low noise stability ({self.noise_stability['stability_score']:.0f}%). Parameters may be poorly constrained. Collect more data points near MPP.")
        
        if self.boundary_stress and self.boundary_stress.get("n_hits", 0) > 0:
            hit_params = [h["parameter"] for h in self.boundary_stress["boundary_hits"]]
            recommendations.append(f"Parameters hitting bounds: {', '.join(hit_params)}. Consider relaxing bounds or collecting higher-quality data.")
        
        return recommendations
