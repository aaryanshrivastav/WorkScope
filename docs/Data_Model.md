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
5. Gold: Pre-aggregated BI marts

---

## Key Tables by Layer

### Bronze Layer
* `bronze.bronze_job_snapshot` - Raw API responses (immutable)
* `bronze.bronze_api_response_log` - API telemetry

### Silver Layer
* `silver.silver_jobs_current` - Current job postings (single source of truth)
* `silver.silver_job_changes` - Complete audit trail (CDC log)
* `silver.silver_skill_mapping` - Extracted skills

### Intermediate Layer
* `intermediate.sem_job_role_map` - Title → canonical role mapping
* `intermediate.sem_company_canonical` - Company master
* `intermediate.sem_skill_catalog` - Master skill taxonomy

### Gold Layer
* **Dimensions (10)**: dim_date, dim_source, dim_sector, dim_skill, dim_role, dim_location, dim_company, dim_company_alias, dim_job_scd2
* **Facts (4)**: fact_job_postings, fact_job_lifecycle, fact_salary, fact_pipeline_runs
* **Bridges (1)**: bridge_job_skill

### Gold Layer
* `gold.gold_salary_trends` - Salary benchmarks with percentiles
* `gold.gold_skill_demand` - Skill trending and co-occurrence
* `gold.gold_hiring_trends` - Job posting velocity
* `gold.gold_company_hiring` - Company-specific hiring activity
* `gold.gold_location_trends` - Geographic patterns
* `gold.gold_sector_overview` - Sector KPIs

For detailed schema definitions, column descriptions, and data contracts, refer to:
* Contract files: `/LMIP/contracts/<layer>/<table>.yaml`
* Layer README files: `/LMIP/notebooks/<layer>/README_<LAYER>.md`