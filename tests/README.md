# LMIP Test Suite

## Overview

This directory contains the comprehensive LMIP test suite, organized into three categories:
1. **Unit Tests** — Logic tests for critical pipeline components (CDC, identity, sector, etc.)
2. **Notebook Tests** — Integration tests for individual notebooks by layer
3. **Workflow Tests** — End-to-end integration tests for complete workflows

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run highest priority tests (CDC + Identity)
pytest -m "cdc or identity"

# Run notebook integration tests
pytest tests/notebooks/

# Run workflow integration tests
pytest tests/workflows/

# Run with coverage
pytest --cov=LMIP --cov-report=html
```

## Test Files (Priority Order)

### Highest Risk (Critical Logic)

**`test_cdc_hash_logic.py`** — CDC Hash Computation and Change Detection
* Hash determinism and consistency
* Change detection (INSERT, UPDATE, DELETE)
* Source-aware deletion logic
* Edge cases: empty batches, duplicate staging records, staleness thresholds

**`test_identity_matching.py`** — Cross-Source Deduplication
* Identity key generation from normalized fields
* Cross-source duplicate detection
* Deduplication ranking strategies (first-seen, source priority)
* Identity mapping table operations

### High Risk (Complex Logic)

**`test_sector_assignment.py`** — Keyword-Based Sector Classification
* Keyword matching (case-insensitive, substring)
* Multi-sector scoring with title/description weighting
* Confidence thresholds
* Edge cases: no matches (unknown sector), partial word matching, special characters

**`test_scd2_key_generation.py`** — Slowly Changing Dimension Type 2
* Surrogate key generation and uniqueness
* SCD2 change detection logic
* Effective date management (effective_from, effective_to)
* is_current flag management
* Historical queries (current version, version at date, complete history)

### Medium Risk (Boolean Logic)

**`test_quarantine_routing.py`** — Data Quality Quarantine Management
* Quarantine rule evaluation (required fields, invalid dates, suspicious content)
* Categorization by failure reason
* Quarantine actions (quarantine, release, retry)
* Retention policies and reporting

**`test_export_bundle_manifest.py`** — Publish Contract Validation
* Manifest JSON structure validation
* Schema consistency checks
* Versioning and backward compatibility
* Data quality metrics in manifest
* Lineage information

## Notebook Integration Tests

Test each notebook's structure, parameters, and execution logic:

### `notebooks/test_bronze_notebooks.py`
Tests for Bronze layer notebooks:
* `bronze_write_api_response_log`
* `bronze_write_job_snapshot`
* `bronze_dedupe_raw_payload`
* `bronze_finalize_batch`
* `bronze_replay_backfill`
* `bronze_rollback_batch`

### `notebooks/test_silver_notebooks.py`
Tests for Silver layer notebooks:
* `silver_standardize_jobs`
* `silver_detect_cdc`
* `silver_job_identity_map`
* `silver_sector_assign`
* `silver_skill_extract`
* `silver_dq_validate`
* `silver_quarantine_route`
* `silver_apply_soft_delete_restore`
* `silver_semantic_review_queue`

### `notebooks/test_intermediate_notebooks.py`
Tests for Intermediate layer notebooks:
* `inter_company_canonicalize`
* `inter_review_resolver`
* `inter_role_map`
* `inter_sector_normalize`
* `inter_skill_catalog_sync`
* `inter_skill_graph_build`
* `metadata_loader`

### `notebooks/test_warehouse_notebooks.py`
Tests for Warehouse layer notebooks:
* `wh_dim_job_scd2`
* `wh_dim_company`, `wh_dim_company_alias`
* `wh_dim_role`, `wh_dim_sector`, `wh_dim_skill`
* `wh_dim_location`, `wh_dim_source`, `wh_dim_date`
* `wh_bridge_job_skill`
* `wh_fact_job_postings`, `wh_fact_job_lifecycle`
* `wh_fact_salary`, `wh_fact_pipeline_runs`

### `notebooks/test_init_notebooks.py`
Tests for Init layer notebooks:
* `init_validate_env`
* `init_create_schemas`
* `init_seed_metadata`
* `init_register_secrets`
* `init_superset_bootstrap`

### `notebooks/test_publish_notebooks.py`
Tests for Publish layer notebooks:
* `publish_manifest_write`
* `publish_csv_snapshot_export`
* `publish_supabase_upsert`
* `publish_load_order_check`

## Workflow Integration Tests

Test complete workflows end-to-end:

### `workflows/test_workflows_integration.py`
Comprehensive workflow tests:
* Configuration validation (JSON structure, tasks, dependencies)
* Dependency graph validation (no cycles, correct ordering)
* Workflow-specific tests (init, ingestion, silver, intermediate, warehouse, gold, publishing, recovery)
* End-to-end execution tests (marked as `@pytest.mark.integration`)

See [workflows/README.md](workflows/README.md) for detailed workflow test documentation.

## Test Configuration

### `conftest.py`

Provides reusable fixtures for all tests:

* **`spark`** — Session-scoped Spark session
* **`clean_spark`** — Function-scoped clean Spark (drops test databases)
* **`sample_bronze_jobs`** — Sample bronze job records
* **`sample_silver_jobs`** — Sample silver job records with normalized fields
* **`sample_dim_jobs`** — Sample dimension job records for SCD2 testing
* **`sample_sector_keywords`** — Sector keyword mappings
* **`record_hash_function`** — Helper function to compute record hashes
* **`workspace_client`** — Databricks workspace client

### `pytest.ini`

Test execution configuration:

* Test discovery patterns
* Markers for selective execution
* Console output formatting
* Logging configuration
* Coverage settings
* Timeout defaults

## Test Execution Patterns

### By Priority

```bash
# Highest risk only
pytest -m "cdc or identity"

# High risk
pytest -m "cdc or identity or sector or scd2"

# All unit tests
pytest tests/test_*.py
```

### By Category

```bash
# Unit tests (logic)
pytest tests/test_*.py

# Notebook integration tests
pytest tests/notebooks/

# Workflow integration tests
pytest tests/workflows/

# All integration tests
pytest -m integration
```

### By Type

```bash
# Unit tests (fast)
pytest -m unit

# Integration tests (require Spark)
pytest -m integration

# Slow tests (>1 second)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### By Module

```bash
# Single test file
pytest tests/test_cdc_hash_logic.py

# Single test class
pytest tests/test_cdc_hash_logic.py::TestCDCHashComputation

# Single test method
pytest tests/test_cdc_hash_logic.py::TestCDCHashComputation::test_hash_identical_records_match

# Single notebook layer
pytest tests/notebooks/test_bronze_notebooks.py

# Single workflow test
pytest tests/workflows/test_workflows_integration.py::TestRecoveryWorkflow
```

### Performance

```bash
# Parallel execution
pytest -n auto

# Show slowest tests
pytest --durations=10

# Stop on first failure
pytest -x
```

## Test Markers

Tests are tagged with markers for selective execution:

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.cdc` | CDC hash logic tests | `pytest -m cdc` |
| `@pytest.mark.identity` | Identity matching tests | `pytest -m identity` |
| `@pytest.mark.sector` | Sector assignment tests | `pytest -m sector` |
| `@pytest.mark.scd2` | SCD2 key generation tests | `pytest -m scd2` |
| `@pytest.mark.quarantine` | Quarantine routing tests | `pytest -m quarantine` |
| `@pytest.mark.manifest` | Export manifest tests | `pytest -m manifest` |
| `@pytest.mark.unit` | Fast unit tests | `pytest -m unit` |
| `@pytest.mark.integration` | Integration tests | `pytest -m integration` |
| `@pytest.mark.slow` | Tests >1 second | `pytest -m "not slow"` |

## Test Coverage

### Current Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| CDC Hash Logic | 95%+ | TBD |
| Identity Matching | 95%+ | TBD |
| Sector Assignment | 90%+ | TBD |
| SCD2 Key Generation | 90%+ | TBD |
| Quarantine Routing | 85%+ | TBD |
| Export Manifest | 85%+ | TBD |
| Notebooks (Integration) | 70%+ | TBD |
| Workflows (Integration) | 70%+ | TBD |

### Generate Coverage Report

```bash
# HTML report
pytest --cov=LMIP --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=LMIP --cov-report=term-missing

# XML report (for CI)
pytest --cov=LMIP --cov-report=xml
```

## Deployment as Databricks Jobs

Test workflows can be deployed as Databricks jobs for CI/CD:

```bash
# Deploy test workflows to dev environment
python deployment/deploy_test_workflows.py --env dev

# Dry run (preview without deploying)
python deployment/deploy_test_workflows.py --env dev --dry-run

# Deploy to prod
python deployment/deploy_test_workflows.py --env prod

# Use existing cluster
python deployment/deploy_test_workflows.py --env dev --cluster-id abc123
```

This creates three Databricks jobs:
1. **LMIP_Test_Unit_Tests_DEV** — Logic and unit tests
2. **LMIP_Test_Notebook_Integration_DEV** — Notebook integration tests
3. **LMIP_Test_Workflow_Integration_DEV** — Workflow integration tests

See [deployment/deploy_test_workflows.py](../deployment/deploy_test_workflows.py) for details.

## Continuous Integration

### GitHub Actions Workflow

Location: `.github/workflows/pytest-ci.yml`

**Triggers:**
* Push to `main`, `develop`, or `feature/*`
* Pull requests to `main` or `develop`
* Manual trigger

**Test Stages:**
1. Highest Risk Tests (CDC + Identity) — **MUST PASS**
2. High Risk Tests (Sector + SCD2)
3. Medium Risk Tests (Quarantine + Manifest)
4. Notebook Integration Tests
5. Workflow Integration Tests
6. All Tests (comprehensive coverage)

**Quality Gates:**
* ❌ FAIL if highest risk tests fail
* ⚠️ WARN if coverage < 70%
* ✅ PASS if all tests pass and coverage >= 70%

### CI Artifacts

* Test reports (HTML, JUnit XML)
* Coverage reports (HTML, XML)
* Test logs
* Retention: 30 days

## Writing New Tests

### Test Template

```python
"""
Test <Module Name>

Brief description of what this test module validates.

Priority: HIGH/MEDIUM/LOW RISK
"""

import pytest
from pyspark.sql import functions as F
from datetime import datetime

class Test<Functionality>:
    """Test <specific functionality>"""
    
    def test_<scenario>(self, spark):
        """Test <what this test validates>"""
        # ARRANGE: Set up test data
        data = [...]
        df = spark.createDataFrame(data, schema)
        
        # ACT: Execute logic
        result = df.transform(...)
        
        # ASSERT: Verify results
        assert result.count() == expected_count
```

### Adding Markers

```python
@pytest.mark.cdc
@pytest.mark.unit
def test_hash_computation(spark):
    pass
```

### Using Fixtures

```python
def test_with_fixture(spark, sample_bronze_jobs):
    # Use the fixture
    count = sample_bronze_jobs.count()
    assert count > 0
```

## Test Data

### Sample Data Guidelines

* **Keep it minimal** — only include fields relevant to test
* **Use realistic values** — representative of production data
* **Document edge cases** — explain unusual test data
* **Avoid hardcoded dates** — use relative dates when possible

### Example

```python
data = [
    ("job_001", "Acme Corp", "Python Developer", datetime(2026, 6, 1)),
    ("job_002", "TechCo", "Data Engineer", datetime(2026, 6, 2)),
]

df = spark.createDataFrame(
    data,
    ["job_id", "company", "title", "posted_at"]
)
```

## Debugging Tests

### Common Issues

**Spark not starting:**
```bash
# Check Java version
java -version

# Set JAVA_HOME
export JAVA_HOME=/path/to/java
```

**Import errors:**
```bash
# Add LMIP to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Tests hanging:**
```bash
# Add timeout
pytest --timeout=60

# Run with verbose output
pytest -v -s
```

### Debug Techniques

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Show debug logs
pytest --log-cli-level=DEBUG

# Run only failed tests
pytest --lf

# Use Python debugger
# Add in test: import pdb; pdb.set_trace()
```

## Directory Structure

```
tests/
├── README.md                          # This file
├── conftest.py                        # Shared fixtures and configuration
├── __init__.py                        # Package marker
│
├── test_cdc_hash_logic.py            # Priority 1: CDC hash logic
├── test_identity_matching.py         # Priority 2: Identity matching
├── test_sector_assignment.py         # Priority 3: Sector classification
├── test_scd2_key_generation.py       # Priority 4: SCD2 logic
├── test_quarantine_routing.py        # Priority 5: Quarantine management
├── test_export_bundle_manifest.py    # Priority 6: Export validation
│
├── notebooks/                         # Notebook integration tests
│   ├── test_bronze_notebooks.py
│   ├── test_silver_notebooks.py
│   ├── test_intermediate_notebooks.py
│   ├── test_warehouse_notebooks.py
│   ├── test_init_notebooks.py
│   └── test_publish_notebooks.py
│
├── workflows/                         # Workflow integration tests
│   ├── README.md                      # Workflow test documentation
│   └── test_workflows_integration.py  # Complete workflow tests
│
├── logs/                              # Test execution logs (gitignored)
└── reports/                           # Test reports (gitignored)
    ├── junit-*.xml                    # JUnit XML reports
    ├── report-*.html                  # HTML test reports
    └── coverage-*.xml                 # Coverage reports
```

## Quick Start

### Essential Commands

```bash
# Run all tests
pytest

# Run highest priority (CDC + Identity) - MUST PASS
pytest -m "cdc or identity"

# Run with coverage
pytest --cov=LMIP --cov-report=html

# Parallel execution
pytest -n auto

# Show slowest tests
pytest --durations=10
```

### Run by Layer

```bash
pytest tests/notebooks/test_bronze_notebooks.py
pytest tests/notebooks/test_silver_notebooks.py
pytest tests/notebooks/test_intermediate_notebooks.py
pytest tests/notebooks/test_warehouse_notebooks.py
```

### Common Options

```bash
pytest -v           # Verbose output
pytest -s           # Show print statements
pytest -x           # Stop on first failure
pytest --lf         # Run last failed only
pytest -m "not slow"  # Skip slow tests
```

## Implementation Summary

### Test Metrics

**Unit Tests (Logic Validation):**
* test_cdc_hash_logic.py — ~250 lines, 17 test methods
* test_identity_matching.py — ~300 lines, 18 test methods
* test_sector_assignment.py — ~200 lines, 17 test methods
* test_scd2_key_generation.py — ~250 lines, 20 test methods
* test_quarantine_routing.py — ~180 lines, 16 test methods
* test_export_bundle_manifest.py — ~150 lines, 26 test methods
* **Total:** ~1,330 lines, 114 test methods

**Notebook Integration Tests:**
* test_bronze_notebooks.py — 268 lines, 6 notebooks covered
* test_silver_notebooks.py — 277 lines, 9 notebooks covered
* test_intermediate_notebooks.py — 172 lines, 7 notebooks covered
* test_warehouse_notebooks.py — 206 lines, 14 notebooks covered
* test_init_notebooks.py — 115 lines, 5 notebooks covered
* test_publish_notebooks.py — 161 lines, 4 notebooks covered
* **Total:** ~1,199 lines, 45 notebooks covered

**Workflow Integration Tests:**
* test_workflows_integration.py — 8 workflow definitions

### Coverage Goals

| Module | Target Coverage |
|--------|-----------------|
| CDC Hash Logic | 95%+ |
| Identity Matching | 95%+ |
| Sector Assignment | 90%+ |
| SCD2 Key Generation | 90%+ |
| Quarantine Routing | 85%+ |
| Export Manifest | 85%+ |
| Notebooks | 70%+ |
| Workflows | 70%+ |

## Pre-Commit Checklist

- [ ] Run highest priority tests: `pytest -m "cdc or identity"`
- [ ] Run affected layer tests: `pytest tests/notebooks/test_<layer>_notebooks.py`
- [ ] Check coverage: `pytest --cov=LMIP --cov-report=term`
- [ ] Run workflow validation: `pytest tests/workflows/ -m "not slow"`
- [ ] All tests pass ✅

## Troubleshooting

### Test Discovery Issues

```bash
# List all tests
pytest --collect-only

# List tests matching pattern
pytest --collect-only -k "bronze"
```

### Spark Issues

```bash
# Check Java version (needs Java 11 or 17)
java -version

# Set JAVA_HOME
export JAVA_HOME=/path/to/java

# Clear Spark metastore
rm -rf metastore_db/ spark-warehouse/
```

### Import Errors

```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests Hanging

```bash
# Add timeout
pytest --timeout=60

# Show detailed output
pytest -vvv -s
```

### Getting Help

```bash
# Show pytest help
pytest --help

# Show markers
pytest --markers

# Show fixtures
pytest --fixtures
```

## CI/CD Quick Facts

* **GitHub Actions:** Runs on push/PR to main, develop, feature/*
* **Test Stages:** Highest → High → Medium → Notebook → Workflow → Full
* **Quality Gates:** Highest risk MUST PASS, coverage >= 70%
* **Artifacts:** Test reports, coverage, logs (30-day retention)
* **Databricks Jobs:** 3 test workflows (unit, notebook, workflow)
* **Python Versions:** 3.10 and 3.11

## Resources

* [Workflow Test Documentation](workflows/README.md)
* [Rollback Mechanism](../docs/rollback-mechanism.md)
* [pytest Documentation](https://docs.pytest.org/)
* [PySpark Testing Guide](https://spark.apache.org/docs/latest/api/python/user_guide/testing.html)

> **Note:** For complete testing strategy and contribution guidelines, see this document. The previous docs/testing-guide.md file has been consolidated into this README.

## Contact

For questions about the test suite:

* Create an issue in the GitHub repository
* Reach out to the data engineering team
* Check the `#data-engineering` Slack channel

---

**Last Updated:** 2026-06-14  
**Owner:** Data Engineering Team
