"use client";

import React from "react";
import { logEvent } from "../lib/telemetry";

export interface FeedbackForm {
  rating_overall: number;
  rating_helpfulness: number;
  rating_friendliness: number;
  rating_task_success: number;
  rating_clarity: number;
  rating_empathy: number;
  rating_accuracy: number;
  resolved: string;
  time_to_resolution: string;
  issues: string[];
  comments_positive: string;
  comments_negative: string;
  comments_other: string;
  would_use_again: string;
  recommend_nps: number;
  contact_ok: boolean;
  contact_email: string;
}

interface FeedbackModalProps {
  show: boolean;
  form: FeedbackForm;
  setForm: React.Dispatch<React.SetStateAction<FeedbackForm>>;
  submittingFeedback: boolean;
  setSubmittingFeedback: React.Dispatch<React.SetStateAction<boolean>>;
  feedbackDone: boolean;
  sessionId: string | undefined;
  participantId: string | undefined;
  participantGroup: "A" | "B" | "";
  selectedScenario: string;
  ensureSessionId: () => string;
  ensureParticipantId: () => string;
}

export default function FeedbackModal({
  show,
  form,
  setForm,
  submittingFeedback,
  setSubmittingFeedback,
  feedbackDone,
  sessionId,
  participantId,
  participantGroup,
  selectedScenario,
  ensureSessionId,
  ensureParticipantId,
}: FeedbackModalProps) {
  if (!show) return null;

  return (
    <div className="feedback-overlay" role="dialog" aria-modal="true" aria-label="Finish Conversation Feedback">
      <div className="feedback-modal">
        <div className="feedback-header">
          <h3>Finish Conversation</h3>
        </div>
        {!feedbackDone ? (
          <form
            className="feedback-form"
            onSubmit={async (e) => {
              e.preventDefault();
              if (submittingFeedback) return;
              setSubmittingFeedback(true);
              try {
                const sid = sessionId || ensureSessionId();
                const pid = participantId || ensureParticipantId();
                const payload: any = {
                  session_id: sid,
                  participant_id: pid,
                  participant_group: participantGroup || null,
                  scenario_id: selectedScenario || null,
                  rating_overall: form.rating_overall || null,
                  rating_helpfulness: form.rating_helpfulness || null,
                  rating_friendliness: form.rating_friendliness || null,
                  rating_task_success: form.rating_task_success || null,
                  rating_clarity: form.rating_clarity || null,
                  rating_empathy: form.rating_empathy || null,
                  rating_accuracy: form.rating_accuracy || null,
                  resolved: form.resolved === "yes" ? true : form.resolved === "no" ? false : null,
                  time_to_resolution: form.time_to_resolution || null,
                  issues: form.issues,
                  comments_positive: form.comments_positive || null,
                  comments_negative: form.comments_negative || null,
                  comments_other: form.comments_other || null,
                  would_use_again: form.would_use_again || null,
                  recommend_nps: form.recommend_nps || null,
                  contact_ok: form.contact_ok,
                  contact_email: form.contact_email || null,
                  user_agent: typeof navigator !== "undefined" ? navigator.userAgent : null,
                  page_url: typeof window !== "undefined" ? window.location.href : null,
                };
                const resp = await fetch("/api/feedback", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload),
                });
                if (!resp.ok) throw new Error("feedback_store_failed");
                const data = await resp.json();
                if (!data?.ok || data?.stored === false) {
                  throw new Error("feedback_not_stored");
                }
                try {
                  await logEvent({
                    session_id: sid,
                    participant_id: pid,
                    participant_group: participantGroup || undefined,
                    event: "submit",
                    component: "feedback_form",
                    label: "finish_conversation",
                    client_ts: Date.now(),
                    page_url: typeof window !== "undefined" ? window.location.href : undefined,
                    meta: payload,
                  });
                } catch {}
                try {
                  localStorage.removeItem("vc_session_id");
                  localStorage.removeItem("vc_scenario_id");
                } catch {}
                window.location.href = "/";
              } catch {
                alert("Sorry—could not save feedback. Please try again.");
              } finally {
                setSubmittingFeedback(false);
              }
            }}
          >
            <div className="feedback-body">
              <p className="muted">Thanks for chatting! Please rate your experience on these key dimensions (matches our AI evaluation criteria).</p>

              <div className="field-row">
                <label className="label">Overall Satisfaction</label>
                <div className="rating-stars" aria-label="Overall satisfaction">
                  {[1,2,3,4,5].map((n) => (
                    <button key={n} type="button" className={"star" + (form.rating_overall >= n ? " filled" : "")} onClick={() => setForm({ ...form, rating_overall: n })} aria-label={`${n} star${n>1?"s":""}`}>★</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Task Success: Did the assistant help you accomplish your goal?</label>
                <div className="rating-stars" aria-label="Task success rating">
                  {[1,2,3,4,5].map((n) => (
                    <button key={n} type="button" className={"star" + (form.rating_task_success >= n ? " filled" : "")} onClick={() => setForm({ ...form, rating_task_success: n })} aria-label={`${n} star${n>1?"s":""}`}>★</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Clarity: Were the responses clear and easy to understand?</label>
                <div className="rating-stars" aria-label="Clarity rating">
                  {[1,2,3,4,5].map((n) => (
                    <button key={n} type="button" className={"star" + (form.rating_clarity >= n ? " filled" : "")} onClick={() => setForm({ ...form, rating_clarity: n })} aria-label={`${n} star${n>1?"s":""}`}>★</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Empathy: Did the assistant acknowledge your situation appropriately?</label>
                <div className="rating-stars" aria-label="Empathy rating">
                  {[1,2,3,4,5].map((n) => (
                    <button key={n} type="button" className={"star" + (form.rating_empathy >= n ? " filled" : "")} onClick={() => setForm({ ...form, rating_empathy: n })} aria-label={`${n} star${n>1?"s":""}`}>★</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Accuracy: Was the information accurate and reliable?</label>
                <div className="rating-stars" aria-label="Accuracy rating">
                  {[1,2,3,4,5].map((n) => (
                    <button key={n} type="button" className={"star" + (form.rating_accuracy >= n ? " filled" : "")} onClick={() => setForm({ ...form, rating_accuracy: n })} aria-label={`${n} star${n>1?"s":""}`}>★</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Was your issue resolved?</label>
                <div className="seg" role="group" aria-label="Resolution">
                  {[
                    {v:"yes", t:"Yes"},
                    {v:"no", t:"No"},
                    {v:"partial", t:"Partially"},
                  ].map((opt) => (
                    <button key={opt.v} type="button" className={form.resolved === opt.v ? "active" : ""} onClick={() => setForm({ ...form, resolved: opt.v })}>{opt.t}</button>
                  ))}
                </div>
              </div>

              <div className="field-row">
                <label className="label">Additional comments (optional)</label>
                <textarea className="textarea" placeholder="Any feedback, suggestions, or concerns?" value={form.comments_other} onChange={(e) => setForm({ ...form, comments_other: e.target.value })} rows={3} />
              </div>
            </div>
            <div className="feedback-actions">
              <button type="submit" className="send-btn" disabled={submittingFeedback}>{submittingFeedback ? "Submitting…" : "Submit feedback"}</button>
            </div>
          </form>
        ) : (
          <div className="feedback-done">
            <h4>Thanks for your feedback!</h4>
            <p className="muted">We really appreciate you taking the time. Your responses help us improve VodaCare support.</p>
            <button className="send-btn" onClick={() => {
              try {
                localStorage.removeItem("vc_session_id");
                localStorage.removeItem("vc_scenario_id");
              } catch {}
              window.location.href = "/";
            }}>Close</button>
          </div>
        )}
      </div>
    </div>
  );
}
