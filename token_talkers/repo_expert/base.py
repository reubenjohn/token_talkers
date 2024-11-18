from dataclasses import dataclass
import logging
import os
from pathlib import Path
import argparse
from typing import List
from dotenv import load_dotenv

from openai import OpenAI
from swarm import Swarm, Agent
from swarm.repl.repl import pretty_print_messages


@dataclass
class State:
    state: str
    contains_code: bool
    elements: List[str]


state = State("init", False, [])


code_classifier_agent = Agent(
    name="Code Classifier Agent",
    model="llama3.1:8b",
    tool_choice="required",
    instructions="""
    You are an expert in identifying code within files.
    Your task is to determine if the file contains code that can be imported from other code.
    If it does, execute the tool file_contains_code(true).
    If it does not, execute the tool file_contains_code(false).
    Do not produce any other output other than calling the tool.

    Example:
    1. A Markdown file does not contain code that can be imported elsewhere.
        So call file_contains_code(false).
    2. A Python file contains functions, classes, or constants that can be imported.
        So call file_contains_code(true).
    """,
)

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
    Once you have registered all elements, you may stop processing the file by
        executing the register_element("<--DONE-->").
    DO NOT PRODUCE ANY OTHER OUTPUT other than calling the tool.

    Example:
    1. In a Python file, you find a class named 'Node' at the top level.
        So execute the register_element('Node') tool provided to you.
        You may find multiple elements in a file.
        So execute the register_element('<ElementName>') tool for each element.
    2. In a JavaScript file, you find a function named 'calculate' at the top level.
        So execute the register_element('calculate') tool provided to you.
    """,
)


def file_contains_code(contains_code: bool):
    input(f"file_contains_code called with {contains_code=}. Press Enter to continue...")
    state.state = "classified"
    state.contains_code = contains_code
    return (
        f"🎉 The file has been marked with {contains_code=}. You're work here is done. "
        + "Now just say 'Goodbye'!"
    )


def register_element(name: str):
    input(f"register_element called with {name=}. Press Enter to continue...")
    if name == "<--DONE-->":
        state.state = "done"
        return "🎉 All elements have been registered. You're work here is done. "
    "Now just say 'Goodbye'!"
    print(f"Registered element: {name}")
    state.elements.append(name)
    return f"""Good job on calling the register_element tool.
Registered elements so far: {state.elements}
You may execute the tool again to register more elements.
If you are done registering elements, execute the tool with '<--DONE-->' as the argument."""


code_classifier_agent.functions.append(file_contains_code)
code_register_agent.functions.append(register_element)


def process_files_recursively(path: Path, client: Swarm) -> None:

    for root, _, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            logging.info(f"✨ Processing file: {file_path} ✨")
            try:
                with open(file_path, "r") as f:
                    lines = f.readlines()
                logging.info(f"📄 Read content from file: {file_path} 📄")

                content = "\n".join(lines)

                messages = [
                    {
                        "role": "user",
                        "content": f"""Consider the file '{file_path}' containing {len(lines)} lines
Does it contain code?

<===START OF FILE  '{file_path}' containing {len(lines)} lines===>
{content}
<=== END OF FILE '{file_path}' containing {len(lines)} lines===>

Your task is to determine if the file contains code that can be imported from other code.
If it does, execute the tool file_contains_code(true).
If it does not, execute the tool file_contains_code(false).
Do not produce any other output other than calling the tool.

Example:
1. A Markdown file does not contain code that can be imported elsewhere.
    So call file_contains_code(false).
2. A Python file contains functions, classes, or constants that can be imported.
    So call file_contains_code(true).
""",
                    }
                ]
                logging.info(
                    f"🚀 Sending content to code classifier agent for file: {file_path} 🚀"
                )
                agent = code_classifier_agent

                while state.state == "init":
                    print(f"{agent.functions=}")
                    print(f"{agent.tool_choice=}")
                    response = client.run(agent=agent, messages=messages, stream=False)

                    logging.info("🔄 Receiving response from agent 🔄")
                    pretty_print_messages(response.messages)
                    logging.info("✅ Response from agent complete ✅")

                    messages.extend(response.messages)
                    system_message = {
                        "role": "system",
                        "content": """❌ You must not produce any output.
Please execute the file_contains_code tool. ❌""",
                    }
                    print(system_message)
                    if response.messages[-1]:
                        messages.append(system_message)
                    agent = response.agent

                input("Press Enter to proceed to extract top level entities...")
                messages = [
                    {
                        "role": "user",
                        "content": f"""Given the below file,
    please register only all top level entities as instructed?

<===START OF FILE  '{file_path}' containing {len(lines)} lines===>
{content}
<=== END OF FILE '{file_path}' containing {len(lines)} lines===>""",
                    }
                ]
                logging.info(
                    f"🚀 Sending content to code classifier agent for file: {file_path} 🚀"
                )
                agent = code_register_agent
                while state.state != "done":
                    print(f"{agent.functions=}")
                    print(f"{agent.tool_choice=}")
                    response = client.run(agent=agent, messages=messages, stream=False)

                    logging.info("🔄 Receiving response from agent 🔄")
                    pretty_print_messages(response.messages)
                    logging.info("✅ Response from agent complete ✅")

                    messages.extend(response.messages)
                    system_message = {
                        "role": "system",
                        "content": """❌ You must not produce any output.
Only execute the tools provided.
If you are done, call the register_element tool with the argument name='<--DONE-->' ❌""",
                    }
                    print(system_message)
                    if response.messages[-1]:
                        messages.append(system_message)
                    agent = response.agent

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
