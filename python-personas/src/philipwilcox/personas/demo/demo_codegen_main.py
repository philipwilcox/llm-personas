import argparse
import asyncio
import json
import logging
import os
import sys

from src.philipwilcox.lib.openai.openai_wrapper import OPENAIWRAPPER
from src.philipwilcox.personas.api.util.persona_data_json import (
    PersonaDataJsonEncoder,
)
from src.philipwilcox.personas.codegen.code_requirements_and_rewriter_persona import (
    CodeRequirementsAndRewriterPersona,
)
from src.philipwilcox.personas.codegen.method_summary import MethodSummary
from src.philipwilcox.personas.console.console_persona_wrapper import (
    ConsolePersonaWrapper,
)

from src.philipwilcox.personas.demo.rewriter import Rewriter

# Needed so this is in sys.modules for reading-from
from src.philipwilcox.personas.codegen.skill_primitives.primitives import Primitives

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# TODO: can I set logging to debug just for my classes?

PRIMITIVES_PATH = os.path.dirname(
    sys.modules[
        "src.philipwilcox.personas.codegen.skill_primitives.primitives"
    ].__file__
)  # type: ignore
PRIMITIVES_DESCRIPTIONS_FILENAME = f"{PRIMITIVES_PATH}/primitives_descriptions.json"


async def main(history_file: str, mode: str) -> None:
    # Lets load our primitives and write code
    primitives = []
    with open(PRIMITIVES_DESCRIPTIONS_FILENAME, "r") as f:
        dicts = json.load(f)
        for s in dicts:
            primitives.append(MethodSummary(**s))

    match mode:
        case "console-demo":
            persona = CodeRequirementsAndRewriterPersona(
                primitives, OPENAIWRAPPER, streaming_console_mode=True
            )
            console_persona = ConsolePersonaWrapper(persona)
            r = await console_persona.console()  # TODO: add hooks to save to history
        case "refactor-demo":
            my_request = """
        can you modify the method called func() in target.py to take an integer argument x and return its factorial?
            """.strip()
            persona = CodeRequirementsAndRewriterPersona(primitives, OPENAIWRAPPER)

            # suggest what to sfscraperend PM
            response = await persona.send_message(my_request)
            # get response back from PM
            response_pm = await persona.process_proposed_response(response)
            # now suggest to delegate to programmer
            prog_del_response = await persona.process_proposed_response(response_pm)
            # now do that
            prog_response = await persona.process_proposed_response(prog_del_response)
            logger.info(f"Got this back from the programmer: {prog_response.message}")
            rewriter = Rewriter("target.py")
            old_code = rewriter.get_method("func")
            final_response = await persona.process_proposed_response(prog_response)
            await persona.process_final_response(final_response)
            new_rewriter = Rewriter("target.py")
            new_code = new_rewriter.get_method("func")
            logger.info(f"Old code was {old_code}; new code is {new_code}")

            history = persona.get_history()
            with open(history_file, "w") as file:
                json.dump(history, file, cls=PersonaDataJsonEncoder, indent=4)
        case "refactor-demo-autonomous":
            my_request = """
can you modify the method called func() in target.py to take an integer argument x and return its factorial?
            """.strip()
            persona = CodeRequirementsAndRewriterPersona(primitives, OPENAIWRAPPER)
            rewriter = Rewriter("target.py")
            old_code = rewriter.get_method("func")
            await persona.send_message_and_process_autonomously(my_request)
            new_rewriter = Rewriter("target.py")
            new_code = new_rewriter.get_method("func")
            logger.info(f"Old code was {old_code}; new code is {new_code}")

            history = persona.get_history()
            with open(history_file, "w") as file:
                json.dump(history, file, cls=PersonaDataJsonEncoder, indent=4)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Codegen Demo")
    parser.add_argument(
        "--history-file",
        type=str,
        default="history.json",
        help="a history file to save/load from, if not an empty string",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="console-demo",
        choices=["console-demo", "refactor-demo", "refactor-demo-autonomous"],
    )
    # # TODO: move some of these demos to "unit test" format files
    args = parser.parse_args()

    asyncio.run(
        main(
            history_file=args.history_file,
            mode=args.mode,
        )
    )
