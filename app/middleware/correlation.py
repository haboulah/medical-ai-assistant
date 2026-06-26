# FastAPI middleware for Correlation ID, timing, and logging.
"""Middleware components for request tracing and monitoring."""

from __future__ import annotations

import time
import uuid

import loguru
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a correlation ID to every request.

    - Generates a UUID for each request if not provided
    - Adds X-Correlation-ID to response headers
    - Measures request execution time
    - Logs all requests
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and add correlation ID."""
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Store in request state BEFORE call_next so route handlers can access it
        request.state.correlation_id = correlation_id

        # Start timer
        start_time = time.perf_counter()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            loguru.logger.error(f"Unhandled exception: {exc}")
            status_code = 500
            response = Response(
                content='{"error": "Internal server error"}',
                status_code=500,
                media_type="application/json",
            )

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Store duration in state
        request.state.duration_ms = duration_ms

        # Log request
        loguru.logger.info(
            f"[{correlation_id}] {request.method} {request.url.path} "
            f"-> {status_code} ({duration_ms:.1f}ms)"
        )

        return response
