"""
FastAPI application factory.

Configures CORS, middleware, routers, and application lifespan events.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.config.settings import get_settings
from app.shared.logging.logger import get_logger, setup_logging
from app.infrastructure.database.connection import db_manager
from app.infrastructure.cache.redis_client import cache
from app.presentation.api.routers import analysis_router, dashboard_router
from app.domain.exceptions.domain_exceptions import DomainException

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        start_time = time.monotonic()
        
        try:
            response = await call_next(request)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms
            )
            return response
            
        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=duration_ms
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle hooks."""
    # Setup
    setup_logging()
    logger.info("Application starting up")
    
    await db_manager.initialize()
    # Create tables when in debug mode or explicitly enabled via DB_INIT
    if get_settings().app_debug or get_settings().db_init:
        await db_manager.create_tables()
        
    await cache.initialize()
    
    yield
    
    # Teardown
    logger.info("Application shutting down")
    await cache.close()
    await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered Sales Intelligence Platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    
    # Exception Handlers
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.message,
                "details": exc.details
            }
        )
        
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred"}
        )
    
    # Routers
    app.include_router(analysis_router.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(dashboard_router.router, tags=["Dashboard"])
    
    # Static Files for Dashboard UI
    try:
        from pathlib import Path
        static_dir = Path(__file__).resolve().parent.parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
        
    @app.get("/api/v1/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}
        
    return app
