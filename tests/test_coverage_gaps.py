"""Tests for lifespan, monitoring edge cases."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.monitoring.service import MonitoringService


class TestLifespanCoverage:
    """Coverage: main.py lifespan lines 23-48 (shutdown, errors, sys_info)."""

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_exception(self):
        """close_db failure during shutdown should not crash the app."""
        with patch("app.main.close_db", side_effect=Exception("Shutdown failed")):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/version")
                assert resp.status_code == 200
            # after context exit, shutdown runs → close_db raises → handled

    @pytest.mark.asyncio
    async def test_lifespan_groq_not_configured(self):
        """When GROQ is not configured, lifespan logs a warning."""
        with patch("app.main.settings.GROQ_API_KEY", ""):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_lifespan_groq_configured(self):
        """When GROQ is configured, lifespan logs the model name."""
        with patch("app.main.settings.GROQ_API_KEY", "mock-key"):
            with patch("app.main.settings.GROQ_MODEL_NAME", "test-model"):
                app = create_app()
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    resp = await client.get("/health")
                    assert resp.status_code == 200


class TestMonitoringCoverage:
    """Coverage: monitoring/service.py lines 63-66, 71-75."""

    def test_get_cpu_percent_returns_float(self):
        result = MonitoringService.get_cpu_percent()
        assert isinstance(result, (int, float))

    def test_get_memory_usage_mb_returns_float(self):
        result = MonitoringService.get_memory_usage_mb()
        assert isinstance(result, (int, float))
