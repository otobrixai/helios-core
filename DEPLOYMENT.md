# Helios Core: Deployment Guide

This guide details the process for deploying Helios Core to production environments.

## 🏗 Stack Overview

- **Frontend**: Next.js (Static Export or Node.js)
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite (Local persistence)
- **Engine**: pvlib/scipy/numpy (Deterministic Numerical context)

---

## 🚀 Option 1: Vercel (Recommended)

Helios Core is designed for seamless deployment on Vercel using the Mono-repo pattern.

### 1. Prerequisites

- A GitHub/GitLab repository with the project.
- A Vercel account.

### 2. Configuration

- **Build Command (Frontend)**: `npm run build`
- **Output Directory**: `.next`
- **Root Directory**: `frontend`
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: The URL of your deployed backend.

### 3. Serverless Functions (Python)

Vercel supports Python Serverless functions. However, because Helios Core handles heavy numerical computation and file persistence in `data/`, a **Render** or **Railway** backend is recommended for the API layer.

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
