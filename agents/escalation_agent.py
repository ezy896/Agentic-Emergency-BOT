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
from core.emergency_lookup import get_emergency_numbers
from config.paths import PROMPTS_DIR
from config.settings import GROQ_API_KEY, MODEL_NAME

with (PROMPTS_DIR / "escalation_prompt.txt").open(encoding="utf-8") as f:
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

        # Fetch real, verified numbers instead of letting the LLM guess.
        emergency_numbers = get_emergency_numbers(state.country)
        print(f"DEBUG — state.country: {state.country!r}, emergency_numbers: {emergency_numbers!r}")

        user_content = (
            f"Situation: {situation}\n"
            f"Reason for escalation: {reason}\n"
            f"User's country: {state.country or 'unknown'}\n"
            f"Verified local emergency numbers (use these exactly, do not "
            f"invent or guess different numbers): {emergency_numbers}"
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": ESCALATION_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            print(
                f"ESCALATION RAW RESPONSE — finish_reason: {response.choices[0].finish_reason}, content: {response.choices[0].message.content!r}")
            escalation_message = (response.choices[0].message.content or "").strip()
            if not escalation_message:
                raise ValueError("Escalation model returned an empty response")
        except Exception as e:
            print(f"ESCALATION AGENT ERROR: {e}")
            escalation_message = (
                f"This situation needs immediate crisis support. Please contact "
                f"{emergency_numbers} or a crisis line now."
            )

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