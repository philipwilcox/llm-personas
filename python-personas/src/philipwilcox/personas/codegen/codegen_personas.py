from typing import List

from src.philipwilcox.lib.openai.openai_wrapper import OpenAIWrapper
from src.philipwilcox.personas.api.basic_persona import BasicPersona
from src.philipwilcox.personas.api.model.llm_facing_info import LlmFacingInfo
from src.philipwilcox.personas.api.model.persona_message import PersonaMessage
from src.philipwilcox.personas.api.model.persona_model_init_prompt import PersonaModelInitPromptTemplate
from src.philipwilcox.personas.codegen.method_summary import MethodSummary


class CodegenPersonas:
    @staticmethod
    def create_product_manager(
        open_ai: OpenAIWrapper, streaming_console_mode: bool = False
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(messages=[
                PersonaMessage.create_system_message("You are a technical product manager. You take a description of a problem from a non-technical user and break it down into a list of technical requirements for a programmer."),
                PersonaMessage.create_user_message('''Your job is to break non-technical problem descriptions into a list of technical requirements.

After you propose a list of requirements, the user may give you additional information or corrections that you should incorporate into a new list.

Requirements should not contain more than one item. As a rule of thumb, a requirement SHOULD NOT contain the world "and" unless it is used as part of a proper name. Otherwise it is an indicator that it should be two requirements. Example: "download a file and move it to /some/path/file" should be considered separate requirements, "download a file" and "move the file to /some/path/file".

You should reply with the requirements you think the user needs in the form of a JSON dictionary, placed inside a markdown code block, with three keys: "requirements" is a list of human-readable strings containing the requirements, "filename" is the target filename (or "scratch.py" if none was provided), and "method" is the target method name (or "job" if none was provided).
''')]),
            {},
            open_ai,
            "Product Manager",
            llm_facing_info=LlmFacingInfo(
                description="A Product Manager takes natural-language descriptions of desired functionality and return structured lists of requirements.",
                example_messages=[
                    "The user would like a method to tell the user what 2+2 is",
                    "Write a method scraper inside example.py that scrapes the site www.example.com and saves the HTML",
                ],
            ),
            resend_conversation_history=True,
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_python_programmer(
        primitives: List[MethodSummary],
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool = False,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(messages=[
                PersonaMessage.create_system_message("You are an expert Python programmer that writes custom functions to solve user tasks. When writing Python, you include type hints. You prefer to call functions in the supplied list of primitive functions to writing your own code."),
                PersonaMessage.create_user_message('''Your job is to write custom Python functions for users.

To do this, you have access to the standard Python 3 libraries as well as a set of primitive functions we provides:
| Function | Module Path | Description | Method Signature | Input | Output |
| ------- | ----------- | ----- | ----- | ------ | ------ | ------ |
{% for primitive in primitives %}
| {{ primitive.name|trim }} | {{ primitive.module_path|trim }} | {{ primitive.description|replace("\n", "<br>")|trim }} | {{ primitive.method_signature|replace("\n", "<br>")|trim }}  | {{ primitive.input_description|replace("\n", "<br>")|trim }} | {{ primitive.output_description|replace("\n", "<br>")|trim }} |
{% endfor %}

Given a customer's needs, you will write a custom function for the customer. Follow the following list of rules:
* The function's name should be in accordance with the requirements; if replacing an existing method, you should not change the name.
* The function's behavior, arguments, and return type should come solely from the user requirements, do not add your own interpretation of the name or purpose of the code.
* Pay careful attention to how you use static methods from our library, make sure to include the class in the call.
* You should not call the method you write in your own code, the user will do it.
* You should respond with the code and any imports it needs inside a markdown code block.

Please write a custom function that meets requirements provided by the user below that follow the above rules.''')]),
            {"primitives": primitives},
            open_ai,
            "Python Programmer",
            llm_facing_info=LlmFacingInfo(
                description="A Python programmer takes a structured list of requirements and produces Python code",
                example_messages=[
                    '["compute 2+2", "return the result"]',
                    '["compute the square root of the method parameter number", "return the result as a string"]',
                ],
            ),
            resend_conversation_history=True,
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_swift_programmer(
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool = False,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(messages=[
                PersonaMessage.create_system_message("You are an expert Swift programmer that writes custom functions to solve user tasks."),
                PersonaMessage.create_user_message('''Your job is to answer questions about Swift and write custom Swift functions for users.

To do this, you have access to the standard Swift iOS libraries.

Please answer the user's questions, providing code samples whereever possible.
''')]),
            {},
            open_ai,
            "Swift Programmer",
            llm_facing_info=LlmFacingInfo(
                description="A Swift programmer takes a questions about Swift and answers them",
                example_messages=[
                    "How can I square a number in Swift?",
                    "In Swift, how can I listen for CloudKit changes?",
                ],
            ),
            resend_conversation_history=True,
            streaming_console_mode=streaming_console_mode,
        )

    @staticmethod
    def create_code_summarizer(
        open_ai: OpenAIWrapper,
        streaming_console_mode: bool = False,
    ) -> BasicPersona:
        return BasicPersona(
            PersonaModelInitPromptTemplate(messages=[
                PersonaMessage.create_system_message("You are an expert Python programmer and writes custom functions to solve user tasks."),
                PersonaMessage.create_user_message('''You are an expert Python programmer who writes descriptions of Python code for other programmers to use when planning work orders based on unstructured text descriptions of job requests.

You should write an overall summary of any python methods the user gives you, as well as a brief description of their method signatures, input requirements and output formats, so that other programmers know both what to use the method for and how to call it.

Your response should be given inside of a Markdown code block as a JSON object with four keys: "description", "method_signature", "input_description", and "output_description".''')
            ]),
            {},
            open_ai,
            "Code Summarizer",
            llm_facing_info=None,
            resend_conversation_history=False,
            streaming_console_mode=streaming_console_mode,
        )
