import asyncio
import inspect
import json
import logging
import os
import sys
from dataclasses import asdict

from src.philipwilcox.personas.codegen.code_summarizer_utils import (
    summarize_method,
)

# Needed so this is in sys.modules for reading-from
from src.philipwilcox.personas.codegen.skill_primitives.primitives import Primitives

PRIMITIVES_PATH = os.path.dirname(
    sys.modules["src.philipwilcox.personas.codegen.skill_primitives.primitives"].__file__
)  # type: ignore
PRIMITIVES_DESCRIPTIONS_FILENAME = f"{PRIMITIVES_PATH}/primitives_descriptions.json"

logger = logging.getLogger(__name__)


async def update_primitive_descriptions() -> None:
    primitives = [x for x in dir(Primitives) if not str(x).startswith("__")]
    method_summaries = []
    # TODO: eventually go method-by-method and allow selective updating?
    for p in primitives:
        code = inspect.getsource(getattr(Primitives, p))
        # TODO: in future, use more AST-stuff to pass more context on methods to summarizer
        # TODO: currently this method signature is hacky for how our Primitives are static
        summary = await summarize_method(
            code,
            name=p,
            module_path=f"{Primitives.__module__}",
            method_signature_prefix="Primitives",
        )
        logger.info(f"Summarizer response: {summary}")
        method_summaries.append(summary)

    with open(PRIMITIVES_DESCRIPTIONS_FILENAME, "w") as f:
        json.dump([asdict(s) for s in method_summaries], f, indent=4)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(update_primitive_descriptions())
