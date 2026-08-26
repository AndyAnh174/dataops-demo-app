import os

from fastapi import APIRouter

from app.models import HealthResponse, MessageResponse

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="dataops-demo-api",
        revision=os.getenv("APP_REVISION", "development"),
    )


@router.get("/message")
def message() -> MessageResponse:
    return MessageResponse(
        message="Next.js + FastAPI deployed by a self-hosted runner",
    )
