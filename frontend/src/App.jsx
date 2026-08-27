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
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">+</div>
          <div>
            <p className="eyebrow">Emergency response assistant</p>
            <h1>Emergency AI</h1>
            <p>Clear next steps when every second matters.</p>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          <span><strong>System ready</strong><small>Pakistan response network</small></span>
        </div>
      </header>

      <main className="container">
        {/* INPUT */}
        <section className="input-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow accent">Start here</p>
              <h2>How can we help right now?</h2>
            </div>
            <span className="step-label">01 / 02</span>
          </div>

          <p className="description">
            Share the key details in your own words. Include your location,
            immediate danger, and whether anyone is injured.
          </p>

          <form onSubmit={handleSubmit}>
            <label htmlFor="situation">Situation details</label>
            <textarea
              id="situation"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Example: There is a fire in my building and I cannot get out..."
              aria-describedby="input-help"
            />
            <div className="input-meta">
              <span id="input-help">Do not wait for this tool if you are in immediate danger. Contact local emergency services.</span>
              <span>{message.length} characters</span>
            </div>

            <button
              type="submit"
              disabled={!message.trim() || loading}
            >
              {loading ? <><span className="button-spinner" aria-hidden="true"></span>Analyzing situation...</> : <>Analyze situation <span aria-hidden="true">→</span></>}
            </button>
          </form>
        </section>

        {/* ERROR */}
        {error && (
          <div className="error-card" role="alert">
            <strong>We could not complete the analysis</strong>
            {error}
          </div>
        )}

        {/* RESULTS */}
        {response && (
          <section className="results">
            <div className="section-heading results-heading">
              <div>
                <p className="eyebrow accent">Assessment complete</p>
                <h2>Situation analysis</h2>
              </div>
              <span className="step-label">02 / 02</span>
            </div>

            <div className="status-grid">
              <div className={`info-card ${response.crisis_flag ? "critical" : "clear"}`}>
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

              <div className={`info-card ${response.escalation_flag ? "critical" : "clear"}`}>
                <span>Escalation</span>
                <strong>
                  {response.escalation_flag ? "YES" : "NO"}
                </strong>
              </div>
            </div>

            {/* FINAL RESPONSE */}
            <div className="response-card">
              <div className="card-title-row"><h3>Emergency guidance</h3><span className="live-label">PRIORITY</span></div>

              <p>{response.final_response}</p>
            </div>

            {/* AGENT TRACE */}
           {/* AGENT TRACE */}
<div className="trace-card">
  <div className="card-title-row"><h3>Agent execution trace</h3><span className="trace-count">{response.agent_trace?.length || 0} steps</span></div>

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