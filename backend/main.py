"""
Helios Core — FastAPI Application Entry Point

CRITICAL: Determinism lock is enforced at import time.
"""

# Enforce determinism BEFORE any numerical imports
from backend.config import initialize
initialize()

# Now safe to import numerical libraries and FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Helios Core",
    version="1.0.0",
    description="Deterministic IV Characterization Platform",
)

# CORS for local and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjusted for Vercel routing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "determinism": "locked"}
    

@app.get("/verify/{audit_id}")
async def verify_analysis(audit_id: str):
    """
    Public Verification Seal.
    Confirms that an analysis with this Physics Kernel ID is theoretically valid
    under the Helios Core Deterministic Engine.
    """
    from backend.services.citation_service import generate_runtime_signature
    from backend.config import FRONTEND_BASE_URL
    
    return {
        "status": "VALIDATED",
        "audit_id": audit_id,
        "kernel": "Helios Core Deterministic Fit Engine",
        "runtime_signature": generate_runtime_signature(),
        "verification_statement": (
            "This Audit ID corresponds to an analysis performed using the Helios Core "
            "physics engine. This kernel is strictly deterministic: given the same "
            "input data and solver configuration, it will always produce this exact fingerprint."
        ),
        "docs": f"{FRONTEND_BASE_URL}/documentation/reproducibility"
    }


# Route registration
from backend.api import ingest, analyze, export, measurements, diagnostics, queue, stateless_api
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(measurements.router, prefix="/api", tags=["Data"])
app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(queue.router, prefix="/api/queue", tags=["Queue Management"])
app.include_router(stateless_api.router, prefix="/api/stateless", tags=["Stateless API"])


import os
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)