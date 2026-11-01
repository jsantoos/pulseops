from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulseops_api.api.routes.audit import router as audit_router
from pulseops_api.api.routes.auth import router as auth_router
from pulseops_api.api.routes.datasets import router as datasets_router
from pulseops_api.api.routes.executive import router as executive_router
from pulseops_api.api.routes.ml import router as ml_router
from pulseops_api.api.routes.opportunities import router as opportunities_router
from pulseops_api.api.routes.organizations import router as organizations_router
from pulseops_api.core.config import get_settings
from pulseops_api.schemas.api import HealthResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "X-PulseOps-Organization", "X-PulseOps-Request"],
)
app.include_router(auth_router, prefix="/v1")
app.include_router(audit_router, prefix="/v1")
app.include_router(organizations_router, prefix="/v1")
app.include_router(datasets_router, prefix="/v1")
app.include_router(executive_router, prefix="/v1")
app.include_router(ml_router, prefix="/v1")
app.include_router(opportunities_router, prefix="/v1")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse()
