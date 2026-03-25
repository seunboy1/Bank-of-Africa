import { useState } from "react";

export default function Sidebar({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
  showTrace,
  onToggleTrace,
}) {
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const formatDate = (date) => {
    const d = new Date(date);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  const handleMenuToggle = (e, sessionId) => {
    e.stopPropagation();
    setMenuOpenId(menuOpenId === sessionId ? null : sessionId);
  };

  const handleRenameStart = (e, session) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditValue(session.title);
    setMenuOpenId(null);
  };

  const handleRenameSubmit = (e, sessionId) => {
    e.preventDefault();
    if (editValue.trim()) {
      onRenameSession(sessionId, editValue.trim());
    }
    setEditingId(null);
    setEditValue("");
  };

  const handleRenameCancel = () => {
    setEditingId(null);
    setEditValue("");
  };

  const handleDelete = (e, sessionId) => {
    e.stopPropagation();
    setMenuOpenId(null);
    onDeleteSession(sessionId);
  };

  // Close menu when clicking outside
  const handleBackdropClick = () => {
    setMenuOpenId(null);
  };

  return (
    <aside className="sidebar">
      {/* Backdrop to close menu */}
      {menuOpenId && <div className="menu-backdrop" onClick={handleBackdropClick} />}

      {/* Logo & Title */}
      <div className="sidebar-header">
        <div className="logo-mark">
          <span className="logo-icon">🏦</span>
        </div>
        <h1 className="sidebar-title">Bank of Africa</h1>
        <p className="sidebar-subtitle">Agentic AI Banking</p>
      </div>

      {/* New Chat Button */}
      <div className="sidebar-section">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span className="new-chat-icon">+</span>
          New Chat
        </button>
      </div>

      {/* Chat History */}
      <div className="sidebar-section chat-history-section">
        <h3 className="section-heading">Chat History</h3>
        <div className="chat-history-list">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`chat-history-item ${
                session.id === activeSessionId ? "active" : ""
              }`}
              onClick={() => onSelectSession(session.id)}
            >
              <div className="chat-history-content">
                <span className="chat-history-icon">💬</span>
                <div className="chat-history-info">
                  {editingId === session.id ? (
                    <form
                      onSubmit={(e) => handleRenameSubmit(e, session.id)}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="text"
                        className="chat-rename-input"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={handleRenameCancel}
                        onKeyDown={(e) => e.key === "Escape" && handleRenameCancel()}
                        autoFocus
                      />
                    </form>
                  ) : (
                    <>
                      <span className="chat-history-title">{session.title}</span>
                      <span className="chat-history-date">
                        {formatDate(session.createdAt)}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Options Menu Button */}
              <div className="chat-options-wrapper">
                <button
                  className="chat-options-btn"
                  onClick={(e) => handleMenuToggle(e, session.id)}
                  title="Options"
                >
                  ⋮
                </button>

                {/* Dropdown Menu */}
                {menuOpenId === session.id && (
                  <div className="chat-options-menu">
                    <button
                      className="chat-menu-item"
                      onClick={(e) => handleRenameStart(e, session)}
                    >
                      <span className="menu-icon">✏️</span>
                      Rename
                    </button>
                    <button
                      className={`chat-menu-item danger ${sessions.length <= 1 ? "disabled" : ""}`}
                      onClick={(e) => sessions.length > 1 && handleDelete(e, session.id)}
                      disabled={sessions.length <= 1}
                      title={sessions.length <= 1 ? "Cannot delete the only chat" : "Delete chat"}
                    >
                      <span className="menu-icon">🗑️</span>
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="sidebar-footer">
        <button className="control-btn" onClick={onToggleTrace}>
          {showTrace ? "Hide" : "Show"} Agent Trace
        </button>
        <div className="powered-by">
          Powered by Amazon Bedrock
          <br />
          <span className="tech-stack">Claude Sonnet 4 · DynamoDB · Knowledge Bases</span>
        </div>
      </div>
    </aside>
  );
}
