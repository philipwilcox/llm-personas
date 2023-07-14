from typing import List

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.basic_persona import BasicPersona
from src.philipwilcox.personas.api.model.llm_facing_info import LlmFacingInfo
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import (
    PersonaModelInitPromptTemplate,
)


class CharacterDialoguePersonas:
    @staticmethod
    def create_goals_persona(
        name: str,
        character_oneliner: str,
        current_goals: List[str],
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(
                [
                    PersonaMessage.create_system_message("{{ character_oneliner }}"),
                    PersonaMessage.create_user_message(
                        '''{{ character_oneliner}}

Currently, your goal(s) from the conversation you're in is:

{% for goal in goals %}
"""
{{ goal }}
"""
{% endfor %}

When presented with a line of dialogue addressed to you from another character, please evaluate if this indicates that you are making progress on your goals, or if their statement is contradictory to your goals. Do not respond yourself, just indicate if this conversation is aligned with your goals.

Give your response as a multi-line Markdown code block delimited with "```", containing a bare JSON boolean variable, true or false, indicating the alignment. See the following examples of user messages and your reponses:
"""
User: Hi, I'm John.
Assistant: ```
true
```
"""

"""
User: I strongly oppose you.
Assistant: ```
false
```
"""
'''
                    ),
                ]
            ),
            {"character_oneliner": character_oneliner, "goals": current_goals},
            open_ai,
            name + " (Goals)",
            llm_facing_info=LlmFacingInfo(
                description="The goals persona is responsible for evaluating if a line in a conversation from a third party suggests that the conversation aligns wit the goals of this person.",
                example_messages=[
                    "Please evaluate the following statement from a conversation partner for alignment with your goals: 'Hi, my name is Philip, how are you?'"
                ],
            ),
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_mood_persona(
        name: str,
        character_oneliner: str,
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(
                [
                    PersonaMessage.create_system_message("{{ character_oneliner }}"),
                    PersonaMessage.create_user_message(
                        '''{{ character_oneliner}}

You are having a conversation with another party. Depending on what they say to you, and your mood, your mood may shift. You will be asked about a line of dialogue that was addressed to you, given your current mood and whether or not the response is lining up with your goals.

Please evaluate if this combination of response alignment and response, including tone, aggressiveness, and other emotional elements of the response, changes your mood.

Please reply with a new mood as a json dictionary string with a single key, "mood", with value being your new mood on a line by itself inside a multi-line markdown code block delimited with ```.

Example Responses:
"""
Because of this statement, my new mood is Inquisitive.
```
{"mood": "Inquisitive"}
```
"""

"""
This statement made me Furious.
```
{"mood": "Furious"}
```
"""

"""
This statement does not effect my mood because it hasn't caught my interest, so my mood remains Impatient..
```
{"mood": "Impatient"}
```
"""'''
                    ),
                ]
            ),
            {"character_oneliner": character_oneliner},
            open_ai,
            name + " (Mood)",
            llm_facing_info=LlmFacingInfo(
                description="The mood persona is responsible for evaluating how this person's mood has changed based on a history of whether or not the current conversation is aligned with this person's goals, as well as on their previous mood.",
                example_messages=[
                    "The last message aligned with your goals, and your previous mood was 'content'. The most recent statement made to you was 'I would love to hear more.' What is your new mood?",
                    "Only one of the last three messages aligned with your goals, and your previous mood was 'bored'. The most recent statement made to you was 'I think you are wasting my time.' What is your new mood?",
                    "All of the last five messages aligned with your goals, and your previous mood was 'happy'. The most recent statement made to you was 'I love you.' What is your new mood?",
                ],
            ),
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_conversation_persona(
        name: str,
        character_oneliner: str,
        current_goals: List[str],
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(
                [
                    PersonaMessage.create_system_message("{{ character_oneliner }}"),
                    PersonaMessage.create_user_message(
                        '''{{ character_oneliner}}

Your current goals are:
{% for goal in goals %}
"""
{{ goal }}
"""
{% endfor %}

When another character speaks to you, please respond with what your natural response would be, given your own attributes and your current mood. Pay close attention to your goals and personality.

Input lines will come in the form of a JSON string representing a dictionary with several keys: "name" representing the name of the person you are addressing (or "" or None if unknown at this point); "line" with the text of what they said; and "mood" with your current mood.

Your response should take into account your current mood with this other person. Your response should be inside of a multi-line markdown code block, starting on the first line after the opening ```. It should be formatted as a JSON string representing a dictionary with three keys: "name", the name of the person you are addressing (or null or "" if unknown); "line", with the text of what you want to say to them; and "mood", your current mood.'''
                    ),
                ]
            ),
            {
                "character_oneliner": character_oneliner,
                "goals": current_goals,
            },
            open_ai,
            name + " (Conversation)",
            llm_facing_info=LlmFacingInfo(
                description="The conversation persona is responsible for tracking the conversation with the third party and generating new responses for this person to new statements from the third party, it should also be given information on current mood.",
                example_messages=[
                    "You are speaking to William, your mood is 'content' and the last message to you was 'I would love to hear more.' What is your response?",
                    "You are speaking to Apple, your mood is 'frustrated' and the last message to you was 'I think you are wasting my time.' What is your response?",
                    "Your mood is 'happy', you are speaking to Shakespeare, and the last message to you was 'I love you.' What is your response?",
                ],
            ),
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_rewriter_persona(
        name: str,
        character_oneliner: str,
        dialogue_examples: List[str],
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(
                [
                    PersonaMessage.create_system_message("{{ character_oneliner }}"),
                    PersonaMessage.create_user_message(
                        '''{{ character_oneliner}}

Here are some example lines of dialogue you've said:

{% for line in dialogue_examples %}
"""
{{ line }}
"""

{% endfor %}

You want to make sure you reply in the same style. You will be given a proposed response that you might say, as a string, as well as a string describing your current mood. You aren't sure if the proposed response fits in your own voice. Please rewrite the response to better match your voice and style. You shouldn't change the mood or meaning of the line, just the conversational style. Pay close attention to the style of your speech - do you speak in short sentences? Long ones? Do you have an angry tone? A contemplative one? Etc. You should also look at overall response length, word choice, contraction usage, abbreviation usage, profanity usage, and dialect or idiom usage.

Respond with your line inside of a Markdown code block. Example response format:

"""
```
I say, that is quite the surprising news!
```
"""'''
                    ),
                ]
            ),
            {
                "character_oneliner": character_oneliner,
                "dialogue_examples": dialogue_examples,
            },
            open_ai,
            name + " (Rewriter)",
            llm_facing_info=LlmFacingInfo(
                description="The dialogue rewriter persona is responsible for making sure this person's statements fit their mood, personality, and dialogue history.",
                example_messages=[
                    "Your mood is enthusiastic and you are thinking about saying, 'I am glad you asked, that is a fascinating subject.'",
                    "Your mood is joyful and you are thinking about saying, 'I love you too.'",
                ],
            ),
            resend_conversation_history=False,
            streaming_console_mode=streaming_console_mode,
        )
