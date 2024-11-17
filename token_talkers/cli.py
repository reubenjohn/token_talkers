import argparse
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os


def main():  # pragma: no cover
    """
    `python -m token_talkers` and `$ token_talkers`.
    This function sets up a command-line interface (CLI) using argparse to parse
    the required `--base_url` argument for the OpenAI API. It then creates an
    OpenAI client and sends a chat completion request to the API with a predefined
    prompt. The response is streamed and printed to the console.
    """

    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Token Talkers CLI")
    parser.add_argument(
        "--base_url",
        type=str,
        default=os.getenv("BASE_URL"),
        help="The base URL for the OpenAI API",
    )
    args = parser.parse_args()

    if args.base_url is None:
        raise ValueError("The --base_url argument is required")
    else:
        logging.info(f"Using base URL: {args.base_url}")

    client = OpenAI(
        base_url=args.base_url,
        api_key="ollama",  # required, but unused
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
