"""
orchestration/tool_registry.py

Wraps each agent as a "tool" the supervisor's LLM can call via
function-calling. Two things live here:
  1. TOOL_DEFINITIONS — the schema describing each tool, in the
     format Groq's (OpenAI-compatible) function-calling API expects.
  2. AGENT_MAP — maps a tool name back to the actual agent instance,
     so the supervisor can execute whichever tool the LLM picks.
"""

from __future__ import annotations

from core.schemas import CaseState
from agents.intake_agent import IntakeAgent
from agents.triage_agent import TriageAgent
from agents.guidance_agent import GuidanceAgent
from agents.escalation_agent import EscalationAgent


# Maps tool name -> agent instance. The supervisor looks up and
# runs the agent by this name after the LLM picks a tool call.
AGENT_MAP = {
    "intake_agent": IntakeAgent(),
    "triage_agent": TriageAgent(),
    "guidance_agent": GuidanceAgent(),
    "escalation_agent": EscalationAgent(),
}


# Tool schemas in OpenAI/Groq function-calling format. Each tool
# takes no arguments beyond the implicit CaseState — the supervisor
# passes state directly when executing, the LLM just picks WHICH
# tool to call next based on the descriptions below.
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "intake_agent",
            "description": (
                "Summarizes the user's raw message into a clean, structured "
                "summary. Should usually be called FIRST, before triage or "
                "guidance, since those work off the summary rather than raw text."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "triage_agent",
            "description": (
                "Assesses the severity/urgency of the situation (low, medium, "
                "high, critical). Requires intake_agent to have run first."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "guidance_agent",
            "description": (
                "Produces the actual advice/response for the user. Requires "
                "both intake_agent and triage_agent to have run first."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalation_agent",
            "description": (
                "Escalates the case for urgent human attention. Call this "
                "ONLY if triage_level came back as 'high' or 'critical', or "
                "if something in the conversation suggests the situation is "
                "more serious than initially thought."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def run_tool(tool_name: str, state: CaseState) -> CaseState:
    """
    Executes the agent mapped to tool_name, updating and returning
    the CaseState. Raises KeyError if the LLM hallucinates a tool
    name that doesn't exist — caller should handle that.
    """
    if tool_name not in AGENT_MAP:
        raise KeyError(f"Unknown tool name: {tool_name}")

    agent = AGENT_MAP[tool_name]
    return agent.run(state)