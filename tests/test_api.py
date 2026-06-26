"""Tests for all API endpoints.

Uses ``httpx.AsyncClient`` wired to the FastAPI app (no real server needed).
The /chat endpoint is tested with a mocked graph invocation to avoid running
the real LangGraph workflow.
"""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.responses import ChatResponse


# ====================================================================
# Root endpoint
# ====================================================================
class TestRoot:
    async def test_get_root(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "Medical AI Assistant"
        assert "version" in data
        assert "docs" in data
        assert "dashboard" in data
        assert data["dashboard"] == "/dashboard"

    async def test_root_includes_all_keys(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        data = resp.json()
        expected_keys = {"name", "version", "description", "docs", "redoc", "dashboard"}
        assert expected_keys.issubset(data.keys())


# ====================================================================
# Health endpoint
# ====================================================================
class TestHealth:
    async def test_health_check(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "database" in data
        assert "llm" in data
        assert "timestamp" in data

    async def test_health_llm_not_configured(self, async_client: AsyncClient) -> None:
        """LLM status should reflect the test environment."""
        resp = await async_client.get("/health")
        data = resp.json()
        assert data["llm"] == "not_configured"


# ====================================================================
# Version endpoint
# ====================================================================
class TestVersion:
    async def test_version(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/version")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "Medical AI Assistant"
        assert data["version"] == "1.0.0"
        assert "python_version" in data
        assert "fastapi_version" in data
        assert "langgraph_version" in data

    async def test_version_types(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/version")
        data = resp.json()
        assert isinstance(data["python_version"], str)
        assert isinstance(data["fastapi_version"], str)


# ====================================================================
# Metrics endpoint
# ====================================================================
class TestMetrics:
    async def test_metrics_empty_db(self, async_client: AsyncClient) -> None:
        """With an empty database, metrics should return defaults/zeros."""
        resp = await async_client.get("/metrics")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_requests"] == 0
        assert data["success_rate"] == 100.0  # No requests → 100 %
        assert data["avg_duration_ms"] == 0
        assert data["max_duration_ms"] == 0
        assert data["min_duration_ms"] == 0
        assert isinstance(data["risk_distribution"], dict)
        assert isinstance(data["agent_calls"], dict)

    async def test_metrics_has_system_values(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/metrics")
        data = resp.json()
        assert data["memory_usage_mb"] == 128.5  # from conftest mock
        assert data["cpu_percent"] == 42.0  # from conftest mock


# ====================================================================
# Logs endpoint
# ====================================================================
class TestLogs:
    async def test_logs_empty(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/logs")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data["logs"], list)

    async def test_logs_with_limit(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/logs?limit=5")
        assert resp.status_code == status.HTTP_200_OK

    async def test_logs_returns_correct_structure(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/logs")
        data = resp.json()
        assert "logs" in data


# ====================================================================
# History endpoint
# ====================================================================
class TestHistory:
    async def test_history_empty(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/history")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data["history"], list)

    async def test_history_with_limit(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/history?limit=10")
        assert resp.status_code == status.HTTP_200_OK


# ====================================================================
# Dashboard endpoints
# ====================================================================
class TestDashboard:
    async def test_dashboard_returns_html(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/dashboard")
        assert resp.status_code == status.HTTP_200_OK
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type or "html" in content_type

    async def test_dashboard_contains_key_elements(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/dashboard")
        text = resp.text
        assert "Medical AI Assistant" in text
        assert "Bootstrap" in text or "bootstrap" in text
        assert "Chart.js" in text or "chart.js" in text

    async def test_dashboard_data(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/dashboard/data")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "total_requests" in data
        assert "success_count" in data
        assert "error_count" in data
        assert "success_rate" in data
        assert "recent_requests" in data
        assert "version" in data
        assert "timestamp" in data

    async def test_dashboard_data_empty_db(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/dashboard/data")
        data = resp.json()
        assert data["total_requests"] == 0
        assert data["error_count"] == 0
        assert data["success_rate"] == 100.0


# ====================================================================
# Chat endpoint
# ====================================================================
class TestChat:
    """Chat endpoint tests — we mock the underlying service layer."""

    @patch("app.api.routes.medical_service.process_chat")
    async def test_chat_valid_message(
        self, mock_process: MagicMock, async_client: AsyncClient
    ) -> None:
        mock_process.return_value = {
            "correlation_id": "cid-123",
            "symptoms": {"symptoms": ["Fièvre", "Toux"], "raw_text": "J'ai de la fièvre et je tousse"},
            "risk": {"level": "MEDIUM", "justification": "Fever needs attention."},
            "medical_advice": {
                "advice": "Consultez un médecin.",
                "disclaimer": "⚠️ Avertissement",
            },
            "monitoring": {
                "correlation_id": "cid-123",
                "uuid": "uuid-1",
                "timestamp": "now",
                "duration_ms": 1200.0,
                "agents_executed": ["Supervisor", "SymptomAnalysis"],
                "execution_times": {"Supervisor": 5.0},
                "status": "success",
                "total_tokens": 42,
            },
            "disclaimer": "⚠️ Avertissement",
        }

        resp = await async_client.post(
            "/chat",
            json={"message": "J'ai de la fièvre et je tousse"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["correlation_id"] == "cid-123"
        assert data["symptoms"]["symptoms"] == ["Fièvre", "Toux"]
        assert data["risk"]["level"] == "MEDIUM"
        assert "advice" in data["medical_advice"]
        assert "disclaimer" in data

    @patch("app.api.routes.medical_service.process_chat")
    async def test_chat_short_message(
        self, mock_process: MagicMock, async_client: AsyncClient
    ) -> None:
        mock_process.return_value = {
            "correlation_id": "cid-456",
            "symptoms": {"symptoms": [], "raw_text": "Bonjour"},
            "risk": {"level": "LOW", "justification": "No symptoms detected."},
            "medical_advice": {
                "advice": "Surveillez votre état.",
                "disclaimer": "⚠️ Avertissement",
            },
            "monitoring": {
                "correlation_id": "cid-456",
                "uuid": "uuid-2",
                "timestamp": "now",
                "duration_ms": 500.0,
                "agents_executed": [],
                "execution_times": {},
                "status": "success",
                "total_tokens": 5,
            },
            "disclaimer": "⚠️ Avertissement",
        }
        resp = await async_client.post(
            "/chat",
            json={"message": "Bonjour"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["correlation_id"] == "cid-456"

    async def test_chat_empty_message(self, async_client: AsyncClient) -> None:
        """Empty message should be rejected by Pydantic validation."""
        resp = await async_client.post("/chat", json={"message": ""})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_chat_missing_message(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/chat", json={})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_chat_long_message(self, async_client: AsyncClient) -> None:
        """Very long messages should be rejected (max 5000 chars)."""
        long_msg = "a" * 5001
        resp = await async_client.post("/chat", json={"message": long_msg})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.api.routes.medical_service.process_chat")
    async def test_chat_response_shape_matches_schema(
        self, mock_process: MagicMock, async_client: AsyncClient
    ) -> None:
        mock_process.return_value = {
            "correlation_id": "cid-schema",
            "symptoms": {"symptoms": ["Headache"], "raw_text": "Headache"},
            "risk": {"level": "LOW", "justification": "Minor."},
            "medical_advice": {
                "advice": "Rest.",
                "disclaimer": "⚠️ Avertissement",
            },
            "monitoring": {
                "correlation_id": "cid-schema",
                "uuid": "uuid-3",
                "timestamp": "now",
                "duration_ms": 300.0,
                "agents_executed": ["SymptomAnalysis"],
                "execution_times": {"SymptomAnalysis": 200.0},
                "status": "success",
                "total_tokens": 10,
            },
            "disclaimer": "⚠️ Avertissement",
        }
        resp = await async_client.post(
            "/chat",
            json={"message": "Headache"},
        )
        data = resp.json()
        # Verify all expected top-level keys exist
        expected = {"correlation_id", "symptoms", "risk", "medical_advice", "monitoring", "disclaimer"}
        assert expected.issubset(data.keys())
        # Verify nested structure
        assert "symptoms" in data["symptoms"]
        assert "raw_text" in data["symptoms"]
        assert "level" in data["risk"]
        assert "justification" in data["risk"]
        assert "advice" in data["medical_advice"]
        assert "disclaimer" in data["medical_advice"]
        assert "agents_executed" in data["monitoring"]
        assert "status" in data["monitoring"]


# ====================================================================
# OpenAPI / docs
# ====================================================================
class TestDocs:
    async def test_swagger_ui(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/docs")
        assert resp.status_code == status.HTTP_200_OK
        assert "swagger" in resp.text.lower()

    async def test_redoc(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/redoc")
        assert resp.status_code == status.HTTP_200_OK

    async def test_openapi_json(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/openapi.json")
        assert resp.status_code == status.HTTP_200_OK
        spec = resp.json()
        assert spec["info"]["title"] == "Medical AI Assistant"
        assert spec["info"]["version"] == "1.0.0"


# ====================================================================
# 404 handling
# ====================================================================
class TestNotFound:
    async def test_unknown_route(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/nonexistent")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
