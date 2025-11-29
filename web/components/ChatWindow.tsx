"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { sendMessage, ChatResponse, sendMessageStream } from "../lib/api";
import { supabase } from "../lib/supabaseClient";
import { logEvent } from "../lib/telemetry";

type Msg = { role: "user" | "assistant"; text: string };

export default function ChatWindow() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Hi, I’m VodaCare Support. How can I help?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  // Default to streaming unless explicitly disabled
  const useStreaming = process.env.NEXT_PUBLIC_USE_STREAMING !== "false";
  const [engine, setEngine] = useState<string | undefined>(undefined);
  // Research participant gate
  const [participantName, setParticipantName] = useState<string>("");
  const [participantGroup, setParticipantGroup] = useState<"A" | "B" | "">("");
  const [participantId, setParticipantId] = useState<string | undefined>(undefined);
  const [started, setStarted] = useState<boolean>(false);
  const [typingStartAt, setTypingStartAt] = useState<number | null>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  // Load participant from localStorage
  useEffect(() => {
    try {
      const name = localStorage.getItem("vc_participant_name") || "";
      const group = (localStorage.getItem("vc_participant_group") || "") as "A" | "B" | "";
      const pid = localStorage.getItem("vc_participant_id") || undefined;
      const sid = localStorage.getItem("vc_session_id") || undefined;
      if (name && (group === "A" || group === "B")) {
        setParticipantName(name);
        setParticipantGroup(group);
        if (pid) setParticipantId(pid);
        if (sid) setSessionId(sid);
        setStarted(true);
      }
    } catch {}
  }, []);

  function ensureParticipantId(): string {
    if (participantId) return participantId;
    const pid = (typeof crypto !== "undefined" && "randomUUID" in crypto)
      ? (crypto as any).randomUUID()
      : Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2);
    setParticipantId(pid);
    try { localStorage.setItem("vc_participant_id", pid); } catch {}
    return pid;
  }

  function ensureSessionId(): string {
    if (sessionId) return sessionId;
    const sid = (typeof crypto !== "undefined" && "randomUUID" in crypto)
      ? (crypto as any).randomUUID().replace(/-/g, "")
      : Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2);
    setSessionId(sid);
    try { localStorage.setItem("vc_session_id", sid); } catch {}
    return sid;
  }

  async function onStartStudy(e: React.FormEvent) {
    e.preventDefault();
    if (!participantName.trim() || !(participantGroup === "A" || participantGroup === "B")) return;
    try {
      localStorage.setItem("vc_participant_name", participantName.trim());
      localStorage.setItem("vc_participant_group", participantGroup);
    } catch {}
    const pid = ensureParticipantId();
    const sid = ensureSessionId();
    // Log enrollment submit
    try {
      await logEvent({
        session_id: sid,
        participant_id: pid,
        participant_group: participantGroup,
        event: "submit",
        component: "start_chat_form",
        label: "Start Chat",
        client_ts: Date.now(),
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
      });
    } catch {}
    // Best-effort participant insert
    try {
      await supabase?.from("participants").insert({
        participant_id: pid,
        name: participantName.trim(),
        group: participantGroup,
        session_id: sid,
      });
    } catch {}
    setStarted(true);
  }

  async function onSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    // Gate: require participant info before chatting
    if (!started || !participantName.trim() || !(participantGroup === "A" || participantGroup === "B")) return;
    setBusy(true);
    const sid = ensureSessionId();
    if (!sessionId) setSessionId(sid);
    // Log typing duration if any
    try {
      if (typingStartAt) {
        const dur = Date.now() - typingStartAt;
        await logEvent({
          session_id: sid,
          participant_id: participantId,
          participant_group: participantGroup || undefined,
          event: "typing",
          component: "text_input",
          duration_ms: dur,
          value: undefined,
          client_ts: Date.now(),
          page_url: typeof window !== "undefined" ? window.location.href : undefined,
          meta: { length: trimmed.length },
        });
      }
    } catch {}
    setTypingStartAt(null);
    // Log message send
    try {
      await logEvent({
        session_id: sid,
        participant_id: participantId,
        participant_group: participantGroup || undefined,
        event: "message_send",
        component: "send_action",
        label: "Send",
        client_ts: Date.now(),
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
        meta: { length: trimmed.length },
      });
    } catch {}
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    // Persist user message (best-effort)
    try {
      const pid = ensureParticipantId();
      await supabase?.from("messages").insert({
        session_id: sid,
        role: "user",
        content: trimmed,
        participant_id: pid,
        participant_name: participantName.trim(),
        participant_group: participantGroup,
      });
    } catch {}
    setInput("");
    try {
      if (useStreaming) {
        // Insert a placeholder assistant message for streaming updates
        setMessages((m) => [...m, { role: "assistant", text: "" }]);
        let assistantText = "";
        let sidLocal: string | undefined = sid;
        await sendMessageStream(trimmed, sid, {
          onInit: (meta) => {
            setSessionId(meta.session_id);
            sidLocal = meta.session_id;
            setEngine((meta as any)?.engine);
            try { console.debug("chat-stream init", meta); } catch {}
            // Best-effort update participant with session id
            try {
              const pid = ensureParticipantId();
              supabase?.from("participants").update({ session_id: meta.session_id }).eq("participant_id", pid);
            } catch {}
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
            try {
              const pid = ensureParticipantId();
              await supabase?.from("messages").insert({
                session_id: sidLocal ?? null,
                role: "assistant",
                content: finalText,
                participant_id: pid,
                participant_name: participantName.trim(),
                participant_group: participantGroup,
              });
              // Also log compact interaction (group, input, output)
              await supabase?.from("interactions").insert({
                group: participantGroup,
                input: trimmed,
                output: finalText,
              });
            } catch {}
          },
          onError: () => {
            setBusy(false);
            setMessages((m) => [
              ...m,
              { role: "assistant", text: "Sorry—something went wrong. Please try again." },
            ]);
          },
        });
      } else {
        const resp: ChatResponse = await sendMessage(trimmed, sid);
        setSessionId(resp.session_id);
        try {
          const pid = ensureParticipantId();
          supabase?.from("participants").update({ session_id: resp.session_id }).eq("participant_id", pid);
        } catch {}
        setMessages((m) => [...m, { role: "assistant", text: resp.reply }]);
        // Persist assistant message (best-effort)
        try {
          const pid = ensureParticipantId();
          await supabase?.from("messages").insert({
            session_id: resp.session_id,
            role: "assistant",
            content: resp.reply,
            participant_id: pid,
            participant_name: participantName.trim(),
            participant_group: participantGroup,
          });
          // Also log compact interaction (group, input, output)
          await supabase?.from("interactions").insert({
            group: participantGroup,
            input: trimmed,
            output: resp.reply,
          });
        } catch {}
        setBusy(false);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry—something went wrong. Please try again." },
      ]);
      setBusy(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSend(input);
  }

  if (!started) {
    return (
      <div className="prechat-shell">
        <div className="prechat-card">
          <h2>Study Enrollment</h2>
          <p className="muted">Enter your details to start the research chat.</p>
          <form onSubmit={onStartStudy} className="prechat-form">
            <div className="field-row">
              <label htmlFor="participant-name" className="label">Name</label>
              <input id="participant-name" className="text-input" placeholder="Your name" value={participantName} onChange={(e) => setParticipantName(e.target.value)} />
            </div>
            <div className="field-row">
              <label htmlFor="participant-group" className="label">Group</label>
              <select id="participant-group" className="select" value={participantGroup} onChange={(e) => setParticipantGroup(e.target.value as any)}>
                <option value="">Select group…</option>
                <option value="A">A</option>
                <option value="B">B</option>
              </select>
            </div>
            <button className="send-btn" type="submit" disabled={!participantName.trim() || !(participantGroup === "A" || participantGroup === "B")}>Start Chat</button>
          </form>
          <p className="consent-note">By starting, you consent to your inputs being used for research. Do not share sensitive information.</p>
        </div>
      </div>
    );
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
        {engine && (
          <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>engine: {engine}</div>
        )}
      </div>
      <form className="input-row" onSubmit={onSubmit}>
        <input
          className="text-input"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => {
            const val = e.target.value;
            if (!typingStartAt && val.trim().length > 0) setTypingStartAt(Date.now());
            setInput(val);
          }}
          onFocus={() => {
            try {
              const sid = sessionId || ensureSessionId();
              logEvent({
                session_id: sid,
                participant_id: participantId,
                participant_group: participantGroup || undefined,
                event: "focus",
                component: "text_input",
                client_ts: Date.now(),
                page_url: typeof window !== "undefined" ? window.location.href : undefined,
              });
            } catch {}
          }}
          onBlur={() => {
            try {
              const sid = sessionId || "";
              if (sid) {
                logEvent({
                  session_id: sid,
                  participant_id: participantId,
                  participant_group: participantGroup || undefined,
                  event: "blur",
                  component: "text_input",
                  client_ts: Date.now(),
                  page_url: typeof window !== "undefined" ? window.location.href : undefined,
                });
              }
            } catch {}
          }}
          disabled={busy}
        />
        <button
          className="send-btn"
          type="submit"
          disabled={busy || !input.trim()}
          onClick={() => {
            try {
              const sid = ensureSessionId();
              logEvent({
                session_id: sid,
                participant_id: participantId,
                participant_group: participantGroup || undefined,
                event: "click",
                component: "send_button",
                label: "Send",
                client_ts: Date.now(),
                page_url: typeof window !== "undefined" ? window.location.href : undefined,
              });
            } catch {}
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
