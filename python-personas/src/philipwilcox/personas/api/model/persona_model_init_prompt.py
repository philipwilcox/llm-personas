import dataclasses
from typing import Any, Dict, List

from jinja2 import Template

from src.philipwilcox.personas.api.model.persona_message import PersonaMessage


@dataclasses.dataclass
class PersonaModelInitPromptTemplate:
    messages: List[PersonaMessage]

    def render(self, keyword_args: Dict[str, Any]) -> List[PersonaMessage]:
        return [
            PersonaMessage(m.role, Template(m.content).render(keyword_args))
            for m in self.messages
        ]
