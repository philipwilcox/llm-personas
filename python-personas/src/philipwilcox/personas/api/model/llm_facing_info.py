import dataclasses
import json
from typing import List, Dict, Any


@dataclasses.dataclass
class LlmFacingInfo:
    description: str
    example_messages: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "example_messages": self.example_messages,
        }

    def format_for_prompt(self, name: str) -> str:
        d = self.to_dict()
        d["name"] = name
        return json.dumps(d, indent=4)
