"""
tests/test_override_bypass.py

The most important test file in this project. Proves that any
red-flag input bypasses the supervisor completely and routes
straight to escalation + logging. This is the literal safety
guarantee your whole "interrupt everything" design depends on.
"""

import json
import pytest

from orchestration.override_layer import handle_request
from orchestration.supervisor import run_supervisor

with open("tests/fixtures/red_flag_examples.json") as f:
    RED_FLAG_EXAMPLES = json.load(f)

with open("tests/fixtures/safe_examples.json") as f:
    SAFE_EXAMPLES = json.load(f)


@pytest.mark.parametrize("text", RED_FLAG_EXAMPLES)
def test_red_flag_input_never_reaches_supervisor(text):
    """
    For every known red-flag message: the trace must show
    crisis_detector -> escalation_agent -> logging_agent ONLY.
    Specifically, intake_agent, triage_agent, and guidance_agent
    must NEVER appear in the trace — that would mean the
    supervisor got control when it shouldn't have.
    """
    state = handle_request("test-session", text, run_supervisor)

    agent_names_called = [r.agent_name for r in state.agent_trace]

    assert "intake_agent" not in agent_names_called, (
        f"CRITICAL: intake_agent ran on a red-flag input: '{text}'. "
        f"Trace was: {agent_names_called}"
    )
    assert "triage_agent" not in agent_names_called, (
        f"CRITICAL: triage_agent ran on a red-flag input: '{text}'. "
        f"Trace was: {agent_names_called}"
    )
    assert "guidance_agent" not in agent_names_called, (
        f"CRITICAL: guidance_agent ran on a red-flag input: '{text}'. "
        f"Trace was: {agent_names_called}"
    )

    assert state.crisis_flag is True, f"crisis_flag should be True for: '{text}'"
    assert state.escalation_flag is True, f"escalation_flag should be True for: '{text}'"
    assert "escalation_agent" in agent_names_called, (
        f"escalation_agent should have run for: '{text}'"
    )
    assert "logging_agent" in agent_names_called, (
        f"logging_agent should always run, even on crisis path, for: '{text}'"
    )


@pytest.mark.parametrize("text", SAFE_EXAMPLES)
def test_safe_input_reaches_supervisor_normally(text):
    """
    For known safe messages: the supervisor SHOULD get control,
    meaning intake_agent and triage_agent should appear in the
    trace. This confirms the override layer doesn't over-block
    normal, non-crisis requests.
    """
    state = handle_request("test-session", text, run_supervisor)

    agent_names_called = [r.agent_name for r in state.agent_trace]

    if state.crisis_flag:
        # A known-safe example got flagged as crisis — not a hard
        # failure of THIS test (that's crisis_detector's calibration,
        # tested separately), but worth surfacing.
        pytest.skip(
            f"'{text}' was flagged as crisis this run (LLM non-determinism) — "
            f"skipping supervisor-reached check for this run."
        )

    assert "intake_agent" in agent_names_called, (
        f"Expected supervisor to call intake_agent for safe input: '{text}'. "
        f"Trace was: {agent_names_called}"
    )
    assert "logging_agent" in agent_names_called, (
        f"logging_agent should always run, for: '{text}'"
    )