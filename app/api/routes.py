# FastAPI route definitions.
"""API endpoints for the Medical AI Assistant."""

from __future__ import annotations

import platform
from datetime import datetime

import fastapi
import langgraph
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.database.connection import get_db
from app.database.models import HistoryRecord, LogRecord, MetricRecord, RequestRecord
from app.monitoring.service import MonitoringService
from app.schemas.responses import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    HistoryItem,
    MetricsResponse,
    RequestItem,
    VersionResponse,
)
from app.services.medical_service import medical_service

router = APIRouter()


@router.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI Medical Pre-Diagnosis Assistant",
        "docs": "/docs",
        "redoc": "/redoc",
        "dashboard": "/dashboard",
        "chat_ui": "/chat-ui",
    }
    
    
@router.get("/chat-ui", tags=["Root"], response_class=HTMLResponse)
async def chat_ui() -> HTMLResponse:
    """Serve the chat interface HTML page."""
    chat_html = Path(__file__).resolve().parent.parent / "templates" / "chat.html"
    return HTMLResponse(content=chat_html.read_text(encoding="utf-8"))


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.database.connection import engine

    db_status = "ok"
    llm_status = "configured" if settings.is_groq_configured else "not_configured"

    try:
        async with engine.connect() as conn:
            await conn.execute(func.now())
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": db_status,
        "llm": llm_status,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics", tags=["Metrics"])
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """Get application metrics."""
    try:
        # Total requests
        result = await db.execute(func.count(RequestRecord.id))
        total_requests = result.scalar() or 0

        # Success count
        result = await db.execute(
            select(func.count(RequestRecord.id)).where(RequestRecord.status == "success")
        )
        success_count = result.scalar() or 0

        # Duration stats
        result = await db.execute(
            select(
                func.avg(RequestRecord.duration_ms),
                func.max(RequestRecord.duration_ms),
                func.min(RequestRecord.duration_ms),
            )
        )
        row = result.one()
        avg_duration = round(row[0] or 0, 2)
        max_duration = round(row[1] or 0, 2)
        min_duration = round(row[2] or 0, 2)

        # Risk distribution
        result = await db.execute(
            select(
                RequestRecord.risk_level,
                func.count(RequestRecord.id).label("count"),
            ).where(RequestRecord.risk_level.isnot(None)).group_by(RequestRecord.risk_level)
        )
        risk_dist = {row.risk_level: row.count for row in result.fetchall()}

        # Agent calls
        result = await db.execute(
            select(
                MetricRecord.agent_name,
                func.count(MetricRecord.id).label("count"),
            ).group_by(MetricRecord.agent_name)
        )
        agent_calls = {row.agent_name: row.count for row in result.fetchall()}

        # System metrics
        memory_mb = MonitoringService.get_memory_usage_mb()
        cpu_percent = MonitoringService.get_cpu_percent()

        success_rate = round((success_count / total_requests * 100) if total_requests > 0 else 100, 2)

        return MetricsResponse(
            total_requests=total_requests,
            success_rate=success_rate,
            avg_duration_ms=avg_duration,
            max_duration_ms=max_duration,
            min_duration_ms=min_duration,
            risk_distribution=risk_dist,
            agent_calls=agent_calls,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", tags=["Logs"])
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get recent application logs."""
    try:
        result = await db.execute(
            select(LogRecord).order_by(LogRecord.created_at.desc()).limit(limit)
        )
        logs = result.scalars().all()
        return {"logs": [{"id": l.id, "level": l.level, "message": l.message, "created_at": l.created_at.isoformat()} for l in logs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", tags=["History"])
async def get_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get recent conversation history."""
    try:
        result = await db.execute(
            select(HistoryRecord).order_by(HistoryRecord.created_at.desc()).limit(limit)
        )
        records = result.scalars().all()
        return {"history": [
            HistoryItem(
                id=r.id,
                correlation_id=r.correlation_id,
                role=r.role,
                content=r.content,
                agent_name=r.agent_name,
                created_at=r.created_at,
            ) for r in records
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version", tags=["Version"])
async def get_version():
    """Get application version information."""
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        python_version=platform.python_version(),
        langgraph_version=getattr(langgraph, "__version__", "unknown"),
        fastapi_version=fastapi.__version__,
    )


@router.get("/dashboard", tags=["Dashboard"], include_in_schema=False)
async def get_dashboard():
    """Serve the dashboard HTML page."""
    from app.dashboard.html import DASHBOARD_HTML
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/dashboard/data", tags=["Dashboard"])
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """Get dashboard data as JSON (for Chart.js)."""
    try:
        # Total requests
        result = await db.execute(func.count(RequestRecord.id))
        total_requests = result.scalar() or 0

        # Success count
        result = await db.execute(
            select(func.count(RequestRecord.id)).where(RequestRecord.status == "success")
        )
        success_count = result.scalar() or 0
        error_count = total_requests - success_count

        # Duration stats
        result = await db.execute(
            select(
                func.avg(RequestRecord.duration_ms),
                func.max(RequestRecord.duration_ms),
                func.min(RequestRecord.duration_ms),
            )
        )
        row = result.one()
        avg_duration = round(row[0] or 0, 2)
        max_duration = round(row[1] or 0, 2)
        min_duration = round(row[2] or 0, 2)

        # Risk distribution
        result = await db.execute(
            select(
                RequestRecord.risk_level,
                func.count(RequestRecord.id).label("count"),
            ).where(RequestRecord.risk_level.isnot(None)).group_by(RequestRecord.risk_level)
        )
        risk_dist = {row.risk_level: row.count for row in result.fetchall()}

        # Agent calls
        result = await db.execute(
            select(
                MetricRecord.agent_name,
                func.count(MetricRecord.id).label("count"),
            ).group_by(MetricRecord.agent_name)
        )
        agent_calls = {row.agent_name: row.count for row in result.fetchall()}

        # System metrics
        memory_mb = MonitoringService.get_memory_usage_mb()
        cpu_percent = MonitoringService.get_cpu_percent()

        # Recent requests
        result = await db.execute(
            select(RequestRecord)
            .order_by(RequestRecord.created_at.desc())
            .limit(10)
        )
        recent = result.scalars().all()

        success_rate = round((success_count / total_requests * 100) if total_requests > 0 else 100, 2)

        return {
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "max_duration_ms": max_duration,
            "min_duration_ms": min_duration,
            "risk_distribution": risk_dist,
            "agent_calls": agent_calls,
            "memory_usage_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "recent_requests": [
                {
                    "correlation_id": r.correlation_id,
                    "user_input": (r.user_input[:97] + "...") if r.user_input and len(r.user_input) > 100 else (r.user_input or ""),
                    "status": r.status or "",
                    "risk_level": r.risk_level or "LOW",
                    "duration_ms": r.duration_ms or 0,
                    "token_count": r.token_count or 0,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
                for r in recent
            ],
            "llm_configured": settings.is_groq_configured,
            "version": settings.APP_VERSION,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", tags=["Chat"])
async def chat(request: ChatRequest, http_request: Request):
    """Process a chat message through the multi-agent workflow.

    Args:
        request: Chat request containing the user's message.
        http_request: HTTP request object (for correlation ID).

    Returns:
        Chat response with symptoms, risk assessment, and advice.
    """
    correlation_id = getattr(http_request.state, "correlation_id", "")

    result = await medical_service.process_chat(
        user_input=request.message,
        correlation_id=correlation_id,
    )

    return result
