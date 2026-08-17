"""
agents/escalation_agent.py

Handles escalation — called from TWO different places:
  1. The override_layer, when the crisis_detector flags a red flag
     (unconditional, bypasses the rest of the pipeline entirely)
  2. The supervisor, when normal triage/judgment decides escalation
     is warranted (conditional, part of normal flow)

Behaves identically either way — the `reason` field on CaseState
is what distinguishes crisis-triggered vs. judgment-triggered
escalation later in the audit log.
"""

from __future__ import annotations
from groq import Groq

from core.schemas import CaseState, AgentResult, AgentStatus
from core.base_agent import BaseAgent
from core.state import mark_escalation
from config.settings import GROQ_API_KEY, MODEL_NAME

with open("config/prompts/escalation_prompt.txt", "r") as f:
    ESCALATION_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


class EscalationAgent(BaseAgent):
    name = "escalation_agent"
    timeout_seconds = 20.0

    def execute(self, state: CaseState) -> AgentResult:
        # Escalation reason may already be set (e.g. crisis_reason from
        # the override layer) — fall back to a generic reason if not.
        reason = state.crisis_reason or state.escalation_reason or "Escalation triggered by system judgment"

        situation = state.intake_summary or state.raw_input

        user_content = (
            f"Situation: {situation}\n"
            f"Reason for escalation: {reason}"
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=200,
            messages=[
                {"role": "system", "content": ESCALATION_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        escalation_message = response.choices[0].message.content.strip()

        # Formally flip the escalation flag on state, using the
        # shared helper from core/state.py for consistency.
        mark_escalation(state, reason)
        state.final_response = escalation_message

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.ESCALATE,
            output={"escalation_message": escalation_message},
            reason=reason,
        )