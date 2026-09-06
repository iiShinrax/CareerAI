import { useState, useRef, useEffect } from "react";
import Layout from "../components/Layout";
import * as api from "../lib/api";

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "How can I help with your career today?" },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setSending(true);

    try {
      const data = await api.sendChatMessage(text, sessionId);
      setSessionId(data.session_id);
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">Chat</h1>
      <p className="text-muted text-sm mb-6">Ask anything about your career, skills, or roadmap.</p>

      <div className="bg-surface border border-line flex flex-col h-[560px]">
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] px-4 py-2.5 text-sm rounded-sm ${
                  m.role === "user"
                    ? "bg-amber text-ink"
                    : "bg-surface2 text-paper border border-line"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-surface2 border border-line px-4 py-2.5 rounded-sm text-sm text-muted">
                Thinking…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSend} className="border-t border-line p-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message…"
            className="flex-1 bg-ink border border-line rounded-sm px-3 py-2 text-sm text-paper focus:border-amber outline-none"
          />
          <button
            type="submit"
            disabled={sending}
            className="bg-amber text-ink px-5 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </Layout>
  );
}
