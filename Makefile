VENV   = .venv
PYTHON = $(VENV)/bin/python3
PIP    = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

.PHONY: venv test test-all test-unit test-slow coverage clean

# ── Environment setup ────────────────────────────────────────────────────────

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt requirements-test.txt
	python3 -m venv $(VENV)
	$(PIP) install --quiet -r requirements.txt -r requirements-test.txt
	@touch $(VENV)/bin/activate
	@echo "venv ready — run 'make test'"

# ── Test targets ─────────────────────────────────────────────────────────────

test: venv
	$(PYTEST) -m "not slow" -v

test-all: venv
	$(PYTEST) -v

test-unit: venv
	$(PYTEST) tests/test_unit.py -v

test-slow: venv
	$(PYTEST) -m "slow" -v

coverage: venv
	$(PYTEST) -m "not slow" --cov=. --cov-report=term-missing

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	rm -rf $(VENV) .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
