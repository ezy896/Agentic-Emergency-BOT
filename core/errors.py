"""
core/errors.py

Custom exceptions used across the system, so error handling
can be specific instead of catching generic Exception everywhere.
"""


class CrisisDetectedException(Exception):
    """Raised (optionally) when a red flag is detected — used
    if you want crisis handling to short-circuit via an exception
    rather than just a flag check. Optional to use."""
    pass


class AgentTimeoutError(Exception):
    """Raised when an agent's LLM call takes too long or hangs."""
    pass


class InvalidStateError(Exception):
    """Raised when a CaseState is malformed or missing required data."""
    pass


class MaxTurnsExceededError(Exception):
    """Raised when the supervisor loop hits its max tool-call limit
    without reaching a final response — prevents infinite loops."""
    pass