# Agentic Emergency Support Bot

An emergency-support workflow with a Streamlit chat interface, a FastAPI
endpoint, a safety-first crisis override, and specialist agents for intake,
triage, guidance, escalation, resources, and logging.

## Setup

Use Python 3.11 or newer and create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

## Run

Start the Streamlit interface:

```powershell
streamlit run streamlit_app.py
```

Start the API:

```powershell
python -m uvicorn api.server:app --reload
```

The API exposes `GET /health` and `POST /process`.

## Test

```powershell
python -m pytest -q
```

The crisis detector runs before the supervisor. Red-flag input bypasses the
normal intake/triage/guidance path and goes directly to escalation and logging.
The application is a support tool, not a substitute for emergency services.
