# Helios Core: Deployment Guide

This guide details the process for deploying Helios Core to production environments.

## 🏗 Stack Overview

- **Frontend**: Next.js 16 (Node.js Server)
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite (Persistent Disk required)
- **Engine**: pvlib/scipy/numpy (Deterministic Numerical context)

---

## 🚀 Option 1: Render.com (Recommended)

Helios Core is optimized for Render using the included `render.yaml` Blueprint. This ensures the database and raw files persist across restarts.

### 1. Simple Deploy

1. Push your code to GitHub.
2. In Render, click **New +** and select **Blueprint**.
3. Connect your repository.
4. Render will automatically configure the Backend and Frontend.

### ⚠️ Free Tier Persistence

On the Render Free tier, the local SQLite database and `data/` folder are **ephemeral**. This means:

- Data is saved while the app is running.
- **Data is deleted** whenever the app "sleeps" (after 15 mins of inactivity) or redeploys.
- **Recommendation**: Always export your analysis results (CSV/Supplement bundle) before closing the app.

---

## 🌐 Option 2: VPS / Docker (Managed)

For full scientific integrity and persistent data storage, a traditional server setup is preferred.

### 1. Backend Setup (Docker)

Create a `Dockerfile` in the root:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Data Persistence

Ensure the `data/` volume is mounted as persistent storage to prevent loss of `raw/` measurements during restarts.

---

## ⚡ Performance Calibration

For production deployments, ensure the following environment variables are set to force bitwise determinism:

```bash
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1
```

These are automatically locked by `backend/config.py`, but setting them at the OS level provides defense-in-depth.
