from core.state import create_case_state
from core.schemas import AgentResult, AgentStatus


def test_create_case_state_accepts_single_raw_input_argument():
    state = create_case_state("I am extremely stressed because my boss is threatening to fire me.")
    assert state.session_id
    assert state.raw_input == "I am extremely stressed because my boss is threatening to fire me."


def test_case_state_exposes_latest_agent_result_as_status_and_output():
    state = create_case_state("session-123", "example")
    state.add_result(
        AgentResult(
            agent_name="intake_agent",
            status=AgentStatus.SUCCESS,
            output={"intake_summary": "created summary"},
        )
    )

    assert state.status == AgentStatus.SUCCESS
    assert state.output == {"intake_summary": "created summary"}
