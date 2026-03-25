import React, { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatInterface({ messages, isLoading, onSend, error }) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-content">
          <h2>Bank of Africa AI Assistant</h2>
          <p className="chat-header-meta">
            Multi-agent banking system powered by Amazon Bedrock
          </p>
        </div>
        <div className="connection-status">
          <span className="status-dot live" />
          <span>Live</span>
        </div>
      </header>

      {/* Messages */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🏦</div>
            <h3>Welcome to Bank of Africa</h3>
            <p>
              I'm your AI banking assistant. I can help you check account
              balances, make transfers, view transaction history, and answer
              questions about our banking products and policies.
            </p>
            <p className="empty-hint">
              Try clicking one of the suggested prompts on the left, or type
              your own question below.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">🏦</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-label">
                  Agents are processing your request...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the Bank of Africa assistant..."
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!input.trim() || isLoading}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
        <p className="input-disclaimer">
          Workshop demo — uses synthetic Nigerian banking data. Not a real
          banking service.
        </p>
      </div>
    </div>
  );
}
