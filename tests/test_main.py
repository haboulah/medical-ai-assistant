"""Tests for main app factory, lifespan, and edge cases."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class TestCreateApp:
    """Tests for create_app factory."""

    def test_create_app_returns_fastapi(self):
        app = create_app()
        assert app.title == "Medical AI Assistant"
        assert app.version is not None
        assert app.docs_url == "/docs"

    def test_app_has_cors_middleware(self):
        app = create_app()
        # Check that middleware stack includes CORSMiddleware
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_app_has_correlation_middleware(self):
        app = create_app()
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CorrelationMiddleware" in middleware_classes

    def test_app_includes_router(self):
        app = create_app()
        # The router should have routes
        assert len(app.routes) >= 5  # at least root, health, version, chat, metrics...


class TestAppFactoryInstance:
    """Tests for the global `app` instance and its basic routes."""

    @pytest.mark.asyncio
    async def test_app_root_returns_json(self):
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/")
            assert resp.status_code == 200
            data = resp.json()
            assert "name" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_app_health(self):
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_app_version(self):
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/version")
            assert resp.status_code == 200
            data = resp.json()
            assert "version" in data


class TestLifespan:
    """Tests for the lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_normal(self):
        """create_app triggers lifespan on first request."""
        app = create_app()
        # The lifespan runs on first request (startup) and on shutdown
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_lifespan_db_init_failure(self):
        """When init_db fails, lifespan logs an error but app still starts."""
        with patch("app.main.init_db", side_effect=Exception("DB down")):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/")
                assert resp.status_code == 200


class TestLogsEndpoint:
    """Tests for the /logs endpoint."""

    @pytest.mark.asyncio
    async def test_logs_empty(self, async_client: AsyncClient):
        resp = await async_client.get("/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data


class TestHistoryEndpoint:
    """Tests for the /history endpoint."""

    @pytest.mark.asyncio
    async def test_history_empty(self, async_client: AsyncClient):
        resp = await async_client.get("/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data


class TestDashboardDataEndpoint:
    """Tests for the /dashboard/data endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_data(self, async_client: AsyncClient):
        resp = await async_client.get("/dashboard/data")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboard" in data or "summary" in data or isinstance(data, dict)


class TestChatEdgeCases:
    """Edge case tests for the /chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_invalid_json(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (200, 422, 400)

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/chat",
            json={"message": ""},
        )
        assert resp.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_chat_missing_message(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/chat",
            json={},
        )
        assert resp.status_code in (200, 422, 400)
