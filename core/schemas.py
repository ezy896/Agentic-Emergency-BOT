"""
core/schemas.py

Defines the data contracts used across the whole system.
Every agent reads/writes data shaped like these models.
Using Pydantic means data gets validated automatically —
if an agent tries to return something malformed, it fails
loudly instead of silently corrupting the pipeline.
"""

from  __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums — fixed sets of allowed values
# ---------------------------------------------------------------------------

class TriageLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ESCALATE = "escalate"

# ---------------------------------------------------------------------------
# Input coming from the user
# ---------------------------------------------------------------------------

class UserInput(BaseModel):
    session_id: str
    raw_text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Standard return shape every agent must produce
# ---------------------------------------------------------------------------

class AgentResult(BaseModel):
    agent_name: str
    status: AgentStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    reason: Optional[str] = None


class SituationCategory(str, Enum):
    SELF_HARM = "self_harm"
    DOMESTIC_VIOLENCE = "domestic_violence"
    MEDICAL = "medical"
    FIRE = "fire"
    CRIME_DANGER = "crime_danger"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# The shared object that flows through every agent / tool call.
# This is what makes agents reusable both in a fixed pipeline
# and as tools the supervisor calls in any order.
# ---------------------------------------------------------------------------

class CaseState(BaseModel):
    session_id: str
    raw_input: str
    country: Optional[str] = None

    # crisis / override tracking
    crisis_flag: bool = False
    crisis_reason: Optional[str] = None
    situation_category: Optional[SituationCategory] = None

    # results accumulated as agents run
    intake_summary: Optional[str] = None
    triage_level: Optional[TriageLevel] = None
    guidance_output: Optional[str] = None
    escalation_flag: bool = False
    escalation_reason: Optional[str] = None

    # full history of what happened, for logging/audit
    agent_trace: List[AgentResult] = Field(default_factory=list)

    # supervisor bookkeeping
    turns_used: int = 0
    final_response: Optional[str] = None

    @property
    def latest_result(self) -> Optional[AgentResult]:
        return self.agent_trace[-1] if self.agent_trace else None

    @property
    def status(self) -> Optional[AgentStatus]:
        result = self.latest_result
        return result.status if result else None

    @property
    def output(self) -> Dict[str, Any]:
        result = self.latest_result
        return result.output if result else {}

    def add_result(self, result: AgentResult) -> None:
        """Append an agent's result to the trace — call this from every agent."""
        self.agent_trace.append(result)