"use client";

import React from "react";

interface EnrollmentFormProps {
  participantName: string;
  setParticipantName: (v: string) => void;
  participantGroup: "A" | "B" | "";
  setParticipantGroup: (v: "A" | "B" | "") => void;
  hasStoredParticipant: boolean;
  scenarios: any[];
  selectedScenario: string;
  setSelectedScenario: (v: string) => void;
  scenarioContext: string;
  setScenarioContext: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export default function EnrollmentForm({
  participantName,
  setParticipantName,
  participantGroup,
  setParticipantGroup,
  hasStoredParticipant,
  scenarios,
  selectedScenario,
  setSelectedScenario,
  scenarioContext,
  setScenarioContext,
  onSubmit,
}: EnrollmentFormProps) {
  return (
    <div className="prechat-shell">
      <div className="prechat-card">
        <h2>Study Enrollment</h2>
        <p className="muted">{hasStoredParticipant ? "Start a new conversation" : "Enter your details to start the research chat."}</p>
        <form onSubmit={onSubmit} className="prechat-form">
          <div className="field-row">
            <label htmlFor="participant-name" className="label">Name</label>
            <input
              id="participant-name"
              className="text-input"
              placeholder="Your name"
              value={participantName}
              onChange={(e) => setParticipantName(e.target.value)}
              disabled={hasStoredParticipant}
            />
          </div>
          <div className="field-row">
            <label htmlFor="participant-group" className="label">Group</label>
            <select
              id="participant-group"
              className="select"
              value={participantGroup}
              onChange={(e) => setParticipantGroup(e.target.value as "A" | "B" | "")}
              disabled={hasStoredParticipant}
            >
              <option value="">Select group…</option>
              <option value="A">A</option>
              <option value="B">B</option>
            </select>
          </div>
          <div className="field-row">
            <label htmlFor="participant-scenario" className="label">Choose Your Scenario (Optional)</label>
            <p className="scenario-help">Select a scenario to roleplay a specific customer support situation. You'll act as the customer with a particular issue.</p>
            <select
              id="participant-scenario"
              className="select"
              value={selectedScenario}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedScenario(val);
                const scenario = scenarios.find((s) => s.id === val);
                setScenarioContext(scenario?.context || "");
              }}
            >
              <option value="">None (free conversation)</option>
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            {scenarioContext && (
              <div className="scenario-wrapper">
                <div className="scenario-role">
                  <strong>📋 Your Role in This Scenario:</strong>
                  <p>{scenarioContext}</p>
                </div>
                <div className="scenario-instructions">
                  <strong>What to do:</strong> Start the conversation by asking the support agent for help with this issue. Respond naturally as if you're a real customer experiencing this situation.
                </div>
                <div className="scenario-end">
                  <strong>When to end:</strong> Click the "Finish" button once your issue is resolved, you've received the information you need, or you feel the conversation has reached a natural conclusion. You can also end if you're not getting helpful responses after 3+ attempts.
                </div>
              </div>
            )}
          </div>
          <button className="send-btn" type="submit" disabled={!participantName.trim() || !(participantGroup === "A" || participantGroup === "B")}>Start Chat</button>
        </form>
        <p className="consent-note">By starting, you consent to your inputs being used for research. Do not share sensitive information.</p>
      </div>
    </div>
  );
}
