# SQLAlchemy ORM models for the Medical AI Assistant.
"""Database models representing requests, logs, metrics, and history."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database.connection import Base


class RequestRecord(Base):
    """Stores each incoming request and its result."""

    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(36), unique=True, nullable=False, index=True)
    user_input = Column(Text, nullable=False)
    final_response = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    duration_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True, default=0)
    risk_level = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<RequestRecord(correlation_id={self.correlation_id}, status={self.status})>"


class LogRecord(Base):
    """Stores application logs."""

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(36), nullable=True, index=True)
    level = Column(String(10), nullable=False, default="INFO")
    logger = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<LogRecord(level={self.level}, message={self.message[:50]})>"


class MetricRecord(Base):
    """Stores application metrics per execution."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="success")
    token_count = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<MetricRecord(agent={self.agent_name}, status={self.status})>"


class HistoryRecord(Base):
    """Stores conversation history."""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, agent
    content = Column(Text, nullable=False)
    agent_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<HistoryRecord(role={self.role}, agent={self.agent_name})>"


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())
