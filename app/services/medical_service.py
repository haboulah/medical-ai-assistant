# Medical AI service - orchestrates the full workflow.
"""Service layer that coordinates the LangGraph workflow and database operations."""

from __future__ import annotations

import time
from datetime import datetime

import loguru

from app.agents.monitoring import MonitoringAgent
from app.database.connection import async_session_factory
from app.database.models import HistoryRecord, MetricRecord, RequestRecord
from app.graph.workflow import compiled_graph
from app.monitoring.service import MonitoringService


class MedicalAIService:
    """Main service class orchestrating the medical assistant workflow."""

    def __init__(self):
        """Initialize the service."""
        self.monitoring_agent = MonitoringAgent()

    async def process_chat(self, user_input: str, correlation_id: str) -> dict:
        """Process a chat message through the full workflow.

        Args:
            user_input: The user's symptom description.
            correlation_id: Unique correlation ID for this request.

        Returns:
            Full response with all agent outputs.

        """
        start_time = time.perf_counter()
        uuid_val = MonitoringService.generate_uuid()
        timestamp = datetime.now().isoformat()

        loguru.logger.info(f"[{correlation_id}] Processing chat input: {user_input[:100]}...")

        # Initialize state for the graph
        initial_state = {
            "user_input": user_input,
            "correlation_id": correlation_id,
            "uuid": uuid_val,
            "timestamp": timestamp,
            "start_time": start_time,
        }

        # Execute the LangGraph workflow
        try:
            final_state = await compiled_graph.ainvoke(initial_state)

            # Extract results
            symptoms_list = final_state.get("symptoms", [])
            risk_level = final_state.get("risk_level", "LOW")
            risk_justification = final_state.get("risk_justification", "")
            medical_advice_text = final_state.get("medical_advice", "")
            disclaimer = final_state.get(
                "disclaimer",
                "⚠️ Avertissement : cette application fournit uniquement une aide "
                "informative et ne remplace pas un professionnel de santé.",
            )
            monitoring_output = final_state.get("monitoring_output", {})

            # Calculate duration
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            # Update monitoring with actual duration
            monitoring_output["duration_ms"] = round(duration_ms, 2)

            # Build response
            response = {
                "correlation_id": correlation_id,
                "symptoms": {
                    "symptoms": symptoms_list,
                    "raw_text": user_input,
                },
                "risk": {
                    "level": risk_level,
                    "justification": risk_justification,
                },
                "medical_advice": {
                    "advice": medical_advice_text,
                    "disclaimer": disclaimer,
                },
                "monitoring": monitoring_output,
                "disclaimer": disclaimer,
            }

            # Save to database asynchronously
            await self._save_request(
                correlation_id=correlation_id,
                user_input=user_input,
                final_response=medical_advice_text,
                status="success",
                duration_ms=duration_ms,
                token_count=monitoring_output.get("total_tokens", 0),
                risk_level=risk_level,
            )

            # Save metrics
            await self._save_metrics(correlation_id, monitoring_output, "success")
            await self._save_history(correlation_id, "user", user_input)
            await self._save_history(
                correlation_id, "assistant", medical_advice_text, "MedicalAdvice"
            )

            loguru.logger.info(
                f"[{correlation_id}] Request completed in {duration_ms:.1f}ms "
                f"- Risk: {risk_level}"
            )

        except Exception as e:
            loguru.logger.error(f"[{correlation_id}] Workflow error: {e}")
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            error_response = {
                "correlation_id": correlation_id,
                "symptoms": {"symptoms": [], "raw_text": user_input},
                "risk": {
                    "level": "LOW",
                    "justification": "Unable to assess risk due to an error.",
                },
                "medical_advice": {
                    "advice": "Désolé, une erreur est survenue lors du traitement de votre demande. "
                    "Veuillez réessayer ou consulter un professionnel de santé.",
                    "disclaimer": "⚠️ Avertissement : cette application fournit uniquement une aide "
                    "informative et ne remplace pas un professionnel de santé.",
                },
                "monitoring": {
                    "correlation_id": correlation_id,
                    "uuid": uuid_val,
                    "timestamp": timestamp,
                    "duration_ms": round(duration_ms, 2),
                    "agents_executed": [],
                    "execution_times": {},
                    "status": "error",
                    "total_tokens": 0,
                    "error_details": [str(e)],
                },
                "disclaimer": "⚠️ Avertissement : cette application fournit uniquement une aide "
                "informative et ne remplace pas un professionnel de santé.",
            }

            await self._save_request(
                correlation_id=correlation_id,
                user_input=user_input,
                final_response=str(e),
                status="error",
                duration_ms=duration_ms,
                token_count=0,
                risk_level="UNKNOWN",
            )

            return error_response

        return response

    async def _save_request(
        self,
        correlation_id: str,
        user_input: str,
        final_response: str | None,
        status: str,
        duration_ms: float,
        token_count: int,
        risk_level: str,
    ) -> None:
        """Save a request record to the database."""
        try:
            async with async_session_factory() as session:
                record = RequestRecord(
                    correlation_id=correlation_id,
                    user_input=user_input,
                    final_response=final_response,
                    status=status,
                    duration_ms=duration_ms,
                    token_count=token_count,
                    risk_level=risk_level,
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            loguru.logger.error(f"Failed to save request record: {e}")

    async def _save_metrics(
        self,
        correlation_id: str,
        monitoring_output: dict,
        status: str,
    ) -> None:
        """Save agent execution metrics to the database."""
        try:
            async with async_session_factory() as session:
                agents = monitoring_output.get("agents_executed", [])
                times = monitoring_output.get("execution_times", {})

                for agent_name in agents:
                    if agent_name == "Monitoring":
                        continue
                    record = MetricRecord(
                        correlation_id=correlation_id,
                        agent_name=agent_name,
                        execution_time_ms=times.get(agent_name, 0),
                        status=status,
                        token_count=0,
                    )
                    session.add(record)

                await session.commit()
        except Exception as e:
            loguru.logger.error(f"Failed to save metrics: {e}")

    async def _save_history(
        self,
        correlation_id: str,
        role: str,
        content: str,
        agent_name: str | None = None,
    ) -> None:
        """Save a history record."""
        try:
            async with async_session_factory() as session:
                record = HistoryRecord(
                    correlation_id=correlation_id,
                    role=role,
                    content=content,
                    agent_name=agent_name,
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            loguru.logger.error(f"Failed to save history: {e}")


# Singleton instance
medical_service = MedicalAIService()
