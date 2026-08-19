"""
agents/resource_agent.py

Looks up relevant emergency numbers based on the user's country
and the classified situation category. Pure lookup, no LLM call —
appends a formatted resource list to guidance/escalation output.
"""

from __future__ import annotations
import json

from core.schemas import CaseState, AgentResult, AgentStatus
from core.base_agent import BaseAgent
from config.paths import EMERGENCY_NUMBERS_PATH

with EMERGENCY_NUMBERS_PATH.open(encoding="utf-8") as f:
    EMERGENCY_NUMBERS = json.load(f)

FALLBACK_MESSAGE = (
    "I don't have verified emergency numbers for your country on file. "
    "Please search '[your country] emergency number' or contact local authorities directly."
)


class ResourceAgent(BaseAgent):
    name = "resource_agent"
    timeout_seconds = 5.0

    def execute(self, state: CaseState) -> AgentResult:
        country = state.country
        category = state.situation_category.value if state.situation_category else "general"

        if not country or country not in EMERGENCY_NUMBERS:
            resource_text = FALLBACK_MESSAGE
        else:
            country_numbers = EMERGENCY_NUMBERS[country]
            number = country_numbers.get(category, country_numbers.get("general"))
            resource_text = f"Relevant number for {country}: {number}"

        state.final_response = (
            (state.final_response or "") + f"\n\n📞 {resource_text}"
        )

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            output={"resource_text": resource_text},
        )