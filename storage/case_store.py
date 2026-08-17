"""
storage/case_store.py

Stores a record of every case (crisis or not) for general
record-keeping and debugging. Separate from audit_log.py,
which is specifically the permanent crisis/escalation trail.
"""

import json
import os
from datetime import datetime

from core.schemas import CaseState

CASE_STORE_PATH = "storage/case_log.jsonl"


def save_case(state: CaseState) -> None:
    """
    Append a record of the completed case. Called from logging_agent
    for every case, regardless of crisis/escalation status.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": state.session_id,
        "raw_input": state.raw_input,
        "crisis_flag": state.crisis_flag,
        "escalation_flag": state.escalation_flag,
        "triage_level": state.triage_level.value if state.triage_level else None,
        "final_response": state.final_response,
        "turns_used": state.turns_used,
        "agent_trace": [result.model_dump() for result in state.agent_trace],
    }

    os.makedirs(os.path.dirname(CASE_STORE_PATH), exist_ok=True)
    with open(CASE_STORE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")