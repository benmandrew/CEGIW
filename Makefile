.PHONY: test unittest expect_test fmt fmt-ci lint ruff pylint mypy bandit doc coverage coverage-html badge

BOLD_CYAN := \033[1;36m
RESET := \033[0m

define log
	@printf '$(BOLD_CYAN)[%s]$(RESET)\n' "$(1)"
endef

all: fmt lint test

test: unittest expect_test

unittest:
	$(call log,Running unit tests)
	@PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"

coverage:
	$(call log,Running coverage tests)
	@coverage erase
	@coverage run --source=src -m unittest discover -s tests -p "test_*.py"
	@for t in $(EXPECT_TESTS); do \
		echo "Running $$t..."; \
		COVERAGE_PROCESS_START=pyproject.toml PYTHONPATH=tests:src expect -- $$t || { echo "Test $$t FAILED"; exit 1; }; \
	done
	@coverage combine
	@coverage report -m
	@coverage-badge -q -f -o docs/coverage.svg

coverage-html:
	$(call log,Running coverage tests (HTML report))
	@coverage erase
	@coverage run --source=src -m unittest discover -s tests -p "test_*.py"
	@for t in $(EXPECT_TESTS); do \
		echo "Running $$t..."; \
		COVERAGE_PROCESS_START=pyproject.toml PYTHONPATH=tests:src expect -- $$t || { echo "Test $$t FAILED"; exit 1; }; \
	done
	@coverage combine
	@coverage html
	@coverage-badge -q -f -o docs/coverage.svg
	@echo "Open htmlcov/index.html to view the coverage report."

EXPECT_TESTS := $(wildcard tests/test_*.exp)

expect_test:
	$(call log,Running expect tests)
	@for t in $(EXPECT_TESTS); do \
		echo "Running $$t..."; \
		expect -- $$t || { echo "Test $$t FAILED"; exit 1; }; \
	done
	@echo "All expect tests passed!"

badge:
	$(call log,Generating coverage badge)
	@coverage-badge -q -f -o docs/coverage.svg

fmt:
	$(call log,Formatting code)
	@python3 -m black -l 80 .

fmt-ci:
	$(call log,Checking code formatting)
	@python3 -m black --check -l 80 .

lint: ruff-fix pylint mypy bandit

ruff:
	$(call log,Running ruff)
	@python3 -m ruff check

ruff-fix:
	$(call log,Running ruff --fix)
	@python3 -m ruff check --fix

pylint:
	$(call log,Running pylint)
	@find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m pylint --score=n

mypy:
	$(call log,Running mypy)
	@find . -name "*.py" -not -path "*/.*" -not -path "./docs/*" | PYTHONPATH=src xargs python3 -m mypy --strict

vulture:
	$(call log,Running vulture)
	@find . -name "*.py" -not -path "*/.*" | PYTHONPATH=src xargs python3 -m vulture

bandit:
	$(call log,Running bandit)
	@python3 -m bandit -c pyproject.toml --exclude "./.venv" -r . -q

docs:
	$(MAKE) -C docs html
