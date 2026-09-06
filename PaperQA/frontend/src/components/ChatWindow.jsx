import { useEffect, useRef, useState } from "react";
import { chatApi } from "../services/api";
import SourceViewer from "./SourceViewer";
import Visualization from "./Visualization";

export default function ChatWindow({ paperId, disabled }) {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const scrollRef = useRef(null);
  const initializedPaperRef = useRef(null);

  // Initialize or fetch session for this paper ONCE per paperId
  useEffect(() => {
    if (!paperId || disabled) return;
    if (initializedPaperRef.current === paperId) return;

    initializedPaperRef.current = paperId;

    async function initSession() {
      try {
        const sessionsRes = await chatApi.listSessions(paperId);
        let activeSessionId;
        if (sessionsRes.data && sessionsRes.data.length > 0) {
          activeSessionId = sessionsRes.data[0].id;
        } else {
          const createRes = await chatApi.createSession(paperId, "Paper Discussion");
          activeSessionId = createRes.data.id;
        }
        setSessionId(activeSessionId);

        const msgsRes = await chatApi.getSessionMessages(activeSessionId);
        if (msgsRes.data && msgsRes.data.messages) {
          setMessages(msgsRes.data.messages);
        }
      } catch (err) {
        console.error("Failed to initialize chat session:", err);
        initializedPaperRef.current = null; // allow retry if failed
      }
    }

    initSession();
  }, [paperId, disabled]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, asking]);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || asking || disabled || !sessionId) return;

    const userTempMsg = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userTempMsg]);
    setQuestion("");
    setAsking(true);

    try {
      const res = await chatApi.sendMessage(sessionId, trimmed);
      const assistantMsg = res.data;
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            err.response?.data?.detail ||
            "Something went wrong answering that.",
          error: true,
        },
      ]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-pencil font-mono">
            {disabled
              ? "waiting for indexing to finish..."
              : "ask something about this paper..."}
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={msg.id || i}
            className={msg.role === "user" ? "text-right" : "text-left"}
          >
            <div
              className={`inline-block max-w-[85%] rounded-sm px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-indigo text-white"
                  : msg.error
                  ? "bg-danger/10 text-danger border border-danger/30"
                  : "bg-paper border border-pencil-light text-ink"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content || msg.text}</p>

              {msg.visualization_spec && (
                <Visualization spec={msg.visualization_spec} />
              )}
            </div>
            {msg.role === "assistant" && !msg.error && (
              <SourceViewer
                sources={msg.sources}
                figures={msg.figures}
                tables={msg.tables}
              />
            )}
          </div>
        ))}

        {asking && (
          <p className="font-mono text-xs text-pencil">agent thinking & running tools...</p>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-pencil-light p-3 flex gap-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={disabled || asking || !sessionId}
          placeholder={
            disabled
              ? "indexing in progress..."
              : !sessionId
              ? "connecting chat session..."
              : "ask a question or request a chart..."
          }
          className="flex-1 border border-pencil-light rounded-sm px-3 py-2 text-sm bg-paper text-ink focus:outline-none focus:ring-2 focus:ring-indigo disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || asking || !sessionId || !question.trim()}
          className="bg-indigo hover:bg-indigo-dim text-white text-sm font-medium px-4 py-2 rounded-sm transition-colors disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
