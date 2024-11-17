import argparse
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os


def main():  # pragma: no cover
    """
    `python -m token_talkers` and `$ token_talkers`.
    This function sets up a command-line interface (CLI) using argparse to parse
    the required `--openai_base_url` and `--api_key` arguments for the OpenAI API.
    It then creates an OpenAI client and sends a chat completion request to the API
    with a predefined prompt. The response is streamed and printed to the console.
    """

    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Token Talkers CLI")
    parser.add_argument(
        "--openai_base_url",
        type=str,
        default=os.getenv("OPENAI_BASE_URL"),
        help="The base URL for the OpenAI API",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="The API key for the OpenAI API",
    )
    args = parser.parse_args()

    if args.openai_base_url is None:
        raise ValueError("The --openai_base_url argument is required")
    else:
        logging.info(f"Using base URL: {args.openai_base_url}")

    if args.api_key is None:
        raise ValueError("The --api_key argument is required")

    client = OpenAI(
        base_url=args.openai_base_url,
        api_key=args.api_key,
    )

    response = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a poem about a rainbow."},
        ],
        stream=True,  # this time, we set stream=True
    )

    for chunk in response:
        print(chunk.choices[0].delta.content, end="")
