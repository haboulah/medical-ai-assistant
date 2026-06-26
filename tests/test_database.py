"""Tests for database models and connection management.

Uses the test SQLite database created by the ``db_conftest`` fixture.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import Base, async_session_factory, close_db, engine, init_db
from app.database.models import (
    HistoryRecord,
    LogRecord,
    MetricRecord,
    RequestRecord,
    generate_uuid,
)


class TestGenerateUUID:
    def test_generate_uuid_returns_string(self) -> None:
        uid = generate_uuid()
        assert isinstance(uid, str)

    def test_generate_uuid_format(self) -> None:
        uid = generate_uuid()
        parts = uid.split("-")
        assert len(parts) == 5

    def test_generate_uuid_unique(self) -> None:
        uids = {generate_uuid() for _ in range(100)}
        assert len(uids) == 100  # All unique


class TestRequestRecord:
    """Tests for the RequestRecord model."""

    async def test_create_request(self, db: AsyncSession) -> None:
        record = RequestRecord(
            correlation_id="req-001",
            user_input="J'ai de la fièvre",
            final_response="Surveillez vos symptômes",
            status="success",
            duration_ms=1500.0,
            token_count=50,
            risk_level="LOW",
        )
        db.add(record)
        await db.commit()

        # Query back
        result = await db.execute(
            select(RequestRecord).where(RequestRecord.correlation_id == "req-001")
        )
        saved = result.scalar_one()
        assert saved.user_input == "J'ai de la fièvre"
        assert saved.status == "success"
        assert saved.risk_level == "LOW"
        assert saved.duration_ms == 1500.0
        assert saved.token_count == 50
        assert saved.id is not None
        assert saved.created_at is not None

    async def test_request_default_status(self, db: AsyncSession) -> None:
        """Default status should be 'pending'."""
        record = RequestRecord(
            correlation_id="req-default",
            user_input="test",
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(RequestRecord).where(RequestRecord.correlation_id == "req-default")
        )
        saved = result.scalar_one()
        assert saved.status == "pending"

    async def test_request_unique_correlation_id(self, db: AsyncSession) -> None:
        """correlation_id should be unique."""
        record1 = RequestRecord(correlation_id="req-unique", user_input="test1")
        db.add(record1)
        await db.commit()

        record2 = RequestRecord(correlation_id="req-unique", user_input="test2")
        db.add(record2)
        with pytest.raises(Exception):
            await db.commit()
        await db.rollback()  # Clear the failed transaction

    async def test_request_multiple_statuses(self, db: AsyncSession) -> None:
        """Create records with different statuses and verify they can be retrieved."""
        for i, status in enumerate(["success", "error", "pending"]):
            record = RequestRecord(
                correlation_id=f"req-status-{i}",
                user_input=f"test {status}",
                status=status,
            )
            db.add(record)
        await db.commit()

        result = await db.execute(select(func.count(RequestRecord.id)))
        total = result.scalar()
        assert total == 3

    async def test_request_repr(self) -> None:
        record = RequestRecord(correlation_id="rep-001", status="success")
        repr_str = repr(record)
        assert "rep-001" in repr_str
        assert "success" in repr_str


class TestLogRecord:
    async def test_create_log(self, db: AsyncSession) -> None:
        record = LogRecord(
            correlation_id="log-001",
            level="INFO",
            logger="test",
            message="Test log message",
            traceback=None,
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(LogRecord).where(LogRecord.correlation_id == "log-001")
        )
        saved = result.scalar_one()
        assert saved.level == "INFO"
        assert saved.message == "Test log message"
        assert saved.logger == "test"
        assert saved.traceback is None

    async def test_log_default_level(self, db: AsyncSession) -> None:
        record = LogRecord(correlation_id="log-default", message="test")
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(LogRecord).where(LogRecord.correlation_id == "log-default")
        )
        saved = result.scalar_one()
        assert saved.level == "INFO"

    async def test_log_with_traceback(self, db: AsyncSession) -> None:
        record = LogRecord(
            correlation_id="log-tb",
            level="ERROR",
            message="Something broke",
            traceback="Traceback (most recent call last):\n  ...",
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(LogRecord).where(LogRecord.correlation_id == "log-tb")
        )
        saved = result.scalar_one()
        assert saved.traceback is not None
        assert "Traceback" in saved.traceback

    async def test_log_repr(self) -> None:
        record = LogRecord(level="WARNING", message="Warning message here")
        repr_str = repr(record)
        assert "WARNING" in repr_str
        assert "Warning" in repr_str


class TestMetricRecord:
    async def test_create_metric(self, db: AsyncSession) -> None:
        record = MetricRecord(
            correlation_id="met-001",
            agent_name="SymptomAnalysis",
            execution_time_ms=500.0,
            status="success",
            token_count=100,
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(MetricRecord).where(MetricRecord.correlation_id == "met-001")
        )
        saved = result.scalar_one()
        assert saved.agent_name == "SymptomAnalysis"
        assert saved.execution_time_ms == 500.0
        assert saved.status == "success"
        assert saved.token_count == 100

    async def test_metric_default_status(self, db: AsyncSession) -> None:
        record = MetricRecord(
            correlation_id="met-default",
            agent_name="Supervisor",
            execution_time_ms=10.0,
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(MetricRecord).where(MetricRecord.correlation_id == "met-default")
        )
        saved = result.scalar_one()
        assert saved.status == "success"

    async def test_metric_with_error(self, db: AsyncSession) -> None:
        record = MetricRecord(
            correlation_id="met-err",
            agent_name="RiskAssessment",
            execution_time_ms=0.0,
            status="error",
            error_message="LLM timeout",
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(MetricRecord).where(MetricRecord.correlation_id == "met-err")
        )
        saved = result.scalar_one()
        assert saved.error_message == "LLM timeout"
        assert saved.status == "error"

    async def test_metric_multiple_agents(self, db: AsyncSession) -> None:
        agents = ["Supervisor", "SymptomAnalysis", "RiskAssessment", "MedicalAdvice"]
        for i, agent in enumerate(agents):
            record = MetricRecord(
                correlation_id=f"met-multi-{i}",
                agent_name=agent,
                execution_time_ms=float(i * 100),
            )
            db.add(record)
        await db.commit()

        result = await db.execute(select(func.count(MetricRecord.id)))
        assert result.scalar() == 4

    async def test_metric_repr(self) -> None:
        record = MetricRecord(agent_name="Supervisor", status="success")
        repr_str = repr(record)
        assert "Supervisor" in repr_str
        assert "success" in repr_str


class TestHistoryRecord:
    async def test_create_history(self, db: AsyncSession) -> None:
        record = HistoryRecord(
            correlation_id="hist-001",
            role="user",
            content="J'ai de la fièvre",
            agent_name=None,
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(HistoryRecord).where(HistoryRecord.correlation_id == "hist-001")
        )
        saved = result.scalar_one()
        assert saved.role == "user"
        assert saved.content == "J'ai de la fièvre"
        assert saved.agent_name is None

    async def test_history_assistant_with_agent(self, db: AsyncSession) -> None:
        record = HistoryRecord(
            correlation_id="hist-002",
            role="assistant",
            content="Medical advice here",
            agent_name="MedicalAdvice",
        )
        db.add(record)
        await db.commit()

        result = await db.execute(
            select(HistoryRecord).where(HistoryRecord.correlation_id == "hist-002")
        )
        saved = result.scalar_one()
        assert saved.role == "assistant"
        assert saved.agent_name == "MedicalAdvice"

    async def test_history_conversation_ordering(self, db: AsyncSession) -> None:
        hist1 = HistoryRecord(correlation_id="hist-order", role="user", content="Hello")
        db.add(hist1)
        await db.commit()

        import asyncio
        await asyncio.sleep(0.01)

        hist2 = HistoryRecord(correlation_id="hist-order", role="assistant", content="Hi there")
        db.add(hist2)
        await db.commit()

        result = await db.execute(
            select(HistoryRecord)
            .where(HistoryRecord.correlation_id == "hist-order")
            .order_by(HistoryRecord.created_at)
        )
        records = result.scalars().all()
        assert len(records) == 2
        assert records[0].role == "user"
        assert records[1].role == "assistant"

    async def test_history_repr(self) -> None:
        record = HistoryRecord(role="user", agent_name=None)
        repr_str = repr(record)
        assert "user" in repr_str


class TestDatabaseConnection:
    """Integration tests for database lifecycle."""

    async def test_init_and_close(self) -> None:
        """Test that init_db and close_db work correctly."""
        # init_db is already called by conftest's db_session_init fixture
        # Here we test the close_db path
        # Since we can't easily re-init, we just verify close_db doesn't crash
        await close_db()
        # Re-init for other tests that need the database
        await init_db()

    async def test_get_db_dependency(self) -> None:
        """Test the get_db dependency generator."""
        from app.database.connection import get_db

        async for session in get_db():
            assert session is not None
            # Verify session works
            result = await session.execute(select(func.now()))
            assert result is not None
            break  # Only need one session
