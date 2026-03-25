import React from "react";

export default function AgentTrace({ traces }) {
  if (!traces || traces.length === 0) return null;

  const getTraceIcon = (type) => {
    switch (type) {
      case "thinking":
        return "🧠";
      case "reasoning":
        return "💭";
      case "action":
        return "⚡";
      case "result":
        return "✅";
      default:
        return "📍";
    }
  };

  const getTraceLabel = (type) => {
    switch (type) {
      case "thinking":
        return "Thinking";
      case "reasoning":
        return "Reasoning";
      case "action":
        return "Agent Action";
      case "result":
        return "Result";
      default:
        return "Trace";
    }
  };

  return (
    <div className="trace-container">
      <div className="trace-header">
        <h3>🔍 Agent Trace</h3>
        <p className="trace-subtitle">
          Watch the Supervisor Agent reason and delegate
        </p>
      </div>
      <div className="trace-timeline">
        {traces.map((trace, i) => (
          <div key={i} className={`trace-item trace-${trace.type}`}>
            <div className="trace-connector">
              <div className="trace-dot">{getTraceIcon(trace.type)}</div>
              {i < traces.length - 1 && <div className="trace-line" />}
            </div>
            <div className="trace-body">
              <span className="trace-label">{getTraceLabel(trace.type)}</span>
              {trace.text && <p className="trace-text">{trace.text}</p>}
              {trace.agent && (
                <div className="trace-agent-badge">
                  <span className="trace-agent-icon">🤖</span>
                  <span>
                    Delegated to: <strong>{trace.agent}</strong>
                  </span>
                  {trace.function && (
                    <span className="trace-fn"> → {trace.function}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
