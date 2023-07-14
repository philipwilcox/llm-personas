import json
import os
from typing import List, Any, AsyncGenerator

import openai

from src.philipwilcox.personas.api.model.persona_message import PersonaMessage


class OpenAIWrapper:

    def __init__(self):
        # TODO: move this out if/when we have other secrets
        # Load secret key from .env.secret.json
        # TODO: make this not be brittle against moving this file
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))

        with open(root_dir + '/.env.secret.json', 'r') as f:
            secrets = json.load(f)
            # override default `openai` library attempt to load from env key or "path" env key
            openai.api_key = secrets["OPENAI_API_KEY"]

    async def stream_chat_completion(self, messages: List[PersonaMessage], **kwargs: Any) -> AsyncGenerator[str, None]:
        messages_as_dicts = [m.as_dict() for m in messages]
        kwargs.setdefault("model", "gpt-4")
        kwargs["stream"] = True
        response = await openai.ChatCompletion.acreate(messages=messages_as_dicts, **kwargs)
        async for chunk in response:
            # TODO: look at other stuff in here
            r = chunk["choices"][0]["delta"].get("content")
            if r:
                # last chunk is None
                yield r



OPENAIWRAPPER = OpenAIWrapper()
