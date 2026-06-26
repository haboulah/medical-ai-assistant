# Medical Advice Agent.
"""Agent that provides general medical advice and recommendations."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.prompts.agent_prompts import MEDICAL_ADVICE_PROMPT


class MedicalAdviceAgent(BaseAgent):
    """Agent that provides general health advice.

    Input: Symptoms list and risk level.
    Output: General advice with disclaimer (never a diagnosis).
    """

    def __init__(self):
        """Initialize the Medical Advice Agent."""
        super().__init__("MedicalAdvice")

    def process(self, state: dict) -> dict:
        """Generate medical advice based on symptoms and risk level.

        Args:
            state: Current state containing symptoms and risk assessment.

        Returns:
            State updated with medical advice.

        """
        symptoms = state.get("symptoms", [])
        risk_level = state.get("risk_level", "LOW")
        risk_justification = state.get("risk_justification", "")

        input_text = (
            f"Symptoms: {', '.join(symptoms)}\n"
            f"Risk Level: {risk_level}\n"
            f"Justification: {risk_justification}"
        )

        if self.llm:
            try:
                messages = [
                    SystemMessage(content=MEDICAL_ADVICE_PROMPT),
                    HumanMessage(content=input_text),
                ]
                response = self.llm.invoke(messages)
                result = self._parse_response(response.content)
            except Exception as e:
                result = self._fallback_advice(risk_level, symptoms)
                result["error"] = str(e)
        else:
            result = self._fallback_advice(risk_level, symptoms)

        return {
            **state,
            "medical_advice": result.get("advice", ""),
            "disclaimer": result.get(
                "disclaimer",
                "⚠️ Avertissement : cette application fournit uniquement une aide informative "
                "et ne remplace pas un professionnel de santé.",
            ),
            "advice_output": result,
        }

    def _parse_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {
            "advice": content,
            "disclaimer": "⚠️ Avertissement : cette application fournit uniquement une aide "
            "informative et ne remplace pas un professionnel de santé.",
        }

    @staticmethod
    def _fallback_advice(risk_level: str, symptoms: list[str]) -> dict:
        """Fallback advice when LLM is unavailable."""
        symptom_list = ", ".join(symptoms) if symptoms else "vos symptômes"

        advice_templates = {
            "LOW": (
                f"Surveillez l'évolution de {symptom_list}. "
                "Reposez-vous, hydratez-vous et prenez soin de vous. "
                "Si les symptômes persistent au-delà de 3 jours, "
                "consultez un médecin généraliste."
            ),
            "MEDIUM": (
                f"Compte tenu de {symptom_list}, il est recommandé de "
                "consulter un médecin dans les 24 à 48 heures. "
                "En attendant, reposez-vous et surveillez l'aggravation "
                "de vos symptômes."
            ),
            "HIGH": (
                "⚠️ URGENCE MÉDICALE DÉTECTÉE ⚠️\n\n"
                f"Vos symptômes ({symptom_list}) nécessitent une prise en charge "
                "médicale immédiate.\n"
                "• Appelez immédiatement les urgences (15 en France, 112 dans l'UE)\n"
                "• Ne restez pas seul(e)\n"
                "• Ne conduisez pas vous-même\n"
                "• Gardez votre téléphone à portée de main"
            ),
        }

        return {
            "advice": advice_templates.get(risk_level, advice_templates["LOW"]),
            "disclaimer": "⚠️ Avertissement : cette application fournit uniquement une aide "
            "informative et ne remplace pas un professionnel de santé.",
        }
