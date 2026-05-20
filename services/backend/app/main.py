from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os
import logfire


# Handle empty token from docker-compose
if os.getenv("LOGFIRE_TOKEN") == "":
    del os.environ["LOGFIRE_TOKEN"]

# Configure Logfire
from app.api.routes import (
    job_description,
    auth,
    users,
    application,
    cover_letter,
    cv_refresh,
    user_cv,
    debug,
)
from app.core.config import settings
from database_pkg import init_db
from app.core.pubsub import pubsub_manager
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (creates tables if they don't exist)
    init_db()
    # Start the PubSub listener in the background
    await pubsub_manager.start()
    yield
    # Stop the PubSub listener on shutdown
    await pubsub_manager.stop()


# Create FastAPI app
app = FastAPI(
    title="Job Wizard API",
    description="AI-powered cover letter generator from job descriptions",
    version="0.1.0",
    lifespan=lifespan,
)

# Instrument FastAPI with Logfire
logfire.instrument_fastapi(app, capture_headers=True)

# Configure CORS
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Create uploads directory if it doesn't exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create logs directory for prompt auditing
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for uploads - DISABLED for security (Unauthenticated File Access)
# app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include API routes
app.include_router(job_description.router, prefix="/api")
app.include_router(application.router, prefix="/api")
app.include_router(cover_letter.router, prefix="/api")
app.include_router(cv_refresh.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(user_cv.router, prefix="/api/users/me/cvs", tags=["user_cv"])


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
