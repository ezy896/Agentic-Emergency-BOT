"""
core/state.py

Helpers for creating and updating CaseState objects.
Agents and orchestration code should go through these
functions rather than mutating CaseState fields directly —
keeps state changes consistent and easy to trace/debug.
"""

import uuid

from core.schemas import CaseState, AgentResult
from core.errors import InvalidStateError


def create_case_state(
    session_id: str | None = None,
    raw_input: str | None = None,
    country: str | None = None,
) -> CaseState:
    """
    Build a brand new CaseState at the very start of a request.

    Supports both legacy usage and the common convenience form:
    create_case_state("user text")
    create_case_state("session-123", "user text")
    """
    if raw_input is None:
        if session_id is None:
            raise InvalidStateError("raw_input is required when creating a CaseState")
        raw_input = session_id
        session_id = None

    if not raw_input or not raw_input.strip():
        raise InvalidStateError("raw_input cannot be empty when creating a CaseState")

    resolved_session_id = session_id or f"session-{uuid.uuid4().hex[:12]}"

    return CaseState(
        session_id=resolved_session_id,
        raw_input=raw_input,
        country=country,
    )


def record_agent_result(state: CaseState, result: AgentResult) -> CaseState:
    """
    Log an agent's result onto the case trace, and bump the
    turn counter. Every agent call — whether from the override
    layer or the supervisor — should pass through here.
    """
    state.add_result(result)
    state.turns_used += 1
    return state


def mark_crisis(state: CaseState, reason: str) -> CaseState:
    """
    Flip the crisis flag. Called by the override layer, and
    also re-checked mid-loop by the supervisor.
    """
    state.crisis_flag = True
    state.crisis_reason = reason
    return state


def mark_escalation(state: CaseState, reason: str) -> CaseState:
    """
    Flip the escalation flag. This can be triggered either by
    a crisis override OR by normal triage/supervisor judgment —
    the reason field is what distinguishes the two later in logs.
    """
    state.escalation_flag = True
    state.escalation_reason = reason
    return state


def set_final_response(state: CaseState, response_text: str) -> CaseState:
    """
    Called at the very end of a case, right before logging_agent
    writes everything to the audit trail.
    """
    state.final_response = response_text
    return state