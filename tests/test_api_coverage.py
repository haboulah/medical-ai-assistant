"""Additional API endpoint tests to fill coverage gaps.

Tests the /metrics, /logs, /history, /dashboard/data endpoints with
populated database data and edge cases.
"""

from __future__ import annotations

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import HistoryRecord, LogRecord, MetricRecord, RequestRecord


# ====================================================================
# Metrics endpoint with populated data
# ====================================================================
class TestMetricsPopulated:
    """Test /metrics with database records present."""

    @pytest.mark.asyncio
    async def test_metrics_with_records(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """Insert records and verify metrics reflect them."""
        # Populate requests with various statuses
        for i, status_val in enumerate(["success", "success", "error"]):
            db.add(
                RequestRecord(
                    correlation_id=f"metrics-pop-{i}-{status_val}",
                    user_input="test",
                    status=status_val,
                    duration_ms=100.0,
                    token_count=10,
                    risk_level="LOW",
                )
            )
        # Populate metrics
        db.add(
            MetricRecord(
                correlation_id="met-1",
                agent_name="Supervisor",
                execution_time_ms=5.0,
                status="success",
            )
        )
        db.add(
            MetricRecord(
                correlation_id="met-2",
                agent_name="SymptomAnalysis",
                execution_time_ms=50.0,
                status="success",
            )
        )
        await db.commit()

        resp = await async_client.get("/metrics")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_requests"] == 3
        assert data["success_rate"] == 66.67  # 2/3
        assert data["avg_duration_ms"] == 100.0
        assert data["max_duration_ms"] == 100.0
        assert data["min_duration_ms"] == 100.0
        assert data["risk_distribution"]["LOW"] == 3
        assert data["agent_calls"]["Supervisor"] == 1
        assert data["agent_calls"]["SymptomAnalysis"] == 1
        assert data["memory_usage_mb"] == 128.5
        assert data["cpu_percent"] == 42.0

    @pytest.mark.asyncio
    async def test_metrics_with_varied_durations(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Durations should be correctly averaged."""
        for i, dur in enumerate([50.0, 200.0, 100.0]):
            db.add(
                RequestRecord(
                    correlation_id=f"duration-{i}",
                    user_input="test",
                    status="success",
                    duration_ms=dur,
                    token_count=5,
                    risk_level="LOW",
                )
            )
        await db.commit()

        resp = await async_client.get("/metrics")
        data = resp.json()
        assert data["total_requests"] == 3
        assert data["avg_duration_ms"] == 116.67
        assert data["max_duration_ms"] == 200.0
        assert data["min_duration_ms"] == 50.0

    @pytest.mark.asyncio
    async def test_metrics_with_risk_distribution(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Risk distribution should correctly group records."""
        levels = ["LOW", "MEDIUM", "LOW", "HIGH", "MEDIUM"]
        for i, level in enumerate(levels):
            db.add(
                RequestRecord(
                    correlation_id=f"risk-{i}",
                    user_input="test",
                    status="success",
                    risk_level=level,
                )
            )
        await db.commit()

        resp = await async_client.get("/metrics")
        data = resp.json()
        assert data["risk_distribution"]["LOW"] == 2
        assert data["risk_distribution"]["MEDIUM"] == 2
        assert data["risk_distribution"]["HIGH"] == 1


# ====================================================================
# Logs endpoint with populated data
# ====================================================================
class TestLogsPopulated:
    @pytest.mark.asyncio
    async def test_logs_with_entries(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """Logs should return entries when present."""
        for i in range(3):
            db.add(
                LogRecord(
                    correlation_id=f"log-{i}",
                    level="INFO",
                    message=f"Test log {i}",
                )
            )
        await db.commit()

        resp = await async_client.get("/logs")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["logs"]) == 3
        assert data["logs"][0]["level"] == "INFO"
        assert "message" in data["logs"][0]
        assert "created_at" in data["logs"][0]

    @pytest.mark.asyncio
    async def test_logs_limit_respected(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """The limit parameter should cap the number of returned logs."""
        for i in range(10):
            db.add(
                LogRecord(
                    correlation_id=f"lim-{i}",
                    level="INFO",
                    message=f"Log {i}",
                )
            )
        await db.commit()

        resp = await async_client.get("/logs?limit=3")
        data = resp.json()
        assert len(data["logs"]) == 3

    @pytest.mark.asyncio
    async def test_logs_multiple_levels(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """Logs at different levels should all be returned."""
        for level in ["INFO", "WARNING", "ERROR", "DEBUG"]:
            db.add(
                LogRecord(
                    correlation_id=f"lvl-{level}",
                    level=level,
                    message=f"{level} message",
                )
            )
        await db.commit()

        resp = await async_client.get("/logs")
        data = resp.json()
        levels = {entry["level"] for entry in data["logs"]}
        assert levels == {"INFO", "WARNING", "ERROR", "DEBUG"}


# ====================================================================
# History endpoint with populated data
# ====================================================================
class TestHistoryPopulated:
    @pytest.mark.asyncio
    async def test_history_with_records(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """History should return conversation records."""
        for i in range(3):
            db.add(
                HistoryRecord(
                    correlation_id=f"hist-{i}",
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i}",
                    agent_name="TestAgent" if i % 2 == 1 else None,
                )
            )
        await db.commit()

        resp = await async_client.get("/history")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["history"]) == 3
        assert data["history"][0]["role"] in ("user", "assistant")
        assert "correlation_id" in data["history"][0]

    @pytest.mark.asyncio
    async def test_history_limit(self, async_client: AsyncClient, db: AsyncSession) -> None:
        for i in range(10):
            db.add(
                HistoryRecord(
                    correlation_id=f"hlim-{i}",
                    role="user",
                    content=f"Message {i}",
                )
            )
        await db.commit()

        resp = await async_client.get("/history?limit=2")
        data = resp.json()
        assert len(data["history"]) == 2

    @pytest.mark.asyncio
    async def test_history_mixed_roles(self, async_client: AsyncClient, db: AsyncSession) -> None:
        """History items should have correct roles."""
        db.add(
            HistoryRecord(
                correlation_id="mixed-1",
                role="user",
                content="Hello",
            )
        )
        db.add(
            HistoryRecord(
                correlation_id="mixed-2",
                role="assistant",
                content="Hi there!",
                agent_name="MedicalAdvice",
            )
        )
        await db.commit()

        resp = await async_client.get("/history")
        data = resp.json()
        roles = {item["role"] for item in data["history"]}
        assert roles == {"user", "assistant"}


# ====================================================================
# Dashboard data with populated data
# ====================================================================
class TestDashboardPopulated:
    @pytest.mark.asyncio
    async def test_dashboard_data_with_records(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Dashboard data should return meaningful values."""
        for i, status_val in enumerate(["success", "success", "error", "error", "success"]):
            db.add(
                RequestRecord(
                    correlation_id=f"dash-{i}-{status_val}",
                    user_input="Patient says they have symptoms",
                    status=status_val,
                    duration_ms=150.0,
                    token_count=20,
                    risk_level="MEDIUM" if status_val == "success" else None,
                )
            )
        db.add(
            MetricRecord(
                correlation_id="dash-met-1",
                agent_name="Supervisor",
                execution_time_ms=10.0,
                status="success",
            )
        )
        await db.commit()

        resp = await async_client.get("/dashboard/data")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_requests"] == 5
        assert data["success_count"] == 3
        assert data["error_count"] == 2
        assert data["success_rate"] == 60.0
        assert data["avg_duration_ms"] == 150.0
        assert data["max_duration_ms"] == 150.0
        assert data["min_duration_ms"] == 150.0
        assert "MEDIUM" in data["risk_distribution"]
        assert len(data["recent_requests"]) == 5
        assert data["recent_requests"][0]["user_input"] == "Patient says they have symptoms"
        assert data["llm_configured"] is False
        assert data["version"] is not None

    @pytest.mark.asyncio
    async def test_dashboard_data_recent_requests_truncated(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Long user_input should be truncated to 100 chars."""
        long_input = "A" * 200
        db.add(
            RequestRecord(
                correlation_id="dash-long",
                user_input=long_input,
                status="success",
                duration_ms=100.0,
                risk_level="LOW",
            )
        )
        await db.commit()

        resp = await async_client.get("/dashboard/data")
        data = resp.json()
        assert len(data["recent_requests"][0]["user_input"]) == 100


class TestDashboardHtmlPopulated:
    """Dashboard HTML rendering with seeded data."""

    @pytest.mark.asyncio
    async def test_dashboard_html_serves_static_page(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """HTML dashboard should be served as a static page without placeholders."""
        from app.database.models import RequestRecord

        for i in range(3):
            db.add(
                RequestRecord(
                    correlation_id=f"html-val-{i}",
                    user_input="Test patient with fever",
                    status="success",
                    duration_ms=250.0,
                    token_count=50,
                    risk_level="LOW",
                )
            )
        await db.commit()

        resp = await async_client.get("/dashboard")
        assert resp.status_code == 200
        text = resp.text

        # Static page has no placeholders
        assert "__TOTAL_REQUESTS__" not in text
        assert "__RECENT_ROWS__" not in text

        # Initial values are 0 (JS will update via fetch)
        assert ">0<" in text  # total_requests starts as 0
        assert ">100%<" in text  # success rate starts as 100%

        # Elements we expect in the HTML
        assert 'id="totalRequests"' in text
        assert 'id="requestsTable"' in text
        assert 'id="riskChart"' in text
        assert "refreshDashboard" in text  # JS function exists

        # JS should fetch data from /dashboard/data
        assert "fetch('/dashboard/data')" in text

    @pytest.mark.asyncio
    async def test_dashboard_html_shows_non_configured_llm(self, async_client: AsyncClient) -> None:
        """LLM badge should say 'Non configure' when GROQ_API_KEY is empty."""
        resp = await async_client.get("/dashboard")
        text = resp.text
        assert "Non configure" in text


# ====================================================================
# Health endpoint edge case
# ====================================================================
class TestHealthDatabaseStatus:
    @pytest.mark.asyncio
    async def test_health_database_ok(self, async_client: AsyncClient) -> None:
        """Database status should be 'ok' when connection works."""
        resp = await async_client.get("/health")
        data = resp.json()
        assert data["database"] == "ok"

    @pytest.mark.asyncio
    async def test_health_database_error(self, async_client: AsyncClient) -> None:
        """Database status should report an error when connection fails."""
        from unittest.mock import AsyncMock, patch

        mock_engine = AsyncMock()
        mock_engine.connect.side_effect = Exception("Connection refused")

        with patch("app.database.connection.engine", mock_engine):
            resp = await async_client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in str(data.get("database", ""))
