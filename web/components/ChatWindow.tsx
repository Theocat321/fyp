"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { sendMessage, ChatResponse, sendMessageStream, fetchMessages } from "../lib/api";
import { logEvent } from "../lib/telemetry";
import { supabase } from "../lib/supabaseClient";

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
  const [atBottom, setAtBottom] = useState(true);
  // Default to streaming unless explicitly disabled
  const useStreaming = process.env.NEXT_PUBLIC_USE_STREAMING !== "false";
  // Research participant gate
  const [participantName, setParticipantName] = useState<string>("");
  const [participantGroup, setParticipantGroup] = useState<"A" | "B" | "">("");
  const [participantId, setParticipantId] = useState<string | undefined>(undefined);
  const [started, setStarted] = useState<boolean>(false);
  const [typingStartAt, setTypingStartAt] = useState<number | null>(null);
  const [lastSendAt, setLastSendAt] = useState<number | null>(null);
  // Feedback modal state
  const [showFeedback, setShowFeedback] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackDone, setFeedbackDone] = useState(false);
  const [form, setForm] = useState({
    rating_overall: 0,
    rating_helpfulness: 0,
    rating_friendliness: 0,
    resolved: "",
    time_to_resolution: "",
    issues: [] as string[],
    comments_positive: "",
    comments_negative: "",
    comments_other: "",
    would_use_again: "",
    recommend_nps: 0,
    contact_ok: false,
    contact_email: "",
  });

  // Lightweight formatting heuristic to make streamed text more readable as it arrives
  function formatStreamingText(input: string): string {
    try {
      let t = input;
      // If a colon is immediately followed by a list start (number or hyphen), insert a newline
      t = t.replace(/:(\s*)?(?=(\d+\.|-\s|•\s))/g, ":\n");
      // Ensure numbered items begin on a new line
      t = t.replace(/([^\n])(\d+\.\s+)/g, (_m, prev, item) => `${prev}\n${item}`);
      // Ensure hyphen/• bullets begin on a new line
      t = t.replace(/([^\n])(\-\s+)/g, (_m, prev, item) => `${prev}\n${item}`);
      t = t.replace(/([^\n])(•\s+)/g, (_m, prev, item) => `${prev}\n${item}`);
      // Collapse more than 2 consecutive newlines to 2 during streaming
      t = t.replace(/\n{3,}/g, "\n\n");
      return t;
    } catch {
      return input;
    }
  }

  useEffect(() => {
    if (!listRef.current) return;
    if (atBottom) {
      listRef.current.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, busy, atBottom]);

  // Load past messages for this session from backend storage (independent of enrollment UI)
  useEffect(() => {
    (async () => {
      try {
        const sid = sessionId || (typeof window !== "undefined" ? localStorage.getItem("vc_session_id") || undefined : undefined);
        if (!sid) return;
        const res = await fetchMessages(sid);
        const msgs = (res.messages || []).map((m: any) => ({ role: m.role as "user" | "assistant", text: m.content as string }));
        if (msgs.length) {
          setMessages(msgs);
        }
      } catch {}
    })();
  }, [sessionId]);

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
        label: "start_chat",
        value: participantGroup,
        client_ts: Date.now(),
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
      });
    } catch {}
    // Participant upsert via Python backend
    try {
      await fetch("/api/participants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          participant_id: pid,
          name: participantName.trim(),
          group: participantGroup,
          session_id: sid,
        }),
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
    // Log typing end with duration if any
    try {
      if (typingStartAt) {
        const dur = Date.now() - typingStartAt;
        await logEvent({
          session_id: sid,
          participant_id: participantId,
          participant_group: participantGroup || undefined,
          event: "typing_end",
          component: "text_input",
          label: "text_input",
          value: String(trimmed.length),
          duration_ms: dur,
          client_ts: Date.now(),
          page_url: typeof window !== "undefined" ? window.location.href : undefined,
          meta: { length: trimmed.length },
        });
      }
    } catch {}
    setTypingStartAt(null);
    // Log message send
    try {
      const now = Date.now();
      setLastSendAt(now);
      // Generic 'send' event for funnel
      await logEvent({
        session_id: sid,
        participant_id: participantId,
        participant_group: participantGroup || undefined,
        event: "send",
        component: "composer",
        label: "send",
        value: String(trimmed.length),
        client_ts: now,
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
      });
      // Legacy/message-specific event
      await logEvent({
        session_id: sid,
        participant_id: participantId,
        participant_group: participantGroup || undefined,
        event: "message_send",
        component: "send_action",
        label: "send",
        client_ts: Date.now(),
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
        meta: { length: trimmed.length },
      });
    } catch {}
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    // Persist user message via Python backend (best-effort)
    try {
      const pid = ensureParticipantId();
      await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sid,
          role: "user",
          content: trimmed,
          participant_id: pid,
          participant_name: participantName.trim(),
          participant_group: participantGroup,
        }),
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
            // Best-effort update participant with session id
            try {
              const pid = ensureParticipantId();
              fetch("/api/participants", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ participant_id: pid, session_id: meta.session_id }),
              });
            } catch {}
          },
          onToken: (token) => {
            assistantText += token;
            const formatted = formatStreamingText(assistantText);
            setMessages((m) => {
              const next = [...m];
              // Update last message (assistant placeholder)
              const idx = next.length - 1;
              if (idx >= 0 && next[idx].role === "assistant") {
                next[idx] = { ...next[idx], text: formatted } as Msg;
              }
              return next;
            });
          },
          onDone: async (finalText) => {
            setBusy(false);
            // Persist assistant message via Python backend (best-effort)
            try {
              const pid = ensureParticipantId();
              await fetch("/api/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: sidLocal ?? null,
                  role: "assistant",
                  content: finalText,
                  participant_id: pid,
                  participant_name: participantName.trim(),
                  participant_group: participantGroup,
                }),
              });
              // Client-side response event for funnel
              try {
                const now = Date.now();
                const dur = lastSendAt ? now - lastSendAt : undefined;
                await logEvent({
                  session_id: sidLocal ?? sid,
                  participant_id: participantId,
                  participant_group: participantGroup || undefined,
                  event: "response",
                  component: "chat_stream",
                  label: "assistant",
                  value: String(finalText.length),
                  duration_ms: dur,
                  client_ts: now,
                  page_url: typeof window !== "undefined" ? window.location.href : undefined,
                });
              } catch {}
            } catch {}
          },
          onError: () => {
            setBusy(false);
            setMessages((m) => [
              ...m,
              { role: "assistant", text: "Sorry—something went wrong. Please try again." },
            ]);
          },
        }, participantGroup, participantId || ensureParticipantId());
      } else {
        const resp: ChatResponse = await sendMessage(trimmed, sid, participantGroup, participantId || ensureParticipantId());
        setSessionId(resp.session_id);
        try {
          const pid = ensureParticipantId();
          fetch("/api/participants", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ participant_id: pid, session_id: resp.session_id }),
          });
        } catch {}
        setMessages((m) => [...m, { role: "assistant", text: resp.reply }]);
        // Persist assistant message via Python backend (best-effort)
        try {
          const pid = ensureParticipantId();
          await fetch("/api/messages", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: resp.session_id,
              role: "assistant",
              content: resp.reply,
              participant_id: pid,
              participant_name: participantName.trim(),
              participant_group: participantGroup,
            }),
          });
          // Client-side response event for funnel (non-stream)
          try {
            const now = Date.now();
            const dur = lastSendAt ? now - lastSendAt : undefined;
            await logEvent({
              session_id: resp.session_id,
              participant_id: participantId,
              participant_group: participantGroup || undefined,
              event: "response",
              component: "chat",
              label: "assistant",
              value: String(resp.reply.length),
              duration_ms: dur,
              client_ts: now,
              page_url: typeof window !== "undefined" ? window.location.href : undefined,
            });
          } catch {}
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
      <div
        className="chat-list"
        ref={listRef}
        onScroll={() => {
          try {
            const el = listRef.current;
            if (!el) return;
            const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 40;
            setAtBottom(nearBottom);
          } catch {}
        }}
      >
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} text={m.text} />
        ))}
        {busy && <MessageBubble role="assistant" typing />}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {busy ? "VodaCare is typing" : ""}
        </div>
      </div>
      <form className="input-row" onSubmit={onSubmit}>
        <button
          type="button"
          className="finish-btn"
          onClick={() => {
            setShowFeedback(true);
            try {
              const sid = sessionId || ensureSessionId();
              logEvent({
                session_id: sid,
                participant_id: participantId,
                participant_group: participantGroup || undefined,
                event: "click",
                component: "finish_button",
                label: "finish_conversation_open",
                client_ts: Date.now(),
                page_url: typeof window !== "undefined" ? window.location.href : undefined,
              });
            } catch {}
          }}
        >
          Finish
        </button>
        <input
          className="text-input"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => {
            const val = e.target.value;
            if (!typingStartAt && val.trim().length > 0) {
              const startedAt = Date.now();
              setTypingStartAt(startedAt);
              try {
                const sid = sessionId || ensureSessionId();
                logEvent({
                  session_id: sid,
                  participant_id: participantId,
                  participant_group: participantGroup || undefined,
                  event: "typing_start",
                  component: "text_input",
                  label: "text_input",
                  value: String(val.length),
                  client_ts: startedAt,
                  page_url: typeof window !== "undefined" ? window.location.href : undefined,
                });
              } catch {}
            }
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
                label: "text_input",
                value: "focus",
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
                  label: "text_input",
                  value: "blur",
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
                label: "send",
                value: String(input.trim().length),
                client_ts: Date.now(),
                page_url: typeof window !== "undefined" ? window.location.href : undefined,
              });
            } catch {}
          }}
        >
          Send
        </button>
      </form>
      {showFeedback && (
        <div className="feedback-overlay" role="dialog" aria-modal="true" aria-label="Finish Conversation Feedback">
          <div className="feedback-modal">
            <div className="feedback-header">
              <h3>Finish Conversation</h3>
              <button className="feedback-close" onClick={() => setShowFeedback(false)} aria-label="Close feedback">×</button>
            </div>
            {!feedbackDone ? (
              <form
                className="feedback-form"
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (submittingFeedback) return;
                  setSubmittingFeedback(true);
                  try {
                    const sid = sessionId || ensureSessionId();
                    const pid = participantId || ensureParticipantId();
                    const payload: any = {
                      session_id: sid,
                      participant_id: pid,
                      participant_group: participantGroup || null,
                      rating_overall: form.rating_overall || null,
                      rating_helpfulness: form.rating_helpfulness || null,
                      rating_friendliness: form.rating_friendliness || null,
                      resolved: form.resolved === "yes" ? true : form.resolved === "no" ? false : null,
                      time_to_resolution: form.time_to_resolution || null,
                      issues: form.issues,
                      comments_positive: form.comments_positive || null,
                      comments_negative: form.comments_negative || null,
                      comments_other: form.comments_other || null,
                      would_use_again: form.would_use_again || null,
                      recommend_nps: form.recommend_nps || null,
                      contact_ok: form.contact_ok,
                      contact_email: form.contact_email || null,
                      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : null,
                      page_url: typeof window !== "undefined" ? window.location.href : null,
                    };
                    if (supabase) {
                      const { error } = await supabase.from("support_feedback").insert(payload);
                      if (error) throw error;
                    }
                    try {
                      await logEvent({
                        session_id: sid,
                        participant_id: pid,
                        participant_group: participantGroup || undefined,
                        event: "submit",
                        component: "feedback_form",
                        label: "finish_conversation",
                        client_ts: Date.now(),
                        page_url: typeof window !== "undefined" ? window.location.href : undefined,
                        meta: payload,
                      });
                    } catch {}
                    setFeedbackDone(true);
                  } catch (err) {
                    alert("Sorry—could not save feedback. Please try again.");
                  } finally {
                    setSubmittingFeedback(false);
                  }
                }}
              >
                <p className="muted">Thanks for chatting with VodaCare. A few quick questions to wrap up your support session.</p>
                <div className="grid-2">
                  <div className="field-row">
                    <label className="label">Overall, how satisfied are you?</label>
                    <div className="radio-row">
                      {[1,2,3,4,5].map((n) => (
                        <label key={n}><input type="radio" name="rating_overall" value={n}
                          checked={form.rating_overall === n}
                          onChange={() => setForm({ ...form, rating_overall: n })} /> {n}</label>
                      ))}
                    </div>
                  </div>
                  <div className="field-row">
                    <label className="label">How helpful was the support?</label>
                    <div className="radio-row">
                      {[1,2,3,4,5].map((n) => (
                        <label key={n}><input type="radio" name="rating_helpfulness" value={n}
                          checked={form.rating_helpfulness === n}
                          onChange={() => setForm({ ...form, rating_helpfulness: n })} /> {n}</label>
                      ))}
                    </div>
                  </div>
                  <div className="field-row">
                    <label className="label">How friendly/professional did the support feel?</label>
                    <div className="radio-row">
                      {[1,2,3,4,5].map((n) => (
                        <label key={n}><input type="radio" name="rating_friendliness" value={n}
                          checked={form.rating_friendliness === n}
                          onChange={() => setForm({ ...form, rating_friendliness: n })} /> {n}</label>
                      ))}
                    </div>
                  </div>
                  <div className="field-row">
                    <label className="label">Was your issue resolved?</label>
                    <div className="radio-row">
                      {[
                        {v:"yes", t:"Yes"},
                        {v:"no", t:"No"},
                        {v:"partial", t:"Partially"},
                      ].map((opt) => (
                        <label key={opt.v}><input type="radio" name="resolved" value={opt.v}
                          checked={form.resolved === opt.v}
                          onChange={() => setForm({ ...form, resolved: opt.v })} /> {opt.t}</label>
                      ))}
                    </div>
                  </div>
                  <div className="field-row">
                    <label className="label">Time to resolution</label>
                    <select className="select" value={form.time_to_resolution} onChange={(e) => setForm({ ...form, time_to_resolution: e.target.value })}>
                      <option value="">Select…</option>
                      <option value="<5m">Under 5 minutes</option>
                      <option value="5-15m">5–15 minutes</option>
                      <option value=">15m">Over 15 minutes</option>
                      <option value="na">Not resolved</option>
                    </select>
                  </div>
                </div>
                <div className="field-row">
                  <label className="label">What did you need help with? (select all that apply)</label>
                  <div className="checkbox-grid">
                    {["Plans","Balance","Billing","Roaming","Network","Device","Other"].map((k) => (
                      <label key={k}>
                        <input
                          type="checkbox"
                          checked={form.issues.includes(k)}
                          onChange={(e) => {
                            const next = new Set(form.issues);
                            if (e.target.checked) next.add(k); else next.delete(k);
                            setForm({ ...form, issues: Array.from(next) });
                          }}
                        /> {k}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="grid-2">
                  <div className="field-row">
                    <label className="label">What went well?</label>
                    <textarea className="textarea" placeholder="Tell us what worked for you" value={form.comments_positive} onChange={(e) => setForm({ ...form, comments_positive: e.target.value })} />
                  </div>
                  <div className="field-row">
                    <label className="label">What could be better?</label>
                    <textarea className="textarea" placeholder="Anything confusing or frustrating?" value={form.comments_negative} onChange={(e) => setForm({ ...form, comments_negative: e.target.value })} />
                  </div>
                </div>
                <div className="field-row">
                  <label className="label">Anything else you'd like us to know?</label>
                  <textarea className="textarea" placeholder="Your suggestions and ideas" value={form.comments_other} onChange={(e) => setForm({ ...form, comments_other: e.target.value })} />
                </div>
                <div className="grid-2">
                  <div className="field-row">
                    <label className="label">Would you use VodaCare support again?</label>
                    <select className="select" value={form.would_use_again} onChange={(e) => setForm({ ...form, would_use_again: e.target.value })}>
                      <option value="">Select…</option>
                      <option value="definitely">Definitely</option>
                      <option value="probably">Probably</option>
                      <option value="not_sure">Not sure</option>
                      <option value="probably_not">Probably not</option>
                      <option value="definitely_not">Definitely not</option>
                    </select>
                  </div>
                  <div className="field-row">
                    <label className="label">How likely are you to recommend us to a friend? (0–10)</label>
                    <input type="number" min={0} max={10} className="text-input" value={form.recommend_nps}
                      onChange={(e) => setForm({ ...form, recommend_nps: Number(e.target.value) })} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="field-row">
                    <label className="label"><input type="checkbox" checked={form.contact_ok} onChange={(e) => setForm({ ...form, contact_ok: e.target.checked })} /> OK to contact me for follow-up</label>
                  </div>
                  <div className="field-row">
                    <label className="label">Email (optional)</label>
                    <input type="email" className="text-input" placeholder="you@example.com" value={form.contact_email}
                      onChange={(e) => setForm({ ...form, contact_email: e.target.value })} />
                  </div>
                </div>
                <div className="feedback-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowFeedback(false)} disabled={submittingFeedback}>Cancel</button>
                  <button type="submit" className="send-btn" disabled={submittingFeedback}>{submittingFeedback ? "Submitting…" : "Submit feedback"}</button>
                </div>
              </form>
            ) : (
              <div className="feedback-done">
                <h4>Thanks for your feedback!</h4>
                <p className="muted">We really appreciate you taking the time. Your responses help us improve VodaCare support.</p>
                <button className="send-btn" onClick={() => { setShowFeedback(false); }}>Close</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
