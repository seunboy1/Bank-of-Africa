import React from "react";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const isError = message.isError;

  // Simple markdown-ish formatting: detect numbered lists, bullets, bold
  const formatContent = (text) => {
    if (!text) return null;

    const lines = text.split("\n");
    return lines.map((line, i) => {
      // Bold: **text**
      let formatted = line.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
      );

      // NGN highlighting
      formatted = formatted.replace(
        /(NGN\s[\d,]+\.?\d*)/g,
        '<span class="currency">$1</span>'
      );

      // Numbered items
      if (/^\d+\./.test(line.trim())) {
        return (
          <div
            key={i}
            className="msg-list-item"
            dangerouslySetInnerHTML={{ __html: formatted }}
          />
        );
      }

      // Bullet items
      if (/^\s*[-•]/.test(line)) {
        return (
          <div
            key={i}
            className="msg-bullet-item"
            dangerouslySetInnerHTML={{ __html: formatted }}
          />
        );
      }

      // Empty line = paragraph break
      if (line.trim() === "") {
        return <div key={i} className="msg-break" />;
      }

      return (
        <div
          key={i}
          className="msg-line"
          dangerouslySetInnerHTML={{ __html: formatted }}
        />
      );
    });
  };

  const formatTime = (date) => {
    if (!date) return "";
    const d = new Date(date);
    return d.toLocaleTimeString("en-NG", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={`message ${isUser ? "user" : "assistant"} ${isError ? "error" : ""}`}>
      <div className="message-avatar">
        {isUser ? "👤" : "🏦"}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-sender">
            {isUser ? "You" : "Bank of Africa AI"}
          </span>
          <span className="message-time">{formatTime(message.timestamp)}</span>
        </div>
        <div className="message-text">{formatContent(message.content)}</div>
      </div>
    </div>
  );
}
