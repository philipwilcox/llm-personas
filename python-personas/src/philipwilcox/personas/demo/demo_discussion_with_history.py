import asyncio
import json
import logging
from typing import Dict, List

from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.util.persona_data_json import (
    PersonaDataJsonEncoder,
    PersonaDataJsonDecoder,
)
from src.philipwilcox.personas.fiction.character_dialogue_agent_orchestration_persona import (
    CharacterDialogueAgentOrchestrationPersona,
)
from src.philipwilcox.personas.demo.demo_characters import DemoCharacters


logger = logging.getLogger(__name__)


CHARACTERS_STREAM_TO_CONSOLE = False

# CHARACTER_CREATOR = CharacterDialogueLinearOrchestrationPersona
CHARACTER_CREATOR = CharacterDialogueAgentOrchestrationPersona


async def main() -> None:
    questions = [
        "I am Joe. Who are you? I haven't met you before.",
        "What is your greatest ambition?",
        "AI is a huge existential danger to humanity.",
    ]

    responses: Dict[str, List[str]] = {"Hamlet": []}

    c = DemoCharacters.create_hamlet(CHARACTER_CREATOR, CHARACTERS_STREAM_TO_CONSOLE)
    assert isinstance(c, DelegatingPersona)
    processed_questions: List[str] = [questions.pop()]
    # first question loop:
    pr = await c.send_message(questions[0])
    while c.delegator.is_in_processing_loop():
        pr = await c.process_proposed_response(pr)
    # Now we have final response to first question back
    processed_questions.append(questions.pop())
    pr = await c.send_message(processed_questions[-1])
    pr = await c.process_proposed_response(pr)
    print(pr)
    # At this point our most recent proposed response is from the Goals persona
    print("Current delegate before SAVE is: " + c.delegator.current_delegate.get_name())  # type: ignore
    with open(f"history-savetest.json", "w") as file:
        json.dump(c.get_history(), file, cls=PersonaDataJsonEncoder, indent=4)

    c2 = DemoCharacters.create_hamlet(CHARACTER_CREATOR, CHARACTERS_STREAM_TO_CONSOLE)
    assert isinstance(c2, DelegatingPersona)
    print(f"Character one was {c}, two is {c2}")
    with open(f"history-savetest.json", "r") as file:
        history = json.load(file, cls=PersonaDataJsonDecoder)
        c2.set_history(history)
        pr = c2.get_last_assistant_response()  # type: ignore
        print(
            "Current delegate after LOAD is: " + c.delegator.current_delegate.get_name()  # type: ignore
        )
        assert pr
        print(pr)
        # Now let's run until the end of the response to the second statement
        while c2.delegator.is_in_processing_loop():
            pr = await c2.process_proposed_response(pr)
        print(pr)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
