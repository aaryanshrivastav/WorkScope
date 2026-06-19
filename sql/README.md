# LMIP SQL Artifacts

## Overview

This directory contains all SQL artifacts generated from LMIP contract definitions. The artifacts implement the defined data warehouse architecture across five layers: Bronze, Silver, Semantic, Warehouse, and Gold.

## Directory Structure

```
LMIP/sql/
├── README.md                 # This file
├── bootstrap/                # Schema initialization scripts
│   └── 00_create_schemas.sql
├── ddl/                      # CREATE TABLE statements (56 files)
│   ├── audit_*.sql           # Audit schema DDL (5 files)
│   ├── bronze_*.sql          # Bronze layer DDL (3 files)
│   ├── gold_*.sql            # Gold dimensional model DDL (14 files)
│   ├── intermediate_*.sql    # Intermediate layer DDL (6 files)
│   ├── metadata_*.sql        # Metadata schema DDL (7 files)
│   ├── publish_*.sql         # Publish schema DDL (2 files)
│   ├── quarantine_*.sql      # Quarantine schema DDL (2 files)
│   ├── reporting_*.sql       # Reporting marts DDL (11 files)
│   └── silver_*.sql          # Silver layer DDL (6 files)
├── views/                    # CREATE VIEW statements (11 files)
│   └── view_gold_*.sql       # Gold layer analytical views
└── validations/              # Data quality validation queries (13 files)
    └── See validations/README.md for dual-track numbering system
```

## Layer Architecture

### Metadata Layer
**Purpose**: System configuration, pipeline control, and governed taxonomy

**Tables**:
* `metadata_pipeline_run_control` - Pipeline execution orchestration
* `metadata_source_config` - Source system configuration
* `metadata_staging_to_current_batches` - Batch tracking
* `metadata_taxonomy_sectors` - Governed sector taxonomy (19 sectors)
* `metadata_taxonomy_role_families` - Role family groupings (13 families)
* `metadata_taxonomy_role_canonical` - Canonical role definitions (22 roles)
* `metadata_taxonomy_skill_catalog` - Master skill catalog (26 skills)

**Characteristics**:
* Seeded from CSV files during bootstrap (taxonomy tables)
* Idempotent MERGE operations for taxonomy data
* Referenced by intermediate and gold layers
* Audit timestamps (created_at, updated_at)

> **⚠️ Note**: Formal schema contracts for the four taxonomy tables (taxonomy_sectors, taxonomy_role_families, taxonomy_role_canonical, taxonomy_skill_catalog) are pending documentation. Current implementations are based on CSV file structures and DDL definitions. See [docs/changelog/2026-06-17-taxonomy-tables-migration.md](../docs/changelog/2026-06-17-taxonomy-tables-migration.md) for interim schema documentation and seeding logic.

### Bronze Layer
**Purpose**: Immutable raw data from source systems

**Tables**:
* `bronze_job_snapshot` - Job execution snapshots
* `bronze_api_response_log` - API request/response audit log
* `dedupe_tracking` - Duplicate occurrence tracking

**Characteristics**:
* Append-only, no updates or deletes
* Partitioned by ingestion timestamp
* Includes full audit trail

### Silver Layer
**Purpose**: Cleaned, standardized, and deduplicated data

**Tables**:
* `silver_jobs_staging` - Temporary staging for batch processing
* `silver_jobs_current` - Current state of all job postings (CDC applied)
* `silver_job_changes` - Change data capture log
* `silver_job_identity_map` - Cross-source job linking
* `silver_skill_mapping` - Extracted skills with confidence scores

**Characteristics**:
* Implements Change Data Capture (CDC)
* Business key deduplication
* Soft delete capability

### Semantic Layer
**Purpose**: Business logic and canonical name mappings

**Tables**:
* `sem_company_canonical` - Company name standardization
* `sem_company_map` - Company-to-canonical mappings
* `sem_job_role_map` - Job title to standard role mapping
* `sem_job_skill_evidence` - Skill extraction evidence
* `sem_sector_map` - Sector classification
* `sem_skill_catalog` - Master skill taxonomy

**Characteristics**:
* Domain-driven design
* Master data management
* Fuzzy matching and confidence scoring

### Warehouse Layer
**Purpose**: Dimensional model for analytical queries

**Dimensions**:
* `dim_date` - Calendar dimension
* `dim_company` - Company dimension
* `dim_company_alias` - Company name variations
* `dim_job` - Job dimension (SCD Type 2)
* `dim_location` - Geographic dimension
* `dim_role` - Standardized job roles
* `dim_sector` - Industry sectors
* `dim_skill` - Skill taxonomy
* `dim_source` - Data source systems

**Facts**:
* `fact_job_postings` - Core fact table for job events
* `fact_job_lifecycle` - Job lifecycle events
* `fact_salary` - Salary information
* `fact_pipeline_runs` - Pipeline execution metrics

**Bridge Tables**:
* `bridge_job_skill` - Many-to-many job-skill relationships

**Characteristics**:
* Star schema design
* SCD Type 2 for slowly changing dimensions
* Conformed dimensions
* Surrogate keys

### Gold Layer
**Purpose**: Aggregated analytical marts and business views

**Marts**:
* `gold_hiring_trends` - Time-series hiring analysis
* `gold_location_trends` - Geographic hiring patterns
* `gold_salary_trends` - Compensation analysis
* `gold_skill_demand` - Skill demand trending
* `gold_sector_overview` - Industry sector metrics
* `gold_company_hiring` - Company-level hiring activity
* `gold_pipeline_health` - Data pipeline monitoring
* `gold_hospitality_hiring` - Hospitality sector focus
* `gold_hospitality_skills` - Hospitality skill trends
* `gold_hospitality_companies` - Hospitality employers
* `role_review_queue` - Role classification review

**Characteristics**:
* Implemented as views over warehouse layer
* Pre-aggregated metrics
* Business-friendly naming
* Optimized for BI tools

## Usage Instructions

### 1. Bootstrap (Initial Setup)

Run the bootstrap script to create all required schemas:

```sql
-- Execute from: LMIP/sql/bootstrap/00_create_schemas.sql
```

This creates six schemas:
* `workspace.bronze`
* `workspace.silver`
* `workspace.semantic`
* `workspace.warehouse`
* `workspace.gold`
* `workspace.audit`

### 2. Create Tables (DDL Execution)

Execute DDL files in layer order:

```bash
# 1. Metadata schema (7 files)
LMIP/sql/ddl/metadata_*.sql

# 2. Bronze layer (3 files)
LMIP/sql/ddl/bronze_*.sql

# 3. Silver layer (6 files)
LMIP/sql/ddl/silver_*.sql

# 4. Intermediate layer (6 files)
LMIP/sql/ddl/intermediate_*.sql

# 5. Gold dimensional model (14 files)
LMIP/sql/ddl/gold_*.sql

# 6. Reporting marts (11 files)
LMIP/sql/ddl/reporting_*.sql

# 7. Audit schema (5 files)
LMIP/sql/ddl/audit_*.sql

# 8. Publish schema (2 files)
LMIP/sql/ddl/publish_*.sql

# 9. Quarantine schema (2 files)
LMIP/sql/ddl/quarantine_*.sql
```

**Important**: Execute in order due to referential dependencies.

### 3. Create Views

After Gold dimensional model tables are populated, create analytical views:

```bash
# Execute all view definitions
LMIP/sql/views/view_gold_*.sql
```

### 4. Run Validations

Execute validation queries to verify data quality:

```sql
-- Row count validation
LMIP/sql/validations/01_row_count_validation.sql

-- Null constraint validation
LMIP/sql/validations/02_null_validation.sql

-- Foreign key integrity
LMIP/sql/validations/03_referential_integrity.sql

-- Duplicate detection
LMIP/sql/validations/04_duplicate_detection.sql

-- Gold mart business logic
LMIP/sql/validations/05_gold_mart_validation.sql
```

## Validation Descriptions

For comprehensive validation documentation including the dual-track numbering system (legacy 01-05 and enhanced 01-08 tracks), see [validations/README.md](./validations/README.md).

## Key Features

### All DDL Files Include:
* Table name and layer
* Business description
* Column definitions with comments
* Primary key constraints
* Partitioning strategy
* Delta Lake optimizations:
  * Change Data Feed enabled
  * Auto-optimize write
  * Auto-compact
* Lineage information (inputs and outputs)

### All VIEW Files Include:
* View name and purpose
* Source table dependencies
* Expected output description
* Placeholder SQL (to be implemented based on business logic)

### All Validation Files Include:
* Validation purpose
* Expected output format
* Dependencies list
* Execution timestamp for audit

## Data Quality Standards

All artifacts enforce the following standards:

1. **Immutability** (Bronze): No updates or deletes
2. **Idempotency**: All scripts can be re-run safely
3. **Audit Trail**: Every table tracks created_at and updated_at
4. **Soft Deletes**: No physical deletes, soft_delete_flag used
5. **Partitioning**: Time-based partitioning for query performance
6. **Change Data Feed**: Enabled for incremental processing
7. **Quality Rules**: Defined in contracts and enforced via validations

## Maintenance

### Regenerating Artifacts

If contracts are updated:

1. Review changed contracts in `LMIP/contracts/`
2. Regenerate DDL using contract generator
3. Update view definitions if aggregation logic changes
4. Update validations if new constraints are added
5. Document changes in this README

### Naming Conventions

* **Bronze**: `bronze_<table_name>`
* **Silver**: `silver_<table_name>`
* **Semantic**: `sem_<table_name>`
* **Warehouse Dimensions**: `dim_<entity>`
* **Warehouse Facts**: `fact_<event>`
* **Warehouse Bridges**: `bridge_<entity1>_<entity2>`
* **Gold Marts**: `gold_<business_area>`
* **Validation Scripts**: `<nn>_<validation_type>.sql`

## Troubleshooting

### Common Issues

**Issue**: Table creation fails with "schema not found"
**Solution**: Run bootstrap script first

**Issue**: Referential integrity violations
**Solution**: Load dimensions before facts, execute DDL in layer order

**Issue**: View creation fails
**Solution**: Ensure warehouse tables exist and contain data

**Issue**: Validation returns unexpected results
**Solution**: Check that ETL pipelines have completed successfully

## Contact & Support

For questions about these SQL artifacts:
* Review contract definitions in `LMIP/contracts/`
* Check gap analysis in `LMIP/contracts/contracts_gap_analysis.md`
* Consult LMIP project documentation in `LMIP/docs/`

## Version Information

* **Contract Version**: 1.0
* **Generated Date**: 2026-06-07
* **Total DDL Files**: 56
* **Total Views**: 11
* **Total Validations**: 13 (dual-track system)
* **Architecture**: Metadata → Bronze → Silver → Intermediate → Gold → Reporting (+ Audit, Publish, Quarantine)