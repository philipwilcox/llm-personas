import abc

from src.philipwilcox.personas.api.response_driven_persona import (
    ResponseDrivenPersona,
)


class ConsolePersonaMixin(ResponseDrivenPersona, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_agent_name_display(self) -> str:
        pass

    @abc.abstractmethod
    def get_user_prompt(self) -> str:
        pass
