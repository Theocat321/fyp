import { NextRequest } from "next/server";
import OpenAI from "openai";
import { AgentTopic, assistantMode, computeEscalate, detectTopic, knowledge, defaultUnknownReply, providerName, generalSuggestions } from "../../../lib/agent";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export type ChatRequest = { message: string; session_id?: string };
export type ChatResponse = {
  reply: string;
  suggestions: string[];
  topic: AgentTopic | string;
  escalate: boolean;
  session_id: string;
  engine?: string;
};

function newSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return (crypto as any).randomUUID().replace(/-/g, "");
  return Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2);
}

export async function POST(req: NextRequest) {
  const body = (await req.json()) as ChatRequest;
  const message = body?.message?.toString() ?? "";
  const session_id = body?.session_id || newSessionId();

  const topic = detectTopic(message);
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

  let reply: string | undefined;
  const apiKey = process.env.OPENAI_API_KEY;
  const baseURL = process.env.OPENAI_BASE_URL;
  if (apiKey) {
    try {
      const client = new OpenAI({ apiKey, baseURL });
      const system =
        assistantMode() === "open"
          ? `You are a helpful support agent for ${providerName}. Keep replies concise. You can chat broadly, and for telecom topics (plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM) give clear, practical guidance. Ask brief follow-ups when needed. Don't guess.`
          : `You are a helpful mobile network support agent for ${providerName}. Keep replies concise. Focus on telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage and devices/SIM. Ask brief follow-ups when needed. Don't guess.`;
      const resp = await client.chat.completions.create({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        messages: [
          { role: "system", content: system },
          { role: "user", content: message },
        ],
        temperature: assistantMode() === "open" ? 0.5 : 0.3,
        max_tokens: 220,
      });
      reply = resp.choices?.[0]?.message?.content ?? undefined;
    } catch {
      // fall through to rule-based reply
    }
  }

  if (!reply) {
    reply = topic === "unknown" ? defaultUnknownReply() : knowledge[topic].reply;
  }

  const escalate = computeEscalate(topic, message);
  const payload: ChatResponse = {
    reply,
    suggestions,
    topic,
    escalate,
    session_id,
    engine: apiKey ? "openai" : "rule-based",
  };
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
  });
}
