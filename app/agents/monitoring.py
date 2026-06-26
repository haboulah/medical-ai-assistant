# Monitoring Agent - tracks execution metrics.
"""Agent that monitors and records execution metrics for the workflow."""

from __future__ import annotations

import json
from datetime import datetime

from app.agents.base import BaseAgent


class MonitoringAgent(BaseAgent):
    """Agent that tracks and records workflow execution metrics.

    Records:
    - Correlation ID
    - UUID
    - Timestamp
    - Duration
    - Agents executed
    - Execution times
    - Success/Error
    - Token count
    - Total time
    """

    def __init__(self):
        """Initialize the Monitoring Agent."""
        super().__init__("Monitoring")

    def process(self, state: dict) -> dict:
        """Compile execution metrics from the workflow state.

        Args:
            state: Final workflow state with all agent execution data.

        Returns:
            State updated with monitoring metrics.
        """
        correlation_id = state.get("correlation_id", "unknown")
        uuid_val = state.get("uuid", "")
        timestamp = datetime.now().isoformat()

        # Collect agent execution data
        agents_executed: list[str] = []
        execution_times: dict[str, float] = {}
        total_tokens = 0
        errors: list[str] = []

        # Gather metrics from state
        agent_fields = {
            "supervisor": "Supervisor",
            "symptom_analysis": "SymptomAnalysis",
            "risk_assessment": "RiskAssessment",
            "medical_advice": "MedicalAdvice",
        }

        for state_key, agent_name in agent_fields.items():
            agent_data = state.get(f"{state_key}_execution", {})
            if agent_data:
                agents_executed.append(agent_name)
                exec_time = agent_data.get("execution_time_ms", 0)
                execution_times[agent_name] = exec_time
                err = agent_data.get("error")
                if err is not None:
                    errors.append(f"{agent_name}: {err}")

        # Also add the monitoring agent itself
        agents_executed.append("Monitoring")

        # Calculate total duration from start time in state
        start_time = state.get("start_time", 0)
        end_time = state.get("end_time", 0)
        total_duration_ms = (end_time - start_time) * 1000 if start_time and end_time else 0

        # Estimate tokens
        user_input = state.get("user_input", "")
        total_tokens = len(user_input) // 4  # Approximate

        # Determine status
        status = "error" if errors else "success"

        monitoring_output = {
            "correlation_id": correlation_id,
            "uuid": uuid_val,
            "timestamp": timestamp,
            "duration_ms": round(total_duration_ms, 2),
            "agents_executed": agents_executed,
            "execution_times": execution_times,
            "status": status,
            "total_tokens": total_tokens,
            "error_details": errors if errors else None,
        }

        return {
            **state,
            "monitoring_output": monitoring_output,
            "monitoring_results": json.dumps(monitoring_output, indent=2),
        }
