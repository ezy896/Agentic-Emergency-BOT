"""
tests/test_crisis_detector.py

Tests the crisis detector against known red-flag and known-safe
inputs. Because LLM calls are non-deterministic, tests run each
case multiple times and check for CONSISTENCY, not just a single
pass — this is what caught the neighbor-message inconsistency.
"""

import json
import pytest

from core.state import create_case_state
from agents.crisis_detector import CrisisDetector

with open("tests/fixtures/red_flag_examples.json") as f:
    RED_FLAG_EXAMPLES = json.load(f)

with open("tests/fixtures/safe_examples.json") as f:
    SAFE_EXAMPLES = json.load(f)

# How many times to repeat each case, to catch non-determinism
RUNS_PER_CASE = 3


def _run_detector(text: str) -> bool:
    state = create_case_state("test-session", text)
    state = CrisisDetector().run(state)
    result = state.agent_trace[-1]
    return bool(result.output.get("crisis_detected"))


@pytest.mark.parametrize("text", RED_FLAG_EXAMPLES)
def test_red_flags_are_always_caught(text):
    """Every clear red-flag example must be flagged EVERY time — no misses allowed."""
    results = [_run_detector(text) for _ in range(RUNS_PER_CASE)]
    assert all(results), (
        f"MISSED a red flag on some runs: '{text}' -> {results}. "
        f"A false negative here is the most dangerous possible failure."
    )


@pytest.mark.parametrize("text", SAFE_EXAMPLES)
def test_safe_examples_are_consistently_not_flagged(text):
    """
    Safe examples SHOULD not be flagged, but we report inconsistency
    rather than hard-failing, since occasional over-caution here is
    a much smaller problem than a missed red flag.
    """
    results = [_run_detector(text) for _ in range(RUNS_PER_CASE)]
    flagged_count = sum(results)
    if flagged_count > 0:
        print(
            f"\n[INCONSISTENT] '{text}' was flagged {flagged_count}/{RUNS_PER_CASE} times. "
            f"Consider reviewing prompt wording or threshold for this kind of case."
        )
    # Soft assertion: fail only if flagged MORE often than not,
    # which would suggest a real false-positive problem, not noise.
    assert flagged_count <= RUNS_PER_CASE // 2, (
        f"'{text}' was flagged in the majority of runs ({flagged_count}/{RUNS_PER_CASE}) — "
        f"this looks like a real false-positive pattern, not just noise."
    )