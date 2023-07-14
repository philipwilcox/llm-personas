import json
import logging
from typing import List, Dict

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.basic_persona import (
    BasicPersona,
)
from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import (
    PersonaModelInitPromptTemplate,
)
from src.philipwilcox.personas.api.persona_message_delegator_agent import (
    PersonaDelegationInfoAgent,
    PersonaMessageDelegatorAgent,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.api.response_driven_persona import (
    ResponseDrivenPersona,
)
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.fiction.character_dialogue_personas import (
    CharacterDialoguePersonas,
)

logger = logging.getLogger(__name__)


class CharacterDialogueAgentOrchestrationPersona(DelegatingPersona):
    INIT_MESSAGES = PersonaModelInitPromptTemplate(
        [
            PersonaMessage.create_system_message("{{ character_oneliner }}"),
            PersonaMessage.create_user_message(
                '''{{ character_oneliner}}

Your current goals are:
{% for goal in goals %}
"""
{{ goal }}
"""
{% endfor %}

When another character speaks to you, please respond with what your natural response would be, given your own attributes and your current mood. Pay close attention to your goals and personality.

Input lines will come in the form of a JSON string representing a dictionary with several keys: "name" representing the name of the person you are addressing (or "" or None if unknown at this point); "line" with the text of what they said; and "mood" with your current mood.

Your response should take into account your current mood with this other person. Your response should be inside of a multi-line markdown code block, starting on the first line after the opening ```. It should be formatted as a JSON string representing a dictionary with three keys: "name", the name of the person you are addressing (or null or "" if unknown); "line", with the text of what you want to say to them; and "mood", your current mood.'''
            ),
        ]
    )

    def __init__(
        self,
        open_ai: OpenAIWrapper,
        name: str,
        character_oneliner: str,
        current_mood: str,
        current_goals: List[str],
        dialogue_examples: List[str],
        streaming_console_mode: bool = False,
    ) -> None:
        self.name = name
        self.initial_mood = current_mood
        goals_persona = CharacterDialoguePersonas.create_goals_persona(
            name, character_oneliner, current_goals, open_ai, streaming_console_mode
        )
        mood_persona = CharacterDialoguePersonas.create_mood_persona(
            name, character_oneliner, open_ai, streaming_console_mode
        )
        conversation_persona = CharacterDialoguePersonas.create_conversation_persona(
            name, character_oneliner, current_goals, open_ai, streaming_console_mode
        )
        rewriter_persona = CharacterDialoguePersonas.create_rewriter_persona(
            name,
            character_oneliner,
            dialogue_examples,
            open_ai,
            streaming_console_mode,
        )
        persona_list = [
            goals_persona,
            mood_persona,
            conversation_persona,
            rewriter_persona,
        ]
        coordinating_persona = BasicPersona(
            init_prompt_template=CharacterDialogueAgentOrchestrationPersona.INIT_MESSAGES,
            template_kwargs={
                "character_oneliner": character_oneliner,
                "available_personas": [
                    p.get_llm_facing_info().format_for_prompt(p.name)
                    for p in persona_list
                ],
                "mood": current_mood,
                "response_format": self.get_response_format_instructions(),
            },
            open_ai=open_ai,
            name=name + "(Coordinator)",
            resend_conversation_history=True,
            streaming_console_mode=streaming_console_mode,
        )
        delegation_info = PersonaDelegationInfoAgent(
            persona_list, coordinating_persona, self
        )
        DelegatingPersona.__init__(self, PersonaMessageDelegatorAgent(delegation_info))

    def get_name(self) -> str:
        return self.name

    async def send_message(self, message: str) -> ProposedPersonaResponse:
        return await self.delegator.send_message(message)

    async def process_proposed_response(
        self, proposed_response: ProposedPersonaResponse
    ) -> ProposedPersonaResponse:
        return await self.delegator.process_proposed_response(proposed_response)

    def get_history(self) -> ResponseDrivenPersonaHistory:
        return self.delegator.get_history()

    def set_history(self, history: ResponseDrivenPersonaHistory) -> None:
        self.delegator.set_history(history)

    async def process_final_response(
        self, proposed_response: ProposedPersonaResponse
    ) -> Dict[str, str]:
        return json.loads(proposed_response.message)

    async def send_message_and_process_autonomously(
        self, message: str
    ) -> Dict[str, str]:
        pr = await self.send_message(message)
        while self.delegator.is_in_processing_loop():
            pr = await self.process_proposed_response(pr)
        logger.warning(f"PR message is:\n\n{pr.message}")
        return await self.process_final_response(pr)
