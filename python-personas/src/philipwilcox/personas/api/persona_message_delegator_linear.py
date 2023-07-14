import dataclasses
from typing import Optional, Callable, Sequence, List

from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.api.persona_message_delegator import (
    PersonaMessageDelegator,
)
from src.philipwilcox.personas.api.response_driven_persona import (
    ResponseDrivenPersona,
)


@dataclasses.dataclass
class PersonaDelegationInfoLinear:
    delegate_personas: Sequence[ResponseDrivenPersona]
    next_message_builder: Optional[
        Callable[[ResponseDrivenPersona, str, str], str]
    ] = None

    def __post_init__(self) -> None:
        self.delegate_personas_by_name = {}
        for p in self.delegate_personas:
            self.delegate_personas_by_name[p.get_name()] = p


class PersonaMessageDelegatorLinear(PersonaMessageDelegator):
    def __init__(self, delegation_info: PersonaDelegationInfoLinear):
        self.delegation_info = delegation_info
        self.next_delegate_index: int = 0
        self.current_delegate: Optional[ResponseDrivenPersona] = None
        self.current_inbound_message: Optional[str] = None
        self.history: List[PersonaMessage] = []

    async def send_message(self, message: str) -> ProposedPersonaResponse:
        if self.current_delegate is None:
            self.current_inbound_message = message
            self.history.append(PersonaMessage.create_user_message(message))
            next_delegate = self.delegation_info.delegate_personas[
                self.next_delegate_index
            ]
            self.next_delegate_index += 1
            self.current_delegate = next_delegate
        return await self.current_delegate.send_message(message)

    async def process_proposed_response(
        self, pr: ProposedPersonaResponse
    ) -> ProposedPersonaResponse:
        assert self.current_delegate
        last_delegate = self.current_delegate

        # TODO: test on state restoration for this version
        if self.delegation_info.next_message_builder:
            assert self.current_inbound_message
            next_message = self.delegation_info.next_message_builder(
                last_delegate, pr.message, self.current_inbound_message
            )
        else:
            next_message = pr.message
        if self.next_delegate_index == len(self.delegation_info.delegate_personas):
            self.current_inbound_message = None
            self.next_delegate_index = 0
            self.current_delegate = None
            self.history.append(PersonaMessage.create_assistant_message(next_message))
            return ProposedPersonaResponse(next_message)
        else:
            next_delegate = self.delegation_info.delegate_personas[
                self.next_delegate_index
            ]
            self.next_delegate_index += 1
            self.current_delegate = next_delegate
            return await self.current_delegate.send_message(next_message)

    def get_history(self) -> ResponseDrivenPersonaHistory:
        return ResponseDrivenPersonaHistory(
            self.history,
            self.history,  # no coordinating messages vs final message distinction for Linear delegator
            {
                name: persona.get_history()
                for name, persona in self.delegation_info.delegate_personas_by_name.items()
            },
        )

    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        self.history = history.messages
        for n, h in history.subhistories.items():
            self.delegation_info.delegate_personas_by_name[n].set_history(h)
        # TODO: set current delegate appropriately, set current inbound appropriately

    def is_in_processing_loop(self) -> bool:
        return self.current_inbound_message is not None

    def get_subpersona_by_name(self, name: str) -> ResponseDrivenPersona:
        return self.delegation_info.delegate_personas_by_name[name]
