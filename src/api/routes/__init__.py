"""API route handlers."""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"ping": "pong"}