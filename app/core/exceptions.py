# Medical AI Assistant - Core Exceptions
"""Custom exception classes for the application."""

from __future__ import annotations


class MedicalAIError(Exception):
    """Base exception for all Medical AI Assistant errors."""

    def __init__(self, message: str = "An error occurred", correlation_id: str | None = None):
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(self.message)


class AgentError(MedicalAIError):
    """Raised when an agent encounters an error."""

    def __init__(
        self,
        agent_name: str,
        message: str = "Agent execution failed",
        correlation_id: str | None = None,
    ):
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}", correlation_id)


class ConfigurationError(MedicalAIError):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message)


class DatabaseError(MedicalAIError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database error", correlation_id: str | None = None):
        super().__init__(message, correlation_id)


class LLMError(MedicalAIError):
    """Raised when the LLM fails to respond."""

    def __init__(self, message: str = "LLM error", correlation_id: str | None = None):
        super().__init__(message, correlation_id)
