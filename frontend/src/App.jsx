import { useState } from "react";
import "./App.css";
import { processEmergency } from "./api";

function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!message.trim()) return;

    setLoading(true);
    setError("");
    setResponse(null);

    try {
     const data = await processEmergency({
  raw_input: message,
  session_id: sessionId,
  country: "Pakistan",
});

      console.log("Backend response:", data);

      setResponse(data);
    } catch (err) {
      console.error("API Error:", err);

      setError(
        err.response?.data?.detail ||
          "Could not connect to the Emergency AI backend."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Emergency AI</h1>
          <p>Agentic Emergency Guidance System</p>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Ready
        </div>
      </header>

      <main className="container">
        {/* INPUT */}
        <section className="input-card">
          <h2>Describe Your Situation</h2>

          <p className="description">
            Tell the system what is happening. Emergency AI will analyze your
            situation and determine the appropriate response.
          </p>

          <form onSubmit={handleSubmit}>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Example: There is a fire in my building and I cannot get out..."
            />

            <button
              type="submit"
              disabled={!message.trim() || loading}
            >
              {loading ? "Analyzing..." : "Analyze Situation"}
            </button>
          </form>
        </section>

        {/* ERROR */}
        {error && (
          <div className="error-card">
            {error}
          </div>
        )}

        {/* RESULTS */}
        {response && (
          <section className="results">
            <h2>Situation Analysis</h2>

            <div className="status-grid">
              <div className="info-card">
                <span>Crisis Status</span>
                <strong>
                  {response.crisis_flag
                    ? "CRISIS DETECTED"
                    : "NO CRISIS"}
                </strong>
              </div>

              <div className="info-card">
                <span>Situation</span>
                <strong>
                  {response.situation_category || "General"}
                </strong>
              </div>

              <div className="info-card">
                <span>Triage</span>
                <strong>
                  {response.triage_level || "N/A"}
                </strong>
              </div>

              <div className="info-card">
                <span>Escalation</span>
                <strong>
                  {response.escalation_flag ? "YES" : "NO"}
                </strong>
              </div>
            </div>

            {/* FINAL RESPONSE */}
            <div className="response-card">
              <h3>Emergency Guidance</h3>

              <p>{response.final_response}</p>
            </div>

            {/* AGENT TRACE */}
           {/* AGENT TRACE */}
<div className="trace-card">
  <h3>Agent Execution Trace</h3>

  {!response.agent_trace ||
  response.agent_trace.length === 0 ? (
    <p className="empty">
      No agent trace available.
    </p>
  ) : (
    response.agent_trace.map((agent, index) => (
      <div className="trace-item" key={index}>
        <div className="trace-content">
          <div className="trace-header">
            <strong>
              {agent.agent_name || "Unknown Agent"}
            </strong>

            <span className="trace-status">
              {agent.status || "unknown"}
            </span>
          </div>

          {agent.reason && (
            <p className="trace-reason">
              {agent.reason}
            </p>
          )}

          {agent.confidence !== undefined &&
            agent.confidence !== null && (
              <p className="trace-confidence">
                Confidence:{" "}
                {(agent.confidence * 100).toFixed(1)}%
              </p>
            )}

          {agent.output &&
            Object.keys(agent.output).length > 0 && (
              <details className="trace-output">
                <summary>Agent Output</summary>

                <pre>
                  {JSON.stringify(
                    agent.output,
                    null,
                    2
                  )}
                </pre>
              </details>
            )}
        </div>
      </div>
    ))
  )}
</div>

            {/* SESSION ID */}
            {response.session_id && (
              <div className="turns">
                Session ID: {response.session_id}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;