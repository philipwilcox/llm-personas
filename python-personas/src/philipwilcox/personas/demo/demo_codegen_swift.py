import asyncio
import logging
import os
import sys

from src.philipwilcox.lib.openai.openai_wrapper import OPENAIWRAPPER
from src.philipwilcox.personas.api.basic_persona import BasicPersona
from src.philipwilcox.personas.api.model.llm_facing_info import LlmFacingInfo
from src.philipwilcox.personas.console.console_persona_mixin import (
    ConsolePersonaMixin,
)
from src.philipwilcox.personas.console.console_persona_wrapper import (
    ConsolePersonaWrapper,
)



logger = logging.getLogger(__name__)

# TODO: can I set logging to debug just for my classes?

PRIMITIVES_PATH = os.path.dirname(
    sys.modules["philipwilcox.experimental.skill_primitives.primitives"].__file__
)  # type: ignore
PRIMITIVES_DESCRIPTIONS_FILENAME = f"{PRIMITIVES_PATH}/primitives_descriptions.json"


class ConsoleProgrammer(BasicPersona, ConsolePersonaMixin):
    # TODO: is there a more mixin-friendly way to do this?
    def get_agent_name_display(self) -> str:
        return "Programmer"

    def get_user_prompt(self) -> str:
        return "Let's write some Swift!"

    def __init__(self) -> None:
        BasicPersona.__init__(
            self,
            "philipwilcox/personas/codegen/swift_programmer_init.chatml",
            {},
            OPENAIWRAPPER,
            "Swift Programmer",
            llm_facing_info=LlmFacingInfo(
                description="A Swift programmer takes a questions about Swift and answers them",
                example_messages=[
                    "How can I square a number in Swift?",
                    "In Swift, how can I listen for CloudKit changes?",
                ],
            ),
            resend_conversation_history=True,
            streaming_console_mode=True,
        )


async def main() -> None:
    # messages = [
    #     """Write a Swift ViewModel class implementing ObservableObject to power a view that depends on two state variables: a "comicId" int and a "currentUrl" string. Behind the scenes, there are also two history lists of comicId and timestamp Items, one for "back navigation" and one for "forward" navigation history tracking.
    #     """
    # ]
    messages = [
        """
In Swift, how would I set a timer with a callback that would run 10 seconds after application start and call a view model called ViewModel to update my view based on some new calculations or CoreData queries?
"""
    ]

    r = ConsolePersonaWrapper(ConsoleProgrammer(), forced_messages=messages)
    await r.console()
    print(r)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
