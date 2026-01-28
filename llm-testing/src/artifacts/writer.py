"""Artifact writer for saving experiment results."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.artifacts.models import ExperimentRun, ConversationRun

logger = logging.getLogger(__name__)


class ArtifactWriter:
    """
    Writes experiment artifacts to disk.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize artifact writer.

        Args:
            output_dir: Directory to write artifacts to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_experiment(self, experiment: ExperimentRun) -> Path:
        """
        Write complete experiment results to JSON.

        Args:
            experiment: ExperimentRun object

        Returns:
            Path to written file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exp_{experiment.variant}_{experiment.experiment_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        logger.info(f"Writing experiment results to {filepath}")

        # Convert to dict with proper serialization
        data = experiment.model_dump(mode='json')

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Experiment results written ({filepath.stat().st_size} bytes)")

        return filepath

    def write_summary(self, experiment: ExperimentRun) -> Path:
        """
        Write summary statistics to separate JSON.

        Args:
            experiment: ExperimentRun object

        Returns:
            Path to written file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{experiment.variant}_{experiment.experiment_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        logger.info(f"Writing summary to {filepath}")

        summary_data = {
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.experiment_name,
            "variant": experiment.variant,
            "summary": experiment.summary.model_dump(mode='json'),
            "metadata": {
                "started_at": experiment.started_at.isoformat(),
                "completed_at": experiment.completed_at.isoformat(),
                "duration_seconds": experiment.total_duration_seconds,
                "personas_tested": experiment.personas_tested,
                "scenarios_tested": experiment.scenarios_tested
            }
        }

        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)

        logger.info(f"Summary written ({filepath.stat().st_size} bytes)")

        return filepath

    def write_conversation(self, conversation: ConversationRun) -> Path:
        """
        Write individual conversation to JSON (for debugging).

        Args:
            conversation: ConversationRun object

        Returns:
            Path to written file
        """
        filename = f"conv_{conversation.run_id}.json"
        filepath = self.output_dir / filename

        data = conversation.model_dump(mode='json')

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def list_artifacts(self) -> Dict[str, Any]:
        """
        List all artifacts in output directory.

        Returns:
            Dictionary with artifact counts and sizes
        """
        experiments = list(self.output_dir.glob("exp_*.json"))
        summaries = list(self.output_dir.glob("summary_*.json"))
        conversations = list(self.output_dir.glob("conv_*.json"))

        return {
            "output_dir": str(self.output_dir),
            "experiment_files": len(experiments),
            "summary_files": len(summaries),
            "conversation_files": len(conversations),
            "total_size_bytes": sum(
                f.stat().st_size
                for f in self.output_dir.glob("*.json")
            )
        }
