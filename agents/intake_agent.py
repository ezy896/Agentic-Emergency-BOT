"""
agents/intake_agent.py

First step of the normal (non-crisis) flow. Takes the raw user
input and produces a clean, structured summary that later agents
(triage, guidance) will work from instead of re-parsing raw text.
"""

from __future__ import annotations
from groq import Groq

from core.schemas import CaseState, AgentResult, AgentStatus
from core.base_agent import BaseAgent
from config.paths import PROMPTS_DIR
from config.settings import GROQ_API_KEY, MODEL_NAME

with (PROMPTS_DIR / "intake_prompt.txt").open(encoding="utf-8") as f:
    INTAKE_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


class IntakeAgent(BaseAgent):
    name = "intake_agent"
    timeout_seconds = 20.0

    def execute(self, state: CaseState) -> AgentResult:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=250,
            messages=[
                {"role": "system", "content": INTAKE_PROMPT},
                {"role": "user", "content": state.raw_input},
            ],
        )
        summary = response.choices[0].message.content.strip()

        # Write directly onto the shared state so later agents can read it
        state.intake_summary = summary

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            output={"intake_summary": summary},
        )