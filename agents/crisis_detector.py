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

from core.schemas import (
    CaseState,
    AgentResult,
    AgentStatus,
    SituationCategory,
)
from core.base_agent import BaseAgent
from config.paths import PROMPTS_DIR
from config.settings import (
    GROQ_API_KEY,
    MODEL_NAME,
    CRISIS_CONFIDENCE_THRESHOLD,
)


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


with (PROMPTS_DIR / "crisis_detector_prompt.txt").open(
    encoding="utf-8"
) as f:
    CRISIS_PROMPT = f.read()


client = Groq(api_key=GROQ_API_KEY)


def _keyword_check(text: str) -> bool:
    """Return True when an obvious crisis keyword/phrase is detected."""

    lowered = text.lower()

    return any(
        keyword in lowered
        for keyword in RED_FLAG_KEYWORDS
    )


def _llm_check(text: str) -> tuple[bool, float, str, str]:
    """
    Run the LLM-based crisis classifier.

    Returns:
        (
            crisis_detected,
            confidence,
            reason,
            category,
        )
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=200,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": CRISIS_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)

        detected = bool(
            parsed.get("crisis_detected", False)
        )

        confidence = float(
            parsed.get("confidence", 0.0)
        )

        reason = str(
            parsed.get("reason", "")
        )

        category = str(
            parsed.get("category", "general")
        )

        return (
            detected
            and confidence >= CRISIS_CONFIDENCE_THRESHOLD,
            confidence,
            reason,
            category,
        )

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return (
            False,
            0.0,
            "Failed to parse classifier output — "
            "treated as not crisis",
            "general",
        )


class CrisisDetector(BaseAgent):
    name = "crisis_detector"
    timeout_seconds = 15.0

    def execute(self, state: CaseState) -> AgentResult:
        """
        Detect whether the user's situation is a crisis.

        Keyword matches are handled immediately and safely.
        LLM classification is used for subtler cases.
        """

        text = state.raw_input

        # =====================================================
        # 1. FAST KEYWORD / RULE CHECK
        # =====================================================

        keyword_hit = _keyword_check(text)

        if keyword_hit:
            lowered = text.lower()

            # -------------------------------------------------
            # Determine category for obvious keyword cases
            # -------------------------------------------------

            if "fire" in lowered:
                state.situation_category = (
                    SituationCategory.FIRE
                )

            elif any(
                phrase in lowered
                for phrase in [
                    "kill myself",
                    "end my life",
                    "suicide",
                    "want to die",
                    "hurt myself",
                    "harm myself",
                    "jump off the bridge",
                    "jump off",
                    "took a bunch of pills",
                    "took pills",
                    "overdose",
                ]
            ):
                state.situation_category = (
                    SituationCategory.SELF_HARM
                )

            else:
                state.situation_category = (
                    SituationCategory.GENERAL
                )

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.ESCALATE,
                output={
                    "crisis_detected": True,
                    "situation_category": (
                        state.situation_category.value
                    ),
                },
                confidence=1.0,
                reason="Keyword match",
            )

        # =====================================================
        # 2. LLM-BASED CRISIS CHECK
        # =====================================================

        try:
            (
                llm_hit,
                confidence,
                llm_reason,
                category,
            ) = _llm_check(text)

        except Exception as exc:
            # If the safety classifier fails, escalate rather
            # than silently treating the situation as safe.

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.ESCALATE,
                output={
                    "crisis_detected": True,
                    "detection_uncertain": True,
                },
                confidence=0.0,
                reason=(
                    "Crisis detector encountered an error "
                    f"({type(exc).__name__}: {exc}); "
                    "escalated for human review"
                ),
            )

        # =====================================================
        # 3. STORE LLM-DETECTED CATEGORY
        # =====================================================

        crisis_detected = llm_hit

        try:
            state.situation_category = SituationCategory(
                category
            )

        except ValueError:
            state.situation_category = (
                SituationCategory.GENERAL
            )

        # =====================================================
        # 4. BUILD RESULT REASON
        # =====================================================

        if llm_hit:
            reason = (
                f"LLM flagged: {llm_reason}"
            )
        else:
            reason = "No crisis indicators found"

        # =====================================================
        # 5. RETURN AGENT RESULT
        # =====================================================

        return AgentResult(
            agent_name=self.name,
            status=(
                AgentStatus.ESCALATE
                if crisis_detected
                else AgentStatus.SUCCESS
            ),
            output={
                "crisis_detected": crisis_detected,
                "situation_category": (
                    state.situation_category.value
                ),
            },
            confidence=confidence,
            reason=reason,
        )