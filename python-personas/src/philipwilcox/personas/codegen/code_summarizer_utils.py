import json
from typing import Optional

from src.philipwilcox.lib.openai.openai_wrapper import OPENAIWRAPPER
from src.philipwilcox.lib.util.md import extract_code_block
from src.philipwilcox.personas.codegen.codegen_personas import CodegenPersonas
from src.philipwilcox.personas.codegen.method_summary import MethodSummary


async def summarize_method(
    code: str, name: str, module_path: str, method_signature_prefix: Optional[str]
) -> MethodSummary:
    summarizer = CodegenPersonas.create_code_summarizer(OPENAIWRAPPER, False)
    message = f"Here is a method to summarize:\n\n```\n{code}```\n"
    response_message = (await summarizer.send_message(message)).message
    summary_block = extract_code_block(response_message)
    ms = MethodSummary(**json.loads(summary_block), name=name, module_path=module_path)
    if method_signature_prefix:
        ms.method_signature = method_signature_prefix + "." + ms.method_signature
    return ms
