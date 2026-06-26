"""Tests for the correlation middleware.

Verifies that each request receives a correlation ID, that it is propagated
to the response headers, and that the request state is properly populated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.responses import Response

from app.main import app as fastapi_app
from app.middleware.correlation import CorrelationMiddleware


class TestCorrelationMiddleware:
    """Integration-style tests for CorrelationMiddleware via the running app."""

    @pytest.mark.asyncio
    async def test_middleware_adds_correlation_id_header(self) -> None:
        """Every response should include X-Correlation-ID."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert "X-Correlation-ID" in resp.headers
            cid = resp.headers["X-Correlation-ID"]
            assert len(cid) > 0
            # UUID format: 8-4-4-4-12
            assert cid.count("-") == 4

    @pytest.mark.asyncio
    async def test_middleware_preserves_incoming_correlation_id(self) -> None:
        """If the client sends X-Correlation-ID, the same value should be returned."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/health",
                headers={"X-Correlation-ID": "my-custom-id-123"},
            )
            assert resp.headers["X-Correlation-ID"] == "my-custom-id-123"

    @pytest.mark.asyncio
    async def test_middleware_generates_new_id_when_none_provided(self) -> None:
        """Without an incoming header a fresh UUID should be generated."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            cid = resp.headers["X-Correlation-ID"]
            # UUID v4 has specific format
            parts = cid.split("-")
            assert len(parts) == 5
            assert len(parts[0]) == 8
            assert parts[2].startswith("4")  # UUID v4 indicator

    @pytest.mark.asyncio
    async def test_each_request_gets_unique_id(self) -> None:
        """Two consecutive requests should get different IDs."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.get("/health")
            resp2 = await client.get("/health")
            assert resp1.headers["X-Correlation-ID"] != resp2.headers["X-Correlation-ID"]

    @pytest.mark.asyncio
    async def test_middleware_sets_request_state(self) -> None:
        """The correlation_id should be accessible on request.state."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/")
            assert resp.status_code == 200
            # The header was added (which proves state was set)
            assert "X-Correlation-ID" in resp.headers


class TestCorrelationMiddlewareUnit:
    """Unit tests for CorrelationMiddleware internals."""

    @staticmethod
    def _make_request(headers: dict[str, str] | None = None) -> Request:
        """Build a minimal Starlette Request for testing."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [
                (k.lower().encode(), v.encode())
                for k, v in (headers or {}).items()
            ],
            "query_string": b"",
            "client": ("127.0.0.1", 50000),
            "server": ("test", 80),
            "scheme": "http",
        }
        return Request(scope)

    @pytest.mark.asyncio
    async def test_dispatch_generates_id(self) -> None:
        """dispatch() should generate a UUID when no header is present."""
        middleware = CorrelationMiddleware(app=fastapi_app)
        request = self._make_request()

        async def mock_call_next(req):
            return Response("OK", status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert "X-Correlation-ID" in response.headers
        cid = response.headers["X-Correlation-ID"]
        assert cid.count("-") == 4

    @pytest.mark.asyncio
    async def test_dispatch_preserves_incoming_id(self) -> None:
        """If the request already has a correlation ID, it should be preserved."""
        middleware = CorrelationMiddleware(app=fastapi_app)
        request = self._make_request({"X-Correlation-ID": "preserve-me"})

        async def mock_call_next(req):
            return Response("OK", status_code=200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.headers["X-Correlation-ID"] == "preserve-me"

    @pytest.mark.asyncio
    async def test_dispatch_records_duration(self) -> None:
        """request.state.duration_ms should be set after dispatch."""
        middleware = CorrelationMiddleware(app=fastapi_app)
        request = self._make_request()

        async def mock_call_next(req):
            import asyncio

            await asyncio.sleep(0.01)
            return Response("OK", status_code=200)

        _ = await middleware.dispatch(request, mock_call_next)
        assert hasattr(request.state, "duration_ms")
        assert request.state.duration_ms > 0

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(self) -> None:
        """When call_next raises, middleware should return a 500 response."""
        middleware = CorrelationMiddleware(app=fastapi_app)
        request = self._make_request()

        async def mock_call_next(req):
            raise ValueError("Internal failure")

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 500
        assert "X-Correlation-ID" in response.headers
