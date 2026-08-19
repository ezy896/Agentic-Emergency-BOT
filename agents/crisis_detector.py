"""
agents/crisis_detector.py

Safety-critical gate. Runs before anything else touches the
user's input. Combines two layers:
  1. Fast keyword/rule check — catches obvious cases instantly,
     no API call needed.
  2. LLM-based check — catches subtler, indirect language that
     keywords would miss.
If EITHER layer flags it, the case is treated as a crisis.
"""

from __future__ import annotations
import json

from groq import Groq

from core.schemas import CaseState, AgentResult, AgentStatus, SituationCategory
from core.base_agent import BaseAgent
from config.paths import PROMPTS_DIR
from config.settings import GROQ_API_KEY, MODEL_NAME, CRISIS_CONFIDENCE_THRESHOLD

RED_FLAG_KEYWORDS = [
    "kill myself",
    "end my life",
    "suicide",
    "want to die",
    "hurt myself",
    "harm myself",
    "jump off the bridge",
    "jump off",
    "don't want to be here anymore",
    "do not want to be here anymore",
    "can't take this anymore",
    "can\'t take this anymore",
    "i just took a bunch of pills",
    "took a bunch of pills",
    "took pills",
    "overdose",
    "kill me",
    "fire in my building",
    "fire in the building",
    "going to kill me",
    "i'm going to kill myself",
    "i want to kill myself",
    "i want to end my life",
    "i'm going to end my life",
    "i'm going to jump off",
    "going to jump off",
    "not want to be here anymore",
]

with (PROMPTS_DIR / "crisis_detector_prompt.txt").open(encoding="utf-8") as f:
    CRISIS_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


def _keyword_check(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in RED_FLAG_KEYWORDS)


def _llm_check(text: str) -> tuple[bool, float, str, str]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=200,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": CRISIS_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
        detected = bool(parsed.get("crisis_detected", False))
        confidence = float(parsed.get("confidence", 0.0))
        reason = str(parsed.get("reason", ""))
        category = str(parsed.get("category", "general"))
        return detected and confidence >= CRISIS_CONFIDENCE_THRESHOLD, confidence, reason, category
    except (json.JSONDecodeError, ValueError, TypeError):
        return False, 0.0, "Failed to parse classifier output — treated as not crisis", "general"


class CrisisDetector(BaseAgent):
    name = "crisis_detector"
    timeout_seconds = 15.0

    def execute(self, state: CaseState) -> AgentResult:
        text = state.raw_input
        try:
            keyword_hit = _keyword_check(text)
            llm_hit, confidence, llm_reason, category = _llm_check(text)
        except Exception as exc:
            fallback_detected = _keyword_check(text)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.ESCALATE if fallback_detected else AgentStatus.SUCCESS,
                output={"crisis_detected": fallback_detected},
                confidence=1.0 if fallback_detected else 0.0,
                reason=(
                    f"Crisis detector encountered an error ({type(exc).__name__}: {exc})"
                    f"; fallback used keyword-only check"
                ),
            )
        crisis_detected = keyword_hit or llm_hit
        try:
            state.situation_category = SituationCategory(category)
        except ValueError:
            state.situation_category = SituationCategory.GENERAL

        if keyword_hit and llm_hit:
            reason = f"Keyword match AND LLM flagged: {llm_reason}"
        elif keyword_hit:
            reason = "Keyword match"
        elif llm_hit:
            reason = f"LLM flagged: {llm_reason}"
        else:
            reason = "No crisis indicators found"

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.ESCALATE if crisis_detected else AgentStatus.SUCCESS,
            output={"crisis_detected": crisis_detected},
            confidence=confidence,
            reason=reason,
        )