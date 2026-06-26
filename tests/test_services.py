"""Tests for MedicalAIService — the main orchestration service.

The service uses ``compiled_graph.ainvoke`` which is mocked via the
``mock_graph_invoke`` fixture defined in conftest.py so we do not run
the real LangGraph workflow during these tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.database.connection import async_session_factory
from app.database.models import HistoryRecord, MetricRecord, RequestRecord
from app.services.medical_service import MedicalAIService, medical_service


class TestMedicalAIServiceInit:
    """Verify the service singleton and its dependencies."""

    def test_singleton_exists(self) -> None:
        assert medical_service is not None
        assert isinstance(medical_service, MedicalAIService)

    def test_has_monitoring_agent(self) -> None:
        assert medical_service.monitoring_agent is not None
        assert medical_service.monitoring_agent.name == "Monitoring"


class TestProcessChat:
    """Tests for the core ``process_chat`` method."""

    @pytest.mark.asyncio
    async def test_process_chat_success(
        self, mock_graph_invoke: MagicMock, sample_state: dict[str, Any]
    ) -> None:
        """A successful workflow should return a fully structured response."""
        mock_graph_invoke.return_value = sample_state

        result = await medical_service.process_chat(
            user_input="J'ai de la fièvre et je tousse",
            correlation_id="test-cid-success",
        )

        # Top-level structure
        assert result["correlation_id"] == "test-cid-success"
        assert "symptoms" in result
        assert "risk" in result
        assert "medical_advice" in result
        assert "monitoring" in result
        assert "disclaimer" in result

        # Nested content
        assert result["symptoms"]["symptoms"] == ["Fièvre", "Toux"]
        assert result["risk"]["level"] == "MEDIUM"
        assert result["monitoring"]["status"] == "success"
        assert result["disclaimer"] != ""

    @pytest.mark.asyncio
    async def test_process_chat_invokes_graph(self, mock_graph_invoke: MagicMock) -> None:
        """process_chat should call compiled_graph.ainvoke with initial state."""
        await medical_service.process_chat(
            user_input="Test symptoms",
            correlation_id="cid-invoke",
        )

        mock_graph_invoke.assert_called_once()
        args, _ = mock_graph_invoke.call_args
        initial_state = args[0]
        assert initial_state["user_input"] == "Test symptoms"
        assert initial_state["correlation_id"] == "cid-invoke"
        assert "start_time" in initial_state
        assert "uuid" in initial_state
        assert "timestamp" in initial_state

    @pytest.mark.asyncio
    async def test_process_chat_handles_graph_error(
        self, mock_graph_invoke_error: MagicMock
    ) -> None:
        """When the graph raises, process_chat should return an error response."""
        result = await medical_service.process_chat(
            user_input="Something broken",
            correlation_id="cid-error",
        )

        # Should still be a valid response structure with error details
        assert result["correlation_id"] == "cid-error"
        assert result["monitoring"]["status"] == "error"
        assert len(result["monitoring"]["error_details"]) > 0
        assert "Simulated workflow failure" in result["monitoring"]["error_details"][0]
        # Error response still has all expected keys
        assert "symptoms" in result
        assert "risk" in result
        assert "medical_advice" in result
        assert "disclaimer" in result
        # Risk should be LOW (fallback during error)
        assert result["risk"]["level"] == "LOW"

    @pytest.mark.asyncio
    async def test_process_chat_saves_request_to_db(
        self, mock_graph_invoke: MagicMock, sample_state: dict[str, Any]
    ) -> None:
        mock_graph_invoke.return_value = sample_state

        await medical_service.process_chat(
            user_input="Save test",
            correlation_id="cid-save-request",
        )

        # Verify a RequestRecord was created
        async with async_session_factory() as session:
            result = await session.execute(
                select(RequestRecord).where(RequestRecord.correlation_id == "cid-save-request")
            )
            record = result.scalar_one_or_none()
            assert record is not None
            assert record.user_input == "Save test"
            assert record.status == "success"
            assert record.risk_level == "MEDIUM"

    @pytest.mark.asyncio
    async def test_process_chat_saves_metrics(
        self, mock_graph_invoke: MagicMock, sample_state: dict[str, Any]
    ) -> None:
        mock_graph_invoke.return_value = sample_state

        await medical_service.process_chat(
            user_input="Metrics test",
            correlation_id="cid-metrics",
        )

        async with async_session_factory() as session:
            # Should have MetricRecords for each non-Monitoring agent
            result = await session.execute(
                select(MetricRecord).where(MetricRecord.correlation_id == "cid-metrics")
            )
            records = result.scalars().all()
            agent_names = [r.agent_name for r in records]
            assert "Supervisor" in agent_names
            assert "SymptomAnalysis" in agent_names
            # Monitoring agent should be skipped in metrics
            assert "Monitoring" not in agent_names

    @pytest.mark.asyncio
    async def test_process_chat_saves_history(
        self, mock_graph_invoke: MagicMock, sample_state: dict[str, Any]
    ) -> None:
        mock_graph_invoke.return_value = sample_state

        await medical_service.process_chat(
            user_input="History test",
            correlation_id="cid-history",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(HistoryRecord)
                .where(HistoryRecord.correlation_id == "cid-history")
                .order_by(HistoryRecord.created_at)
            )
            records = result.scalars().all()
            assert len(records) >= 2  # user message + assistant response
            assert records[0].role == "user"
            assert records[0].content == "History test"
            assert records[-1].role == "assistant"

    @pytest.mark.asyncio
    async def test_process_chat_error_saves_request(
        self, mock_graph_invoke_error: MagicMock
    ) -> None:
        await medical_service.process_chat(
            user_input="Error save test",
            correlation_id="cid-err-save",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(RequestRecord).where(RequestRecord.correlation_id == "cid-err-save")
            )
            record = result.scalar_one_or_none()
            assert record is not None
            assert record.status == "error"
            assert record.risk_level == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_process_chat_handles_empty_input(self, mock_graph_invoke: MagicMock) -> None:
        """Empty user input should still produce a valid response."""
        mock_graph_invoke.return_value = {
            "user_input": "",
            "correlation_id": "cid-empty",
            "uuid": "uuid-empty",
            "timestamp": "now",
            "start_time": 1.0,
            "end_time": 1.5,
            "symptoms": [],
            "risk_level": "LOW",
            "risk_justification": "",
            "medical_advice": "Surveillez votre état.",
            "disclaimer": "⚠️ Avertissement",
            "monitoring_output": {
                "correlation_id": "cid-empty",
                "uuid": "uuid-empty",
                "timestamp": "now",
                "duration_ms": 500.0,
                "agents_executed": [],
                "execution_times": {},
                "status": "success",
                "total_tokens": 0,
                "error_details": None,
            },
        }

        result = await medical_service.process_chat(
            user_input="",
            correlation_id="cid-empty",
        )
        assert result["correlation_id"] == "cid-empty"
        assert result["risk"]["level"] == "LOW"
        assert result["monitoring"]["status"] == "success"


class TestSaveMethods:
    """Direct tests for the private _save_* methods."""

    @pytest.mark.asyncio
    async def test_save_request_success(self) -> None:
        await medical_service._save_request(
            correlation_id="save-req-1",
            user_input="Test",
            final_response="Response",
            status="success",
            duration_ms=100.0,
            token_count=10,
            risk_level="LOW",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(RequestRecord).where(RequestRecord.correlation_id == "save-req-1")
            )
            assert result.scalar_one() is not None

    @pytest.mark.asyncio
    async def test_save_request_error(self) -> None:
        await medical_service._save_request(
            correlation_id="save-req-err",
            user_input="Error",
            final_response="Error detail",
            status="error",
            duration_ms=50.0,
            token_count=0,
            risk_level="HIGH",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(RequestRecord).where(RequestRecord.correlation_id == "save-req-err")
            )
            record = result.scalar_one()
            assert record.status == "error"
            assert record.risk_level == "HIGH"

    @pytest.mark.asyncio
    async def test_save_metrics(self) -> None:
        monitoring_output: dict[str, Any] = {
            "agents_executed": ["Supervisor", "SymptomAnalysis"],
            "execution_times": {"Supervisor": 5.0, "SymptomAnalysis": 200.0},
        }
        await medical_service._save_metrics(
            correlation_id="save-met-1",
            monitoring_output=monitoring_output,
            status="success",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(MetricRecord).where(MetricRecord.correlation_id == "save-met-1")
            )
            records = result.scalars().all()
            assert len(records) == 2
            names = [r.agent_name for r in records]
            assert "Supervisor" in names
            assert "SymptomAnalysis" in names

    @pytest.mark.asyncio
    async def test_save_metrics_skips_monitoring(self) -> None:
        monitoring_output: dict[str, Any] = {
            "agents_executed": ["Supervisor", "Monitoring"],
            "execution_times": {"Supervisor": 5.0, "Monitoring": 1.0},
        }
        await medical_service._save_metrics(
            correlation_id="save-met-skip",
            monitoring_output=monitoring_output,
            status="success",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(MetricRecord).where(MetricRecord.correlation_id == "save-met-skip")
            )
            records = result.scalars().all()
            agent_names = [r.agent_name for r in records]
            assert "Supervisor" in agent_names
            assert "Monitoring" not in agent_names

    @pytest.mark.asyncio
    async def test_save_history_user(self) -> None:
        await medical_service._save_history(
            correlation_id="save-hist-1",
            role="user",
            content="Hello",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(HistoryRecord).where(HistoryRecord.correlation_id == "save-hist-1")
            )
            record = result.scalar_one()
            assert record.role == "user"
            assert record.agent_name is None

    @pytest.mark.asyncio
    async def test_save_history_assistant(self) -> None:
        await medical_service._save_history(
            correlation_id="save-hist-2",
            role="assistant",
            content="Advice",
            agent_name="MedicalAdvice",
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(HistoryRecord).where(HistoryRecord.correlation_id == "save-hist-2")
            )
            record = result.scalar_one()
            assert record.role == "assistant"
            assert record.agent_name == "MedicalAdvice"


class TestServiceEdgeCases:
    """Edge cases and error-handling in the service layer."""

    @pytest.mark.asyncio
    async def test_save_request_handles_db_error_gracefully(
        self,
    ) -> None:
        """_save_request should log errors but not crash the service."""
        # Patch async_session_factory to raise on session creation
        with patch(
            "app.services.medical_service.async_session_factory",
            side_effect=Exception("DB down"),
        ):
            await medical_service._save_request(
                correlation_id="fail-cid",
                user_input="Test",
                final_response=None,
                status="error",
                duration_ms=0,
                token_count=0,
                risk_level="LOW",
            )
            # Success = no exception raised

    @pytest.mark.asyncio
    async def test_save_metrics_handles_db_error(self) -> None:
        with patch(
            "app.services.medical_service.async_session_factory",
            side_effect=Exception("DB down"),
        ):
            await medical_service._save_metrics(
                correlation_id="fail-met",
                monitoring_output={
                    "agents_executed": ["Supervisor"],
                    "execution_times": {},
                },
                status="error",
            )
            # Success = no exception raised

    @pytest.mark.asyncio
    async def test_save_history_handles_db_error(self) -> None:
        with patch(
            "app.services.medical_service.async_session_factory",
            side_effect=Exception("DB down"),
        ):
            await medical_service._save_history(
                correlation_id="fail-hist",
                role="user",
                content="Test",
            )
            # Success = no exception raised
