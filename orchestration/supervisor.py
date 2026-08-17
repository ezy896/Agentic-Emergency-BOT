"""
orchestration/supervisor.py

The LLM-driven orchestrator. Given a CaseState, repeatedly asks
the LLM which tool to call next (from tool_registry), executes it,
updates state, and re-checks for crisis indicators after every
step. Stops when the LLM decides it's done, or when max turns
is hit.

Includes a deterministic fallback: if the LLM's tool-calling
fails repeatedly in a row (e.g. malformed function-call output),
stop retrying identical requests and fall back to the standard
intake -> triage -> guidance/escalation order directly.
"""

from __future__ import annotations
from groq import Groq

from core.schemas import CaseState, AgentStatus, TriageLevel
from core.state import mark_crisis
from config.settings import GROQ_API_KEY, MODEL_NAME, MAX_SUPERVISOR_TURNS
from orchestration.tool_registry import TOOL_DEFINITIONS, run_tool
from agents.crisis_detector import CrisisDetector
from agents.escalation_agent import EscalationAgent

with open("config/prompts/supervisor_prompt.txt", "r") as f:
    SUPERVISOR_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)

# If the LLM fails to produce a usable tool call this many times
# IN A ROW, stop trusting it and fall back to deterministic order.
MAX_CONSECUTIVE_LLM_FAILURES = 2


def _build_status_message(state: CaseState) -> str:
    lines = [f"Raw input: {state.raw_input}"]
    if state.intake_summary:
        lines.append(f"Intake summary: {state.intake_summary}")
    if state.triage_level:
        lines.append(f"Triage level: {state.triage_level.value}")
    if state.guidance_output:
        lines.append(f"Guidance already produced: {state.guidance_output}")
    if state.escalation_flag:
        lines.append(f"Escalation already triggered: {state.escalation_reason}")
    return "\n".join(lines)


def _recheck_crisis(state: CaseState) -> bool:
    state_copy = CrisisDetector().run(state)
    crisis_result = state_copy.agent_trace[-1]
    if crisis_result.output.get("crisis_detected"):
        mark_crisis(state, crisis_result.reason)
        return True
    return False


def _deterministic_next_tool(state: CaseState) -> str | None:
    """
    Fallback logic when the LLM's tool-calling is unreliable.
    Mirrors the order described in supervisor_prompt.txt, but
    applied directly in code rather than trusting the LLM to
    pick it. Returns None if nothing left to do.
    """
    if not state.intake_summary:
        return "intake_agent"
    if not state.triage_level:
        return "triage_agent"
    if state.triage_level in (TriageLevel.HIGH, TriageLevel.CRITICAL) and not state.escalation_flag:
        return "escalation_agent"
    if not state.guidance_output and not state.escalation_flag:
        return "guidance_agent"
    return None


def run_supervisor(state: CaseState) -> CaseState:
    """
    Main supervisor loop. Called by override_layer.py on the
    non-crisis path.
    """
    consecutive_llm_failures = 0

    while state.turns_used < MAX_SUPERVISOR_TURNS:

        if _recheck_crisis(state):
            state = EscalationAgent().run(state)
            return state

        if state.guidance_output or state.escalation_flag:
            if not state.final_response:
                state.final_response = state.guidance_output
            return state

        # If the LLM has failed too many times in a row, stop asking
        # it and just run the next tool in the standard order directly.
        if consecutive_llm_failures >= MAX_CONSECUTIVE_LLM_FAILURES:
            next_tool = _deterministic_next_tool(state)
            if next_tool is None:
                break
            state = run_tool(next_tool, state)
            consecutive_llm_failures = 0  # reset after a successful direct call
            continue

        status_message = _build_status_message(state)

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                max_tokens=200,
                messages=[
                    {"role": "system", "content": SUPERVISOR_PROMPT},
                    {"role": "user", "content": status_message},
                ],
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
        except Exception:
            consecutive_llm_failures += 1
            state.turns_used += 1
            continue

        message = response.choices[0].message

        if not message.tool_calls:
            if not state.final_response:
                state.final_response = state.guidance_output or "Unable to produce a response."
            return state

        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name

        try:
            state = run_tool(tool_name, state)
            consecutive_llm_failures = 0  # reset on success
        except KeyError:
            consecutive_llm_failures += 1
            state.turns_used += 1
            continue

    if not state.final_response:
        state.final_response = (
            state.guidance_output
            or "We were unable to fully process your request. Please try again "
               "or contact support directly."
        )
    return state