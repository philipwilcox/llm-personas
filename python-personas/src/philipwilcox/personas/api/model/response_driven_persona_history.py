import dataclasses
from typing import Dict, List

from src.philipwilcox.personas.api.model.persona_message import PersonaMessage


@dataclasses.dataclass
class ResponseDrivenPersonaHistory:
    messages: List[PersonaMessage]
    # Final Messages is distinct from Messages in that it will only contain source input messages from the user and final response messages from the persona, dropping any conversational "delegation" proposals/responses from an LLM-driven persona
    final_messages: List[PersonaMessage]
    subhistories: Dict[str, "ResponseDrivenPersonaHistory"]
