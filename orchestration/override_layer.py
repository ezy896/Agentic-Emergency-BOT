"""
orchestration/override_layer.py

The hard interrupt. Runs BEFORE the supervisor ever gets control.
Checks for crisis indicators in the raw user input. If found,
routes straight to escalation + logging and returns — the
supervisor and all its tools are never invoked. If clear, hands
control to the supervisor for normal processing.
"""

from __future__ import annotations

from core.schemas import CaseState
from core.state import create_case_state
from agents.crisis_detector import CrisisDetector
from agents.escalation_agent import EscalationAgent
from agents.logging_agent import LoggingAgent


def handle_request(session_id: str, raw_input: str, run_supervisor_fn) -> CaseState:
    """
    Entry point for a new user request.

    run_supervisor_fn: a function that takes a CaseState and returns
    a CaseState, run only on the non-crisis path. Passed in rather
    than imported directly, to avoid a circular import between
    override_layer.py and supervisor.py.
    """
    state = create_case_state(session_id, raw_input)

    # Step 1: crisis check — always runs, no exceptions
    state = CrisisDetector().run(state)
    crisis_result = state.agent_trace[-1]

    if crisis_result.output.get("crisis_detected"):
        # RED FLAG — bypass everything else
        state.crisis_flag = True
        state.crisis_reason = crisis_result.reason
        state = EscalationAgent().run(state)
    # Step 2: clear — hand off to the supervisor for normal processing
    state = run_supervisor_fn(state)

    # Step 3: always log at the end, regardless of what supervisor did
    state = LoggingAgent().run(state)
    return state