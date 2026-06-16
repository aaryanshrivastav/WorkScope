# LMIP Deployment Architecture

Production-grade automated deployment tools for the Labor Market Intelligence Platform (LMIP) on Databricks.

---

## 🎯 Overview

This directory provides a **5-layer deployment architecture** with clear separation between:
- **One-time infrastructure provisioning** (bootstrap)
- **Repeatable code deployment** (workspace + jobs)
- **Independent verification** (validation)
- **Safe teardown** (environment reset)

### Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 0: bootstrap.py (ONE-TIME)                            │
│  Create schemas, tables, seed metadata                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: deploy_workspace.py (REPEATABLE)                   │
│  Upload notebooks, SQL files, helper scripts                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 2: deploy_jobs.py (REPEATABLE)                        │
│  Create/update Databricks Jobs from workflow definitions     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: validate_deployment.py (VERIFICATION)              │
│  Verify schemas, tables, notebooks, jobs deployed correctly  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 4: reset_environment.py (TEARDOWN)                    │
│  Safe cleanup - full/partial schema drops                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Orchestrator: deploy_all.py                                 │
│  One-command deployment of all layers                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
deployment/
├── README.md                    # This file
├── .env.example                 # Environment template
# (See ../requirements.txt for Python dependencies)
│
├── config.py                    # Configuration management
│
├── bootstrap.py                 # Layer 0: Infrastructure (ONE-TIME)
├── deploy_workspace.py          # Layer 1: Workspace assets (REPEATABLE)
├── deploy_jobs.py               # Layer 2: Jobs (REPEATABLE)
├── validate_deployment.py       # Layer 3: Validation (VERIFICATION)
├── reset_environment.py         # Layer 4: Teardown (CLEANUP)
└── deploy_all.py                # Orchestrator
```

---

## 🚀 Quick Start

### First-Time Deployment

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your Databricks credentials

# 2. Install dependencies
pip install -r ../requirements.txt

# 3. Full deployment (bootstrap + workspace + jobs + validation)
python deploy_all.py
```

### Subsequent Deployments (Code Updates)

```bash
# Skip bootstrap, update existing resources
python deploy_all.py --skip-bootstrap --update
```

---

## 📋 Deployment Scripts

### Layer 0: `bootstrap.py` (Infrastructure - ONE-TIME)

**Purpose**: Create Unity Catalog infrastructure

**Responsibilities**:
- Create 9 UC schemas (metadata, bronze, silver, intermediate, gold, reporting, audit, publish, quarantine)
- Execute 40+ DDL files to create tables (dependency-aware)
- Seed baseline metadata from CSV files (canonical roles, skills, sectors)

**Idempotent**: ✅ Safe to rerun (uses `CREATE IF NOT EXISTS` and `MERGE`)

**Usage**:
```bash
# Bootstrap with default catalog
python bootstrap.py

# Bootstrap with custom catalog
python bootstrap.py --catalog my_catalog

# Dry run (preview changes)
python bootstrap.py --dry-run
```

**When to run**:
- Initial project setup
- After full environment reset
- When adding new schemas/tables

**Output**:
- Creates 9 schemas
- Creates 40+ tables across all layers
- Seeds ~200 metadata records

---

### Layer 1: `deploy_workspace.py` (Workspace Assets - REPEATABLE)

**Purpose**: Deploy code artifacts to Databricks workspace

**Responsibilities**:
- Upload notebooks from `notebooks/` directory
- Upload helper scripts
- Upload SQL files

**Idempotent**: ✅ Safe to rerun (overwrites with `--update`)

**Usage**:
```bash
# Deploy notebooks
python deploy_workspace.py

# Update existing notebooks
python deploy_workspace.py --update

# Dry run
python deploy_workspace.py --dry-run
```

**When to run**:
- Every time notebook code changes
- When adding new notebooks
- After pulling from Git

---

### Layer 2: `deploy_jobs.py` (Databricks Jobs - REPEATABLE)

**Purpose**: Configure Databricks Jobs for workflow orchestration

**Responsibilities**:
- Read workflow JSON definitions from `workflows/`
- Create/update Databricks Jobs
- Resolve notebook paths dynamically
- Configure schedules, clusters, notifications

**Idempotent**: ✅ Safe to rerun (updates existing jobs by name)

**Usage**:
```bash
# Deploy all workflow definitions
python deploy_jobs.py

# Deploy specific workflow
python deploy_jobs.py --workflow init.json

# Update existing jobs
python deploy_jobs.py --update

# Dry run
python deploy_jobs.py --dry-run
```

**When to run**:
- When job definitions change
- When adding new workflows
- When updating schedules/notifications

---

### Layer 3: `validate_deployment.py` (Validation - VERIFICATION)

**Purpose**: Independent verification layer

**Responsibilities**:
- Verify all 9 schemas exist
- Verify critical tables exist and have data
- Verify metadata tables seeded (row counts > 0)
- Verify notebooks deployed to correct paths
- Verify jobs exist and are configured correctly

**Read-only**: ✅ No modifications, pure verification

**Usage**:
```bash
# Validate deployment
python validate_deployment.py

# Verbose output
python validate_deployment.py --verbose
```

**When to run**:
- After any deployment
- Before starting jobs
- For troubleshooting
- In CI/CD pipelines

**Output**:
- Validation summary table
- Pass/fail for each component
- Overall success rate

---

### Layer 4: `reset_environment.py` (Teardown - CLEANUP)

**Purpose**: Safe environment cleanup for testing/reset

**Responsibilities**:
- Drop schemas in reverse dependency order
- Support full reset (all schemas)
- Support partial reset (specific layers)
- Support tables-only reset (preserve schemas)
- **Never drops the Unity Catalog itself**

**Safety Features**:
- ⚠️ Confirmation prompts (can be skipped with `--confirm`)
- ✅ Dry-run support
- ✅ Reverse dependency order
- ❌ Never drops catalog

**Usage**:
```bash
# Full reset (requires typing "DELETE ALL")
python reset_environment.py --full

# Quick full reset (skip confirmation)
python reset_environment.py --full --confirm

# Drop specific layer
python reset_environment.py --layer bronze

# Drop multiple layers
python reset_environment.py --layer bronze --layer silver

# Drop medallion (bronze + silver + gold)
python reset_environment.py --layer medallion

# Drop tables only (keep schemas)
python reset_environment.py --tables-only

# Dry run
python reset_environment.py --full --dry-run
```

**Layer Aliases**:
- `medallion`: bronze, silver, gold
- `analytics`: reporting, publish
- `all`: All LMIP schemas

**When to run**:
- Testing/development reset
- Before major schema changes
- Disaster recovery scenarios

---

### Orchestrator: `deploy_all.py`

**Purpose**: One-command full deployment

**Execution Order**:
1. **Bootstrap** (if not skipped) - Create infrastructure
2. **Deploy Workspace** - Upload notebooks
3. **Deploy Jobs** - Create/update jobs
4. **Validate** (if not skipped) - Verify deployment

**Usage**:
```bash
# Full deployment
python deploy_all.py

# Deploy with updates
python deploy_all.py --update

# Skip bootstrap (schemas exist)
python deploy_all.py --skip-bootstrap

# Skip validation
python deploy_all.py --skip-validation

# Dry run
python deploy_all.py --dry-run

# Force deploy even if errors
python deploy_all.py --force
```

---

## 🔄 Common Workflows

### First-Time Setup (Day 1)
```bash
python deploy_all.py
```

### Iterative Development (Day 2+)
```bash
# Option 1: Update everything
python deploy_all.py --skip-bootstrap --update

# Option 2: Granular updates
python deploy_workspace.py --update
python deploy_jobs.py --update
python validate_deployment.py
```

### Full Reset + Redeploy
```bash
python reset_environment.py --full --confirm
python deploy_all.py
```

### Partial Reset (Bronze Layer Only)
```bash
python reset_environment.py --layer bronze
python bootstrap.py  # Recreate bronze schema and tables
python deploy_workspace.py --update
```

### CI/CD Deployment
```bash
# In CI pipeline (no bootstrap, update existing)
python deploy_all.py --skip-bootstrap --update --skip-validation
python validate_deployment.py  # Separate validation step
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Databricks Connection
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_WAREHOUSE_ID=abc123def456  # Optional, auto-selects if not provided

# Workspace Paths
WORKSPACE_ROOT=/Users/your.email@company.com/LMIP

# Unity Catalog
CATALOG=workspace
BRONZE_SCHEMA=bronze
SILVER_SCHEMA=silver
INTERMEDIATE_SCHEMA=intermediate
GOLD_SCHEMA=gold
REPORTING_SCHEMA=reporting
METADATA_SCHEMA=metadata
AUDIT_SCHEMA=audit
QUARANTINE_SCHEMA=quarantine
PUBLISH_SCHEMA=publish

# Notifications
NOTIFICATION_EMAIL=your.email@company.com

# Compute
USE_SERVERLESS=true
```

### Environment-Specific Deployment

```bash
# Development
cp .env.example .env.dev
# Edit .env.dev with dev settings
export $(cat .env.dev | xargs)
python deploy_all.py --skip-bootstrap --update

# Production
cp .env.example .env.prod
# Edit .env.prod with prod settings
export $(cat .env.prod | xargs)
python deploy_all.py
```

---

## 🔐 Prerequisites

### 1. Python Dependencies

```bash
pip install -r ../requirements.txt
```

Key packages:
- `databricks-sdk>=0.20.0` - Databricks SDK
- `rich>=13.0.0` - Console formatting
- `python-dotenv>=1.0.0` - Environment management

### 2. Databricks Authentication

**Option A: Environment Variables**
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

**Option B: Databricks CLI**
```bash
databricks configure --token
```

**Option C: .env File** (Recommended)
```bash
cp .env.example .env
# Edit .env
```

### 3. Required Permissions

Your Databricks user/service principal needs:
- ✅ **Unity Catalog**: `USE CATALOG` + `CREATE SCHEMA` on target catalog
- ✅ **Workspace**: `CAN_MANAGE` on workspace folders
- ✅ **Jobs**: `CAN_MANAGE_RUN` or `CAN_MANAGE`
- ✅ **SQL Warehouse**: Access to at least one warehouse

---

## 🆓 Databricks Free Edition Compatibility

**What WORKS**:
- ✅ Unity Catalog (3-level namespace)
- ✅ Serverless SQL warehouses
- ✅ Databricks SDK
- ✅ Workspace notebooks/files
- ✅ Statement Execution API
- ✅ Jobs (limited concurrency)

**What DOESN'T work**:
- ❌ Clusters (all-purpose compute)
- ❌ Repos (Git integration) - Use `deploy_workspace.py` instead
- ❌ MLflow (experiment tracking)
- ❌ Delta Live Tables / Lakeflow Pipelines
- ❌ Advanced job features

**Recommendation**: Always use `USE_SERVERLESS=true` in `.env`

---

## 🚀 Production Deployment Best Practices

### 1. Use Service Principals

```bash
# .env.prod
DATABRICKS_CLIENT_ID=<service-principal-app-id>
DATABRICKS_CLIENT_SECRET=<secret>
```

### 2. Environment-Specific Catalogs

```bash
# dev.env
CATALOG=lmip_dev

# prod.env
CATALOG=lmip_prod
```

### 3. Deployment Gates

```python
# In CI/CD: Require approval for production
if CATALOG == "lmip_prod":
    require_manual_approval()
```

### 4. Immutable Infrastructure

```bash
# Production: Always bootstrap fresh
python reset_environment.py --full --confirm
python deploy_all.py
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy LMIP
on:
  push:
    branches: [main]

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Deploy to Dev
        env:
          DATABRICKS_HOST: ${{ secrets.DEV_DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DEV_DATABRICKS_TOKEN }}
          CATALOG: lmip_dev
        run: |
          python deployment/deploy_all.py --skip-bootstrap --update
      
      - name: Validate
        run: python deployment/validate_deployment.py
```

---

## 🐛 Troubleshooting

### "No SQL warehouses found"
**Solution**: Set `DATABRICKS_WAREHOUSE_ID` in `.env` or create a SQL warehouse

### "DDL directory not found"
**Solution**: Run from project root or use `--project-root`
```bash
cd LMIP
python deployment/bootstrap.py
```

### "Permission denied"
**Solution**: Verify your token has required permissions:
- `CREATE SCHEMA` on catalog
- `CAN_MANAGE` on workspace
- SQL warehouse access

### "Schema already exists"
**Solution**: This is normal! Scripts are idempotent. Use `--skip-bootstrap` for subsequent deploys:
```bash
python deploy_all.py --skip-bootstrap --update
```

### Validation Failures
```bash
# Run standalone validation
python deployment/validate_deployment.py --verbose

# Check specific components
python -c "from config import get_config; config = get_config(); print(config.__dict__)"
```

---

## 📊 Deployment Metrics

After successful deployment, you'll have:
- ✅ **9 Unity Catalog schemas** (metadata, bronze, silver, intermediate, gold, reporting, audit, publish, quarantine)
- ✅ **40+ tables** across all layers
- ✅ **~200 metadata records** (canonical roles, skills, sectors)
- ✅ **Notebooks deployed** to workspace
- ✅ **Databricks Jobs created** for orchestration
- ✅ **100% validation pass rate**

---

## 📚 Additional Documentation

- **Architecture**: `LMIP/docs/Architecture.md`
- **Data Model**: `LMIP/docs/Data_Model.md`
- **Pipeline Flow**: `LMIP/docs/Pipeline_Flow.md`
- **Bootstrap Details**: `deployment/bootstrap.py` (inline docs)
- **Reset Safety**: `deployment/reset_environment.py` (inline docs)

---

## 🆘 Support

**Issues**: Review error logs in each script
**Validation**: `python deployment/validate_deployment.py`
**Reset**: `python deployment/reset_environment.py --help`
**Full Docs**: `LMIP/README.md`

---

**Last Updated**: 2025-01-02
**Architecture Version**: 2.0 (5-Layer Model)
**Deployment Owner**: LMIP Platform Engineering Team
