# Pydantic schemas for API request/response validation.
"""Data transfer objects and validation schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for the /chat endpoint."""

    message: str = Field(
        ..., min_length=1, max_length=5000, description="User's symptoms description"
    )


class SymptomOutput(BaseModel):
    """Output from the Symptom Analysis Agent."""

    symptoms: list[str] = Field(default_factory=list, description="List of detected symptoms")
    raw_text: str = Field(default="", description="Raw symptoms text")


class RiskOutput(BaseModel):
    """Output from the Risk Assessment Agent."""

    level: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH)$", description="Risk level")
    justification: str = Field(..., description="Justification for the risk level")


class AdviceOutput(BaseModel):
    """Output from the Medical Advice Agent."""

    advice: str = Field(..., description="General medical advice")
    disclaimer: str = Field(
        default="⚠️ Avertissement : cette application fournit uniquement une aide informative "
        "et ne remplace pas un professionnel de santé.",
        description="Medical disclaimer",
    )


class MonitoringOutput(BaseModel):
    """Output from the Monitoring Agent."""

    correlation_id: str = Field(default="", description="Correlation ID")
    uuid: str = Field(default="", description="Execution UUID")
    timestamp: str = Field(default="", description="Execution timestamp")
    duration_ms: float = Field(default=0.0, description="Total execution duration")
    agents_executed: list[str] = Field(default_factory=list, description="List of executed agents")
    execution_times: dict[str, float] = Field(
        default_factory=dict, description="Per-agent execution times"
    )
    status: str = Field(default="success", description="Execution status")
    total_tokens: int = Field(default=0, description="Total tokens used")


class ChatResponse(BaseModel):
    """Response schema for the /chat endpoint."""

    correlation_id: str = Field(..., description="Correlation ID")
    symptoms: SymptomOutput = Field(..., description="Detected symptoms")
    risk: RiskOutput = Field(..., description="Risk assessment")
    medical_advice: AdviceOutput = Field(..., description="Medical advice")
    monitoring: MonitoringOutput = Field(..., description="Execution monitoring")
    disclaimer: str = Field(
        default="⚠️ Avertissement : cette application fournit uniquement une aide informative "
        "et ne remplace pas un professionnel de santé.",
        description="Legal disclaimer",
    )


class HealthResponse(BaseModel):
    """Response schema for the /health endpoint."""

    status: str = Field(default="healthy", description="Application status")
    version: str = Field(default="1.0.0", description="Application version")
    database: str = Field(default="ok", description="Database status")
    llm: str = Field(default="configured", description="LLM status")


class MetricsResponse(BaseModel):
    """Response schema for the /metrics endpoint."""

    total_requests: int = Field(default=0, description="Total requests processed")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    avg_duration_ms: float = Field(default=0.0, description="Average execution duration")
    max_duration_ms: float = Field(default=0.0, description="Maximum execution duration")
    min_duration_ms: float = Field(default=0.0, description="Minimum execution duration")
    risk_distribution: dict[str, int] = Field(
        default_factory=dict, description="Risk level distribution"
    )
    agent_calls: dict[str, int] = Field(default_factory=dict, description="Per-agent call count")
    memory_usage_mb: float = Field(default=0.0, description="Memory usage in MB")
    cpu_percent: float = Field(default=0.0, description="CPU usage percentage")


class VersionResponse(BaseModel):
    """Response schema for the /version endpoint."""

    name: str = Field(default="Medical AI Assistant", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    python_version: str = Field(default="", description="Python version")
    langgraph_version: str = Field(default="", description="LangGraph version")
    fastapi_version: str = Field(default="", description="FastAPI version")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    correlation_id: str | None = Field(default=None, description="Correlation ID")
    detail: str | None = Field(default=None, description="Additional details")


class HistoryItem(BaseModel):
    """Single history entry."""

    id: int
    correlation_id: str
    role: str
    content: str
    agent_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RequestItem(BaseModel):
    """Single request record."""

    id: int
    correlation_id: str
    user_input: str
    final_response: str | None
    status: str
    duration_ms: float | None
    token_count: int | None
    risk_level: str | None
    created_at: datetime

    class Config:
        from_attributes = True
