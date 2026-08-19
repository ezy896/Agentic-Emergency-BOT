"""
agents/guidance_agent.py

Produces the actual response/advice given to the user, informed
by the intake summary and triage level. This is the core "help"
output for non-crisis cases.
"""

from __future__ import annotations
from groq import Groq

from core.schemas import CaseState, AgentResult, AgentStatus
from core.base_agent import BaseAgent
from config.paths import PROMPTS_DIR
from config.settings import GROQ_API_KEY, MODEL_NAME

with (PROMPTS_DIR / "guidance_prompt.txt").open(encoding="utf-8") as f:
    GUIDANCE_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


class GuidanceAgent(BaseAgent):
    name = "guidance_agent"
    timeout_seconds = 20.0

    def execute(self, state: CaseState) -> AgentResult:
        if not state.intake_summary or not state.triage_level:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILURE,
                reason="Guidance requires both intake_summary and triage_level to be set first",
            )

        user_content = (
            f"Situation summary: {state.intake_summary}\n"
            f"Triage level: {state.triage_level}"
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=300,
            messages=[
                {"role": "system", "content": GUIDANCE_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        guidance_text = response.choices[0].message.content.strip()

        state.guidance_output = guidance_text

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            output={"guidance_output": guidance_text},
        )