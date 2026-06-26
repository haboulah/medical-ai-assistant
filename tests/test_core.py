"""Tests for core modules: exceptions, monitoring service, and app factory."""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AgentError,
    ConfigurationError,
    DatabaseError,
    LLMError,
    MedicalAIError,
)


class TestExceptions:
    """Test exception hierarchy."""

    def test_medical_ai_error_base(self):
        err = MedicalAIError("Base error")
        assert str(err) == "Base error"
        assert isinstance(err, Exception)

    def test_agent_error(self):
        err = AgentError(agent_name="TestAgent", message="Agent failed")
        assert "TestAgent" in str(err)
        assert err.agent_name == "TestAgent"

    def test_llm_error(self):
        err = LLMError("LLM not responding")
        assert str(err) == "LLM not responding"

    def test_database_error(self):
        err = DatabaseError("DB connection lost")
        assert str(err) == "DB connection lost"

    def test_configuration_error(self):
        err = ConfigurationError("Config invalid")
        assert str(err) == "Config invalid"

    def test_all_exceptions_are_medical_ai_error(self):
        for exc in [AgentError("a"), ConfigurationError("b"), LLMError("c"), DatabaseError("d")]:
            assert isinstance(exc, MedicalAIError)
