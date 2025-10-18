export type ChatResponse = {
  reply: string;
  suggestions: string[];
  topic: string;
  escalate: boolean;
  session_id: string;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
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
  handlers: StreamHandlers
) {
  const res = await fetch(`${BASE_URL}/api/chat-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
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
            dataLines.push(line.slice(5).trimStart());
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
