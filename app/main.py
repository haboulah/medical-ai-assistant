# FastAPI application factory.
"""Application setup, middleware registration, and lifespan management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core import settings
from app.database.connection import close_db, init_db
from app.middleware.correlation import CorrelationMiddleware
from app.monitoring.service import MonitoringService, logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting {} v{}", settings.APP_NAME, settings.APP_VERSION)
    MonitoringService.setup_logging()

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error("❌ Database initialization failed: {}", e)

    # Log system info
    sys_info = MonitoringService.get_system_info()
    logger.info("💻 System: {} | Python {}", sys_info["platform"], sys_info["python"])

    # Log Groq status
    if settings.is_groq_configured:
        logger.info("🤖 Groq LLM configured: {}", settings.GROQ_MODEL_NAME)
    else:
        logger.warning("⚠️  GROQ_API_KEY not configured. Using fallback extraction.")

    yield

    # Shutdown
    logger.info("🛑 Shutting down {}...", settings.APP_NAME)
    await close_db()
    logger.info("👋 Goodbye!")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.

    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Medical Pre-Diagnosis Assistant - Multi-Agent LangGraph System",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add correlation middleware
    app.add_middleware(CorrelationMiddleware)

    # Include routers
    app.include_router(router, prefix="")

    return app


# Create the application instance
app = create_app()
