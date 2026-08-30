# LMIP Developer Guide & Local Setup

A concise single-page guide for building, running, and maintaining the Labor Market Intelligence Platform (LMIP).

---

## Prerequisites

- **Python**: 3.10+ (System Python or virtual environment)
- **Java**: JDK 11 or 17 (Required for PySpark local unit tests)
- **Databricks CLI / SDK**: Required for workspace deployment

---

## Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd WorkScope

# 2. Install dependencies
pip install -r requirements.txt

# 3. Environment configuration
cp deployment/.env.example .env
# Edit .env with your DATABRICKS_HOST and DATABRICKS_TOKEN
```

---

## Essential Commands

### 1. Local Testing & Quality Checks
```bash
# Run workflow integration tests
python -m pytest tests/workflows/test_workflows_integration.py

# Run core deployment unit tests
python -m pytest tests/test_deployment_core.py

# Run CDC and identity matching unit tests
python -m pytest tests/test_cdc_hash_logic.py tests/test_identity_matching.py
```

### 2. Infrastructure Bootstrap (Dry-Run & Execution)
```bash
# Dry-run infrastructure provisioning (preview DDLs and taxonomy seed loading)
python deployment/bootstrap.py --dry-run

# Provision infrastructure live on Databricks Unity Catalog
python deployment/bootstrap.py --catalog workspace
```

### 3. Workflow & Job Deployment
```bash
# Deploy Databricks workflows and jobs
python deployment/deploy_jobs.py

# Validate deployment status
python deployment/validate_deployment.py
```

---

## Maintenance Conventions

- **Branching**: Develop directly on `main` or short-lived feature branches (`feat/feature-name`).
- **Code Style**: Follow standard PEP 8 conventions and type hints.
- **DDL & Schema Contracts**: Any new DDL file added to `sql/ddl/<layer>_<table_name>.sql` requires a corresponding YAML contract in `contracts/<layer>/<table_name>.yaml`.
