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
## File Index

"""
Schema Documentation:

The SQLite database schema consists of two tables: `hard_files` and `soft_files`.

1. `hard_files` Table:
  - `path` (TEXT PRIMARY KEY): The absolute path to the file.
  - `size` (INTEGER): The size of the file in bytes.
  - `is_binary` (BOOLEAN): A flag indicating whether the file is binary.
  - `number_of_lines` (INTEGER): The number of lines in the file (0 for binary files).
  - `processed` (BOOLEAN): A flag indicating whether the file has been processed.

  This table stores metadata about the actual files present in the file system.

2. `soft_files` Table:
  - `path` (TEXT PRIMARY KEY): The absolute path to the symbolic link.
  - `hard_path` (TEXT): The absolute path to the actual file that the symbolic link points to.
    - FOREIGN KEY(hard_path) REFERENCES `hard_files`(path)

  This table stores metadata about symbolic links and their corresponding actual files.

The schema is used to index files and symbolic links in a directory, allowing for efficient querying and management of file metadata.
"""

### Running File Index

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
