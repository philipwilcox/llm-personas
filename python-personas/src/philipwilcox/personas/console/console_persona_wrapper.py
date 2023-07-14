import copy
from typing import Any, Optional, List

from src.philipwilcox.personas.api.delegating_persona import DelegatingPersona
from src.philipwilcox.personas.api.model.response_driven_persona_flat_history import (
    ResponseDrivenPersonaFlatHistory,
)
from src.philipwilcox.personas.api.response_driven_persona import (
    ResponseDrivenPersona,
)
from src.philipwilcox.personas.console.console_persona_mixin import (
    ConsolePersonaMixin,
)


class ConsolePersonaWrapper:
    def __init__(
        self, persona: ConsolePersonaMixin, forced_messages: Optional[List[str]] = None
    ) -> None:
        self.persona = persona
        if forced_messages:
            self.forced_messages = forced_messages
        else:
            self.forced_messages = []

    async def console(self) -> Any:
        if isinstance(self.persona, DelegatingPersona):
            flat_history = ResponseDrivenPersonaFlatHistory.from_nested_history(
                self.persona.get_history(), self.persona
            )
            # TODO: create the ability to distinguish between "hidden" init messages for full audit history dumps
            for m in flat_history.messages:
                # TODO: get stack displayed in here too in the user messages
                print(f"[{m.message.role}]\n{m.message.content}")
                print()
            if len(flat_history.messages) > 0:
                last_message_stack = flat_history.messages[-1].stack
                last_message = flat_history.messages[-1].message
            else:
                last_message_stack = []
                last_message = None
        else:
            message_history = self.persona.get_history().messages
            last_message_stack = []
            if len(message_history) > 0:
                last_message = message_history[-1]
            else:
                last_message = None

        if last_message:
            # TODO: do something with last_message_stack here to indicate who we're talking to?
            last_response = self.persona.get_last_assistant_response()
        else:
            last_response = None
            print(f"{self.persona.get_agent_name_display()}")
            print(self.persona.get_user_prompt())
        remaining_messages = copy.deepcopy(self.forced_messages)
        while True:
            agent_name = self.persona.get_agent_name_display()
            print(f"[ user - speaking to {agent_name} ]")
            if len(remaining_messages) > 0:
                user_input = remaining_messages.pop()
            else:
                user_input = input()
            if isinstance(self.persona, DelegatingPersona):
                if last_response:
                    accepted = self.proposal_accepted(user_input)
                    try_to_execute = self.try_to_execute(user_input)
                    # TODO: possibly add a "get next agent name" hook in Persona for when about to do a "process_proposed_response" call...
                    print("[ assistant ]")
                    if accepted:
                        last_response = await self.persona.process_proposed_response(
                            last_response
                        )
                    elif try_to_execute:
                        r = await self.persona.process_final_response(last_response)
                        print(
                            f"We finalized the session, with response {r}, returning now."
                        )
                        return r
                    else:
                        last_response = await self.persona.send_message(user_input)
                else:
                    last_response = await self.persona.send_message(user_input)
            else:
                last_response = await self.persona.send_message(user_input)
            print()

    def proposal_accepted(self, user_input: str) -> bool:
        return user_input.lower() in {"done", "ok", "sounds good", "yes"}

    def try_to_execute(self, user_input: str) -> bool:
        return user_input.lower() in {"execute", "finalize", "do it"}
