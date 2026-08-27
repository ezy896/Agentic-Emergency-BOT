# Agentic Emergency Support Bot

An emergency-support application with a React frontend and a FastAPI backend.
The backend coordinates specialist agents for intake, triage, guidance,
escalation, emergency-resource lookup, and audit logging.

The system is designed around a safety-first crisis override: red-flag input is
detected before normal supervisor processing and is routed directly to
escalation and logging.

> **Important:** This application is a support tool, not a substitute for local
> emergency services. If someone is in immediate danger, contact the relevant
> emergency service first.

## Features

- React interface for describing an emergency or concerning situation.
- FastAPI endpoint for processing requests and returning a stable JSON response.
- Early crisis detection before supervisor-controlled agent execution.
- Specialist agents for intake, triage, guidance, escalation, resources, and logging.
- Country-aware emergency-number lookup, with Pakistan supported by default in
  the current frontend.
- Session IDs for associating related requests.
- Agent execution trace with status, reason, confidence, and structured output.
- JSONL case and audit logs stored under `storage/`.
- Automated tests for crisis detection, routing, triage behavior, resources,
  state compatibility, and supervisor behavior.

## Architecture

The application has two separately started processes:

```text
React + Vite frontend
				|
				| POST /process
				v
FastAPI adapter (api/server.py)
				|
				v
main_controller.handle_user_request()
				|
				v
override_layer
	 |                 |
	 | crisis          | normal
	 v                 v
escalation       supervisor
	 |                 |
	 +--------+--------+
						v
			 logging + response
```

### Request flow

1. The user enters a description in the React interface.
2. The frontend sends the text, optional session ID, and country to `POST /process`.
3. `main_controller.py` creates or reuses a session and passes the request to
   the override layer.
4. The crisis detector runs first.
5. Crisis input bypasses the normal supervisor path and is sent to escalation
   and logging.
6. Non-crisis input continues through the supervisor and specialist agents.
7. The API returns the final guidance, classification flags, triage level,
   session ID, turn count, and agent trace.

## Project Structure

```text
agents/                 Specialist agent implementations
api/server.py           FastAPI application and HTTP contracts
config/                 Runtime settings and prompt files
core/                   Shared schemas, state, errors, and lookup logic
frontend/               React + Vite user interface
orchestration/          Crisis override, supervisor, and tool registry
storage/                Emergency numbers and JSONL case/audit logs
tests/                  Automated backend tests and fixtures
main_controller.py      Shared application entry point
requirements.txt        Python dependencies
```

## Requirements

- Python 3.11 or newer
- Node.js and npm
- A Groq API key
- PowerShell on Windows, or equivalent shell commands on another platform

## Installation

### 1. Create and activate the Python environment

From the project root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution for the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure the API key

Create a `.env` file in the project root. Do not commit real credentials.

```text
GROQ_API_KEY=your_groq_api_key
```

Optional model configuration:

```text
MODEL_NAME=llama-3.3-70b-versatile
```

The backend loads values from `.env` or normal environment variables. The
application fails during startup when `GROQ_API_KEY` is not configured.

### 4. Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

## Running Locally

Use two terminals from the project root.

### Terminal 1: start the FastAPI backend

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
```

The backend is available at `http://127.0.0.1:8000`.

Useful backend URLs:

- Health check: `http://127.0.0.1:8000/health`
- Interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`
- Alternative API documentation: `http://127.0.0.1:8000/redoc`

### Terminal 2: start the React frontend

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

The frontend currently sends requests to `http://127.0.0.1:8000` as configured
in `frontend/src/api.js`. The FastAPI CORS configuration allows local
`localhost` and `127.0.0.1` development origins.

## Frontend Commands

Run these commands from `frontend/`:

```powershell
# Start the Vite development server
npm run dev

# Type-check and create a production build
npm run build

# Preview the production build locally
npm run preview
```

## API Reference

### `GET /health`

Confirms that the backend is running.

Response:

```json
{
  "status": "ok"
}
```

### `POST /process`

Processes one emergency-support request.

Request body:

```json
{
  "raw_input": "I am feeling dizzy and weak",
  "session_id": null,
  "country": "Pakistan"
}
```

Fields:

| Field        | Type             | Required | Description                                                |
| ------------ | ---------------- | -------- | ---------------------------------------------------------- |
| `raw_input`  | string           | Yes      | User's situation description. Must not be empty.           |
| `session_id` | string or `null` | No       | Existing session to continue, or `null` for a new session. |
| `country`    | string or `null` | No       | Country used for emergency-resource lookup.                |

Response shape:

```json
{
  "session_id": "generated-session-id",
  "final_response": "Guidance returned by the workflow",
  "crisis_flag": false,
  "escalation_flag": false,
  "situation_category": "medical",
  "triage_level": "medium",
  "turns_used": 3,
  "agent_trace": []
}
```

The `agent_trace` array contains the agents that ran during the request. Each
trace item may include `agent_name`, `status`, `output`, `confidence`, and
`reason`.

Example PowerShell request:

```powershell
$body = @{
		raw_input = "There is smoke in the kitchen and I cannot find the exit"
		session_id = $null
		country = "Pakistan"
} | ConvertTo-Json

Invoke-RestMethod `
		-Uri "http://127.0.0.1:8000/process" `
		-Method Post `
		-ContentType "application/json" `
		-Body $body
```

## Testing

Run the backend test suite from the project root with the virtual environment
activated:

```powershell
python -m pytest -q
```

The tests cover:

- Red-flag detection against emergency examples.
- Supervisor bypass for crisis input.
- Normal supervisor routing for safe input.
- Triage fallback behavior when model output is incomplete.
- Emergency-resource lookup behavior.
- Linear pipeline execution.
- Case-state compatibility and supervisor behavior.

The agent tests may call the configured model provider unless a test replaces
the client with a fake. Keep the API key available when running tests that use
the live agent implementations.

## Troubleshooting

### `Could not connect to the Emergency AI backend`

Make sure the FastAPI process is running and listening on port `8000`:

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/health").Content
```

Expected output:

```json
{ "status": "ok" }
```

If the check fails, start the backend from the project root with:

```powershell
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
```

### Backend exits during startup

Check that the virtual environment is active and `GROQ_API_KEY` exists in the
root `.env` file. The key must not be wrapped in extra quotes or left as the
placeholder value.

### Frontend cannot load `App.css`

Run the frontend commands from the `frontend/` directory and confirm that
`frontend/src/App.css` exists. Reinstalling dependencies is usually not needed
for a missing source-file error.

### Port `8000` is already in use

Either stop the process using the port or start the backend on another port:

```powershell
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8001
```

If you change the backend port, update `baseURL` in `frontend/src/api.js` to
the same port.

## Data and Privacy

The backend writes case and audit information to JSONL files in `storage/`.
Review the storage and retention approach before using the application with
real personal or medical information. Do not commit `.env` files, API keys,
or sensitive logs to source control.

## Safety Notes

- The application does not replace trained emergency responders or medical
  professionals.
- Model output should be treated as assistance, not authoritative diagnosis
  or dispatch.
- For immediate danger, contact local emergency services without waiting for
  the application to respond.
- The crisis override is intentionally prioritized over the normal supervisor
  workflow.
