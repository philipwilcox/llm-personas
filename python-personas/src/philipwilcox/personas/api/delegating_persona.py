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
from src.philipwilcox.personas.api.persona_message_delegator import (
    PersonaMessageDelegator,
)
from src.philipwilcox.personas.api.response_driven_persona import ResponseDrivenPersona


class DelegatingPersona(ResponseDrivenPersona):
    def __init__(self, delegator: PersonaMessageDelegator):
        self.delegator = delegator

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    async def send_message(self, message: str) -> ProposedPersonaResponse:
        pass

    @abc.abstractmethod
    async def process_proposed_response(
        self, proposed_response: ProposedPersonaResponse
    ) -> ProposedPersonaResponse:
        pass

    @abc.abstractmethod
    def get_history(self) -> ResponseDrivenPersonaHistory:
        pass

    @abc.abstractmethod
    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        pass

    @abc.abstractmethod
    async def send_message_and_process_autonomously(self, message: str) -> Any:
        pass

    @abc.abstractmethod
    async def process_final_response(
        self, proposed_response: ProposedPersonaResponse
    ) -> Any:
        pass

    def get_response_format_instructions(self) -> str:
        return (
            "You should respond with three consecutive Markdown multi-line code "
            'blocks. The first one should follow a header of "Reasoning" and describe '
            "your reasoning for the selection. The second one should follow a header of "
            '"Message" and should contain just the string text of the message you wish to send to the next '
            'persona. The third one should follow a header of "Recipient" and should '
            'have the name of the recipient persona to which you\'re delegating.\n\nHere are some examples:\n"""\n## Reasoning\n```\nThe reasoning for this step reasoning goes here.\n```\n\n## Message\n```\nThis is a sample message to the next subpersona.\n```\n\n## Recipient\n```\nExample Persona (Equation Processor)\n```\n"""\n\n"""\n## Reasoning\n```\nWe need to hand this off to the goal evaluator persona.\n```\n\n## Message\n```\nDid this message align with our goals: Pizza is awesome!.\n```\n\n## Recipient\n```\nExample Persona (Goal Evaluator)\n```\n"""\n'
        )

    def get_subpersona_by_name(self, name: str) -> ResponseDrivenPersona:
        return self.delegator.get_subpersona_by_name(name)

    def get_llm_facing_info(self) -> LlmFacingInfo:
        raise PersonaException(
            "LLM-facing info not implemented for this Persona, please implement this to return a dict of strings for use in prompting a coordinating persona's LLM if desired."
        )

    def get_last_assistant_response(self) -> Optional[ProposedPersonaResponse]:
        # Local import to prevent circular dep vs shoving these into one file. :(
        from src.philipwilcox.personas.api.model.response_driven_persona_flat_history import (
            ResponseDrivenPersonaFlatHistory,
        )

        flat_history = ResponseDrivenPersonaFlatHistory.from_nested_history(
            self.get_history(), self
        )
        assistant_messages = [
            m
            for m in flat_history.messages
            if isinstance(m.message, AssistantPersonaMessage)
        ]
        if len(assistant_messages) == 0:
            return None
        else:
            last_message = assistant_messages[-1]
            if len(last_message.stack) > 0:
                # go directly to the source
                last_agent = last_message.stack[-1]
                return last_agent.get_last_assistant_response()
            else:
                # parse my own last messsage to recreate my delegation info
                new_pr = ProposedPersonaResponse.from_markdown_response(
                    last_message.message.content
                )
                return new_pr
