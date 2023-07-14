import asyncio
import copy
import logging
from typing import Dict, Any, List

from aiohttp import ClientPayloadError
from openai.error import RateLimitError, ServiceUnavailableError, APIError

from src.philipwilcox.lib.openai.messages_wrapper import MessagesWrapper
from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.model.persona_exception import PersonaException
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import (
    PersonaModelInitPromptTemplate,
)

logger = logging.getLogger(__name__)


# TODO: less-hacky way to set this; make PersonaMessenger more injectable for testing
MESSENGER_OVERRIDES = {
    "temperature": 0.0,
    # "model": "gpt-3.5-turbo",
    "model": "gpt-4",
}


class PersonaMessenger:
    def __init__(
        self,
        init_prompt_template: PersonaModelInitPromptTemplate,
        template_kwargs: Dict[str, Any],
        open_ai: OpenAIWrapper,
        resend_conversation_history: bool = True,
        streaming_console_mode: bool = False,
        retry_count: int = 5,
        initial_delay_ms: int = 750,
        temperature: float = 0.0,
        llm_model: str = "gpt-4",
    ):
        self.prompt_messages = init_prompt_template.render(keyword_args=template_kwargs)
        self.history: List[PersonaMessage] = []
        # TODO: figure out a way to have my cake and eat it too re: prompt messages so that I can preserve them in
        #       "fully logged" history but not mess with things like console view...
        self.openai = open_ai
        self.resend_conversation_history = resend_conversation_history
        self.streaming_console_mode = streaming_console_mode
        self.retry_count = retry_count
        self.initial_delay_ms = initial_delay_ms
        if MESSENGER_OVERRIDES["temperature"]:
            self.temperature = MESSENGER_OVERRIDES["temperature"]
        else:
            self.temperature = temperature
        if MESSENGER_OVERRIDES["model"]:
            self.llm_model = MESSENGER_OVERRIDES["model"]
        else:
            self.llm_model = llm_model

    async def send(self, m: PersonaMessage) -> PersonaMessage:
        assert m.is_user_message()
        self.history.append(m)

        messages_to_send = copy.copy(self.prompt_messages)
        if self.resend_conversation_history:
            messages_to_send += copy.copy(self.history)
        else:
            messages_to_send.append(m)

        logger.debug(f"WILL SEND>>> {[str(m) for m in self.history]}")
        num_attempts = 1
        chunks: List[str] = []
        while num_attempts < self.retry_count:
            chunks = []
            try:
                async for chunk in self.openai.stream_chat_completion(
                    messages=messages_to_send,
                    temperature=self.temperature,
                    model=self.llm_model,
                ):
                    chunks.append(chunk)
                    if self.streaming_console_mode:
                        print(chunk, end="")
            except (
                RateLimitError,
                ServiceUnavailableError,
                APIError,
                ClientPayloadError,
            ) as e:
                delay_ms = num_attempts * self.initial_delay_ms
                logger.warning(
                    f"Got a {type(e)} error from OpenAI on retry attempt {num_attempts}, retrying after {delay_ms}ms"
                )
                await asyncio.sleep(delay_ms / 1000)
                num_attempts += 1
                if num_attempts >= self.retry_count:
                    raise e
            else:
                break
        # Process and return at top-level instead of in `else` to avoid mypy complaining about missing return
        # for the `except` case
        response = PersonaMessage.create_assistant_message("".join(chunks))
        self.history.append(response)
        return response
