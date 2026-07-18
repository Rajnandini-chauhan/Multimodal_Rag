import { useState } from "react";
import { paperApi } from "../services/api";
import SourceViewer from "./SourceViewer";

export default function ChatWindow({ paperId, disabled }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || asking) return;

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setQuestion("");
    setAsking(true);

    try {
      const res = await paperApi.ask(paperId, trimmed);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.data.answer,
          sources: res.data.sources,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
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
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-pencil font-mono">
            {disabled
              ? "waiting for indexing to finish..."
              : "ask something about this paper"}
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={msg.role === "user" ? "text-right" : "text-left"}
          >
            <div
              className={`inline-block max-w-[85%] rounded-sm px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-indigo text-white"
                  : msg.error
                  ? "bg-danger/10 text-danger border border-danger/30"
                  : "bg-white border border-pencil-light"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
            {msg.role === "assistant" && !msg.error && (
              <SourceViewer sources={msg.sources} />
            )}
          </div>
        ))}

        {asking && (
          <p className="font-mono text-xs text-pencil">thinking...</p>
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
          disabled={disabled || asking}
          placeholder={
            disabled ? "indexing in progress..." : "ask a question..."
          }
          className="flex-1 border border-pencil-light rounded-sm px-3 py-2 text-sm bg-paper focus:outline-none focus:ring-2 focus:ring-indigo disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || asking || !question.trim()}
          className="bg-indigo hover:bg-indigo-dim text-white text-sm font-medium px-4 py-2 rounded-sm transition-colors disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}