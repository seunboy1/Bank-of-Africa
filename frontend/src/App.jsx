import { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import AgentTrace from "./components/AgentTrace";
import { sendMessage, createSessionId } from "./utils/api";

export default function App() {
  // Chat sessions: array of { id, title, messages, createdAt }
  const [sessions, setSessions] = useState(() => {
    const initialSession = {
      id: createSessionId(),
      title: "New Chat",
      messages: [],
      createdAt: new Date(),
    };
    return [initialSession];
  });
  const [activeSessionId, setActiveSessionId] = useState(() => sessions[0]?.id);
  const [traces, setTraces] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const [error, setError] = useState(null);

  // Get current session
  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];
  const messages = activeSession?.messages || [];

  // Create new chat session
  const handleNewChat = useCallback(() => {
    const newSession = {
      id: createSessionId(),
      title: "New Chat",
      messages: [],
      createdAt: new Date(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setTraces([]);
    setError(null);
  }, []);

  // Switch to a session
  const handleSelectSession = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
    setTraces([]);
    setError(null);
  }, []);

  // Delete a session
  const handleDeleteSession = useCallback(
    (sessionId) => {
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== sessionId);
        // If deleting active session, switch to first available or create new
        if (sessionId === activeSessionId) {
          if (filtered.length === 0) {
            const newSession = {
              id: createSessionId(),
              title: "New Chat",
              messages: [],
              createdAt: new Date(),
            };
            setActiveSessionId(newSession.id);
            return [newSession];
          }
          setActiveSessionId(filtered[0].id);
        }
        return filtered;
      });
      setTraces([]);
    },
    [activeSessionId]
  );

  // Rename a session
  const handleRenameSession = useCallback((sessionId, newTitle) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
    );
  }, []);

  // Generate title from first user message
  const generateTitle = (text) => {
    const maxLen = 30;
    const cleaned = text.replace(/\s+/g, " ").trim();
    return cleaned.length > maxLen ? cleaned.substring(0, maxLen) + "..." : cleaned;
  };

  const handleSend = useCallback(
    async (text) => {
      if (!text.trim() || isLoading) return;

      const userMsg = { role: "user", content: text, timestamp: new Date() };

      // Update session with new message
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id === activeSessionId) {
            const updatedMessages = [...s.messages, userMsg];
            // Update title if this is the first message
            const newTitle = s.messages.length === 0 ? generateTitle(text) : s.title;
            return { ...s, messages: updatedMessages, title: newTitle };
          }
          return s;
        })
      );

      setIsLoading(true);
      setError(null);
      setTraces([]);

      try {
        const data = await sendMessage(text, activeSessionId);
        const assistantMsg = {
          role: "assistant",
          content: data.response,
          timestamp: new Date(),
        };

        setSessions((prev) =>
          prev.map((s) => {
            if (s.id === activeSessionId) {
              return { ...s, messages: [...s.messages, assistantMsg] };
            }
            return s;
          })
        );

        if (data.traces && data.traces.length > 0) {
          setTraces(data.traces);
        }
      } catch (err) {
        setError(err.message);
        const errorMsg = {
          role: "assistant",
          content:
            "I'm sorry, I encountered an error processing your request. Please try again.",
          timestamp: new Date(),
          isError: true,
        };
        setSessions((prev) =>
          prev.map((s) => {
            if (s.id === activeSessionId) {
              return { ...s, messages: [...s.messages, errorMsg] };
            }
            return s;
          })
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeSessionId, isLoading]
  );

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        showTrace={showTrace}
        onToggleTrace={() => setShowTrace((p) => !p)}
      />
      <main className="main-content">
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          onSend={handleSend}
          error={error}
        />
      </main>
      {showTrace && traces.length > 0 && (
        <aside className="trace-panel">
          <AgentTrace traces={traces} />
        </aside>
      )}
    </div>
  );
}
