from dataclasses import dataclass
from enum import Enum
import logging
import os
from pathlib import Path
import argparse
from typing import List, Optional
from dotenv import load_dotenv

from openai import OpenAI
from swarm import Swarm, Agent
from swarm.repl.repl import pretty_print_messages

CLASSIFICATION_RETRY_LIMIT = 3  # Define the retry limit


@dataclass
class State:
    state: str
    contains_code: bool
    elements: List[str]


state = State("init", False, [])


class CodeFileClassification(Enum):
    CODE_FILE = "CODE_FILE"
    NOT_CODE_FILE = "NOT_CODE_FILE"
    INVALID = "INVALID"


code_classifier_agent = Agent(
    name="Code Classifier Agent",
    model="llama3.1:8b",
    tool_choice="required",
    instructions="""You are an expert in identifying code within files.
Your task is to determine if the file contains code that can be imported from other code.
If it does, then say "The file is a CODE file".
If it does not, "The file is NOT a code file".
Explain your reasoning as you read the input document.

Example:
1. Input <A Markdown file does not contain code>
    Expected output:
    The provided file is a markdown file that describes how to set up the project.
    It is not a code file, and thus does not contain code that can be imported.
    The file is NOT a code file
2. Input: <A Python file contains functions, classes, or constants that can be imported>
    Expected output:
    The provided file is a Python file.
    It includes implementations for parsing command line arguments, reading files,
        and writing to files.
    I have identified constants such as MAX_LEN, a function called consume_stream,
        and a classes such as ArgumentContainer, etc.
    This function and class among others can be imported and used in other code.
    The file is a CODE file
    """,
)

code_file_pattern = "The file is a CODE file"
not_code_file_pattern = "The file is NOT a code file"

code_register_agent = Agent(
    name="Code Register Agent",
    model="llama3.1:8b",
    tool_choice="required",
    instructions="""
You are an expert in code analysis.
Your task is to register all top-level elements in the code, such as classes, constants,
    and functions.
Do not process nested functions, classes, or methods of classes.
Register each top level element by executing the tool register_element(name)
Provide your reasoning or justification as to why you register an element
    before you use the tool to register the element.
Once you have registered all elements, say:
ALL ELEMENTS REGISTERED

Example:
1. Input:
<===START OF FILE  '/path/cookies.py' containing 411 lines===>
\"\"\"
requests.cookies
~~~~~~~~~~~~~~~~

...
\"\"\"

import calendar
...
from .compat import Morsel, MutableMapping, cookielib, urlparse, urlunparse


class MockRequest:
    \"\"\"Wraps a `requests.Request` to mimic a `urllib2.Request`.

    The code in `http.cookiejar.CookieJar` ...
    \"\"\"

    class State:
        ...

    def __init__(self, request):
        self._r = request
        ...

    ...

    def get_full_url(self):
        # Only return the response's URL if the user hadn't set the Host
        ...
        return urlunparse([...])


class MockResponse:
    ...


def extract_cookies_to_jar(jar, request, response):
    ...

class CookieConflictError(RuntimeError):
    ...
<=== END OF FILE '/path/cookies.py' containing 411 lines===>

Expected Output:
The file contains code that can be imported.
The first top-level element is a class named 'MockRequest'.
'MockRequest' has nested methods and a nested class called 'State' but they aren't to be registered
    since they are nested.
Here you would call the register_element('MockRequest') tool provided to you.

The next top level is a class called 'MockResponse'.
...
The next top level is a function called 'extract_cookies_to_jar'.
...
The last top level is a class called 'CookieConflictError'.

In total, you would use the register_element tool 4 times to register the elements.

2. You would proceed similarly when provided with a Javascript file.
    """,
)

code_registered_pattern = "ALL ELEMENTS REGISTERED"


# def file_contains_code(contains_code: bool):
#     input(f"file_contains_code called with {contains_code=}. Press Enter to continue...")
#     state.state = "classified"
#     state.contains_code = contains_code
#     return (
#         f"🎉 The file has been marked with {contains_code=}. You're work here is done. "
#         + "Now just say 'Goodbye'!"
#     )


def register_element(name: str):
    input(f"register_element called with {name=}. Press Enter to continue...")
    state.elements.append(name)
    return f"""Good job on calling the register_element tool.
Registered elements so far: {state.elements}
You may execute the tool again to register more elements."""


# code_classifier_agent.functions.append(file_contains_code)
code_register_agent.functions.append(register_element)


def classify_code_file_agent_response(messages: List[dict]) -> CodeFileClassification:
    if not messages:
        return CodeFileClassification.INVALID
    content = messages[-1]["content"]
    if code_file_pattern.lower() in content.lower():
        return CodeFileClassification.CODE_FILE
    elif not_code_file_pattern.lower() in content.lower():
        return CodeFileClassification.NOT_CODE_FILE
    else:
        return CodeFileClassification.INVALID


def classify_file(file_path: Path, content: str, n_lines: int, client: Swarm) -> bool:
    messages = [
        {
            "role": "user",
            "content": f"""Consider the file '{file_path}' containing {n_lines} lines
Does it contain code?

<===START OF FILE  '{file_path}' containing {n_lines} lines===>
{content}
<=== END OF FILE '{file_path}' containing {n_lines} lines===>
Your task is to determine if the file contains code that can be imported from other code.
If it does, then say "The file is a CODE file".
If it does not, "The file is NOT a code file".
Explain your reasoning as you read the input document.

Example:
1. Input <A Markdown file does not contain code>
    Expected output:
    The provided file is a markdown file that describes how to set up the project.
    It is not a code file, and thus does not contain code that can be imported.
    The file is NOT a code file
2. Input: <A Python file contains functions, classes, or constants that can be imported>
    Expected output:
    The provided file is a Python file.
    It includes implementations for parsing command line arguments, reading files,
        and writing to files.
    I have identified constants such as MAX_LEN, a function called consume_stream,
        and a classes such as ArgumentContainer, etc.
    This function and class among others can be imported and used in other code.
    The file is a CODE file
""",
        }
    ]
    for _ in range(CLASSIFICATION_RETRY_LIMIT):
        response = client.run(agent=code_classifier_agent, messages=messages, stream=False)
        messages.extend(response.messages)

        logging.info("🔄 Receiving response from agent 🔄")
        pretty_print_messages(response.messages)

        logging.info("❔ Inspecting agent response")

        agent_classification = classify_code_file_agent_response(response.messages)
        if agent_classification == CodeFileClassification.INVALID:
            feedback_message = {
                "role": "system",
                "content": """❌ Invalid response. ❌
Your task is to register all top-level elements in the code, such as classes, constants,
    and functions.
Do not process nested functions, classes, or methods of classes.
Register each top level element by executing the tool register_element(name)
Provide your reasoning or justification as to why you register an element
    before you use the tool to register the element.
Once you have registered all elements, say:
ALL ELEMENTS REGISTERED
""",
            }
            pretty_print_messages([feedback_message])
            messages.append(feedback_message)

        else:
            if agent_classification == CodeFileClassification.CODE_FILE:
                logging.info(f"✅ Response from agent is valid: {agent_classification} ✅")
                return True
            elif agent_classification == CodeFileClassification.NOT_CODE_FILE:
                logging.info(f"✅ Response from agent is valid: {agent_classification} ✅")
                return False
            else:
                raise ValueError(f"Unknown CodeFileClassification: {agent_classification}")

    raise ValueError(f"Code classification retry limit ({CLASSIFICATION_RETRY_LIMIT}) exceeded")


def classify_code_register_agent_response(messages: List[dict]) -> Optional[str]:
    if not messages:
        return None
    content = messages[-1]["content"]
    if code_registered_pattern.lower() not in content.lower():
        return """If you are done using the register_element tool, say 'ALL ELEMENTS REGISTERED'.
Otherwise, continue to provide justifications and use the tool to register elements."""

    if not state.elements:
        feedback = """You said 'ALL ELEMENTS REGISTERED',
    but did not provide any elements to register.
Did you forget to execute the register_element tool that was provided to you?"""
        if "register_element" in content.lower():
            feedback += """
I also detected that your response included 'register_element'.
If you meant to use the register_element tool instead,
    please use the provided tool instead of including it in your response."""
        return feedback

    return "SUCCESS"


def register_elements(file_path: Path, content: str, num_lines: int, client: Swarm) -> None:
    messages = [
        {
            "role": "user",
            "content": f"""Given the below file,
please register only all top level entities as instructed.

<===START OF FILE  '{file_path}' containing {num_lines} lines===>
{content}
<=== END OF FILE '{file_path}' containing {num_lines} lines===>""",
        }
    ]
    for _ in range(CLASSIFICATION_RETRY_LIMIT):
        logging.info(f"🚀 Sending content to code register agent for file: {file_path} 🚀")
        response = client.run(agent=code_register_agent, messages=messages, stream=False)
        messages.extend(response.messages)

        logging.info("🔄 Receiving response from agent 🔄")
        pretty_print_messages(response.messages)

        logging.info("❔ Inspecting agent response")

        feedback = classify_code_register_agent_response(response.messages)
        if feedback is None:
            feedback_message = {
                "role": "system",
                "content": """❌ There was a problem processing your response. Please try again ❌""",
            }
        elif feedback == "SUCCESS":
            logging.info("✅ Response from agent complete ✅")
            return
        else:
            feedback_message = {
                "role": "system",
                "content": f"""❌ Invalid response. ❌
{feedback}
Note: This feedback was provided by an automated system and is not monitored by humans.
Please do not expect any human feedback on the task.""",
            }
        pretty_print_messages([feedback_message])
        messages.append(feedback_message)

    raise ValueError(f"Code registration retry limit ({CLASSIFICATION_RETRY_LIMIT}) exceeded")


def process_files_recursively(path: Path, client: Swarm) -> None:

    for root, _, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            # file_path = Path("../demo_repos/requests/setup.py")
            logging.info(f"✨ Processing file: {file_path} ✨")
            try:
                with open(file_path, "r") as f:
                    lines = f.readlines()
                logging.info(f"📄 Read content from file: {file_path} 📄")
                content = "\n".join(lines)

                is_code_file = classify_file(file_path, content, len(lines), client)

                if not is_code_file:
                    logging.info(f"🎉 File {file_path} does not contain code 🎉")
                    print(f"File: {file_path} - Contains code: False")
                    continue

                input("Press Enter to proceed to extract top level entities...")
                register_elements(file_path, content, len(lines), client)

            except Exception as e:
                logging.error(f"❌ Error processing file {file_path}: {e} ❌")
                raise e

            input("Press Enter to proceed to next file...")

            # if response.next_agent == code_register_agent:
            #     messages = [{"role": "user", "content": content}]
            #     response = client.run(agent=code_register_agent, messages=messages)
            #     print(
            #         f"File: {file_path} - Registered elements: {response.messages[-1]['content']}"
            #     )
            # else:
            #     print(f"File: {file_path} - Contains code: False")


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Process files recursively")
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="The input directory to process files recursively",
    )
    parser.add_argument(
        "--swarm_base_url",
        type=str,
        default=os.getenv("OPENAI_BASE_URL"),
        help="The base URL for the Swarm API",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="The API key for the Swarm API",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args.swarm_base_url is None:
        raise ValueError("The --swarm_base_url argument is required")

    if args.api_key is None:
        raise ValueError("The --api_key argument is required")

    openai_client = OpenAI(
        base_url=args.swarm_base_url,
        api_key=args.api_key,
    )
    client = Swarm(client=openai_client)

    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        raise ValueError(f"The input path {input_path} is not a directory")

    process_files_recursively(input_path, client)
