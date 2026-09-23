import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api.google_drive_routes import (
    router as google_drive_router,
)
from backend.api.google_auth_routes import (
    router as google_auth_router,
)
from backend.api.routes import router
from backend.api.evaluation_routes import router as evaluation_router
from backend.security.public_demo import (
    PublicDemoConfig,
    PublicDemoProtectionMiddleware,
)


load_dotenv()


public_demo_config = PublicDemoConfig.from_env()


app = FastAPI(
    title="Engineering Knowledge Copilot API",
    description=(
        "Backend API for a repository-connected, "
        "permission-aware engineering knowledge copilot."
    ),
    version="0.4.0",
    docs_url=(
        None
        if public_demo_config.enabled
        else "/docs"
    ),
    redoc_url=(
        None
        if public_demo_config.enabled
        else "/redoc"
    ),
    openapi_url=(
        None
        if public_demo_config.enabled
        else "/openapi.json"
    ),
)


# Browser frontend origins.
# Production origins can be supplied through FRONTEND_ORIGINS.
frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

if (
    public_demo_config.enabled
    and "*" in frontend_origins
):
    raise RuntimeError(
        "Wildcard CORS origins are not allowed "
        "when PUBLIC_DEMO_MODE=true."
    )


app.add_middleware(
    PublicDemoProtectionMiddleware,
    config=public_demo_config,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

session_secret = os.getenv("APP_SESSION_SECRET")

if not session_secret:
    raise RuntimeError(
        "APP_SESSION_SECRET is missing from .env"
    )


app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    same_site="lax",
    https_only=(
        public_demo_config.session_cookie_secure
    ),
)


app.include_router(router)
app.include_router(google_auth_router)
app.include_router(google_drive_router)
app.include_router(evaluation_router)


@app.get("/")
def root():
    return {
        "product": "Engineering Knowledge Copilot",
        "status": "running",
        "version": "0.4.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "engineering-knowledge-copilot-api",
    }
