export type ChatResponse = {
  reply: string;
  suggestions: string[];
  topic: string;
  escalate: boolean;
  session_id: string;
  engine?: string;
};

// Use relative API paths; Next.js proxies to Python in dev via rewrites
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function apiUrl(path: string) {
  // If a localhost base is set but we're not on localhost (e.g., Vercel), ignore it.
  try {
    if (typeof window !== "undefined") {
      const onLocalhost = /localhost|127\.0\.0\.1/.test(window.location.host);
      const baseIsLocalhost = /localhost|127\.0\.0\.1/.test(BASE_URL);
      if (!onLocalhost && baseIsLocalhost) return path;
    }
  } catch {}
  return BASE_URL ? `${BASE_URL}${path}` : path;
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  participantGroup?: string,
  participantId?: string
): Promise<ChatResponse> {
  const res = await fetch(apiUrl(`/api/chat`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      participant_group: participantGroup,
      participant_id: participantId,
      page_url: typeof window !== "undefined" ? window.location.href : undefined,
    }),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}

export type StreamHandlers = {
  onInit?: (meta: { session_id: string; suggestions: string[]; topic: string; escalate: boolean }) => void;
  onToken?: (token: string) => void;
  onDone?: (finalText: string) => void;
  onError?: (err: unknown) => void;
};

export async function sendMessageStream(
  message: string,
  sessionId: string | undefined,
  handlers: StreamHandlers,
  participantGroup?: string,
  participantId?: string
) {
  const res = await fetch(apiUrl(`/api/chat-stream`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      participant_group: participantGroup,
      participant_id: participantId,
      page_url: typeof window !== "undefined" ? window.location.href : undefined,
    }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Stream error ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalText = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // Parse complete SSE events
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const lines = rawEvent.split(/\r?\n/);
        let eventType = "message";
        let dataLines: string[] = [];
        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            // Per SSE spec, remove one optional leading space after the colon only
            let v = line.slice(5);
            if (v.startsWith(" ")) v = v.slice(1);
            dataLines.push(v);
          }
        }
        const data = dataLines.join("\n");
        if (eventType === "init") {
          try {
            const meta = JSON.parse(data);
            handlers.onInit?.(meta);
          } catch {}
        } else if (eventType === "token") {
          handlers.onToken?.(data);
          finalText += data;
        } else if (eventType === "done") {
          try {
            const payload = JSON.parse(data);
            finalText = payload?.reply ?? finalText;
          } catch {}
          handlers.onDone?.(finalText);
        }
      }
    }
  } catch (err) {
    handlers.onError?.(err);
    throw err;
  }
}
