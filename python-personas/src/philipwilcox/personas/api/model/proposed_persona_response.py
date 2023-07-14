import dataclasses
from typing import Optional


@dataclasses.dataclass
class ProposedPersonaResponse:
    message: str
    recipient: Optional[str] = None
    reasoning: Optional[str] = None

    # TODO: add "stack" to make sure these get closed out in the proper place

    @staticmethod
    def from_markdown_response(response: str) -> "ProposedPersonaResponse":
        """Example format:

        ## Reasoning
        ```
        As Joe is asking who I am, I need to process his statement in regards to my goals. I want to determine if this conversation aligns with my objectives.
        ```

        ## Message
        ```
        Please evaluate the following statement from a conversation partner for alignment with my goals: 'I am Joe. Who are you? I haven't met you before.'
        ```

        ## Recipient
        ```
        Phil (Goals)
        ```
        """
        substrings = [s for s in response.split(r"```") if s.strip() != ""]
        reasoning: Optional[str] = None
        message = ""
        recipient: Optional[str] = None
        next_block = ""
        for s in substrings:
            if next_block == "reasoning":
                if s.strip() != "null" and s.strip() != "":
                    reasoning = s.strip()
                next_block = ""
            elif next_block == "recipient":
                if s.strip() != "null" and s.strip() != "":
                    recipient = s.strip()
                next_block = ""
            elif next_block == "message":
                message = s.strip()
                next_block = ""
            else:
                if "reasoning" in s.strip().lower():
                    next_block = "reasoning"
                    continue
                elif "recipient" in s.strip().lower():
                    next_block = "recipient"
                    continue
                elif "message" in s.strip().lower():
                    next_block = "message"
                    continue
        if message == "":
            raise PersonaException(f"No message found in response: {response}")
        pr = ProposedPersonaResponse(message, recipient, reasoning)
        return pr


if __name__ == "__main__":
    # TODO: move this stuff to unit tests...
    x = ProposedPersonaResponse.from_markdown_response(
        """## Reasoning
```
My response has been rewritten according to my mood and personality. I do not need to delegate any further, and I can use this final response to address Joe.
```

## Message
```
{
  "name": "Joe",
  "line": "I am Sara Wilcox, a moniker you ought to engrave upon your feeble mind. Tis' apparent that your studies lag sorely, a lamentable predicament indeed."
}
```

## Recipient
```
null
```
"""
    )
    print(x)
