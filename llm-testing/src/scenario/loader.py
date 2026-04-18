import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .models import Scenario


class ScenarioLoader:

    def __init__(self, scenarios_dir: Optional[Path] = None):
        if scenarios_dir is None:
            scenarios_dir = Path(__file__).parent.parent.parent / "data" / "scenarios"
        self.scenarios_dir = Path(scenarios_dir)
        if not self.scenarios_dir.exists():
            raise FileNotFoundError(f"Scenarios directory not found: {self.scenarios_dir}")
        self._cache: Dict[str, Scenario] = {}

    def load(self, scenario_id: str) -> Scenario:
        if scenario_id in self._cache:
            return self._cache[scenario_id]
        scenario_file = self.scenarios_dir / f"{scenario_id}.yaml"
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
        with open(scenario_file, 'r') as f:
            data = yaml.safe_load(f)
        try:
            scenario = Scenario(**data)
        except Exception as e:
            raise ValueError(f"Invalid scenario YAML in {scenario_file}: {e}") from e
        self._cache[scenario_id] = scenario
        return scenario

    def load_all(self) -> List[Scenario]:
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
        return scenarios

    def list_available(self) -> List[str]:
        return [f.stem for f in sorted(self.scenarios_dir.glob("*.yaml"))]

    def clear_cache(self):
        self._cache.clear()
