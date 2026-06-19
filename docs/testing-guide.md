# LMIP Testing Guide

> **Note:** This document has been consolidated into the canonical test documentation at [tests/README.md](../tests/README.md).

For comprehensive testing documentation, see:

**[tests/README.md](../tests/README.md)** — Complete test suite documentation including:
* Test structure and priority organization
* Installation and setup
* Execution patterns and commands
* Test markers and selective execution
* Coverage goals and reporting
* Notebook and workflow integration tests
* Pre-commit checklist
* Troubleshooting guide
* CI/CD integration details

## Quick Links

* **Test Files:** [tests/](../tests/)
* **Workflow Tests:** [tests/workflows/README.md](../tests/workflows/README.md)
* **CI Configuration:** [.github/workflows/pytest-ci.yml](../.github/workflows/pytest-ci.yml)
* **Test Configuration:** [pytest.ini](../pytest.ini)
* **Test Fixtures:** [tests/conftest.py](../tests/conftest.py)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run highest priority tests (CDC + Identity)
pytest -m "cdc or identity"

# Run with coverage
pytest --cov=LMIP --cov-report=html
```

For detailed documentation, see **[tests/README.md](../tests/README.md)**.
