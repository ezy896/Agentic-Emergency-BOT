"""
agents/logging_agent.py

Final step of every case, crisis or not. Writes the case to
general storage (case_store) always, and to the audit log
(audit_log) if it involved a crisis or escalation. No LLM call —
this is a pure bookkeeping agent.
"""

from __future__ import annotations

from core.schemas import CaseState, AgentResult, AgentStatus
from core.base_agent import BaseAgent
from storage.case_store import save_case
from storage.audit_log import write_audit_entry


class LoggingAgent(BaseAgent):
    name = "logging_agent"
    timeout_seconds = 10.0

    def execute(self, state: CaseState) -> AgentResult:
        save_case(state)
        write_audit_entry(state)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            output={"logged": True},
        )