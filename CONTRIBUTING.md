# How to develop on this project

token_talkers welcomes contributions from the community.

**You need PYTHON3!**

This instructions are for linux base systems. (Linux, MacOS, BSD, etc.)

## Setting up your own fork of this repo.

- On github interface click on `Fork` button.
- Clone your fork of this repo. `git clone git@github.com:YOUR_GIT_USERNAME/token_talkers.git`
- Enter the directory `cd token_talkers`
- Add upstream repo `git remote add upstream https://github.com/reubenjohn/token_talkers`

## Help

Run `make help` to show the available make targets.

## Show the current environment

Run `make show` to display the current environment information.

## Install the project in develop mode

Run `make install` to install the project in develop mode.

## IDE reccomendations

### VS Code

#### Install VS Code Extensions

To ensure that you have all the necessary tools for development, install the following VS Code extensions:

- Python (ms-python.python)
- Flake8 (ms-python.flake8)
- MyPy (ms-python.mypy-type-checker)
- Black Formatter (ms-python.black-formatter)

You can install these extensions by searching for them in the Extensions view (`Ctrl+Shift+X`) in VS Code.

#### ExampleVS Code Settings
Create a `.vscode/settings.json` file in the root of your project with the following content (some of these settings can also be configured using the UI):

```json
{
    "python.analysis.autoImportCompletions": true,
    "python.testing.unittestArgs": [
        "-v",
        "-s",
        "./tests",
        "-p",
        "test_*.py"
    ],
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "flake8.importStrategy": "fromEnvironment",
    "mypy-type-checker.importStrategy": "fromEnvironment",
    "black-formatter.importStrategy": "fromEnvironment"
}
```

This configuration will set up VS Code to use the appropriate settings for linting, formatting, and testing.
## Run the tests to ensure everything is working

Run `make test` to run the tests.

## Create a new branch to work on your contribution

Run `git checkout -b my_contribution`

## Make your changes

Edit the files using your preferred editor. (we recommend VIM or VSCode)

## Format the code

Run `make fmt` to format the code.

## Run the linter

Run `make lint` to run the linter.

## Test your changes

Run `make test` to run the tests.

Ensure code coverage report shows `100%` coverage, add tests to your PR.

## Watch tests

Run `make watch` to run tests on every change.

## Build the docs locally

Run `make docs` to build the docs.

Ensure your new changes are documented.

## Clean the project

Run `make clean` to remove unused files and directories.

## Commit your changes

This project uses [conventional git commit messages](https://www.conventionalcommits.org/en/v1.0.0/).

Example: `fix(package): update setup.py arguments 🎉` (emojis are fine too)

## Push your changes to your fork

Run `git push origin my_contribution`

## Submit a pull request

On github interface, click on `Pull Request` button.

Wait CI to run and one of the developers will review your PR.
## Makefile utilities

This project comes with a `Makefile` that contains a number of useful utility.

```bash 
❯ make
Usage: make <target>

Targets:
help:             ## Show the help.
install:          ## Install the project in dev mode.
fmt:              ## Format code using black & isort.
lint:             ## Run pep8, black, mypy linters.
test: lint        ## Run tests and generate coverage report.
watch:            ## Run tests on every change.
clean:            ## Clean unused files.
release:          ## Create a new tag for release.
docs:             ## Build the documentation.
```

## Making a new release

This project uses [semantic versioning](https://semver.org/) and tags releases with `X.Y.Z`
Every time a new tag is created and pushed to the remote repo, github actions will
automatically create a new release on github and trigger a release on PyPI.

For this to work you need to setup a secret called `PIPY_API_TOKEN` on the project settings>secrets, 
this token can be generated on [pypi.org](https://pypi.org/account/).

To trigger a new release all you need to do is.

1. If you have changes to add to the repo
    * Make your changes following the steps described above.
    * Commit your changes following the [conventional git commit messages](https://www.conventionalcommits.org/en/v1.0.0/).
2. Run the tests to ensure everything is working.
4. Run `make release` to create a new tag and push it to the remote repo.

the `make release` will ask you the version number to create the tag, ex: type `0.1.1` when you are asked.

> **CAUTION**:  The make release will change local changelog files and commit all the unstaged changes you have.
