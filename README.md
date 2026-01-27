# 🚀 **Helios Core: Scientific IV Analysis Platform**

## 📋 **Executive Summary**

**Helios Core** is a **deterministic, auditable, and publication-ready** environment for solar cell current-voltage (IV) characterization. It replaces subjective, manual workflows with standards-compliant, reproducible analysis, ensuring that identical inputs produce bitwise-identical outputs within defined scientific tolerances.

---

## 🎯 **Core Mission & Philosophy**

### **Scientific Prime Directive:**

> "If the same data is analyzed twice under the same conditions, the result must be numerically consistent within defined tolerances, fully explainable, and independently reproducible."

### **Design Principles:**

1. **Determinism Over Speed** - Reproducibility prioritized over computational efficiency
2. **Transparency Over Convenience** - No black-box mathematics; all equations visible
3. **Immutability Over Flexibility** - Raw data is sacred and never modified
4. **Auditability Over Simplicity** - Every calculation is logged and traceable

---

## 🔬 **Scientific Capabilities**

### **1. Physics Engine**

#### **Supported Models:**

- **One-Diode Model** (Standard Shockley + Rs + Rsh)
- **Two-Diode Model** (Dual recombination pathways)

#### **Parameter Extraction:**

| Parameter                     | Symbol | Physical Meaning           | Typical Range |
| ----------------------------- | ------ | -------------------------- | ------------- |
| Short-circuit current density | Jsc    | Photogenerated current     | 0-50 mA/cm²   |
| Open-circuit voltage          | Voc    | Maximum voltage output     | 0-1.5 V       |
| Fill Factor                   | FF     | Squareness of IV curve     | 0.3-0.85      |
| Power conversion efficiency   | PCE    | Overall device performance | 0-30%         |
| Series resistance             | Rs     | Contact/transport losses   | 0-100 Ω·cm²   |
| Shunt resistance              | Rsh    | Recombination losses       | 10-10⁶ Ω·cm²  |
| Ideality factor               | n      | Recombination mechanism    | 0.8-2.5       |

### **2. Deterministic Solver Pipeline**

1. **Preconditioning** - Data normalization and validation
2. **Global Search** - Differential Evolution with fixed seed
3. **Local Refinement** - Levenberg-Marquardt optimization
4. **Post-fit Validation** - Physical plausibility checks

### **3. Advanced Analysis Features**

- **Hysteresis Index (HI)** - Forward vs reverse scan comparison
- **STC Normalization** - IEC 60891 standard corrections
- **Maximum Power Point (MPP)** - Cubic spline interpolation
- **Residual Analysis** - Model mismatch detection

---

## 🖥️ **User Workflow**

### **Phase 1: Data Ingestion**

```
Raw CSV/TXT/XLS → Auto-detection → Multi-pixel segmentation → Immutable storage
```

- **Smart Parser:** Detects voltage, current, hardware profiles (Keithley, Keysight, Ossila)
- **Provenance Tracking:** SHA-256 hashes of all raw data
- **Batch Processing:** Multi-pixel substrates automatically segmented

### **Phase 2: Interactive Analysis**

#### **Exploration Mode:**

- Manual data scrubbing/masking
- Interactive parameter adjustment
- Rapid preliminary fitting (~8 seconds/curve)
- Hypothesis testing and diagnostics

#### **Reference Mode (Publication Lock):**

- Deterministic analysis only
- Fixed seeds and tolerances
- Manual interventions disabled
- Bitwise reproducible results (~60 seconds/curve)

### **Phase 3: Scientific Output**

#### **Visualization Suite:**

- Primary IV and power curves
- Residual plots for model validation
- Batch statistical distributions
- Pixel spatial mapping

#### **Publication-Ready Export:**

```
Supplementary Bundle (.zip)
├── report.pdf          # Vector graphics, journal-compatible
├── data.csv            # Normalized IV data
├── audit.json          # Complete provenance and parameters
└── reproduce_analysis.py # Standalone reproduction script
```

---

## 🏗️ **Technical Architecture**

### **Frontend (Next.js + React)**

- **Three-Column Command Center:**
  1. **Inventory & Provenance** - Dataset management
  2. **Visual Analysis Hub** - IV/Power plots + residuals
  3. **Parameter Inspector** - Extracted metrics + diagnostics
- **Deterministic UI:** No hidden state, no UI-side calculations
- **Physics Audit Sidebar:** Real-time diagnostic monitoring

### **Backend (FastAPI + Python)**

- **Deterministic Physics Engine:** Fixed seeds, single-threaded BLAS
- **File-based Persistence:** SQLite + raw file storage
- **REST API:** Stateless, deterministic endpoints

### **Scientific Stack:**

- **pvlib-python** - Photovoltaic modeling (IEC-aligned)
- **SciPy** - Numerical optimization (Differential Evolution, LM)
- **NumPy** - Numerical primitives (float64 only)
- **Pandas** - Structured data handling

---

## 🔍 **Quality Assurance & Validation**

### **Determinism Contracts:**

| Aspect         | Control Method                           | Verification              |
| -------------- | ---------------------------------------- | ------------------------- |
| Floating-point | float64 only, explicit casting           | Bitwise hash equality     |
| Randomness     | Fixed seed (42) in Reference Mode        | SHA-256 output hashes     |
| Threading      | Single-threaded BLAS (OMP_NUM_THREADS=1) | Environment variable lock |
| Convergence    | Explicit tolerances (xtol, ftol, gtol)   | Solver log validation     |

### **Validation Suite:**

1. **Synthetic Dataset Testing** - 100+ curves with known parameters
2. **Noise Robustness** - Parameter stability under ±2% Gaussian noise
3. **Boundary Stress Testing** - Edge case handling (high Rs, low Rsh)
4. **Residual Pattern Analysis** - Systematic error detection

### **Performance Benchmarks:**

| Mode        | Time per Curve | Accuracy           | Use Case              |
| ----------- | -------------- | ------------------ | --------------------- |
| Exploration | 7-10 seconds   | ~99% of Reference  | Interactive screening |
| Reference   | 55-65 seconds  | 100% deterministic | Publication analysis  |

---

## 📊 **Output Artifacts**

### **1. Scientific Metrics**

- **Primary Parameters:** Jsc, Voc, FF, PCE, Rs, Rsh, n
- **Derived Metrics:** Hysteresis index, temperature coefficients
- **Quality Indicators:** RMS residuals, convergence status
- **Health Checks:** Parameter bounds, physical plausibility

### **2. Visualization Assets**

- **Publication-ready plots** (PDF, SVG, PNG)
- **Interactive web visualizations**
- **Batch comparison overlays**
- **Residual analysis charts**

### **3. Reproducibility Package**

- **Python reproduction script** - Standalone, dependency-managed
- **Audit metadata JSON** - Complete analysis provenance
- **Determinism hashes** - SHA-256 verification chains
- **Configuration snapshots** - Exact solver parameters

---

## 🎯 **Target Users & Applications**

### **Primary Users:**

1. **Solar Cell Researchers** - Perovskite, silicon, organic PV
2. **Device Fabrication Labs** - Process optimization, quality control
3. **Academic Institutions** - Teaching, student projects
4. **Industrial R&D** - Prototype characterization

### **Use Cases:**

- **Daily lab analysis** - Quick screening of fabrication batches
- **Publication preparation** - Reference-grade figure generation
- **Method validation** - Comparison against established techniques
- **Educational demonstrations** - Transparent physics education
- **Inter-lab comparisons** - Standardized analysis protocols

---

## ⚡ **Key Innovations**

### **1. Deterministic Analysis**

- First IV analysis tool guaranteeing bitwise reproducibility
- Cryptographic hash verification of all results
- Cross-platform numerical consistency within 0.1%

### **2. Physics Audit Trail**

- Real-time diagnostic monitoring
- Systematic error pattern detection
- Actionable scientific recommendations

### **3. Mode-Specific Workflows**

- **Exploration:** Fast, interactive hypothesis testing
- **Reference:** Locked, reproducible publication analysis

### **4. Complete Provenance**

- Raw data immutability
- Full parameter traceability
- Standalone reproduction capability

---

## 🚀 **Deployment & Access**

### **Current Deployment:**

- **Backend:** Render.com (Python FastAPI)
- **Frontend:** Vercel (Next.js React)
- **Storage:** File-based (SQLite + raw files)
- **Cost:** $0/month (free tier)

### **Access Methods:**

1. **Web Application** - Full interactive interface
2. **API Endpoints** - Programmatic access
3. **Export Scripts** - Standalone Python reproduction

---

## 📈 **Future Roadmap**

### **Short-term (v1.1):**

- Two-diode model validation
- Temperature-dependent analysis
- Batch statistical reporting

### **Medium-term (v2.0):**

- Transient photovoltage analysis
- Impedance spectroscopy integration
- Machine learning-assisted diagnostics

### **Long-term Vision:**

- Multi-technique characterization platform
- Collaborative analysis environments
- Cloud-based reproducibility archives

---

## 🔬 **Scientific Impact**

### **For Researchers:**

- Eliminates "analysis variability" between research groups
- Provides standardized methodology for IV characterization
- Enables true reproducibility in photovoltaic research
- Reduces time from measurement to publication

### **For the Field:**

- Sets new standards for computational reproducibility
- Provides reference implementation for IV analysis algorithms
- Creates audit trail for scientific data processing
- Democratizes advanced analysis capabilities

---

## 📞 **Getting Started**

### **For New Users:**

1. Upload CSV/TXT measurement file
2. Explore data in Exploration Mode
3. Switch to Reference Mode for final analysis
4. Export complete publication bundle

### **For Developers:**

- **Repository:** github.com/otobrixai/helios-core
- **Documentation:** Complete FRD, SAD, SOP specifications
- **API:** RESTful endpoints with OpenAPI documentation
- **Testing:** Comprehensive validation suite

---

## 🎯 **Final Value Proposition**

**Helios Core transforms IV characterization from an art into a science by providing:**

1. **🔬 Scientific Rigor** - Deterministic, physics-based analysis
2. **📊 Publication Readiness** - Complete export bundles with reproducibility scripts
3. **⚡ Practical Usability** - Fast exploration with rigorous reference modes
4. **🔍 Complete Transparency** - No black boxes, all mathematics exposed
5. **💰 Zero Cost** - Fully functional on free-tier infrastructure

---

**Helios Core isn't just software—it's a scientific instrument for the computational age, bringing the reproducibility crisis in photovoltaic research to an end, one deterministic analysis at a time.**
