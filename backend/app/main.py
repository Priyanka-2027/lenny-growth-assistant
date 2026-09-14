"""
Lenny Growth Assistant — FastAPI application entry point.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.db.session import init_db

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logging()
    logger.info(
        "starting_up",
        env=settings.app_env,
        provider=settings.llm_provider,
        model=settings.active_model_name,
    )
    await init_db()
    logger.info("database_ready")
    yield
    logger.info("shutting_down")


app = FastAPI(
    title="Lenny Growth Assistant",
    description="AI-powered product & growth assistant grounded in Lenny's Podcast transcripts.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    logger.debug(
        "request_handled",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=elapsed,
    )
    return response


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error("app_error", detail=exc.detail, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", path=request.url.path, exc=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please try again."},
    )


# ── Routers ──────────────────────────────────────────────────────────────────
from app.api.routes import health, sessions, chat, artifacts, ingest  # noqa: E402

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["artifacts"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
