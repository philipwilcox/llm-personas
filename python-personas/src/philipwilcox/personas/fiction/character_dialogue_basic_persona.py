import json
from typing import List, Dict

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.lib.util.md import extract_code_block
from src.philipwilcox.personas.api.basic_persona import BasicPersona


def create_character_dialogue_basic_persona(
    open_ai: OpenAIWrapper,
    name: str,
    character_oneliner: str,
    current_mood: str,
    current_goals: List[str],
    dialogue_examples: List[str],
    streaming_console_mode: bool = False,
) -> BasicPersona:
    p = BasicPersona(
        "philipwilcox/personas/fiction/basic_character_dialogue_conversation_init.chatml",
        {
            "character_oneliner": character_oneliner,
            "goals": current_goals,
            "mood": current_mood,
            "dialogue_examples": dialogue_examples,
        },
        open_ai,
        f"{name} - Dialogue Persona",
        resend_conversation_history=True,
        streaming_console_mode=streaming_console_mode,
    )

    # TODO: how to do a less hacky monkey-patched version of the below? Rewrite the prompt and the return type in general?
    async def new_message_processor(message: str) -> Dict[str, str]:
        x = (await p.send_message(message)).message
        return json.loads(extract_code_block(x))

    p.send_message_and_process_autonomously = new_message_processor  # type: ignore   # mypy hackery to support monkey-patched BasicPersona
    return p
