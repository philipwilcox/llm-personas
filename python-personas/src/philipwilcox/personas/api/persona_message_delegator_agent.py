import dataclasses
import json
import logging
from typing import Optional, Sequence, List

from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_flat_history import (
    ResponseDrivenPersonaFlatHistory,
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


logger = logging.getLogger(
    __name__
)  # TODO: compare this type of logger-getting to the MethodHeirarchyVisitor stuff


@dataclasses.dataclass
class PersonaDelegationInfoAgent:
    delegate_personas: Sequence[ResponseDrivenPersona]
    coordinating_persona: ResponseDrivenPersona
    root_persona: DelegatingPersona

    def __post_init__(self) -> None:
        self.delegate_personas_by_name = {}
        for p in self.delegate_personas:
            self.delegate_personas_by_name[p.get_name()] = p


class PersonaMessageDelegatorAgent(PersonaMessageDelegator):
    def __init__(self, delegation_info: PersonaDelegationInfoAgent):
        self.delegation_info = delegation_info
        self.current_delegate: Optional[ResponseDrivenPersona] = None
        self.current_inbound_message: Optional[str] = None
        self.final_history: List[PersonaMessage] = []

    async def send_message(self, message: str) -> ProposedPersonaResponse:
        if self.current_delegate is None:
            self.current_inbound_message = message
            self.final_history.append(PersonaMessage.create_user_message(message))
            coordinator_response = (
                await self.delegation_info.coordinating_persona.send_message(message)
            )
            # TODO: might still need to make this safer
            # TODO: fix this for history restore too
            return ProposedPersonaResponse.from_markdown_response(
                coordinator_response.message
            )
        else:
            delegated_response = await self.current_delegate.send_message(message)
            return delegated_response

    async def process_proposed_response(
        self, pr: ProposedPersonaResponse
    ) -> ProposedPersonaResponse:
        if self.current_delegate is None:
            new_delegate_name = pr.recipient
            assert new_delegate_name
            # TODO: sometimes my current prompts are wrapping this in too many quotes
            new_delegate = self.delegation_info.delegate_personas_by_name[
                new_delegate_name
            ]
            self.current_delegate = new_delegate
            return await self.current_delegate.send_message(pr.message)
        else:
            # TODO: this structure wouldn't allow us to close out multi-layer delegation...
            # TODO: for multi-layer delegation we'd need to check if CHILD was delegating too; we'd need an interface for that
            last_delgate = self.current_delegate
            self.current_delegate = None
            coordinating_message = (
                f"The response from {last_delgate.get_name()} was:\n\n{pr.message}"
            )
            logger.warning(f"SENDING COORDINATOR: {coordinating_message}")
            coordinator_response = (
                await self.delegation_info.coordinating_persona.send_message(
                    coordinating_message
                )
            )
            logger.warning(
                f"Got {coordinator_response.message} after passing response from {last_delgate.get_name()}"
            )
            # TODO: is this going to work correctly for nested delegation as-is?
            new_pr = ProposedPersonaResponse.from_markdown_response(
                coordinator_response.message
            )
            # TODO: get rid of this after restructuring how we return ProposedPersonaResponse entirely
            if isinstance(new_pr.message, dict):
                new_pr.message = json.dumps(new_pr.message)
            if not new_pr.recipient:
                self.current_inbound_message = None
                self.final_history.append(
                    PersonaMessage.create_assistant_message(new_pr.message)
                )
            return new_pr

    def get_history(self) -> ResponseDrivenPersonaHistory:
        return ResponseDrivenPersonaHistory(
            self.delegation_info.coordinating_persona.get_history().messages,
            self.final_history,
            {
                name: persona.get_history()
                for name, persona in self.delegation_info.delegate_personas_by_name.items()
            },
        )

    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        bare_history = ResponseDrivenPersonaHistory(
            messages=history.messages,
            final_messages=history.final_messages,
            subhistories={},
        )
        self.delegation_info.coordinating_persona.set_history(bare_history)
        self.final_history = history.final_messages
        for n, h in history.subhistories.items():
            self.delegation_info.delegate_personas_by_name[n].set_history(h)
        flat_history = ResponseDrivenPersonaFlatHistory.from_nested_history(
            history, self.delegation_info.root_persona
        )
        if len(flat_history.messages) > 0:
            last_message = flat_history.messages[-1]
            if last_message.message.is_user_message():
                # If we have a user message as our last message, that means we saved before getting the most recent response
                # for that one, so let's discard it with a warning so the user can re-send
                # TODO: unit tests for this
                agent = last_message.stack[-1]
                agent_history = agent.get_history()
                agent_history.messages.pop()
                agent.set_history(agent_history)
            # Now let's find and set our current inbound message appropriately
            # TODO: test this for nesting
            if len(self.final_history) > 0:
                last_top_level_message = self.final_history[-1]
                # Last inbound is last top level (final) message IFF the last one was an inbound User message we haven't replied to
                if last_top_level_message.is_user_message():
                    self.current_inbound_message = last_top_level_message.content

            # TODO: should we rethink our outer state history structure? This is getting rough - but also need to support both Agent and Linear?
            # Now let's find and set our current delegate appropriately
            assistant_messages = [
                m for m in flat_history.messages if m.message.is_assistant_message()
            ]
            if len(assistant_messages) > 0:
                # TODO: when we do nested personas we'll need to test/debug this extensively
                last_assistant_message = assistant_messages[-1]
                last_stack = last_assistant_message.stack
                last_was_self = False
                for potential_agent in last_stack:
                    if last_was_self:
                        self.current_delegate = potential_agent
                        break
                    elif potential_agent == self.delegation_info.root_persona:
                        last_was_self = True

    def is_in_processing_loop(self) -> bool:
        return self.current_inbound_message is not None

    def get_subpersona_by_name(self, name: str) -> ResponseDrivenPersona:
        return self.delegation_info.delegate_personas_by_name[name]
