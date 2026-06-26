# Risk Assessment Agent.
"""Agent that evaluates symptom severity and assigns risk levels."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.prompts.agent_prompts import RISK_ASSESSMENT_PROMPT


class RiskAssessmentAgent(BaseAgent):
    """Agent that assesses risk level based on symptoms.

    Input: List of detected symptoms.
    Output: Risk level (LOW, MEDIUM, HIGH) with justification.
    """

    HIGH_RISK_SYMPTOMS = [
        "douleur thoracique", "chest pain", "difficulté respiratoire",
        "difficulty breathing", "perte de conscience", "loss of consciousness",
        "saignement abondant", "severe bleeding", "confusion soudaine",
        "sudden confusion", "paralysie", "paralysis",
    ]

    MEDIUM_RISK_SYMPTOMS = [
        "fièvre persistante", "persistent fever", "forte fièvre", "high fever",
        "douleur sévère", "severe pain", "vomissement répété", "repeated vomiting",
        "déshydratation", "dehydration", "éruption cutanée", "skin rash",
        "gonflement", "swelling", "vertige intense", "severe dizziness",
    ]

    def __init__(self):
        """Initialize the Risk Assessment Agent."""
        super().__init__("RiskAssessment")

    def process(self, state: dict) -> dict:
        """Assess risk level from detected symptoms.

        Args:
            state: Current state containing symptoms list.

        Returns:
            State updated with risk assessment.
        """
        symptoms = state.get("symptoms", [])
        symptoms_text = ", ".join(symptoms) if symptoms else state.get("user_input", "")

        if self.llm:
            try:
                messages = [
                    SystemMessage(content=RISK_ASSESSMENT_PROMPT),
                    HumanMessage(content=f"Analyze these symptoms: {symptoms_text}"),
                ]
                response = self.llm.invoke(messages)
                result = self._parse_response(response.content)
            except Exception as e:
                result = self._fallback_assessment(symptoms_text)
                result["error"] = str(e)
        else:
            result = self._fallback_assessment(symptoms_text)

        return {
            **state,
            "risk_level": result.get("level", "LOW"),
            "risk_justification": result.get("justification", ""),
            "risk_assessment": result,
        }

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return self._fallback_assessment(content)

    def _fallback_assessment(self, symptoms_text: str) -> dict:
        """Fallback risk assessment when LLM is unavailable."""
        text_lower = symptoms_text.lower()

        # Check HIGH risk first
        for symptom in self.HIGH_RISK_SYMPTOMS:
            if symptom in text_lower:
                return {
                    "level": "HIGH",
                    "justification": f"Les symptômes incluent '{symptom}' qui nécessite une attention médicale immédiate.",
                }

        # Check MEDIUM risk
        for symptom in self.MEDIUM_RISK_SYMPTOMS:
            if symptom in text_lower:
                return {
                    "level": "MEDIUM",
                    "justification": f"Le symptôme '{symptom}' peut nécessiter une consultation médicale.",
                }

        # Default LOW risk
        return {
            "level": "LOW",
            "justification": "Les symptômes sont légers et ne présentent pas de signes d'urgence. Surveillez l'évolution.",
        }
