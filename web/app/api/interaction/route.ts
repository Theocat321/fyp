import { NextRequest } from "next/server";
import { getSupabaseAdmin } from "../../../lib/supabaseAdmin";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

type InteractionEvent = {
  session_id: string;
  participant_id?: string;
  participant_group?: "A" | "B";
  event: string; // e.g., click, focus, blur, input, typing, submit, message_send
  component?: string; // e.g., send_button, text_input, suggestion_chip
  label?: string; // e.g., button text, chip text
  value?: string; // sanitized short value (optional)
  duration_ms?: number; // typing duration or dwell time
  client_ts?: string | number; // client time (ISO or epoch ms)
  page_url?: string;
  user_agent?: string;
  meta?: Record<string, any>;
};

type Payload = InteractionEvent | { events: InteractionEvent[] } | InteractionEvent[];

function normalize(body: Payload): InteractionEvent[] {
  if (Array.isArray(body)) return body;
  if ("events" in body && Array.isArray(body.events)) return body.events;
  return [body as InteractionEvent];
}

export async function POST(req: NextRequest) {
  let body: Payload;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid_json" }), { status: 400 });
  }

  const events = normalize(body).filter((e) => e && typeof e.session_id === "string" && e.session_id.length > 0);
  if (!events.length) {
    return new Response(JSON.stringify({ error: "no_valid_events" }), { status: 400 });
  }

  const ua = req.headers.get("user-agent") || undefined;
  const withContext = events.map((e) => {
    const ts = typeof e.client_ts === "number"
      ? new Date(e.client_ts).toISOString()
      : (typeof e.client_ts === "string" ? e.client_ts : null);
    return {
      session_id: e.session_id,
      participant_id: e.participant_id ?? null,
      participant_group: e.participant_group ?? null,
      event: (e.event || "unknown").slice(0, 64),
      component: e.component?.slice(0, 128) ?? null,
      label: e.label?.slice(0, 512) ?? null,
      value: e.value?.slice(0, 1024) ?? null,
      duration_ms: typeof e.duration_ms === "number" ? Math.max(0, Math.floor(e.duration_ms)) : null,
      client_ts: ts,
      page_url: e.page_url?.slice(0, 1024) ?? null,
      user_agent: e.user_agent?.slice(0, 1024) ?? ua ?? null,
      meta: e.meta ?? null,
    };
  });

  const admin = getSupabaseAdmin();
  if (!admin) {
    // Accept but not persisted when admin client is not configured
    return new Response(JSON.stringify({ ok: true, stored: 0, skipped: withContext.length }), { status: 202 });
  }

  const { error } = await admin.from("interaction_events").insert(withContext);
  if (error) {
    return new Response(JSON.stringify({ error: "insert_failed", details: error.message }), { status: 500 });
  }
  return new Response(JSON.stringify({ ok: true, stored: withContext.length }), { status: 200 });
}
