import dataclasses
import json
import logging
from typing import List, Dict, Optional, Callable

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.lib.util.md import extract_code_block
from src.philipwilcox.personas.api.basic_persona import (
    BasicPersona,
)
from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.persona_exception import (
    PersonaException,
)
from src.philipwilcox.personas.api.persona_message_delegator_linear import (
    PersonaMessageDelegatorLinear,
    PersonaDelegationInfoLinear,
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
from src.philipwilcox.personas.fiction.character_dialogue_agent_orchestration_persona import (
    CharacterDialogueAgentOrchestrationPersona,
)
from src.philipwilcox.personas.fiction.character_dialogue_personas import (
    CharacterDialoguePersonas,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CharacterDialogueOrchestrationResponseState:
    alignment: bool
    mood: Optional[str] = None
    other_person_name: Optional[str] = None
    proposed_response_dict: Optional[Dict[str, str]] = None
    actual_response_dict: Optional[Dict[str, str]] = None


class CharacterDialogueLinearOrchestrationPersona(DelegatingPersona):
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
        ordered_persona_list = [
            goals_persona,
            mood_persona,
            conversation_persona,
            rewriter_persona,
        ]
        next_message_closure = (
            CharacterDialogueLinearOrchestrationPersona.create_message_builder_closure(
                current_mood,
                goals_persona,
                mood_persona,
                conversation_persona,
                rewriter_persona,
            )
        )
        self.delegation_info = PersonaDelegationInfoLinear(
            ordered_persona_list, next_message_closure
        )
        DelegatingPersona.__init__(
            self, PersonaMessageDelegatorLinear(self.delegation_info)
        )

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

    async def send_message_and_process_autonomously(
        self, message: str
    ) -> Dict[str, str]:
        pr = await self.send_message(message)
        while self.delegator.is_in_processing_loop():
            pr = await self.process_proposed_response(pr)
        # TODO: call out to a provided "final conversion method" instead, here, too
        return await self.process_final_response(pr)

    async def process_final_response(
        self, proposed_response: ProposedPersonaResponse
    ) -> Dict[str, str]:
        return json.loads(proposed_response.message)

    @staticmethod
    def create_message_builder_closure(
        initial_mood: str,
        goals_persona: BasicPersona,
        mood_persona: BasicPersona,
        conversation_persona: BasicPersona,
        rewriter_persona: BasicPersona,
    ) -> Callable[[ResponseDrivenPersona, str, str], str]:
        response_state_history: List[CharacterDialogueOrchestrationResponseState] = []

        def message_builder(
            persona: ResponseDrivenPersona,
            subpersona_message: str,
            inbound_message: str,
        ) -> str:
            if persona == goals_persona:
                # TODO: this would be cleaner if we bundled optional response handlers INTO BasicPersona creation for a parse_response method?
                alignment = json.loads(extract_code_block(subpersona_message))
                # let's start tracking a new state history since this is the first in our sequence for this line of input dialogue
                response_state_history.append(
                    CharacterDialogueOrchestrationResponseState(
                        alignment=alignment, mood=initial_mood
                    )
                )
                if len(response_state_history) > 1:
                    # Terribly hacky way of keeping this in our working memory
                    response_state_history[
                        -1
                    ].other_person_name = response_state_history[-2].other_person_name
                # To make a message to pass to mood evaluator, accumulate current mood + recent goal alignment
                last_mood = response_state_history[-1].mood
                response_alignment_history = [
                    x.alignment for x in response_state_history
                ][-5:]
                mood_message = f"Your current mood is {last_mood}.\n\nYou are having a conversation, and the last few responses (up to five, if the conversation has contained that many or more) from the other party have either aligned with your goals, or not, as represented by a list of boolean variables, where true means the response was aligned: {response_alignment_history}.\n\nGiven the following line of dialogue, respond with your mood after processing that dialogue from the other party - either your original mood, or a new one if you have shifted your position due to the history, statement, and its tone and contents: {inbound_message}"
                return mood_message
            if persona == mood_persona:
                new_mood = json.loads(extract_code_block(subpersona_message))["mood"]
                response_state_history[-1].mood = new_mood
                return json.dumps(
                    {
                        "name": response_state_history[-1].other_person_name,
                        "line": inbound_message,
                        "mood": new_mood,
                    }
                )
            if persona == conversation_persona:
                response_state_history[-1].proposed_response_dict = json.loads(
                    extract_code_block(subpersona_message)
                )
                assert response_state_history[-1].proposed_response_dict
                name = response_state_history[-1].proposed_response_dict["name"]
                response_state_history[-1].other_person_name = name
                return json.dumps(
                    {
                        "mood": response_state_history[-1].mood,
                        "line": response_state_history[-1].proposed_response_dict[
                            "line"
                        ],
                    }
                )
            if persona == rewriter_persona:
                # all we need to do here is stuff the rewritten line in the proposed response JSON and repack it
                assert response_state_history[-1].proposed_response_dict
                response_state_history[-1].proposed_response_dict[
                    "line"
                ] = extract_code_block(subpersona_message)
                return json.dumps(response_state_history[-1].proposed_response_dict)
            raise PersonaException(
                f"Somehow our subpersona of {persona} didn't match any expected ones for this persona!"
            )

        return message_builder
