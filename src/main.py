"""AutoTest-Agent Application Entry Point.

Main FastAPI application with all routes mounted.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.api.routes.agent import router as agent_router
from src.api.routes.analysis import router as analysis_router
from src.api.routes.documents import router as documents_router
from src.api.routes.languages import router as languages_router
from src.api.routes.batch import router as batch_router
from src.api.routes.llm import router as llm_router
from src.api.routes.scoring import router as scoring_router
from src.api.routes.tests import router as tests_router
from src.common.config import get_settings
from src.common.logger import setup_logger

settings = get_settings()
logger = setup_logger(level=settings.log_level, log_file=settings.log_file)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("AutoTest-Agent starting up...")
    logger.info(f"Environment: {'development' if settings.is_development else 'production'}")
    logger.info(f"API listening on {settings.api_host}:{settings.api_port}")
    yield
    logger.info("AutoTest-Agent shutting down...")


app = FastAPI(
    title="AutoTest-Agent",
    description="AI-powered Auto-Test Agent supporting C/C++, Python, and Java",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Mount API routes
app.include_router(api_router)
app.include_router(agent_router)
app.include_router(llm_router)
app.include_router(documents_router)
app.include_router(analysis_router)
app.include_router(languages_router)
app.include_router(scoring_router)
app.include_router(tests_router)
app.include_router(batch_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root health check endpoint."""
    return {
        "name": "AutoTest-Agent",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": "development" if settings.is_development else "production",
    }