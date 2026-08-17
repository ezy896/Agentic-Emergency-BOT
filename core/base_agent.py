"""
core/base_agent.py

Abstract base class every agent inherits from. Guarantees every
agent has the same interface (run(state) -> state), and handles
shared concerns — timing, error handling, and writing results
onto the CaseState trace — in one place instead of repeating
that logic in every single agent file.
"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod

from core.schemas import CaseState, AgentResult, AgentStatus
from core.state import record_agent_result
from core.errors import AgentTimeoutError


class BaseAgent(ABC):
    # Every subclass must set this — used in logs/tool registry
    name: str = "base_agent"

    # Optional per-agent timeout in seconds
    timeout_seconds: float = 30.0

    @abstractmethod
    def execute(self, state: CaseState) -> AgentResult:
        """
        Subclasses implement THIS method with their actual logic
        (calling an LLM, running a classifier, etc.) and must
        return an AgentResult. Do not call this directly —
        call run() instead, which wraps this with error handling.
        """
        raise NotImplementedError

    def run(self, state: CaseState) -> CaseState:
        """
        Public entrypoint every orchestrator/tool_registry calls.
        Wraps execute() with timing + error handling, then logs
        the result onto the shared CaseState.
        """
        start = time.time()
        try:
            result = self.execute(state)
        except Exception as exc:
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILURE,
                reason=f"{type(exc).__name__}: {exc}",
            )

        elapsed = time.time() - start
        if elapsed > self.timeout_seconds:
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILURE,
                reason=f"Agent exceeded timeout of {self.timeout_seconds}s",
            )

        state = record_agent_result(state, result)
        return state