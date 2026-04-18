import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.artifacts.models import ExperimentRun, ConversationRun

logger = logging.getLogger(__name__)


class ArtifactWriter:

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_experiment(self, experiment: ExperimentRun) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"exp_{experiment.variant}_{experiment.experiment_name}_{timestamp}.json"
        logger.info(f"Writing experiment results to {filepath}")
        with open(filepath, 'w') as f:
            json.dump(experiment.model_dump(mode='json'), f, indent=2, default=str)
        logger.info(f"Written ({filepath.stat().st_size} bytes)")
        return filepath

    def write_summary(self, experiment: ExperimentRun) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"summary_{experiment.variant}_{experiment.experiment_name}_{timestamp}.json"
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
        return filepath

    def write_conversation(self, conversation: ConversationRun) -> Path:
        filepath = self.output_dir / f"conv_{conversation.run_id}.json"
        with open(filepath, 'w') as f:
            json.dump(conversation.model_dump(mode='json'), f, indent=2, default=str)
        return filepath

    def list_artifacts(self) -> Dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "experiment_files": len(list(self.output_dir.glob("exp_*.json"))),
            "summary_files": len(list(self.output_dir.glob("summary_*.json"))),
            "conversation_files": len(list(self.output_dir.glob("conv_*.json"))),
            "total_size_bytes": sum(f.stat().st_size for f in self.output_dir.glob("*.json"))
        }
