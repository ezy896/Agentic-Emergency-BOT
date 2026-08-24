"""FastAPI adapter for the shared emergency-support workflow."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main_controller import handle_user_request


app = FastAPI(title="Agentic Emergency Support API")


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    """Input accepted by the process endpoint."""

    raw_input: str = Field(min_length=1)
    session_id: str | None = None
    country: str | None = None


class ProcessResponse(BaseModel):
    """Stable public response shape for API callers."""

    session_id: str
    final_response: str | None

    crisis_flag: bool
    escalation_flag: bool

    situation_category: str | None
    triage_level: str | None

    turns_used: int
    agent_trace: list[dict]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
def process_request(request: ProcessRequest) -> ProcessResponse:

    state = handle_user_request(
        raw_input=request.raw_input,
        session_id=request.session_id,
        country=request.country,
    )

    return ProcessResponse(
        session_id=state.session_id,
        final_response=state.final_response,

        crisis_flag=state.crisis_flag,
        escalation_flag=state.escalation_flag,

        situation_category=(
            state.situation_category.value
            if state.situation_category
            else None
        ),

        triage_level=(
            state.triage_level.value
            if state.triage_level
            else None
        ),

        turns_used=state.turns_used,

        agent_trace=[
            result.model_dump()
            for result in state.agent_trace
        ],
    )