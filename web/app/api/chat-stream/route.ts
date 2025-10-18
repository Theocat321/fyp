import { NextRequest } from "next/server";
import OpenAI from "openai";
import { AgentTopic, assistantMode, computeEscalate, defaultUnknownReply, detectTopic, generalSuggestions, knowledge, providerName } from "../../../lib/agent";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export type ChatRequest = { message: string; session_id?: string };

function newSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return (crypto as any).randomUUID().replace(/-/g, "");
  return Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2);
}

function chunkText(text: string, size = 40): string[] {
  const words = text.split(/\s+/);
  const out: string[] = [];
  let buf: string[] = [];
  let count = 0;
  for (const w of words) {
    if (count + w.length + (buf.length ? 1 : 0) > size) {
      out.push(buf.join(" ") + " ");
      buf = [w];
      count = w.length;
    } else {
      buf.push(w);
      count += w.length + (count > 0 ? 1 : 0);
    }
  }
  if (buf.length) out.push(buf.join(" "));
  return out;
}

export async function POST(req: NextRequest) {
  const { message, session_id: sidIn } = (await req.json()) as ChatRequest;
  const session_id = sidIn || newSessionId();
  const topic: AgentTopic = detectTopic(message);
  const mode = assistantMode();
  const baseUnknown = [
    "Show plan options",
    "Check data balance",
    "View my bill",
    "Roaming rates",
    "Coverage map",
    "Talk to an agent",
  ];
  const suggestions = topic === "unknown"
    ? (mode === "open" ? [...generalSuggestions, ...baseUnknown] : baseUnknown)
    : (mode === "open" ? [...knowledge[topic].suggestions, generalSuggestions[0]] : knowledge[topic].suggestions);
  const escalate = computeEscalate(topic, message);
  const hasOpenAI = !!process.env.OPENAI_API_KEY;

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: string, data: string | object) => {
        const payload = typeof data === "string" ? data : JSON.stringify(data);
        controller.enqueue(encoder.encode(`event: ${event}\n`));
        controller.enqueue(encoder.encode(`data: ${payload}\n\n`));
      };

      // init metadata (includes engine used)
      send("init", { session_id, suggestions, topic, escalate, engine: hasOpenAI ? "openai" : "rule-based" });

      const apiKey = process.env.OPENAI_API_KEY;
      const baseURL = process.env.OPENAI_BASE_URL;
      let full = "";

      if (apiKey) {
        try {
          const client = new OpenAI({ apiKey, baseURL });
          const system =
            assistantMode() === "open"
              ? `You are a helpful support agent for ${providerName}. Keep replies concise. You can chat broadly, and for telecom topics (plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM) give clear, practical guidance. Ask brief follow-ups when needed. Don't guess.`
              : `You are a helpful mobile network support agent for ${providerName}. Keep replies concise. Focus on telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage and devices/SIM. Ask brief follow-ups when needed. Don't guess.`;
          const completion = await client.chat.completions.create({
            model: process.env.OPENAI_MODEL || "gpt-4o-mini",
            messages: [
              { role: "system", content: system },
              { role: "user", content: message },
            ],
            temperature: assistantMode() === "open" ? 0.5 : 0.3,
            max_tokens: 220,
            stream: true,
          });
          for await (const chunk of completion) {
            const token = (chunk as any)?.choices?.[0]?.delta?.content as string | undefined;
            if (token) {
              full += token;
              send("token", token);
            }
          }
        } catch {
          // fallback to rule-based
          const reply = topic === "unknown" ? defaultUnknownReply() : knowledge[topic].reply;
          for (const part of chunkText(reply)) {
            full += part;
            send("token", part);
          }
        }
      } else {
        const reply = topic === "unknown" ? defaultUnknownReply() : knowledge[topic].reply;
        for (const part of chunkText(reply)) {
          full += part;
          send("token", part);
        }
      }

      send("done", { reply: full });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
