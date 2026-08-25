"""
orchestration/override_layer.py

The hard interrupt. Runs BEFORE the supervisor ever gets control.
Checks for crisis indicators in the raw user input. If found,
routes straight to escalation + logging and returns — the
supervisor and all its tools are never invoked. If clear, hands
control to the supervisor for normal processing.
"""

from __future__ import annotations

from core.schemas import CaseState, TriageLevel
from core.state import create_case_state
from agents.crisis_detector import CrisisDetector
from agents.escalation_agent import EscalationAgent
from agents.logging_agent import LoggingAgent


def handle_request(
    session_id: str | CaseState,
    raw_input: str | None = None,
    run_supervisor_fn=None,
    country: str | None = None,
) -> CaseState:
    """
    Entry point for a new user request.

    Accepts either the original separate arguments or an existing
    CaseState as the first argument. The supervisor is imported lazily
    when no function is supplied, avoiding an import cycle.
    """
    if isinstance(session_id, CaseState):
        if raw_input is not None:
            raise TypeError("raw_input must be omitted when passing a CaseState")
        state = session_id
    else:
        if raw_input is None:
            raise TypeError("raw_input is required when passing session_id")
        state = create_case_state(session_id, raw_input, country=country)

    if run_supervisor_fn is None:
        from orchestration.supervisor import run_supervisor

        run_supervisor_fn = run_supervisor

    # Step 1: crisis check — always runs, no exceptions
    state = CrisisDetector().run(state)
    crisis_result = state.agent_trace[-1]

    if crisis_result.output.get("crisis_detected"):
        # RED FLAG — bypass everything else
        state.crisis_flag = True
        state.crisis_reason = crisis_result.reason
        state.triage_level = TriageLevel.HIGH
        state = EscalationAgent().run(state)
        state = LoggingAgent().run(state)
        return state

    # Step 2: clear — hand off to the supervisor for normal processing
    state = run_supervisor_fn(state)

    # Step 3: always log at the end, regardless of what supervisor did
    state = LoggingAgent().run(state)
    return state