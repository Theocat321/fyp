"use client";

import { useEffect, useRef, useState } from "react";
import { sendMessage, ChatResponse, sendMessageStream, fetchMessages, fetchScenarios } from "../lib/api";
import { logEvent } from "../lib/telemetry";
import EnrollmentForm from "./EnrollmentForm";
import MessageList from "./MessageList";
import FeedbackModal, { FeedbackForm } from "./FeedbackModal";

type Msg = { role: "user" | "assistant"; text: string };

export default function ChatWindow() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Hi, I'm VodaCare Support. How can I help?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const [atBottom, setAtBottom] = useState(true);
  const useStreaming = process.env.NEXT_PUBLIC_USE_STREAMING !== "false";
  // Research participant gate
  const [participantName, setParticipantName] = useState<string>("");
  const [participantGroup, setParticipantGroup] = useState<"A" | "B" | "">("");
  const [participantId, setParticipantId] = useState<string | undefined>(undefined);
  const [started, setStarted] = useState<boolean>(false);
  const [hasStoredParticipant, setHasStoredParticipant] = useState<boolean>(false);
  // Scenario selection
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [scenarioContext, setScenarioContext] = useState<string>("");
  const [typingStartAt, setTypingStartAt] = useState<number | null>(null);
  const [lastSendAt, setLastSendAt] = useState<number | null>(null);
  // Feedback modal state
  const [showFeedback, setShowFeedback] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackDone, setFeedbackDone] = useState(false);
  const [form, setForm] = useState<FeedbackForm>({
    rating_overall: 0,
    rating_helpfulness: 0,
    rating_friendliness: 0,
    rating_task_success: 0,
    rating_clarity: 0,
    rating_empathy: 0,
    rating_accuracy: 0,
    resolved: "",
    time_to_resolution: "",
    issues: [],
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

  useEffect(() => {
    try {
      const name = localStorage.getItem("vc_participant_name") || "";
      const group = (localStorage.getItem("vc_participant_group") || "") as "A" | "B" | "";
      const pid = localStorage.getItem("vc_participant_id") || undefined;
      const sid = localStorage.getItem("vc_session_id") || undefined;
      const scenarioId = localStorage.getItem("vc_scenario_id") || "";
      if (name && (group === "A" || group === "B")) {
        setParticipantName(name);
        setParticipantGroup(group);
        setHasStoredParticipant(true);
        if (pid) setParticipantId(pid);
        if (sid) {
          setSessionId(sid);
          if (scenarioId) setSelectedScenario(scenarioId);
          // Only auto-start if they have an active session
          setStarted(true);
        }
      }
    } catch {}
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchScenarios();
        setScenarios(data.scenarios || []);
      } catch (e) {
        console.error("Failed to load scenarios:", e);
      }
    })();
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
      localStorage.setItem("vc_scenario_id", selectedScenario);
    } catch {}
    const pid = ensureParticipantId();
    const sid = ensureSessionId();
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
        meta: { scenario_id: selectedScenario || null },
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
          scenario_id: selectedScenario || null,
        }),
      });
    } catch {}
    setStarted(true);
  }

  async function onSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    if (!started || !participantName.trim() || !(participantGroup === "A" || participantGroup === "B")) return;
    setBusy(true);
    const sid = ensureSessionId();
    if (!sessionId) setSessionId(sid);
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
      <EnrollmentForm
        participantName={participantName}
        setParticipantName={setParticipantName}
        participantGroup={participantGroup}
        setParticipantGroup={setParticipantGroup}
        hasStoredParticipant={hasStoredParticipant}
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        setSelectedScenario={setSelectedScenario}
        scenarioContext={scenarioContext}
        setScenarioContext={setScenarioContext}
        onSubmit={onStartStudy}
      />
    );
  }

  return (
    <div className="chat-shell">
      <MessageList
        messages={messages}
        busy={busy}
        listRef={listRef}
        onScroll={() => {
          try {
            const el = listRef.current;
            if (!el) return;
            const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 40;
            setAtBottom(nearBottom);
          } catch {}
        }}
      />
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
      <FeedbackModal
        show={showFeedback}
        form={form}
        setForm={setForm}
        submittingFeedback={submittingFeedback}
        setSubmittingFeedback={setSubmittingFeedback}
        feedbackDone={feedbackDone}
        sessionId={sessionId}
        participantId={participantId}
        participantGroup={participantGroup}
        selectedScenario={selectedScenario}
        ensureSessionId={ensureSessionId}
        ensureParticipantId={ensureParticipantId}
      />
    </div>
  );
}
