"""
FastAPI Backend — AI Career Intelligence & Skill Gap Analyzer
=============================================================

Start the API server with:
    uvicorn backend:app --reload --port 8000

Swagger UI:     http://localhost:8000/docs
ReDoc:          http://localhost:8000/redoc
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Career Intelligence API",
    description="Backend API for the AI Career Intelligence & Skill Gap Analyzer.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow Streamlit dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# ── Health check ───────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service":  "AI Career Intelligence API",
        "version":  "1.0.0",
        "status":   "ok",
        "docs":     "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# ── Standalone runner ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
