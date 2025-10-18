export type InteractionEvent = {
  session_id: string;
  participant_id?: string;
  participant_group?: "A" | "B";
  event: string;
  component?: string;
  label?: string;
  value?: string;
  duration_ms?: number;
  client_ts?: string | number;
  page_url?: string;
  user_agent?: string;
  meta?: Record<string, any>;
};

function apiUrl(path: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "";
  try {
    if (typeof window !== "undefined") {
      const onLocalhost = /localhost|127\.0\.0\.1/.test(window.location.host);
      const baseIsLocalhost = /localhost|127\.0\.0\.1/.test(base);
      if (!onLocalhost && baseIsLocalhost) return path;
    }
  } catch {}
  return base ? `${base}${path}` : path;
}

export async function logEvent(ev: InteractionEvent | InteractionEvent[]): Promise<void> {
  try {
    const payload = Array.isArray(ev) ? ev : [ev];
    const body = JSON.stringify(payload);
    // Prefer sendBeacon for best-effort fire-and-forget
    if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon(apiUrl("/api/interaction"), blob);
      if (ok) return;
    }
    await fetch(apiUrl("/api/interaction"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  } catch {
    // swallow — telemetry is best-effort
  }
}

