export type AgentTopic = "plans" | "balance" | "billing" | "roaming" | "network" | "support" | "device" | "unknown";

export const providerName = process.env.PROVIDER_NAME || "VodaCare";

// Assistant mode controls how narrow or open-ended the chat feels.
// "open": general chat allowed; "strict": telecom-focused only.
export function assistantMode(): "open" | "strict" {
  const v = (process.env.ASSISTANT_MODE || "open").toLowerCase();
  return v === "strict" ? "strict" : "open";
}

export const generalSuggestions: string[] = [
  "Ask me anything",
  "Tell me more",
  "Something else",
];

export const knowledge: Record<string, { desc: string; reply: string; suggestions: string[]; keywords: string[] }> = {
  plans: {
    desc: "Plans and upgrades",
    reply:
      "We offer SIM‑only and device plans with flexible data. Popular choices include 25GB, 100GB and Unlimited. You can upgrade any time in your account.",
    suggestions: ["Show plan options", "How to upgrade", "What is unlimited?"],
    keywords: ["plan", "plans", "upgrade", "contract", "tariff", "unlimited"],
  },
  balance: {
    desc: "Data and usage",
    reply: "Check remaining data and minutes in the app or text BALANCE to 12345.",
    suggestions: ["Check data balance", "Data add-ons", "Usage alerts"],
    keywords: ["data", "balance", "usage", "allowance", "left"],
  },
  billing: {
    desc: "Bills and payments",
    reply: "Bills are monthly. Pay by card or Direct Debit. For a breakdown, open Billing in your account.",
    suggestions: ["View my bill", "Change payment method", "Late payment"],
    keywords: ["bill", "billing", "payment", "invoice", "charge"],
  },
  roaming: {
    desc: "Roaming and international",
    reply:
      "Roaming works on most plans. In the EU you can usually use your allowance like at home. For other countries, check our roaming page for rates.",
    suggestions: ["EU roaming", "Roaming rates", "Enable roaming"],
    keywords: ["roam", "roaming", "international", "abroad", "travel"],
  },
  network: {
    desc: "Coverage and issues",
    reply:
      "Share your postcode and device model and I’ll check coverage and any local issues.",
    suggestions: ["Coverage map", "Report an outage", "Network reset steps"],
    keywords: ["signal", "coverage", "network", "no service", "5g", "4g"],
  },
  support: {
    desc: "Live support",
    reply:
      "I can connect you with a specialist. Advisors are available 8am–8pm. Should I connect you?",
    suggestions: ["Talk to an agent", "Open a ticket", "Live chat hours"],
    keywords: ["agent", "human", "person", "support", "advisor", "representative"],
  },
  device: {
    desc: "Devices and SIM",
    reply:
      "For SIM swap, eSIM setup, or lost/stolen devices, I can guide you through the steps in your account.",
    suggestions: ["SIM swap", "Set up eSIM", "Lost my phone"],
    keywords: ["device", "phone", "sim", "esim", "lost", "stolen"],
  },
};

export const quickMap: Record<string, AgentTopic> = {
  "Show plan options": "plans",
  "How to upgrade": "plans",
  "What is unlimited?": "plans",
  "Check data balance": "balance",
  "Data add-ons": "balance",
  "Usage alerts": "balance",
  "View my bill": "billing",
  "Change payment method": "billing",
  "Late payment": "billing",
  "EU roaming": "roaming",
  "Roaming rates": "roaming",
  "Enable roaming": "roaming",
  "Coverage map": "network",
  "Report an outage": "network",
  "Network reset steps": "network",
  "Talk to an agent": "support",
  "Open a ticket": "support",
  "Live chat hours": "support",
  "SIM swap": "device",
  "Set up eSIM": "device",
  "Lost my phone": "device",
};

export function detectTopic(text: string): AgentTopic {
  const t = (text || "").toLowerCase().trim();
  if (text in quickMap) return quickMap[text];
  for (const [topic, info] of Object.entries(knowledge)) {
    for (const kw of info.keywords) {
      const re = new RegExp(`\\b${escapeRegExp(kw)}\\b`, "i");
      if (re.test(t)) return topic as AgentTopic;
    }
  }
  return "unknown";
}

export function defaultUnknownReply(): string {
  if (assistantMode() === "open") {
    return (
      `Hi — I’m ${providerName} Support. I can chat broadly and help with plans, data/balance, billing, roaming, coverage or devices. How can I help?`
    );
  }
  return (
    `Hi — I’m ${providerName} Support. I can help with plans, data/balance, billing, roaming, coverage or devices. What do you need help with?`
  );
}

export function computeEscalate(topic: AgentTopic, text: string): boolean {
  return (
    topic === "support" || ["agent", "human", "person", "escalate"].some((w) => text.toLowerCase().includes(w))
  );
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&");
}
