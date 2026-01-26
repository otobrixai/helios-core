# Helios Core

**Deterministic, Auditable, Publication-Ready IV Characterization**

> Version 1.0 — Scientific Reference Edition

---

## 🚀 High-Performance Scientific UI

Helios Core now features a specialized scientific viewport with:

- **Min-Max Data Decimation**: Instant rendering of high-resolution curves (10,000+ points) without losing critical extrema.
- **GPU-Accelerated Plots**: 60fps interaction using hardware-layer rendering for all IV and Power curves.
- **Progressive Diagnostics**: Multi-stage physics audit (Quick Residuals → Full Validation) for immediate feedback.
- **Export Integrity Guard**: Fresh-recalculated ZIP bundles with SHA-256 verification and automated MD5 checksums.
- **Performance Shield**: Real-time telemetry HUD tracking FPS, JS Memory, and Data Integrity.

---

## 🛠 Quick Start

### Local Development

```bash
# 1. Start Backend (Root)
python -m venv .venv
# Activate venv (.venv\Scripts\activate on Windows)
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# 2. Start Frontend (Separate Terminal)
cd frontend
npm install
npm run dev
```

### 📦 Deployment

For production-grade scientific hosting, see the [Full Deployment Guide](./DEPLOYMENT.md).

---

## 🧬 System Architecture

- **Physics Engine**: Determinism-locked solver using L-M refinement and Differential Evolution.
- **Data Layer**: SQLite persistence with self-healing file ingestion.
- **Frontend**: Next.js 16 (Turbopack) with custom Recharts wrappers.

---

## 📄 Documentation

- [Deployment Specifications](./DEPLOYMENT.md)

## License

MIT
