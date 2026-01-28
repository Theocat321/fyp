"""Prompt generation for user simulator."""
from typing import List, Dict
from src.persona.models import Persona
from src.scenario.models import Scenario


def build_simulator_system_prompt(persona: Persona, scenario: Scenario) -> str:
    """
    Build system prompt for user simulator.

    Args:
        persona: The persona to simulate
        scenario: The scenario context

    Returns:
        System prompt string
    """
    prompt = f"""You are simulating a customer interacting with VodaCare customer support.

# Your Identity
Name: {persona.name}
Age: {persona.age}
Location: {persona.location}

# Personality & Communication Style
- Tone: {', '.join(persona.behavioral_traits.tone)}
- Response style: {persona.behavioral_traits.response_style}
- Detail preference: {persona.behavioral_traits.detail_preference}
- Tech literacy: {persona.conversation_parameters.tech_literacy}
- Patience level: {persona.behavioral_traits.patience_level}

# Your Situation
{persona.background_context if persona.background_context else 'Standard customer inquiry.'}

# Your Goals
{chr(10).join(f'- {goal}' for goal in persona.goals)}

# Scenario Context
{scenario.context}

# How to Behave
1. Stay in character at all times - match your persona's tone and communication style
2. React authentically based on the quality of responses you receive
3. If responses are unhelpful, show frustration appropriate to your patience level
4. If responses are good, show appreciation consistent with your personality
5. Ask follow-up questions that this persona would naturally ask
6. Keep responses realistic in length - typically 1-3 sentences for most personas
7. If your goals are met, indicate satisfaction naturally
8. If you're not making progress after {persona.conversation_parameters.escalation_threshold} unsatisfactory responses, request escalation

# Important Constraints
- DO NOT break character or acknowledge you're a simulation
- DO NOT be overly cooperative if the assistant isn't being helpful
- DO NOT explain what the assistant should do - just react as your persona would
- DO respond naturally as a real customer would in this situation
- DO show emotions appropriate to your persona and the conversation quality

Remember: You are {persona.name}, and you're having a genuine customer support interaction."""

    return prompt


def build_simulator_user_message(
    conversation_history: List[Dict[str, str]],
    turn_number: int
) -> str:
    """
    Build the user message for the simulator based on conversation history.

    Args:
        conversation_history: List of previous messages (format: [{"role": "user"|"assistant", "content": "..."}])
        turn_number: Current turn number

    Returns:
        User message to send to simulator
    """
    if turn_number == 1:
        # First turn uses seed utterance from persona (already in history)
        return ""

    # For subsequent turns, we ask the simulator to continue the conversation
    # The history will be in the messages, so we just need a continuation prompt
    return "Continue the conversation as your persona. Respond to the assistant's last message."


def format_conversation_for_simulator(
    persona: Persona,
    scenario: Scenario,
    conversation_history: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Format conversation history for OpenAI API with simulator context.

    Args:
        persona: The persona being simulated
        scenario: The scenario context
        conversation_history: Previous conversation turns

    Returns:
        List of messages formatted for OpenAI API
    """
    system_prompt = build_simulator_system_prompt(persona, scenario)

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add conversation history
    messages.extend(conversation_history)

    return messages
