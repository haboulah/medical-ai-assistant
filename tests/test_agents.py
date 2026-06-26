"""Tests for all agents: supervisor, symptom_analysis, risk_assessment,
medical_advice, monitoring, and the base agent class.

Since the test environment disables GROQ (``GROQ_API_KEY=""``), every agent
uses the *fallback* path.  This also serves as coverage for the fallback logic.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.base import BaseAgent
from app.agents.medical_advice import MedicalAdviceAgent
from app.agents.monitoring import MonitoringAgent
from app.agents.risk_assessment import RiskAssessmentAgent
from app.agents.supervisor import SupervisorAgent
from app.agents.symptom_analysis import SymptomAnalysisAgent
from app.core import settings


# ====================================================================
# BaseAgent
# ====================================================================
class ConcreteAgent(BaseAgent):
    """Minimal concrete agent for testing the base class."""

    def __init__(self) -> None:
        super().__init__("TestAgent")

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"result": "ok", **state}


class TestBaseAgent:
    def test_init_without_groq(self) -> None:
        """Agent should have ``llm=None`` when GROQ is not configured."""
        agent = ConcreteAgent()
        assert agent.name == "TestAgent"
        assert agent.llm is None

    def test_execute_adds_timing(self) -> None:
        """``execute()`` should add agent_name and execution_time_ms."""
        agent = ConcreteAgent()
        state = {"user_input": "test"}
        result = agent.execute(state)
        assert result["result"] == "ok"
        assert result["agent_name"] == "TestAgent"
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] >= 0

    def test_get_token_count(self) -> None:
        """Token count should be roughly len(content) // 4."""
        from langchain_core.messages import HumanMessage

        agent = ConcreteAgent()
        msgs = [HumanMessage(content="Hello world, this is a test message with enough chars to count.")]
        count = agent.get_token_count(msgs)
        assert count > 0
        # Should be ~ len(content) // 4
        expected = len(msgs[0].content) // 4
        assert count == expected

    def test_get_token_count_empty(self) -> None:
        """Empty message list should return 0 tokens."""
        agent = ConcreteAgent()
        assert agent.get_token_count([]) == 0

    def test_create_llm_not_called_when_not_configured(self) -> None:
        """If GROQ is not configured, ``_create_llm`` should not be called."""
        agent = ConcreteAgent()
        assert agent.llm is None


# ====================================================================
# SupervisorAgent
# ====================================================================
class TestSupervisorAgent:
    def test_init(self) -> None:
        agent = SupervisorAgent()
        assert agent.name == "Supervisor"
        assert agent.llm is None

    def test_process_with_valid_input(self) -> None:
        agent = SupervisorAgent()
        state = {"user_input": "J'ai mal à la tête"}
        result = agent.process(state)
        assert result["supervisor_decision"] == "proceed"
        assert result["next_agent"] == "symptom_analysis"
        assert "supervisor_message" in result
        assert "user_input" in result

    def test_process_with_empty_input(self) -> None:
        agent = SupervisorAgent()
        state = {"user_input": ""}
        result = agent.process(state)
        assert "error" in result
        assert result["error"] == "No user input provided"

    def test_process_with_missing_input(self) -> None:
        agent = SupervisorAgent()
        state: dict[str, Any] = {}
        result = agent.process(state)
        assert "error" in result

    def test_process_preserves_other_state(self) -> None:
        agent = SupervisorAgent()
        state = {"user_input": "test", "correlation_id": "abc123"}
        result = agent.process(state)
        assert result["correlation_id"] == "abc123"
        assert result["user_input"] == "test"


# ====================================================================
# SymptomAnalysisAgent
# ====================================================================
class TestSymptomAnalysisAgent:
    def test_init(self) -> None:
        agent = SymptomAnalysisAgent()
        assert agent.name == "SymptomAnalysis"
        assert agent.llm is None

    def test_process_uses_fallback(self) -> None:
        """Without LLM, should use _fallback_extract."""
        agent = SymptomAnalysisAgent()
        state = {"user_input": "J'ai de la fièvre et de la toux"}
        result = agent.process(state)
        assert "symptoms" in result
        assert "Fièvre" in result["symptoms"]
        assert "Toux" in result["symptoms"]
        assert result["symptoms_raw"] == state["user_input"]

    def test_process_multiple_symptoms(self) -> None:
        agent = SymptomAnalysisAgent()
        state = {
            "user_input": (
                "J'ai de la fièvre, des maux de tête, "
                "et une grande fatigue"
            )
        }
        result = agent.process(state)
        symptoms = result["symptoms"]
        assert "Fièvre" in symptoms
        assert "Maux de tête" in symptoms or "Maux de tête" in str(symptoms)
        assert "Fatigue" in symptoms

    def test_process_no_known_symptoms(self) -> None:
        """When no known keywords match, fallback should return a generic symptom."""
        agent = SymptomAnalysisAgent()
        state = {"user_input": "Je ne me sens pas bien"}
        result = agent.process(state)
        assert "Symptômes non spécifiés" in result["symptoms"]

    def test_process_empty_input(self) -> None:
        agent = SymptomAnalysisAgent()
        state = {"user_input": ""}
        result = agent.process(state)
        assert result["symptoms"] == []

    def test_fallback_extract_deduplicates(self) -> None:
        """Repeated keywords should only appear once."""
        text = "fièvre fièvre fièvre toux"
        symptoms = SymptomAnalysisAgent._fallback_extract(text)
        assert symptoms.count("Fièvre") == 1

    def test_fallback_extract_empty(self) -> None:
        assert SymptomAnalysisAgent._fallback_extract("") == []

    def test_fallback_extract_none(self) -> None:
        assert SymptomAnalysisAgent._fallback_extract(None) == []

    def test_parse_response_valid_json(self) -> None:
        """_parse_response should extract JSON from LLM output."""
        agent = SymptomAnalysisAgent()
        content = '{"symptoms": ["Fièvre", "Toux"], "raw_text": "test"}'
        result = agent._parse_response(content)
        assert result["symptoms"] == ["Fièvre", "Toux"]

    def test_parse_response_invalid_json(self) -> None:
        """When JSON parsing fails, fall back to keyword extraction."""
        agent = SymptomAnalysisAgent()
        content = "No JSON here at all"
        result = agent._parse_response(content)
        assert "symptoms" in result

    def test_llm_error_falls_back(self) -> None:
        """If LLM.invoke raises, the agent should fall back gracefully."""
        agent = SymptomAnalysisAgent()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ValueError("API error")
        agent.llm = mock_llm
        state = {"user_input": "I feel sick"}
        result = agent.process(state)
        assert "symptoms" in result
        assert "error" in result.get("symptoms_analysis", {})


# ====================================================================
# RiskAssessmentAgent
# ====================================================================
class TestRiskAssessmentAgent:
    def test_init(self) -> None:
        agent = RiskAssessmentAgent()
        assert agent.name == "RiskAssessment"
        assert agent.llm is None

    def test_fallback_high_risk(self) -> None:
        agent = RiskAssessmentAgent()
        text = "J'ai une douleur thoracique"
        result = agent._fallback_assessment(text)
        assert result["level"] == "HIGH"

    def test_fallback_medium_risk(self) -> None:
        agent = RiskAssessmentAgent()
        text = "J'ai une forte fièvre"
        result = agent._fallback_assessment(text)
        assert result["level"] == "MEDIUM"

    def test_fallback_low_risk(self) -> None:
        agent = RiskAssessmentAgent()
        text = "Je suis fatigué"
        result = agent._fallback_assessment(text)
        assert result["level"] == "LOW"

    def test_fallback_high_over_medium(self) -> None:
        """HIGH risk symptoms should take priority over MEDIUM."""
        agent = RiskAssessmentAgent()
        text = "douleur thoracique et forte fièvre"
        result = agent._fallback_assessment(text)
        assert result["level"] == "HIGH"

    def test_process_with_fallback(self) -> None:
        agent = RiskAssessmentAgent()
        state = {"symptoms": ["Fièvre"]}
        result = agent.process(state)
        assert "risk_level" in result
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_process_without_symptoms(self) -> None:
        """When symptoms list is empty, use user_input as fallback text."""
        agent = RiskAssessmentAgent()
        state = {"symptoms": [], "user_input": "chest pain"}
        result = agent.process(state)
        assert result["risk_level"] == "HIGH"

    def test_llm_error_falls_back(self) -> None:
        agent = RiskAssessmentAgent()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ValueError("API error")
        agent.llm = mock_llm
        state = {"symptoms": ["Fatigue"]}
        result = agent.process(state)
        assert "risk_level" in result
        assert "error" in result.get("risk_assessment", {})

    def test_parse_response_valid(self) -> None:
        agent = RiskAssessmentAgent()
        content = '{"level": "HIGH", "justification": "Urgent"}'
        result = agent._parse_response(content)
        assert result["level"] == "HIGH"

    def test_parse_response_invalid(self) -> None:
        agent = RiskAssessmentAgent()
        content = "Not JSON"
        result = agent._parse_response(content)
        assert result["level"] in ("LOW", "MEDIUM", "HIGH")


# ====================================================================
# MedicalAdviceAgent
# ====================================================================
class TestMedicalAdviceAgent:
    def test_init(self) -> None:
        agent = MedicalAdviceAgent()
        assert agent.name == "MedicalAdvice"
        assert agent.llm is None

    def test_fallback_advice_low(self) -> None:
        result = MedicalAdviceAgent._fallback_advice("LOW", ["Fatigue"])
        assert "Surveillez" in result["advice"]

    def test_fallback_advice_medium(self) -> None:
        result = MedicalAdviceAgent._fallback_advice("MEDIUM", ["Fièvre"])
        assert "consulter" in result["advice"]

    def test_fallback_advice_high(self) -> None:
        result = MedicalAdviceAgent._fallback_advice("HIGH", ["Douleur thoracique"])
        assert "URGENCE" in result["advice"]
        assert "15" in result["advice"]

    def test_fallback_advice_unknown_level(self) -> None:
        """Unknown risk level should default to LOW template."""
        result = MedicalAdviceAgent._fallback_advice("UNKNOWN", ["Symptôme"])
        assert "Surveillez" in result["advice"]

    def test_fallback_advice_empty_symptoms(self) -> None:
        result = MedicalAdviceAgent._fallback_advice("LOW", [])
        assert "vos symptômes" in result["advice"]

    def test_fallback_advice_includes_disclaimer(self) -> None:
        result = MedicalAdviceAgent._fallback_advice("LOW", ["Fatigue"])
        assert "Avertissement" in result["disclaimer"]

    def test_process_with_fallback(self) -> None:
        agent = MedicalAdviceAgent()
        state = {
            "symptoms": ["Fièvre", "Toux"],
            "risk_level": "MEDIUM",
            "risk_justification": "Test justification",
        }
        result = agent.process(state)
        assert "medical_advice" in result
        assert "disclaimer" in result
        assert result["disclaimer"] != ""

    def test_process_without_symptoms(self) -> None:
        agent = MedicalAdviceAgent()
        state = {"symptoms": [], "risk_level": "LOW", "risk_justification": ""}
        result = agent.process(state)
        assert "medical_advice" in result

    def test_llm_error_falls_back(self) -> None:
        agent = MedicalAdviceAgent()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ValueError("API error")
        agent.llm = mock_llm
        state = {"symptoms": ["Fatigue"], "risk_level": "LOW", "risk_justification": ""}
        result = agent.process(state)
        assert "medical_advice" in result
        assert "error" in result.get("advice_output", {})

    def test_parse_response_valid(self) -> None:
        agent = MedicalAdviceAgent()
        content = '{"advice": "Rest", "disclaimer": "Not a doctor"}'
        result = agent._parse_response(content)
        assert result["advice"] == "Rest"
        assert result["disclaimer"] == "Not a doctor"

    def test_parse_response_invalid(self) -> None:
        agent = MedicalAdviceAgent()
        content = "Plain text advice"
        result = agent._parse_response(content)
        assert result["advice"] == content
        assert "Avertissement" in result["disclaimer"]


# ====================================================================
# MonitoringAgent
# ====================================================================
class TestMonitoringAgent:
    def test_init(self) -> None:
        agent = MonitoringAgent()
        assert agent.name == "Monitoring"
        assert agent.llm is None

    def test_process_with_full_state(self, sample_state: dict[str, Any]) -> None:
        agent = MonitoringAgent()
        result = agent.process(sample_state)
        assert "monitoring_output" in result
        mo = result["monitoring_output"]
        assert mo["correlation_id"] == "test-correlation-id"
        assert mo["status"] == "success"
        assert "Supervisor" in mo["agents_executed"]
        assert "SymptomAnalysis" in mo["agents_executed"]
        assert "Monitoring" in mo["agents_executed"]
        assert mo["total_tokens"] > 0

    def test_process_with_errors(self) -> None:
        state: dict[str, Any] = {
            "user_input": "test",
            "correlation_id": "err-123",
            "uuid": "uuid-err",
            "timestamp": "now",
            "supervisor_execution": {"execution_time_ms": 5.0, "error": "Something broke"},
        }
        agent = MonitoringAgent()
        result = agent.process(state)
        mo = result["monitoring_output"]
        assert mo["status"] == "error"
        assert mo["error_details"] is not None

    def test_process_minimal_state(self) -> None:
        agent = MonitoringAgent()
        state: dict[str, Any] = {
            "user_input": "hello",
            "correlation_id": "minimal",
            "uuid": "",
            "timestamp": "",
        }
        result = agent.process(state)
        mo = result["monitoring_output"]
        assert mo["correlation_id"] == "minimal"
        assert mo["status"] == "success"
        assert mo["agents_executed"] == ["Monitoring"]

    def test_process_start_end_times(self) -> None:
        state: dict[str, Any] = {
            "user_input": "test",
            "correlation_id": "c1",
            "uuid": "",
            "timestamp": "",
            "start_time": 1000.0,
            "end_time": 1002.5,
        }
        agent = MonitoringAgent()
        result = agent.process(state)
        mo = result["monitoring_output"]
        # 2.5 seconds * 1000 = 2500 ms
        assert mo["duration_ms"] == 2500.0
