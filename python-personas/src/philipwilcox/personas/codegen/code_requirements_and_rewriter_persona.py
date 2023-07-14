import json
import logging
from typing import List

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.basic_persona import BasicPersona
from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import PersonaModelInitPromptTemplate
from src.philipwilcox.personas.api.persona_message_delegator_agent import (
    PersonaDelegationInfoAgent,
    PersonaMessageDelegatorAgent,
)
from src.philipwilcox.personas.codegen.codegen_personas import CodegenPersonas
from src.philipwilcox.personas.api.model.proposed_persona_response import (
    ProposedPersonaResponse,
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)
from src.philipwilcox.personas.codegen.method_summary import MethodSummary
from src.philipwilcox.personas.console.console_persona_mixin import (
    ConsolePersonaMixin,
)
from src.philipwilcox.personas.demo.rewriter import Rewriter

logger = logging.getLogger(__name__)


class CodeRequirementsAndRewriterPersona(DelegatingPersona, ConsolePersonaMixin):
    def __init__(
        self,
        primitives: List[MethodSummary],
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool = False,
    ):
        self.name = "Code Writer"
        pm_persona = CodegenPersonas.create_product_manager(
            open_ai, streaming_console_mode=streaming_console_mode
        )
        programmer_persona = CodegenPersonas.create_python_programmer(
            primitives, open_ai, streaming_console_mode=streaming_console_mode
        )
        persona_list = [pm_persona, programmer_persona]
        coordinating_persona = BasicPersona(
            PersonaModelInitPromptTemplate(messages=[
                PersonaMessage.create_system_message("You are an engineering manager. Your job is to take human-friendly natural-language requests from users and create tasks to get the requirements turned into code."),
                PersonaMessage.create_user_message('''You are an engineering manager with two types of employees working for you:
```
{% for p in available_personas %}
{{ p }}
{% endfor %}
```

Your task is to listen to a user and create messages to be forwarded to one of these employees.

{{ response_format }}

If you do not need to delegate any further, reply with null in the code block for the delegate recipient. For the message code block part of your response, include a JSON string of a dictionary with three keys: "filename" for the name of the file the user asked to modify, or null if not known; "method_name" for the name of the method they asked to write, or null if not known; and "code" for the actual code of this new method, from the programmer, such as in the following example:
, such as in the following example:

"""
## Reasoning
```
We have a response with filename, method name, and code, so we can execute now.
```

## Message
```
{
  "filename": "something.py",
  "method_name": "nonsense",
  "code": "def nonsense(input_integer: int) -> int:\n    pass"
}
```

## Recipient
```
null
```
''')]),
            template_kwargs={
                "available_personas": [
                    p.get_llm_facing_info().format_for_prompt(p.name)
                    for p in persona_list
                ],
                "response_format": self.get_response_format_instructions(),
            },
            open_ai=open_ai,
            # TODO: make this persona name (rewriter vs writer, etc) consistent everywhere
            name=self.name + " (Coordinator)",
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
    ) -> None:
        instructions = json.loads(proposed_response.message)
        # TODO: unsure about having side effects in here, but left in for now for demo
        rewriter = Rewriter(instructions["filename"])
        rewriter.update_method(instructions["method_name"], instructions["code"])
        rewriter.rewrite_file()
        return instructions

    async def send_message_and_process_autonomously(self, message: str) -> None:
        pr = await self.send_message(message)
        while self.delegator.is_in_processing_loop():
            pr = await self.process_proposed_response(pr)
        # TODO: call out to a provided "final conversion method" instead, here, too
        logger.warning(f"PR message is:\n\n{pr.message}")
        return await self.process_final_response(pr)

    def get_agent_name_display(self) -> str:
        if self.delegator.current_delegate:
            if isinstance(self.delegator.current_delegate, ConsolePersonaMixin):
                return f"{self.name} || {self.delegator.current_delegate.get_agent_name_display()}"
            else:
                return f"{self.name} || {self.delegator.current_delegate.get_name()}"
        else:
            return self.name

    def get_user_prompt(self) -> str:
        return "Welcome! Please describe the changes you'd like us to make to a specified method in a given file, a la 'please update radius in circle.py to compute the radius from a floating point area argument'"
