import asyncio
import logging
import os
from os import makedirs
from typing import Dict, List, Tuple

from src.philipwilcox.personas.api.persona_messenger import MESSENGER_OVERRIDES
from src.philipwilcox.personas.demo.demo_characters import DemoCharacters
from src.philipwilcox.personas.fiction.character_dialogue_agent_orchestration_persona import (
    CharacterDialogueAgentOrchestrationPersona,
)
from src.philipwilcox.personas.fiction.character_dialogue_basic_persona import (
    create_character_dialogue_basic_persona,
)
from src.philipwilcox.personas.fiction.character_dialogue_linear_orchestration_persona import (
    CharacterDialogueLinearOrchestrationPersona,
)

logger = logging.getLogger(__name__)

CHARACTERS_STREAM_TO_CONSOLE = True


async def multi_temp_loop() -> None:
    temperatures = [0.0, 0.7, 1.0, 1.2]
    # Note: 1.4 goes off the rails for GPT-4 even in basic mode, e.g.
    # I have much on my mind, let's talk about AI first. AI is a huge existential danger to humanity.
    #
    #      Ah, the burgeoning realm of AI, a matter worthy of contemplation, indeed. This modern yet uncanny prowess provokes trepidation alongside appreciation. Long hath humanity striven to manufacture a prodigious envoy fraught with abetting manner, unknowing of reciprocal sovereignties. Musk falls scarce upon mention as that which weighs magnitude far greater than nomenclature.
    # I think you are a fool.
    #
    #      Peradventure dost thou dub marbled jabber bespoke a fool, mine strivings ineffable end no conquest clear of confused manacles of verbosity dismiss taunts do linger. To each own paradigm of nuance imbued intellect, call thine what languishes with, I humbly labour.
    models = ["gpt-3.5-turbo", "gpt-4"]
    char_modes = ["basic", "agent", "code"]

    to_skip: List[Tuple[float, str, str]] = []

    for temperature in temperatures:
        for model in models:
            for char_mode in char_modes:
                if model == "gpt-3.5-turbo" and char_mode == "agent":
                    # NOTE: 3.5 goes off the rails entirely in the agent world right now, lol
                    continue
                if (
                    model == "gpt-3.5-turbo"
                    and char_mode == "code"
                    and temperature > 1.0
                ):
                    # 3.5 tends to get off-script with my prompt return format for these
                    continue
                if (temperature, model, char_mode) in to_skip:
                    print(
                        f"Skipping {(temperature, model, char_mode)} from previous run"
                    )
                    continue
                await run_dialogues(temperature, model, char_mode)


async def run_dialogues(temperature: float, model: str, char_mode: str) -> None:
    print(f"STARTING RUN FOR TEMP {temperature}, MODEL {model}, MODE {char_mode}")
    MESSENGER_OVERRIDES["model"] = model
    MESSENGER_OVERRIDES["temperature"] = temperature
    if char_mode == "code":
        CHARACTER_CREATOR = CharacterDialogueLinearOrchestrationPersona  # type: ignore
    elif char_mode == "agent":
        CHARACTER_CREATOR = CharacterDialogueAgentOrchestrationPersona  # type: ignore
    elif char_mode == "basic":
        CHARACTER_CREATOR = create_character_dialogue_basic_persona  # type: ignore
    else:
        raise Exception(f"Unknown character mode {char_mode}")

    FILENAME_SUFFIX = f"temp{temperature}-{char_mode}-{model}"
    questions = [
        "I am Joe. Who are you? I haven't met you before.",
        "Tell me more about yourself. What is your greatest ambition?",
        "I have much on my mind, let's talk about AI first. AI is a huge existential danger to humanity.",
        "I think you are a fool.",
        "Maybe we'll agree more on sports. I think football is more fun than basketball.",
    ]

    responses: Dict[str, List[str]] = {
        "Hamlet": [],
        "Lady Macbeth": [],
        "Jon Johns": [],
    }

    root_dir = os.path.dirname(__file__)

    for char in responses.keys():
        if char == "Hamlet":
            c = DemoCharacters.create_hamlet(
                CHARACTER_CREATOR, CHARACTERS_STREAM_TO_CONSOLE
            )
        elif char == "Lady Macbeth":
            c = DemoCharacters.create_lady_macbeth(
                CHARACTER_CREATOR, CHARACTERS_STREAM_TO_CONSOLE
            )
        elif char == "Jon Johns":
            c = DemoCharacters.create_jon_johns(
                CHARACTER_CREATOR, CHARACTERS_STREAM_TO_CONSOLE
            )
        else:
            raise Exception("Unknown character")
        for q in questions:
            response = await c.send_message_and_process_autonomously(q)
            responses[char].append(response["line"])  # type: ignore   # mypy hackery to support monkey-patched BasicPersona
        makedirs(f"{root_dir}/convos", exist_ok=True)

        response_string = ""
        for i, r in enumerate(responses[char]):
            this_exchange = questions[i] + "\n\n     " + r + "\n\n"
            response_string += this_exchange

        with open(
            f"{root_dir}/convos/history-{char}-{FILENAME_SUFFIX}.txt",
            "w",
        ) as file:
            output = f"Char {char}\n\n{response_string}\n\n\n"
            print(output)
            file.write(output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # asyncio.run(multi_temp_loop())
    asyncio.run(run_dialogues(0.0, "gpt-4", "code"))
