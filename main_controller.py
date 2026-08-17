"""
main_controller.py

The single entry point for the whole system. Anything that wants
to process a user's message — the API, the Streamlit app, a test
script — should call handle_user_request() from here, rather than
reaching into orchestration/ directly.

This is also the one place that imports both override_layer and
supervisor and wires them together, avoiding a circular import
between those two files.
"""

from __future__ import annotations
import uuid

from core.schemas import CaseState
from orchestration.override_layer import handle_request
from orchestration.supervisor import run_supervisor


def handle_user_request(raw_input: str, session_id: str | None = None) -> CaseState:
    """
    Process one user message end to end:
      override_layer -> (crisis path OR supervisor path) -> logging

    session_id: pass an existing session id to continue a session,
    or leave blank to auto-generate a new one for a fresh request.

    Returns the final CaseState — callers typically care about
    state.final_response for what to show the user, and the other
    fields (crisis_flag, escalation_flag, triage_level, agent_trace)
    for debugging/display purposes.
    """
    if not raw_input or not raw_input.strip():
        raise ValueError("raw_input cannot be empty")

    if session_id is None:
        session_id = str(uuid.uuid4())

    state = handle_request(session_id, raw_input, run_supervisor)
    return state


# Quick manual test when running this file directly:
# python main_controller.py
if __name__ == "__main__":
    print("Emergency Agent — quick manual test")
    print("-" * 50)

    test_message = input("Enter a message to test: ").strip()
    if not test_message:
        test_message = "I've been feeling stressed about work lately"
        print(f"(using default test message: '{test_message}')")

    result_state = handle_user_request(test_message)

    print()
    print("CRISIS FLAG:", result_state.crisis_flag)
    print("ESCALATION FLAG:", result_state.escalation_flag)
    print("TRIAGE LEVEL:", result_state.triage_level)
    print()
    print("FINAL RESPONSE:")
    print(result_state.final_response)
    print()
    print("FULL TRACE:")
    for r in result_state.agent_trace:
        print(f"  - {r.agent_name} | {r.status}")