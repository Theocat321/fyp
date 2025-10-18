"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { sendMessage, ChatResponse, sendMessageStream } from "../lib/api";
import { supabase } from "../lib/supabaseClient";

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
  const useStreaming = process.env.NEXT_PUBLIC_USE_STREAMING === "true";

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function onSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    // Persist user message (best-effort)
    try { await supabase?.from("messages").insert({ session_id: sessionId, role: "user", content: trimmed }); } catch {}
    setInput("");
    try {
      if (useStreaming) {
        // Insert a placeholder assistant message for streaming updates
        setMessages((m) => [...m, { role: "assistant", text: "" }]);
        let assistantText = "";
        let sidLocal: string | undefined = sessionId;
        await sendMessageStream(trimmed, sessionId, {
          onInit: (meta) => {
            setSessionId(meta.session_id);
            sidLocal = meta.session_id;
            setSuggestions(meta.suggestions || []);
          },
          onToken: (token) => {
            assistantText += token;
            setMessages((m) => {
              const next = [...m];
              // Update last message (assistant placeholder)
              const idx = next.length - 1;
              if (idx >= 0 && next[idx].role === "assistant") {
                next[idx] = { ...next[idx], text: assistantText } as Msg;
              }
              return next;
            });
          },
          onDone: async (finalText) => {
            setBusy(false);
            // Persist assistant message (best-effort)
            try { await supabase?.from("messages").insert({ session_id: sidLocal ?? null, role: "assistant", content: finalText }); } catch {}
          },
          onError: () => {
            setBusy(false);
            setMessages((m) => [
              ...m,
              { role: "assistant", text: "Sorry, I couldn't reach support right now." },
            ]);
          },
        });
      } else {
        const resp: ChatResponse = await sendMessage(trimmed, sessionId);
        setSessionId(resp.session_id);
        setMessages((m) => [...m, { role: "assistant", text: resp.reply }]);
        setSuggestions(resp.suggestions || []);
        // Persist assistant message (best-effort)
        try { await supabase?.from("messages").insert({ session_id: resp.session_id, role: "assistant", content: resp.reply }); } catch {}
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, I couldn't reach support right now." },
      ]);
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
