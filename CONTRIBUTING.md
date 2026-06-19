# Contributing to LMIP

Thank you for your interest in contributing to the Labor Market Intelligence Platform (LMIP)! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

* **Python 3.10+** — Required for local development
* **Java 11 or 17** — Required for PySpark testing
* **Databricks CLI** — For deployment and workspace operations
* **Git** — For version control

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd LMIP

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
pytest tests/ -m "cdc or identity"
```

## Development Workflow

### Branching Strategy

* **`main`** — Production-ready code, protected branch
* **`develop`** — Integration branch for feature testing
* **`feature/*`** — Feature development branches
* **`bugfix/*`** — Bug fix branches
* **`hotfix/*`** — Urgent production fixes

### Creating a Feature Branch

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: descriptive commit message"

# Push and create pull request
git push origin feature/your-feature-name
```

## Code Standards

### Python Code Style

* **PEP 8** — Follow Python style guidelines
* **Type Hints** — Use type annotations for function signatures
* **Docstrings** — Document all functions, classes, and modules
* **Line Length** — 120 characters maximum
* **Imports** — Organize with isort, group by stdlib, third-party, local

### SQL Code Style

* **Keywords** — UPPERCASE (SELECT, FROM, WHERE, JOIN)
* **Identifiers** — lowercase_with_underscores for table/column names
* **Indentation** — 2 spaces for query structure
* **Comments** — Use `--` for inline comments, document complex logic

### Notebook Standards

* **Cell Titles** — Always provide descriptive titles for code cells
* **Documentation** — Include markdown cells explaining logic
* **Parameters** — Use widgets for configurable values
* **Error Handling** — Wrap critical operations in try/except blocks
* **Output** — Use `display()` for DataFrames, not implicit display

## Testing Requirements

### Pre-Commit Checklist

Before submitting a pull request:

- [ ] Run highest priority tests: `pytest -m "cdc or identity"`
- [ ] Run affected layer tests: `pytest tests/notebooks/test_<layer>_notebooks.py`
- [ ] Check code coverage: `pytest --cov=LMIP --cov-report=term`
- [ ] Run linting: `flake8 . --count --show-source --statistics`
- [ ] Format code: `black . --check`
- [ ] All tests pass ✅

### Writing Tests

* **Unit Tests** — Test critical logic in isolation (CDC, identity, sector, SCD2)
* **Integration Tests** — Test notebook execution end-to-end
* **Workflow Tests** — Test complete orchestration flows
* **Coverage Goal** — 70%+ for new code, 95%+ for critical logic

See [tests/README.md](tests/README.md) for comprehensive testing documentation.

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

* **feat** — New feature
* **fix** — Bug fix
* **docs** — Documentation changes
* **style** — Code style changes (formatting, no logic change)
* **refactor** — Code refactoring (no feature or bug fix)
* **test** — Adding or updating tests
* **chore** — Maintenance tasks (dependencies, build, etc.)
* **perf** — Performance improvements

### Examples

```bash
feat(bronze): add API response log deduplication logic

fix(silver): correct CDC hash computation for null values

docs(deployment): update bootstrap.py taxonomy seeding documentation

test(unit): add edge case tests for identity matching
```

## Pull Request Process

### Before Submitting

1. **Sync with base branch**: `git pull origin develop --rebase`
2. **Run full test suite**: `pytest tests/`
3. **Verify no linting errors**: `flake8 .`
4. **Update documentation** if API or architecture changes
5. **Add entry to CHANGELOG.md** under "Unreleased" section

### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] CHANGELOG.md updated
```

### Review Process

* **Minimum 1 approval** required for feature branches
* **Minimum 2 approvals** required for main branch
* **All CI checks must pass** before merge
* **Address all review comments** or explain why not

## Architecture Guidelines

### Layer Responsibilities

* **Bronze** — Raw data ingestion, minimal transformation
* **Silver** — Data standardization, CDC detection, DQ validation
* **Intermediate** — Deduplication, canonicalization, enrichment
* **Warehouse** — Dimensional modeling (SCD2, facts, bridges)
* **Gold** — Aggregated metrics, business-ready views
* **Publish** — External export, manifest generation

### Naming Conventions

**Tables**:
* Bronze: `<source>_<entity>_raw` (e.g., `linkedin_jobs_raw`)
* Silver: `<entity>_<stage>` (e.g., `jobs_standardized`, `jobs_cdc`)
* Intermediate: `<entity>_<process>` (e.g., `company_canonical`, `role_mapped`)
* Warehouse: `dim_<entity>`, `fact_<entity>`, `bridge_<entity>`
* Gold: `agg_<metric>`, `<entity>_metrics`

**Notebooks**:
* Layer prefix: `bronze_`, `silver_`, `inter_`, `wh_`, `gold_`, `publish_`
* Verb-noun pattern: `bronze_write_api_response_log`, `silver_detect_cdc`

**Workflows**:
* Environment suffix: `LMIP_<workflow>_<ENV>` (e.g., `LMIP_Bronze_Ingestion_DEV`)

## Documentation Standards

### Code Documentation

* **Functions** — Docstring with description, parameters, returns, raises
* **Classes** — Docstring with description, attributes, methods
* **Modules** — Top-level docstring with purpose and usage
* **Complex Logic** — Inline comments explaining "why", not "what"

### Project Documentation

* **README.md** — Project overview, quick start, architecture
* **docs/** — Detailed documentation by topic
* **tests/README.md** — Testing guide and standards
* **sql/README.md** — SQL layer architecture
* **deployment/README.md** — Deployment guide

### Documentation Updates

Documentation must be updated when:
* Adding new notebooks or workflows
* Changing table schemas or data contracts
* Modifying deployment procedures
* Adding new testing requirements
* Changing architecture patterns

## Deployment Guidelines

### Environment Promotion

```
Development (DEV) → Staging (STG) → Production (PROD)
```

* **DEV** — Feature development and testing
* **STG** — Pre-production validation
* **PROD** — Production workloads

### Deployment Process

1. **Test in DEV**: Full test suite passes
2. **Deploy to STG**: Smoke test critical workflows
3. **Validate STG**: End-to-end validation with production-like data
4. **Deploy to PROD**: Blue-green or canary deployment
5. **Monitor**: Check metrics, logs, and alerts

See [deployment/README.md](deployment/README.md) for detailed deployment procedures.

## Getting Help

* **Documentation**: Check docs/ directory first
* **Tests**: See tests/README.md for testing guidance
* **Issues**: Search GitHub issues for similar problems
* **Slack**: #data-engineering channel for team support
* **Code Review**: Tag @data-engineering-team for reviews

## Code of Conduct

* **Be respectful** — Treat all contributors with respect
* **Be constructive** — Provide actionable feedback
* **Be collaborative** — Work together to solve problems
* **Be inclusive** — Welcome diverse perspectives
* **Be professional** — Maintain a professional environment

## License

By contributing to LMIP, you agree that your contributions will be licensed under the project's license (see LICENSE file).

---

**Questions?** Open an issue or reach out to the Data Engineering team.

Thank you for contributing! 🚀
