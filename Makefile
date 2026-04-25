PYTHON = python3
VENV   = .fly_venv
BIN    = $(VENV)/bin
MAP    = maps/easy/01_linear_path.txt

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -r requirements.txt

run:
	$(BIN)/python fly_in.py $(MAP)

visual:
	$(BIN)/python fly_in.py $(MAP) --visual

debug:
	$(BIN)/python -m pdb fly_in.py $(MAP)

tests:
	$(BIN)/pytest tests/

lint:
	$(BIN)/flake8 . --exclude=$(VENV),.pytest_cache,tests/.pytest_cache
	$(BIN)/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(BIN)/flake8 . --exclude=$(VENV),.pytest_cache,tests/.pytest_cache
	$(BIN)/mypy . --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

.PHONY: install run debug lint lint-strict clean visual tests
