# Symptom Analysis Agent.
"""Agent that analyzes and extracts symptoms from user input."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.prompts.agent_prompts import SYMPTOM_ANALYSIS_PROMPT


class SymptomAnalysisAgent(BaseAgent):
    """Agent that detects and extracts symptoms from natural language.

    Input: Free text describing symptoms.
    Output: Structured list of detected symptoms.
    """

    def __init__(self):
        """Initialize the Symptom Analysis Agent."""
        super().__init__("SymptomAnalysis")

    def process(self, state: dict) -> dict:
        """Analyze user input and extract symptoms.

        Args:
            state: Current state containing user_input.

        Returns:
            State updated with detected symptoms.
        """
        user_input = state.get("user_input", "")

        if self.llm:
            try:
                messages = [
                    SystemMessage(content=SYMPTOM_ANALYSIS_PROMPT),
                    HumanMessage(content=user_input),
                ]
                response = self.llm.invoke(messages)
                result = self._parse_response(response.content)
            except Exception as e:
                result = {
                    "symptoms": self._fallback_extract(user_input),
                    "raw_text": user_input,
                }
                result["error"] = str(e)
        else:
            result = {
                "symptoms": self._fallback_extract(user_input),
                "raw_text": user_input,
            }

        return {
            **state,
            "symptoms": result.get("symptoms", []),
            "symptoms_raw": result.get("raw_text", user_input),
            "symptoms_analysis": result,
        }

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        # Try to extract JSON from the response
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"symptoms": self._fallback_extract(content), "raw_text": content}

    @staticmethod
    def _fallback_extract(text: str) -> list[str]:
        """Fallback extraction when LLM is unavailable."""
        if not text:
            return []

        symptoms = []
        # Common symptom keywords (French)
        keywords = [
            "fièvre", "toux", "fatigue", "maux de tête", "céphalée",
            "douleur", "nausée", "vomissement", "diarrhée", "vertige",
            "essoufflement", "dyspnée", "frisson", "sueur", "courbature",
            "mal de gorge", "écoulement nasal", "éternuement", "congestion",
            "perte d'odorat", "perte de goût", "douleur thoracique",
            "palpitation", "confusion", "évanouissement", "saignement",
            "gonflement", "éruption cutanée", "démangeaison", "insomnie",
            "anxiété", "dépression", "perte de poids", "prise de poids",
            "soif excessive", "urination fréquente", "vision trouble",
        ]

        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                symptoms.append(keyword.capitalize())

        # Deduplicate
        seen = set()
        unique_symptoms = []
        for s in symptoms:
            if s not in seen:
                seen.add(s)
                unique_symptoms.append(s)

        return unique_symptoms if unique_symptoms else ["Symptômes non spécifiés"]
