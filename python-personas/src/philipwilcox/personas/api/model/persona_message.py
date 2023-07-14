import datetime
from enum import Enum
from typing import Optional, Dict

from src.philipwilcox.personas.api.model.persona_exception import PersonaException


class MessageRole(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


# TODO: rename this to "LlmMessage"?
class PersonaMessage:
    def __init__(
        self,
        role: str | MessageRole,
        content: str,
        timestamp: Optional[datetime.datetime] = None,
    ):
        if type(role) == str:
            if role not in MessageRole.__members__:
                raise PersonaException(
                    f'Invalid role for message: "{role}" not a known role'
                )
            self.role = MessageRole(role)
        else:
            self.role = role
        self.content = content
        if timestamp is not None:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

    def create_system_message(content: str,
                              timestamp: Optional[datetime.datetime] = None,) -> "PersonaMessage":
        return PersonaMessage(role=MessageRole.SYSTEM, content=content, timestamp=timestamp)

    def create_user_message(content: str,
                            timestamp: Optional[datetime.datetime] = None,) -> "PersonaMessage":
        return PersonaMessage(role=MessageRole.USER, content=content, timestamp=timestamp)

    def create_assistant_message(content: str,
                                 timestamp: Optional[datetime.datetime] = None,) -> "PersonaMessage":
        return PersonaMessage(role=MessageRole.ASSISTANT, content=content, timestamp=timestamp)

    def as_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}

    def is_system_message(self) -> bool:
        return self.role == MessageRole.SYSTEM

    def is_user_message(self) -> bool:
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        return self.role == MessageRole.ASSISTANT

    def __str__(self) -> str:
        return str(self.as_dict())
