"""Loader for scenario YAML files."""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .models import Scenario


class ScenarioLoader:
    """Loads and caches scenario definitions from YAML files."""

    def __init__(self, scenarios_dir: Optional[Path] = None):
        """
        Initialize the scenario loader.

        Args:
            scenarios_dir: Directory containing scenario YAML files.
                          Defaults to data/scenarios/ relative to project root.
        """
        if scenarios_dir is None:
            # Default to data/scenarios relative to project root
            project_root = Path(__file__).parent.parent.parent
            scenarios_dir = project_root / "data" / "scenarios"

        self.scenarios_dir = Path(scenarios_dir)
        if not self.scenarios_dir.exists():
            raise FileNotFoundError(
                f"Scenarios directory not found: {self.scenarios_dir}"
            )

        self._cache: Dict[str, Scenario] = {}

    def load(self, scenario_id: str) -> Scenario:
        """
        Load a scenario by ID.

        Args:
            scenario_id: The scenario identifier (e.g., "scenario_001_esim_setup")

        Returns:
            Scenario object

        Raises:
            FileNotFoundError: If scenario file doesn't exist
            ValueError: If YAML is invalid
        """
        # Check cache first
        if scenario_id in self._cache:
            return self._cache[scenario_id]

        # Find the YAML file
        scenario_file = self.scenarios_dir / f"{scenario_id}.yaml"
        if not scenario_file.exists():
            raise FileNotFoundError(
                f"Scenario file not found: {scenario_file}"
            )

        # Load and validate
        with open(scenario_file, 'r') as f:
            data = yaml.safe_load(f)

        try:
            scenario = Scenario(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid scenario YAML in {scenario_file}: {e}"
            ) from e

        # Cache and return
        self._cache[scenario_id] = scenario
        return scenario

    def load_all(self) -> List[Scenario]:
        """
        Load all scenarios from the directory.

        Returns:
            List of all Scenario objects
        """
        scenarios = []
        for yaml_file in sorted(self.scenarios_dir.glob("*.yaml")):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            try:
                scenario = Scenario(**data)
                self._cache[scenario.id] = scenario
                scenarios.append(scenario)
            except Exception as e:
                print(f"Warning: Skipping invalid scenario file {yaml_file}: {e}")
                continue

        return scenarios

    def list_available(self) -> List[str]:
        """
        List all available scenario IDs.

        Returns:
            List of scenario IDs
        """
        return [
            yaml_file.stem
            for yaml_file in sorted(self.scenarios_dir.glob("*.yaml"))
        ]

    def clear_cache(self):
        """Clear the scenario cache."""
        self._cache.clear()
