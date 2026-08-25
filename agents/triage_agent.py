"""
agents/triage_agent.py

Reads the intake summary and assesses severity/urgency,
writing a TriageLevel onto the shared CaseState. Downstream,
this can inform whether guidance alone is enough or whether
escalation should be triggered.
"""

from __future__ import annotations
import json
from groq import Groq

from core.schemas import CaseState, AgentResult, AgentStatus, TriageLevel
from core.base_agent import BaseAgent
from config.paths import PROMPTS_DIR
from config.settings import GROQ_API_KEY, MODEL_NAME

with (PROMPTS_DIR / "triage_prompt.txt").open(encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


class TriageAgent(BaseAgent):
    name = "triage_agent"
    timeout_seconds = 20.0

    def execute(self, state: CaseState) -> AgentResult:
        # Triage works off the CLEAN summary, not raw input —
        # intake must have run first.
        if not state.intake_summary:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILURE,
                reason="No intake_summary found on state — intake_agent must run before triage_agent",
            )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=150,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": TRIAGE_PROMPT},
                {"role": "user", "content": state.intake_summary},
            ],
        )
        try:
            raw_text = response.choices[0].message.content or ""
            parsed = json.loads(raw_text)
            raw_level = parsed.get("triage_level")
            level = TriageLevel(raw_level) if raw_level else TriageLevel.HIGH
            reason = str(parsed.get("reason", ""))
        except (json.JSONDecodeError, ValueError):
            # Fail toward caution, not toward silence — if we can't parse
            # the triage output, treat it as "high" rather than defaulting low.
            level = TriageLevel.HIGH
            reason = "Failed to parse triage output — defaulted to HIGH for caution"

        state.triage_level = level

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            output={"triage_level": level.value},
            reason=reason,
        )