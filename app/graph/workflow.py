# LangGraph workflow definition for the medical pre-diagnosis system.
"""Graph state, node definitions, and workflow compilation using LangGraph."""

from __future__ import annotations

import time
from typing import Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import StateGraph as StateGraphType

from app.agents.base import BaseAgent
from app.agents.medical_advice import MedicalAdviceAgent
from app.agents.monitoring import MonitoringAgent
from app.agents.risk_assessment import RiskAssessmentAgent
from app.agents.supervisor import SupervisorAgent
from app.agents.symptom_analysis import SymptomAnalysisAgent
from app.monitoring.service import Timer


def create_workflow_graph() -> StateGraphType:
    """Create and compile the LangGraph workflow.

    Workflow:
        START -> Supervisor -> SymptomAnalysis -> RiskAssessment -> MedicalAdvice -> Monitoring -> END

    Returns:
        Compiled LangGraph workflow.
    """
    # Initialize agents
    supervisor = SupervisorAgent()
    symptom_analysis = SymptomAnalysisAgent()
    risk_assessment = RiskAssessmentAgent()
    medical_advice = MedicalAdviceAgent()
    monitoring = MonitoringAgent()

    # Create graph
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("supervisor", _wrap_agent(supervisor))
    workflow.add_node("symptom_analysis", _wrap_agent(symptom_analysis))
    workflow.add_node("risk_assessment", _wrap_agent(risk_assessment))
    workflow.add_node("medical_advice", _wrap_agent(medical_advice))
    workflow.add_node("monitoring", _wrap_agent(monitoring))

    # Define edges
    workflow.add_edge("supervisor", "symptom_analysis")
    workflow.add_edge("symptom_analysis", "risk_assessment")
    workflow.add_edge("risk_assessment", "medical_advice")
    workflow.add_edge("medical_advice", "monitoring")
    workflow.add_edge("monitoring", END)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Compile
    return workflow.compile()


def _wrap_agent(agent: BaseAgent):
    """Wrap an agent's execute method with timing and state tracking."""

    def node_fn(state: dict) -> dict:
        timer = Timer(agent.name)
        with timer:
            result = agent.execute(state)

        # Store execution metrics
        exec_info = {
            "execution_time_ms": timer.elapsed_ms,
            "agent_name": agent.name,
        }
        error = result.get("error")
        if error:
            exec_info["error"] = error

        result[f"{_get_state_key(agent.name)}_execution"] = exec_info
        return result

    return node_fn


def _get_state_key(agent_name: str) -> str:
    """Convert agent name to state dictionary key."""
    mapping = {
        "Supervisor": "supervisor",
        "SymptomAnalysis": "symptom_analysis",
        "RiskAssessment": "risk_assessment",
        "MedicalAdvice": "medical_advice",
        "Monitoring": "monitoring",
    }
    return mapping.get(agent_name, agent_name.lower())


# Create compiled graph singleton
compiled_graph = create_workflow_graph()
