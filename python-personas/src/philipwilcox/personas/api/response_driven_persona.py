import abc
from typing import Any, Optional

from src.philipwilcox.personas.api.model.llm_facing_info import LlmFacingInfo
from src.philipwilcox.personas.api.model.persona_exception import PersonaException
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)


# TODO: GOAL - would be great if I could "chat-gpt" the stuff like "create a data class in a separate file, ProposedPersonaResponse, with..." instead of manually creating the file manually
class ResponseDrivenPersona(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    async def send_message(self, message: str) -> ProposedPersonaResponse:
        pass

    @abc.abstractmethod
    def get_history(self) -> ResponseDrivenPersonaHistory:
        pass

    @abc.abstractmethod
    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        pass

    @abc.abstractmethod
    def get_last_assistant_response(self) -> Optional[ProposedPersonaResponse]:
        """This is needed for resuming from history with a proper ProposedPersonaResponse"""

    @abc.abstractmethod
    # TODO: do I need this in BasicPersona? No? Or does it belong in DelegatingPersona?
    async def send_message_and_process_autonomously(self, message: str) -> Any:
        pass

    def get_llm_facing_info(self) -> LlmFacingInfo:
        raise PersonaException(
            "LLM-facing info not implemented for this Persona, please implement this to return a dict of strings for use in prompting a coordinating persona's LLM if desired."
        )
