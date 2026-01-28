"""Loader for persona YAML files."""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .models import Persona


class PersonaLoader:
    """Loads and caches persona definitions from YAML files."""

    def __init__(self, personas_dir: Optional[Path] = None):
        """
        Initialize the persona loader.

        Args:
            personas_dir: Directory containing persona YAML files.
                         Defaults to data/personas/ relative to project root.
        """
        if personas_dir is None:
            # Default to data/personas relative to project root
            project_root = Path(__file__).parent.parent.parent
            personas_dir = project_root / "data" / "personas"

        self.personas_dir = Path(personas_dir)
        if not self.personas_dir.exists():
            raise FileNotFoundError(
                f"Personas directory not found: {self.personas_dir}"
            )

        self._cache: Dict[str, Persona] = {}

    def load(self, persona_id: str) -> Persona:
        """
        Load a persona by ID.

        Args:
            persona_id: The persona identifier (e.g., "persona_001_frustrated_commuter")

        Returns:
            Persona object

        Raises:
            FileNotFoundError: If persona file doesn't exist
            ValueError: If YAML is invalid
        """
        # Check cache first
        if persona_id in self._cache:
            return self._cache[persona_id]

        # Find the YAML file
        persona_file = self.personas_dir / f"{persona_id}.yaml"
        if not persona_file.exists():
            raise FileNotFoundError(
                f"Persona file not found: {persona_file}"
            )

        # Load and validate
        with open(persona_file, 'r') as f:
            data = yaml.safe_load(f)

        try:
            persona = Persona(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid persona YAML in {persona_file}: {e}"
            ) from e

        # Cache and return
        self._cache[persona_id] = persona
        return persona

    def load_all(self) -> List[Persona]:
        """
        Load all personas from the directory.

        Returns:
            List of all Persona objects
        """
        personas = []
        for yaml_file in sorted(self.personas_dir.glob("*.yaml")):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            try:
                persona = Persona(**data)
                self._cache[persona.id] = persona
                personas.append(persona)
            except Exception as e:
                print(f"Warning: Skipping invalid persona file {yaml_file}: {e}")
                continue

        return personas

    def list_available(self) -> List[str]:
        """
        List all available persona IDs.

        Returns:
            List of persona IDs
        """
        return [
            yaml_file.stem
            for yaml_file in sorted(self.personas_dir.glob("*.yaml"))
        ]

    def clear_cache(self):
        """Clear the persona cache."""
        self._cache.clear()
