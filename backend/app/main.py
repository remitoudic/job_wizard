from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
import logfire

from app.api import routes

# Handle empty token from docker-compose
if os.getenv("LOGFIRE_TOKEN") == "":
    del os.environ["LOGFIRE_TOKEN"]

# Configure Logfire
logfire.configure(send_to_logfire='if-token-present')

# Create FastAPI app
app = FastAPI(
    title="Job Wizard API",
    description="AI-powered cover letter generator from job descriptions",
    version="0.1.0",
)

# Instrument FastAPI with Logfire
logfire.instrument_fastapi(app)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include API routes
app.include_router(routes.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Wizard API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
