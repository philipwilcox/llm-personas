import abc
import logging
from typing import Optional

from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.api.response_driven_persona import (
    ResponseDrivenPersona,
)


logger = logging.getLogger(
    __name__
)  # TODO: compare this type of logger-getting to the MethodHeirarchyVisitor stuff


class PersonaMessageDelegator(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        # Note: this dummy init is the least-annoying way I can find to make mypy know all instances of this should have this property
        self.current_delegate: Optional[ResponseDrivenPersona] = None

    @abc.abstractmethod
    async def send_message(self, message: str) -> ProposedPersonaResponse:
        pass

    @abc.abstractmethod
    async def process_proposed_response(
        self, pr: ProposedPersonaResponse
    ) -> ProposedPersonaResponse:
        pass

    @abc.abstractmethod
    def get_history(self) -> ResponseDrivenPersonaHistory:
        pass

    @abc.abstractmethod
    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        pass

    @abc.abstractmethod
    def is_in_processing_loop(self) -> bool:
        pass

    @abc.abstractmethod
    def get_subpersona_by_name(self, name: str) -> ResponseDrivenPersona:
        pass
