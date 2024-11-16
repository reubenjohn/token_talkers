.ONESHELL:
ENV_PREFIX="$(shell poetry env list --full-path | grep Activated | cut -d' ' -f1)/bin/"

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@poetry env info

.PHONY: install
install:          ## Install the project in dev mode.
	@if ! poetry --version > /dev/null 2>&1; then \
		echo "Poetry is not installed. Installing..."; \
		python -m pip install poetry; \
	else \
		echo "Poetry is already installed."; \
	fi
	@poetry install

.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)isort token_talkers/
	$(ENV_PREFIX)black token_talkers/
	$(ENV_PREFIX)black tests/

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	@echo $(ENV_PREFIX)
	$(ENV_PREFIX)flake8 token_talkers/
	$(ENV_PREFIX)black --check token_talkers/
	$(ENV_PREFIX)black --check tests/
	$(ENV_PREFIX)mypy --ignore-missing-imports token_talkers/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -v --cov-config .coveragerc --cov=token_talkers -l --tb=short --maxfail=1 tests/
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr $(ENV_PREFIX)pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > token_talkers/VERSION
	@$(ENV_PREFIX)gitchangelog > HISTORY.md
	@git add token_talkers/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: docs
docs:             ## Build the documentation.
	@echo "building documentation ..."
	@$(ENV_PREFIX)mkdocs build
	URL="site/index.html"; xdg-open $$URL || sensible-browser $$URL || x-www-browser $$URL || gnome-open $$URL || open $$URL

.PHONY: init
init:             ## Initialize the project based on an application template.
	@./.github/init.sh


# This project has been generated from rochacbruno/python-project-template
# __author__ = 'rochacbruno'
# __repo__ = https://github.com/rochacbruno/python-project-template
# __sponsor__ = https://github.com/sponsors/rochacbruno/
