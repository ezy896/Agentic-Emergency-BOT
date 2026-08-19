"""
storage/audit_log.py

Append-only audit log for crisis and escalation events.
Every entry written here is permanent — never overwritten or
deleted by the app. This is the record you'd pull for review
or compliance purposes.
"""

import json
from datetime import datetime, timezone

from core.schemas import CaseState
from config.paths import AUDIT_LOG_PATH



def write_audit_entry(state: CaseState) -> None:
    """
    Append one line of JSON to the audit log for any case that
    involved a crisis flag or escalation. Called from logging_agent.
    """
    if not (state.crisis_flag or state.escalation_flag):
        return  # only crisis/escalation cases go in the audit log

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": state.session_id,
        "crisis_flag": state.crisis_flag,
        "crisis_reason": state.crisis_reason,
        "escalation_flag": state.escalation_flag,
        "escalation_reason": state.escalation_reason,
        "triage_level": state.triage_level.value if state.triage_level else None,
        "final_response": state.final_response,
        "agent_trace": [result.model_dump() for result in state.agent_trace],
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")