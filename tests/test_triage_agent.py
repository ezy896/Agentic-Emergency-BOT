import pytest

from agents import triage_agent
from agents.triage_agent import TriageAgent
from core.schemas import AgentStatus, CaseState, TriageLevel


class FakeClient:
    def __init__(self, content):
        self.chat = self
        self.completions = self
        self.content = content

    def create(self, **kwargs):
        message = type("Message", (), {"content": self.content})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


@pytest.mark.parametrize("content", [
    '{"triage_level": null, "reason": "missing classification"}',
    '{"reason": "missing classification"}',
    "",
])
def test_triage_never_leaves_level_null(monkeypatch, content):
    monkeypatch.setattr(triage_agent, "client", FakeClient(content))
    state = CaseState(
        session_id="test-session",
        raw_input="test",
        intake_summary="test summary",
    )

    result = TriageAgent().execute(state)

    assert result.status == AgentStatus.SUCCESS
    assert state.triage_level == TriageLevel.HIGH
    assert result.output["triage_level"] == "high"