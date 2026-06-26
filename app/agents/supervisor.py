# Supervisor Agent - orchestrates the multi-agent workflow.
"""Supervisor Agent responsible for routing and coordinating agents."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.prompts.agent_prompts import SUPERVISOR_PROMPT


class SupervisorAgent(BaseAgent):
    """Supervisor Agent that orchestrates the workflow.

    Responsibilities:
    - Route requests to appropriate agents
    - Manage workflow execution
    - Handle errors
    - Control execution flow
    """

    def __init__(self):
        """Initialize the Supervisor Agent."""
        super().__init__("Supervisor")

    def process(self, state: dict) -> dict:
        """Process the state and route to the next step.

        Args:
            state: Current workflow state containing user input.

        Returns:
            Updated state with supervisor routing information.
        """
        user_input = state.get("user_input", "")
        if not user_input:
            return {
                **state,
                "error": "No user input provided",
                "next_agent": "__end__",
            }

        return {
            **state,
            "supervisor_decision": "proceed",
            "next_agent": "symptom_analysis",
            "supervisor_message": SUPERVISOR_PROMPT,
        }
