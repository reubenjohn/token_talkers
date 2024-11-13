from openai import OpenAI
import argparse


def main():  # pragma: no cover
    """
    `python -m token_talkers` and `$ token_talkers`.
    This function sets up a command-line interface (CLI) using argparse to parse
    the required `--base_url` argument for the OpenAI API. It then creates an
    OpenAI client and sends a chat completion request to the API with a predefined
    prompt. The response is streamed and printed to the console.
    """

    parser = argparse.ArgumentParser(description="Token Talkers CLI")
    parser.add_argument(
        "--base_url", type=str, required=True, help="The base URL for the OpenAI API"
    )
    args = parser.parse_args()

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
