"""AutoTest-Agent Application Entry Point.

Main FastAPI application with all routes mounted,
unified exception handling, and request validation middleware.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from src.common.database import close_db, init_db
from src.common.exceptions import (
    AutoTestError,
    LLMProviderError,
    NotFoundError,
    SandboxError,
    ValidationError,
)
from src.common.logger import setup_logger

settings = get_settings()
logger = setup_logger(level=settings.log_level, log_file=settings.log_file)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("AutoTest-Agent starting up...")
    logger.info(f"Environment: {'development' if settings.is_development else 'production'}")
    logger.info(f"API listening on {settings.api_host}:{settings.api_port}")

    # Initialize database tables in development mode
    if settings.is_development:
        logger.info("Initializing database tables...")
        await init_db()

    yield

    # Cleanup on shutdown
    logger.info("Closing database connections...")
    await close_db()
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

# ===== Middleware =====

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(duration)

    return response


# ===== Exception Handlers =====

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": exc.message,
            "field": getattr(exc, "field", None),
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle resource not found errors."""
    logger.warning(f"Not found: {exc.resource} ({exc.identifier})")
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": exc.message,
            "resource": exc.resource,
            "identifier": exc.identifier,
        },
    )


@app.exception_handler(SandboxError)
async def sandbox_error_handler(request: Request, exc: SandboxError):
    """Handle sandbox execution errors."""
    logger.error(f"Sandbox error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "sandbox_error",
            "message": exc.message,
            "sandbox_id": getattr(exc, "sandbox_id", None),
        },
    )


@app.exception_handler(LLMProviderError)
async def llm_provider_error_handler(request: Request, exc: LLMProviderError):
    """Handle LLM provider errors."""
    logger.error(f"LLM provider error: {exc.message}")
    return JSONResponse(
        status_code=503,
        content={
            "error": "llm_provider_error",
            "message": exc.message,
            "provider": getattr(exc, "provider", None),
        },
    )


@app.exception_handler(AutoTestError)
async def autotest_error_handler(request: Request, exc: AutoTestError):
    """Handle generic AutoTest errors."""
    logger.error(f"AutoTest error [{exc.code}]: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "autotest_error",
            "message": exc.message,
            "code": exc.code,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors from FastAPI."""
    logger.warning(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "request_validation_error",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
        },
    )


# ===== Routes =====

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


# ===== Endpoints =====

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
