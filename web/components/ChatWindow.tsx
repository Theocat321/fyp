"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { sendMessage, ChatResponse } from "../lib/api";

type Msg = { role: "user" | "assistant"; text: string };

export default function ChatWindow() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Hi! I’m your VodaCare virtual assistant. How can I help today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>(["Show plan options", "Check data balance", "View my bill", "Roaming rates"]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function onSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    setInput("");
    try {
      const resp: ChatResponse = await sendMessage(trimmed, sessionId);
      setSessionId(resp.session_id);
      setMessages((m) => [...m, { role: "assistant", text: resp.reply }]);
      setSuggestions(resp.suggestions || []);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, I couldn't reach support right now." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onSuggestionClick(s: string) {
    onSend(s);
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSend(input);
  }

  return (
    <div className="chat-shell">
      <div className="chat-list" ref={listRef}>
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} text={m.text} />
        ))}
        {busy && <MessageBubble role="assistant" typing />}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {busy ? "VodaCare is typing" : ""}
        </div>
      </div>
      <div className="suggestions">
        {suggestions.map((s) => (
          <button
            className="chip"
            key={s}
            onClick={() => onSuggestionClick(s)}
            disabled={busy}
            aria-label={`Suggestion: ${s}`}
          >
            {s}
          </button>
        ))}
      </div>
      <form className="input-row" onSubmit={onSubmit}>
        <input
          className="text-input"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
        />
        <button className="send-btn" type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
