import { NextResponse } from 'next/server';

// Scenario definitions matching Python backend
const SCENARIOS = [
  {
    id: "scenario_001_esim_setup",
    name: "eSIM Setup",
    topic: "device",
    description: "Get help setting up an eSIM on your device",
    context: "You want to activate an eSIM but need guidance on compatibility and setup steps."
  },
  {
    id: "scenario_002_roaming_activation",
    name: "EU Roaming Activation",
    topic: "roaming",
    description: "Learn how to activate roaming for EU travel",
    context: "You're traveling to the EU and need to understand roaming charges and activation."
  },
  {
    id: "scenario_003_billing_dispute",
    name: "Billing Dispute",
    topic: "billing",
    description: "Resolve an issue with your bill",
    context: "You've noticed unexpected charges on your bill and want them explained or corrected. You've been charged $24 dollars more than required."
  },
  {
    id: "scenario_004_plan_upgrade",
    name: "Plan Upgrade",
    topic: "plans",
    description: "Find the best plan for your needs",
    context: "Your current plan isn't meeting your needs and you want to explore upgrade options. You're on the LITE plan and want to upgrade."
  },
  {
    id: "scenario_005_network_issue",
    name: "Network Issue",
    topic: "network",
    description: "Fix connectivity or signal problems",
    context: "You're experiencing poor signal or connection issues everywhere you go and need troubleshooting help. Ask the bot for some good advice."
  }
];

export async function GET() {
  return NextResponse.json({ scenarios: SCENARIOS });
}
