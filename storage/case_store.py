"""
storage/case_store.py

Stores a record of every case (crisis or not) for general
record-keeping and debugging. Separate from audit_log.py,
which is specifically the permanent crisis/escalation trail.
"""

import json
from datetime import datetime, timezone

from core.schemas import CaseState
from config.paths import CASE_LOG_PATH


def save_case(state: CaseState) -> None:
    """
    Append a record of the completed case. Called from logging_agent
    for every case, regardless of crisis/escalation status.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": state.session_id,
        "raw_input": state.raw_input,
        "crisis_flag": state.crisis_flag,
        "escalation_flag": state.escalation_flag,
        "triage_level": state.triage_level.value if state.triage_level else None,
        "final_response": state.final_response,
        "turns_used": state.turns_used,
        "agent_trace": [result.model_dump() for result in state.agent_trace],
    }

    CASE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CASE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")