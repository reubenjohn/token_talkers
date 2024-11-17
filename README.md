# token_talkers

[![codecov](https://codecov.io/gh/reubenjohn/token_talkers/branch/main/graph/badge.svg?token=token_talkers_token_here)](https://codecov.io/gh/reubenjohn/token_talkers/branch/main)
[![CI](https://github.com/reubenjohn/token_talkers/actions/workflows/main.yml/badge.svg)](https://github.com/reubenjohn/token_talkers/actions/workflows/main.yml)

## Usage

```py
from token_talkers import BaseClass
from token_talkers import base_function

BaseClass().base_method()
base_function()
```

```bash
$ python -m token_talkers
#or
$ token_talkers
```

## Setup

To set up the environment variables, create a `.env` file in the root directory of your project and add the following lines:

```shell
OPENAI_BASE_URL=http://192.168.1.199:11434/v1
OPENAI_API_KEY=your_openai_api_key_here
```

Alternatively, you can provide the `--openai_base_url` and `--openai_api_key` arguments when running the CLI:

```bash
$ python -m token_talkers --openai_base_url http://192.168.1.199:11434/v1 --openai_api_key your_openai_api_key_here
#or
$ token_talkers --openai_base_url http://192.168.1.199:11434/v1 --openai_api_key your_openai_api_key_here
```
## Running File Index

To run the `file_index.py` script from the command line, use the following instructions:

1. Ensure you have Python installed on your system.
2. Clone an example repository to use as a codebase. You can use the provided `setup_demo_repo.sh` script to clone the `requests` repository:

```bash
$ ./setup_demo_repo.sh /path/to/destination_folder
```

3. Run the `file_index.py` script to populate the file index database:

```bash
$ python file_index.py /path/to/destination_folder /path/to/database.db --wipe
```

This will index all files in the specified directory and store the information in the SQLite database.

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
