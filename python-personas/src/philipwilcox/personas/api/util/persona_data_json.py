import datetime
import json
from typing import Any

from src.philipwilcox.personas.api.model.persona_exception import (
    PersonaException,
)
from src.philipwilcox.personas.api.model.persona_message import (
    PersonaMessage
)
from src.philipwilcox.personas.api.model.response_driven_persona_history import (
    ResponseDrivenPersonaHistory,
)


class PersonaDataJsonEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, PersonaMessage):
            return {
                "role": obj.role.value,
                "content": obj.content,
                "timestamp": obj.timestamp,
            }
        elif isinstance(obj, ResponseDrivenPersonaHistory):
            messages = [self.default(m) for m in obj.messages]
            final_messages = [self.default(m) for m in obj.final_messages]
            subhistories = {k: self.default(v) for k, v in obj.subhistories.items()}
            return {
                "messages": messages,
                "final_messages": final_messages,
                "subhistories": subhistories,
            }
        elif isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S.%f%Z")
        return super().default(obj)


class PersonaDataJsonDecoder(json.JSONDecoder):
    def __init__(self) -> None:
        json.JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, dct: Any) -> Any:
        if isinstance(dct, dict):
            if "role" in dct and "content" in dct and "timestamp" in dct:
                match dct["role"]:
                    case "assistant":
                        return PersonaMessage.create_assistant_message(
                            dct["content"],
                            datetime.datetime.strptime(
                                dct["timestamp"], "%Y-%m-%d %H:%M:%S.%f%Z"
                            ),
                        )
                    case "user":
                        return PersonaMessage.create_user_message(
                            dct["content"],
                            datetime.datetime.strptime(
                                dct["timestamp"], "%Y-%m-%d %H:%M:%S.%f%Z"
                            ),
                        )
                    case "system":
                        return PersonaMessage.create_system_message(
                            dct["content"],
                            datetime.datetime.strptime(
                                dct["timestamp"], "%Y-%m-%d %H:%M:%S.%f%Z"
                            ),
                        )
                    case _:
                        raise PersonaException(
                            f"Invalid role {dct['role']} in json data"
                        )
            elif (
                "messages" in dct and "final_messages" in dct and "subhistories" in dct
            ):
                messages = [self.object_hook(m) for m in dct["messages"]]
                final_messages = [self.object_hook(m) for m in dct["final_messages"]]
                subhistories = {
                    k: self.object_hook(v) for k, v in dct["subhistories"].items()
                }
                return ResponseDrivenPersonaHistory(
                    messages, final_messages, subhistories
                )
        return dct
