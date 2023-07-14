import re

# Based on GPT query to my Python Programmer persona: write a compiled Python regex to extract the inner match of just the code (this match should be named 'text' inside of a multi-line markdown block delimited with "```" lines, with optionally text right after the opening "```" on the same line specifying the name of the language
PATTERN = pattern = r"```(?:\w+)?\s*\n(?P<text>.*?)\n```"


def extract_code_block(text: str) -> str:
    match = re.search(PATTERN, text, re.DOTALL)
    if match:
        return match.group("text")
    raise Exception("No text match found")
