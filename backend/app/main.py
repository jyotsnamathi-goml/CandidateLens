from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine, init_db_and_migrate
from app.logging_setup import setup_logging
from app.routers import admin, assessment, auth, candidates, results, roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging and database tables on startup
    setup_logging()
    init_db_and_migrate()
    yield


app = FastAPI(
    title="CandidateLens API",
    description="Explainable Candidate Readiness Signal platform for pre-Round 1 hiring.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware - allows localhost and any LAN/network origin
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api/v1
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(roles.router, prefix=API_PREFIX)
app.include_router(candidates.router, prefix=API_PREFIX)
app.include_router(assessment.router, prefix=API_PREFIX)
app.include_router(results.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "mock_mode": settings.LLM_MOCK,
        "app": "CandidateLens",
        "version": "1.0.0",
    }
