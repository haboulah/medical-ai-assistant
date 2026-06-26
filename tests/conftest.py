"""Shared fixtures and test configuration for the Medical AI Assistant test suite.

Critical: Test environment variables are set at module level BEFORE any app imports
to ensure the test database and disabled LLM configuration are picked up.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Set test environment BEFORE any application modules are imported.
# This ensures pydantic-settings / app.core.Settings picks them up.
# ---------------------------------------------------------------------------
_db_path = tempfile.mktemp(suffix=".test.db")
_test_db_url = f"sqlite+aiosqlite:///{_db_path}"
os.environ["DATABASE_URL"] = _test_db_url
os.environ["GROQ_API_KEY"] = ""  # empty → agents use fallback extraction
os.environ["LOG_LEVEL"] = "CRITICAL"


# ---------------------------------------------------------------------------
# Ensure tables exist at module load time so any test using
# async_session_factory directly (e.g. service DB-verification tests)
# doesn't hit "no such table" errors.
# ---------------------------------------------------------------------------
import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Application imports – these trigger module-level singleton creation
from app.core import settings
from app.database.connection import async_session_factory, close_db, init_db
from app.main import app as fastapi_app
from app.monitoring.service import MonitoringService

asyncio.run(init_db())

# ---------------------------------------------------------------------------
# Sanity checks – ensure we are NOT pointing at production DB / real LLM
# ---------------------------------------------------------------------------
assert not settings.is_groq_configured, "GROQ must NOT be configured during tests"
db_url = settings.DATABASE_URL
assert "test" in db_url or ":memory:" in db_url, f"Tests must use test DB, got {db_url}"

_data_dir = Path(_db_path).parent
_data_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Database lifecycle — session-scoped so tables exist for all tests, including
# API endpoint tests that hit the database.
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def db_session_init() -> None:
    """Create all tables once per test session; clean up on finish."""
    await init_db()
    yield
    await close_db()
    if _db_path and Path(_db_path).exists():
        Path(_db_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Auto-use fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_monitoring_initialized() -> None:
    """Reset the MonitoringService singleton flag before every test."""
    MonitoringService._initialized = False
    yield


@pytest.fixture(autouse=True)
def _verify_no_groq() -> None:
    """Double-check that no test accidentally enables real LLM calls."""
    assert not settings.is_groq_configured
    yield


@pytest.fixture(autouse=True)
def _mock_system_metrics() -> None:
    """Prevent tests from calling real psutil functions."""
    with patch.object(MonitoringService, "get_memory_usage_mb", return_value=128.5):
        with patch.object(MonitoringService, "get_cpu_percent", return_value=42.0):
            yield


# ---------------------------------------------------------------------------
# Database session fixture — provides a clean session for each test.
# Clears all data after the test yields to ensure isolation.
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db(db_session_init: None) -> AsyncSession:
    """Provide a clean database session for each test function."""
    from app.database.models import HistoryRecord, LogRecord, MetricRecord, RequestRecord

    async with async_session_factory() as session:
        yield session
        # Clean up all data after the test
        try:
            for model in [RequestRecord, LogRecord, MetricRecord, HistoryRecord]:
                await session.execute(model.__table__.delete())
            await session.commit()
        except Exception:
            await session.rollback()
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# HTTP client fixture — depends on db_session_init so tables are available.
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_client(db_session_init: None) -> AsyncClient:
    """Provide an ``httpx.AsyncClient`` wired to the FastAPI application."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Sample workflow state fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_state() -> dict[str, Any]:
    """Return a representative workflow state dict as if all agents had run."""
    return {
        "user_input": "J'ai de la fièvre et de la toux",
        "correlation_id": "test-correlation-id",
        "uuid": "test-uuid",
        "timestamp": "2025-01-01T00:00:00",
        "start_time": 1000.0,
        "end_time": 1002.5,
        "supervisor_decision": "proceed",
        "next_agent": "symptom_analysis",
        "symptoms": ["Fièvre", "Toux"],
        "symptoms_raw": "J'ai de la fièvre et de la toux",
        "risk_level": "MEDIUM",
        "risk_justification": "Le symptôme 'fièvre' peut nécessiter une consultation médicale.",
        "medical_advice": (
            "Surveillez l'évolution de vos symptômes. " "Reposez-vous et hydratez-vous."
        ),
        "disclaimer": "⚠️ Avertissement",
        # Execution metadata that MonitoringAgent reads
        "supervisor_execution": {
            "execution_time_ms": 10.0,
            "agent_name": "Supervisor",
        },
        "symptom_analysis_execution": {
            "execution_time_ms": 500.0,
            "agent_name": "SymptomAnalysis",
        },
        "risk_assessment_execution": {
            "execution_time_ms": 300.0,
            "agent_name": "RiskAssessment",
        },
        "medical_advice_execution": {
            "execution_time_ms": 400.0,
            "agent_name": "MedicalAdvice",
        },
        "monitoring_output": {
            "correlation_id": "test-correlation-id",
            "uuid": "test-uuid",
            "timestamp": "2025-01-01T00:00:00",
            "duration_ms": 1500.0,
            "agents_executed": [
                "Supervisor",
                "SymptomAnalysis",
                "RiskAssessment",
                "MedicalAdvice",
                "Monitoring",
            ],
            "execution_times": {
                "Supervisor": 10.0,
                "SymptomAnalysis": 500.0,
                "RiskAssessment": 300.0,
                "MedicalAdvice": 400.0,
            },
            "status": "success",
            "total_tokens": 50,
            "error_details": None,
        },
    }


# ---------------------------------------------------------------------------
# Mock for compiled_graph.ainvoke
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_graph_invoke(sample_state: dict[str, Any]) -> MagicMock:
    """Mock ``compiled_graph.ainvoke`` so it returns *sample_state*.

    Use this fixture in any test that exercises :class:`MedicalAIService` or
    the ``/chat`` endpoint without running the real LangGraph workflow.
    """
    with patch("app.graph.workflow.compiled_graph.ainvoke") as mock:
        mock.return_value = sample_state
        yield mock


@pytest.fixture
def mock_graph_invoke_error() -> MagicMock:
    """Mock ``compiled_graph.ainvoke`` so it raises an exception.

    Use this to test the error-handling path of :class:`MedicalAIService`.
    """
    with patch("app.graph.workflow.compiled_graph.ainvoke") as mock:
        mock.side_effect = RuntimeError("Simulated workflow failure")
        yield mock
