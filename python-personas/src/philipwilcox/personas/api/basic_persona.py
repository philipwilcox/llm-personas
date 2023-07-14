from typing import Dict, Any, Optional, List

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.model.llm_facing_info import LlmFacingInfo
from src.philipwilcox.personas.api.model.persona_exception import PersonaException
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import (
    PersonaModelInitPromptTemplate,
)
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.api.persona_messenger import PersonaMessenger
from src.philipwilcox.personas.api.response_driven_persona import ResponseDrivenPersona


class BasicPersona(ResponseDrivenPersona):
    """This basic type is basically a passthrough to PersonaMessenger."""

    def __init__(
        self,
        init_prompt_template: PersonaModelInitPromptTemplate,
        template_kwargs: Dict[str, Any],
        open_ai: OpenAIWrapper,
        name: str,
        llm_facing_info: Optional[LlmFacingInfo] = None,
        resend_conversation_history: bool = True,
        streaming_console_mode: bool = False,
    ):
        # TODO: document that template_kwargs are what is PASSED IN to this agent's LLM prompt; LLM-facing-info is used to tell a PARENT COORDINATING LLM how to use this agent
        self.name = name
        self.llm_facing_info = llm_facing_info
        self.messenger = PersonaMessenger(
            init_prompt_template,
            template_kwargs,
            open_ai,
            resend_conversation_history=resend_conversation_history,
            streaming_console_mode=streaming_console_mode,
        )

    def get_name(self) -> str:
        # TODO: can I put name in the abstract base one and avoid this boilerplate every time?
        return self.name

    async def send_message(self, message: str) -> ProposedPersonaResponse:
        r = await self.messenger.send(PersonaMessage.create_user_message(message))
        return ProposedPersonaResponse(r.content)

    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        if len(history.subhistories) > 0:
            raise PersonaException(
                "A BasicPersona without delegation cannot be instantiated from history that includes sub-persona histories"
            )
        self.messenger.history = history.messages

    def get_history(self) -> ResponseDrivenPersonaHistory:
        # For a non-delegating agent "history" vs "final history" is the same
        return ResponseDrivenPersonaHistory(
            self.messenger.history, self.messenger.history, {}
        )

    async def send_message_and_process_autonomously(self, message: str) -> str:
        return (await self.send_message(message)).message

    def get_llm_facing_info(self) -> LlmFacingInfo:
        if self.llm_facing_info:
            return self.llm_facing_info
        else:
            raise PersonaException(
                "No `llm_facing_info` passed to this BasicPersona constructor; cannot call get_llm_facing_info without it"
            )

    def get_last_assistant_response(self) -> Optional[ProposedPersonaResponse]:
        assistant_messages = [
            m for m in self.messenger.history if m.is_assistant_message()
        ]
        if len(assistant_messages) == 0:
            return None
        else:
            last_message = assistant_messages[-1]
            return ProposedPersonaResponse(last_message.content)
