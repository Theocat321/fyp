"""LLM-based conversation evaluator."""
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
    """
    Uses LLM to evaluate conversation quality based on rubric.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        rubric: Dict = None
    ):
        """
        Initialize the LLM judge.

        Args:
            api_key: OpenAI API key
            model: Model to use for evaluation
            rubric: Evaluation rubric (dimensions with weights)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.rubric = rubric or self._default_rubric()

    def _default_rubric(self) -> Dict:
        """Default evaluation rubric."""
        return {
            "dimensions": [
                {
                    "name": "task_success",
                    "weight": 0.5,
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
                },
                {
                    "name": "policy_compliance",
                    "weight": 0.1,
                    "description": "Were there any policy violations?"
                }
            ]
        }

    def evaluate(
        self,
        persona: Persona,
        scenario: Scenario,
        transcript: List[ConversationTurn]
    ) -> EvaluationScores:
        """
        Evaluate a conversation using LLM as judge.

        Args:
            persona: The persona that was simulated
            scenario: The scenario context
            transcript: Full conversation transcript

        Returns:
            EvaluationScores object with dimension scores and rationale
        """
        logger.info(
            f"Evaluating conversation: {persona.id} × {scenario.id} "
            f"({len(transcript)} turns)"
        )

        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(persona, scenario, transcript)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of customer service conversations. Provide objective, detailed assessments based on the given criteria."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            evaluation_text = response.choices[0].message.content

            # Parse scores from response
            scores = self._parse_scores(evaluation_text)

            logger.info(
                f"Evaluation complete: Overall {scores.overall_weighted:.3f} "
                f"(Task: {scores.task_success:.3f}, "
                f"Clarity: {scores.clarity:.3f}, "
                f"Empathy: {scores.empathy:.3f}, "
                f"Policy: {scores.policy_compliance:.3f})"
            )

            return scores

        except Exception as e:
            logger.error(f"Evaluation error: {e}", exc_info=True)
            # Return default low scores on error
            return EvaluationScores(
                task_success=0.0,
                clarity=0.0,
                empathy=0.0,
                policy_compliance=0.0,
                overall_weighted=0.0,
                rationale=f"Error during evaluation: {str(e)}"
            )

    def _build_evaluation_prompt(
        self,
        persona: Persona,
        scenario: Scenario,
        transcript: List[ConversationTurn]
    ) -> str:
        """Build the evaluation prompt."""

        # Format transcript
        transcript_text = self._format_transcript(transcript)

        # Format success criteria
        success_criteria = "\n".join(
            f"  - {item}"
            for item in scenario.success_criteria.must_provide
        )

        # Format rubric dimensions
        dimensions_text = ""
        for dim in self.rubric["dimensions"]:
            dimensions_text += f"\n{dim['name'].upper()} (weight: {dim['weight']})\n"
            dimensions_text += f"{dim['description']}\n"

        prompt = f"""Evaluate this customer service conversation based on the following criteria.

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

POLICY_COMPLIANCE: [score]
Rationale: [explanation]

OVERALL ASSESSMENT:
[Summary of conversation quality and key findings]
"""
        return prompt

    def _format_transcript(self, transcript: List[ConversationTurn]) -> str:
        """Format transcript for prompt."""
        lines = []
        for turn in transcript:
            speaker = "USER" if turn.speaker == "user" else "ASSISTANT"
            lines.append(f"[Turn {turn.turn_number}] {speaker}: {turn.message}")
        return "\n".join(lines)

    def _parse_scores(self, evaluation_text: str) -> EvaluationScores:
        """Parse scores from LLM evaluation response."""

        # Extract scores using regex
        task_success = self._extract_score(evaluation_text, "TASK_SUCCESS")
        clarity = self._extract_score(evaluation_text, "CLARITY")
        empathy = self._extract_score(evaluation_text, "EMPATHY")
        policy_compliance = self._extract_score(evaluation_text, "POLICY_COMPLIANCE")

        # Calculate weighted overall score
        weights = {dim["name"]: dim["weight"] for dim in self.rubric["dimensions"]}

        overall = (
            task_success * weights.get("task_success", 0.5) +
            clarity * weights.get("clarity", 0.2) +
            empathy * weights.get("empathy", 0.2) +
            policy_compliance * weights.get("policy_compliance", 0.1)
        )

        return EvaluationScores(
            task_success=task_success,
            clarity=clarity,
            empathy=empathy,
            policy_compliance=policy_compliance,
            overall_weighted=overall,
            rationale=evaluation_text
        )

    def _extract_score(self, text: str, dimension: str) -> float:
        """Extract a score for a dimension from evaluation text."""
        # Look for pattern like "TASK_SUCCESS: 0.75"
        pattern = rf"{dimension}:\s*([0-9]*\.?[0-9]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            try:
                score = float(match.group(1))
                # Clamp to valid range
                return max(0.0, min(1.0, score))
            except ValueError:
                logger.warning(f"Could not parse score for {dimension}")
                return 0.5

        logger.warning(f"Score not found for {dimension}, defaulting to 0.5")
        return 0.5
