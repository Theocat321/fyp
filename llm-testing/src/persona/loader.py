import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .models import Persona


class PersonaLoader:

    def __init__(self, personas_dir: Optional[Path] = None):
        if personas_dir is None:
            personas_dir = Path(__file__).parent.parent.parent / "data" / "personas"
        self.personas_dir = Path(personas_dir)
        if not self.personas_dir.exists():
            raise FileNotFoundError(f"Personas directory not found: {self.personas_dir}")
        self._cache: Dict[str, Persona] = {}

    def load(self, persona_id: str) -> Persona:
        if persona_id in self._cache:
            return self._cache[persona_id]
        persona_file = self.personas_dir / f"{persona_id}.yaml"
        if not persona_file.exists():
            raise FileNotFoundError(f"Persona file not found: {persona_file}")
        with open(persona_file, 'r') as f:
            data = yaml.safe_load(f)
        try:
            persona = Persona(**data)
        except Exception as e:
            raise ValueError(f"Invalid persona YAML in {persona_file}: {e}") from e
        self._cache[persona_id] = persona
        return persona

    def load_all(self) -> List[Persona]:
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
        return personas

    def list_available(self) -> List[str]:
        return [f.stem for f in sorted(self.personas_dir.glob("*.yaml"))]

    def clear_cache(self):
        self._cache.clear()
