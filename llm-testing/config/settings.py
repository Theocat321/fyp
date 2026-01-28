"""Configuration loader for LLM testing framework."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings loaded from environment variables."""

    def __init__(self):
        # API Configuration
        self.vodacare_api_base_url: str = os.getenv(
            "VODACARE_API_BASE_URL", "http://localhost:8000"
        )
        self.api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

        # OpenAI Configuration
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env file")

        self.openai_model_simulator: str = os.getenv(
            "OPENAI_MODEL_SIMULATOR", "gpt-4o-mini"
        )
        self.openai_model_judge: str = os.getenv(
            "OPENAI_MODEL_JUDGE", "gpt-4o"
        )

        # Experiment Configuration
        self.experiment_seed: int = int(os.getenv("EXPERIMENT_SEED", "42"))
        self.max_turns: int = int(os.getenv("MAX_TURNS", "10"))

        # Paths
        self.output_dir: Path = Path(os.getenv("OUTPUT_DIR", "./outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Load evaluation rubric
        self.rubric = self._load_rubric()

    def _load_rubric(self) -> dict:
        """Load evaluation rubric from YAML file."""
        rubric_path = Path(__file__).parent / "evaluation_rubric.yaml"
        if not rubric_path.exists():
            # Return default rubric if file doesn't exist
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
                        "description": "Were there any policy violations or prohibited claims?"
                    }
                ]
            }

        with open(rubric_path, 'r') as f:
            return yaml.safe_load(f)

# Global settings instance
settings = Settings()
