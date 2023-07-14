import dataclasses
from typing import List

from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.api.response_driven_persona import ResponseDrivenPersona


@dataclasses.dataclass
class PersonaMessageWithStack:
    stack: List[ResponseDrivenPersona]
    message: PersonaMessage


@dataclasses.dataclass
class ResponseDrivenPersonaFlatHistory:
    messages: List[PersonaMessageWithStack]

    @staticmethod
    def from_nested_history(
        h: ResponseDrivenPersonaHistory, root_persona: DelegatingPersona
    ) -> "ResponseDrivenPersonaFlatHistory":
        all_messages = [PersonaMessageWithStack([root_persona], m) for m in h.messages]
        # TODO: make a recursive "all messages" iterator on ResponseDrivenPersonaHistory that I can use here + in hydration methods?
        # TODO: at least make CodeWriterAndRunnerPersona hydrator a library thing
        remaining_histories = [
            ([root_persona, root_persona.get_subpersona_by_name(k)], v)
            for k, v in h.subhistories.items()
        ]
        while remaining_histories:
            next_history = remaining_histories.pop(0)
            current_stack = next_history[0]
            current_agent = current_stack[-1]
            messages = next_history[1].messages
            all_messages += [
                PersonaMessageWithStack(current_stack, m) for m in messages
            ]
            if len(next_history[1].subhistories.items()) > 0:
                assert isinstance(current_agent, DelegatingPersona)
                child_histories = [
                    (current_stack + [current_agent.get_subpersona_by_name(k)], v)
                    for k, v in next_history[1].subhistories.items()
                ]
                remaining_histories += child_histories
        all_messages.sort(key=lambda x: x.message.timestamp)
        return ResponseDrivenPersonaFlatHistory(all_messages)

    # TODO: create a method to go the other way
