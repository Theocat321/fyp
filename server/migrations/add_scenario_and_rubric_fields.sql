-- Add scenario_id to participants table
ALTER TABLE participants
ADD COLUMN IF NOT EXISTS scenario_id TEXT;

-- Add scenario_id and rubric ratings to support_feedback table
ALTER TABLE support_feedback
ADD COLUMN IF NOT EXISTS scenario_id TEXT,
ADD COLUMN IF NOT EXISTS rating_task_success INTEGER CHECK (rating_task_success >= 1 AND rating_task_success <= 5),
ADD COLUMN IF NOT EXISTS rating_clarity INTEGER CHECK (rating_clarity >= 1 AND rating_clarity <= 5),
ADD COLUMN IF NOT EXISTS rating_empathy INTEGER CHECK (rating_empathy >= 1 AND rating_empathy <= 5),
ADD COLUMN IF NOT EXISTS rating_accuracy INTEGER CHECK (rating_accuracy >= 1 AND rating_accuracy <= 5);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_participants_scenario_id ON participants(scenario_id);
CREATE INDEX IF NOT EXISTS idx_support_feedback_scenario_id ON support_feedback(scenario_id);

-- Add comments for documentation
COMMENT ON COLUMN participants.scenario_id IS 'Scenario ID selected for testing session (e.g., scenario_001_esim_setup)';
COMMENT ON COLUMN support_feedback.scenario_id IS 'Scenario ID for this feedback session';
COMMENT ON COLUMN support_feedback.rating_task_success IS 'Rubric rating: Did assistant help accomplish goal? (1-5)';
COMMENT ON COLUMN support_feedback.rating_clarity IS 'Rubric rating: How clear were responses? (1-5)';
COMMENT ON COLUMN support_feedback.rating_empathy IS 'Rubric rating: How well did assistant acknowledge situation? (1-5)';
COMMENT ON COLUMN support_feedback.rating_accuracy IS 'Rubric rating: Information accuracy without unsupported claims? (1-5)';
