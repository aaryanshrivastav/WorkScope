# LMIP Data Model Documentation

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: Data engineers, analysts, BI developers

---

## Overview

The LMIP data model implements a **multi-layered medallion architecture** with intermediate enrichment and dimensional modeling. All tables reside in the `workspace` Unity Catalog.

**Architecture Layers**:
1. Bronze: Raw API snapshots
2. Silver: Cleansed and standardized data
3. Intermediate: Enriched canonical entities
4. Gold: Star schema dimensional model
5. Reporting: Pre-aggregated BI marts
6. Publish: Export manifests and consumer tracking

---

## Key Tables by Layer

### Metadata Layer
* `metadata.metadata_pipeline_run_control` - Pipeline execution orchestration
* `metadata.metadata_source_config` - Data source configurations
* `metadata.metadata_staging_to_current_batches` - Batch tracking
* `metadata.taxonomy_sectors` - Governed sector taxonomy (19 sectors)
* `metadata.taxonomy_role_families` - Role family groupings (13 families)
* `metadata.taxonomy_role_canonical` - Canonical role definitions (22 roles)
* `metadata.taxonomy_skill_catalog` - Master skill catalog (26 skills)

> **Schema Contract Status**: All 56 schema contracts across 9 schemas are complete and active in `contracts/<layer>/`.

### Bronze Layer
* `bronze.bronze_job_snapshot` - Raw API responses (immutable)
* `bronze.bronze_api_response_log` - API telemetry

### Silver Layer
* `silver.silver_jobs_current` - Current job postings (single source of truth)
* `silver.silver_job_changes` - Complete audit trail (CDC log)
* `silver.silver_skill_mapping` - Extracted skills

### Intermediate Layer
* `intermediate.inter_job_role_map` - Title → canonical role mapping
* `intermediate.inter_company_canonical` - Company master
* `intermediate.inter_skill_catalog` - Master skill taxonomy

### Gold Layer (Kimball Star Schema)
* **Dimensions (9)**: dim_date, dim_source, dim_sector, dim_skill, dim_role, dim_location, dim_company, dim_company_alias, dim_job
* **Facts (4)**: fact_job_postings, fact_job_lifecycle, fact_salary, fact_pipeline_runs
* **Bridges (1)**: bridge_job_skill

### Reporting Layer (Analytical BI Marts)
* `reporting.reporting_salary_trends` - Salary benchmarks with percentiles
* `reporting.reporting_skill_demand` - Skill trending and co-occurrence
* `reporting.reporting_hiring_trends` - Job posting velocity
* `reporting.reporting_company_hiring` - Company-specific hiring activity
* `reporting.reporting_location_trends` - Geographic patterns
* `reporting.reporting_sector_overview` - Sector KPIs
* `reporting.reporting_company_activity` - Company activity metrics
* `reporting.reporting_pipeline_health` - Pipeline telemetry & DQ health
* `reporting.role_review_queue` - Taxonomy review queue

For detailed schema definitions, column descriptions, and data contracts, refer to:
* Contract files: `/LMIP/contracts/<layer>/<table>.yaml`
* Layer README files: `/LMIP/notebooks/<layer>/README_<LAYER>.md`