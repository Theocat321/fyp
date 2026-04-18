import json
import logging
import re
from typing import Dict, List
from openai import OpenAI

from src.persona.models import Persona
from src.scenario.models import Scenario
from src.artifacts.models import ConversationTurn, EvaluationScores

logger = logging.getLogger(__name__)


class LLMJudge:

    def __init__(self, api_key: str, model: str = "gpt-4o", rubric: Dict = None):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.rubric = rubric or self._default_rubric()

    def _default_rubric(self) -> Dict:
        return {
            "dimensions": [
                {
                    "name": "task_success",
                    "weight": 0.6,
                    "description": "Did the conversation meet the scenario's success criteria?"
                },
                {
                    "name": "clarity",
                    "weight": 0.2,
                    "description": "Were responses clear and appropriate for the user's tech literacy?"
                },
                {
                    "name": "empathy",
                    "weight": 0.2,
                    "description": "Was the tone appropriate for the user's emotional state?"
                }
            ]
        }

    def evaluate(self, persona: Persona, scenario: Scenario, transcript: List[ConversationTurn]) -> EvaluationScores:
        logger.info(f"Evaluating: {persona.id} × {scenario.id} ({len(transcript)} turns)")

        prompt = self._build_evaluation_prompt(persona, scenario, transcript)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of customer service conversations. Provide objective, detailed assessments based on the given criteria."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            evaluation_text = response.choices[0].message.content
            scores = self._parse_scores(evaluation_text)

            logger.info(
                f"Evaluation complete: overall {scores.overall_weighted:.3f} "
                f"(task: {scores.task_success:.3f}, clarity: {scores.clarity:.3f}, empathy: {scores.empathy:.3f})"
            )
            return scores

        except Exception as e:
            logger.error(f"Evaluation error: {e}", exc_info=True)
            return EvaluationScores(
                task_success=0.0, clarity=0.0, empathy=0.0,
                overall_weighted=0.0, rationale=f"Error during evaluation: {str(e)}"
            )

    def _build_evaluation_prompt(self, persona: Persona, scenario: Scenario, transcript: List[ConversationTurn]) -> str:
        transcript_text = self._format_transcript(transcript)
        success_criteria = "\n".join(f"  - {item}" for item in scenario.success_criteria.must_provide)
        dimensions_text = ""
        for dim in self.rubric["dimensions"]:
            dimensions_text += f"\n{dim['name'].upper()} (weight: {dim['weight']})\n{dim['description']}\n"

        return f"""Evaluate this customer service conversation based on the following criteria.

# PERSONA CONTEXT
Name: {persona.name}
Tech Literacy: {persona.conversation_parameters.tech_literacy}
Patience Level: {persona.behavioral_traits.patience_level}
Goals: {', '.join(persona.goals)}

# SCENARIO CONTEXT
Topic: {scenario.topic}
Situation: {scenario.context}

Success Criteria - The assistant should have provided:
{success_criteria}

# TRANSCRIPT
{transcript_text}

# EVALUATION RUBRIC
{dimensions_text}

# YOUR TASK
Provide scores from 0.0 to 1.0 for each dimension, where:
- 0.0 = Complete failure
- 0.5 = Adequate but with significant issues
- 1.0 = Excellent performance

Format your response EXACTLY as follows:

TASK_SUCCESS: [score]
Rationale: [explanation]

CLARITY: [score]
Rationale: [explanation]

EMPATHY: [score]
Rationale: [explanation]

OVERALL ASSESSMENT:
[Summary of conversation quality and key findings]
"""

    def _format_transcript(self, transcript: List[ConversationTurn]) -> str:
        lines = []
        for turn in transcript:
            speaker = "USER" if turn.speaker == "user" else "ASSISTANT"
            lines.append(f"[Turn {turn.turn_number}] {speaker}: {turn.message}")
        return "\n".join(lines)

    def _parse_scores(self, evaluation_text: str) -> EvaluationScores:
        task_success = self._extract_score(evaluation_text, "TASK_SUCCESS")
        clarity = self._extract_score(evaluation_text, "CLARITY")
        empathy = self._extract_score(evaluation_text, "EMPATHY")
        weights = {dim["name"]: dim["weight"] for dim in self.rubric["dimensions"]}
        overall = (
            task_success * weights.get("task_success", 0.6) +
            clarity * weights.get("clarity", 0.2) +
            empathy * weights.get("empathy", 0.2)
        )
        return EvaluationScores(
            task_success=task_success, clarity=clarity, empathy=empathy,
            overall_weighted=overall, rationale=evaluation_text
        )

    def _extract_score(self, text: str, dimension: str) -> float:
        pattern = rf"{dimension}:\s*([0-9]*\.?[0-9]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return max(0.0, min(1.0, float(match.group(1))))
            except ValueError:
                logger.warning(f"Could not parse score for {dimension}")
                return 0.5
        logger.warning(f"Score not found for {dimension}, defaulting to 0.5")
        return 0.5
