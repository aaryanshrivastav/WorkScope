# Warehouse Layer - Dimensional Modeling

## Overview

This directory contains notebooks for building and maintaining the **enterprise data warehouse** dimensional model. The warehouse layer implements **Kimball-style dimensional modeling** with conformed dimensions, slowly changing dimensions (SCD Type 2), and transactional fact tables.

**Purpose**: Provide a stable, historized, analysis-ready data model optimized for:
* Business intelligence and reporting
* Trend analysis and time-series comparisons
* Cross-source job market analytics
* Operational monitoring and data quality tracking

**Target Schema**: `workspace.warehouse`

---

## Dimensional Model Architecture

### 📐 Star Schema Design

```
                    ┌─────────────────┐
                    │   dim_date      │
                    └────────┬────────┘
                             │
    ┌────────────┐          │          ┌────────────┐
    │ dim_source │◄─────────┼─────────►│ dim_role   │
    └────────────┘          │          └────────────┘
                             │
    ┌────────────┐    ┌─────▼──────┐    ┌────────────┐
    │dim_company │◄───│ FACT TABLES│───►│dim_location│
    └────────────┘    └─────┬──────┘    └────────────┘
                             │
    ┌────────────┐          │          ┌────────────┐
    │ dim_sector │◄─────────┼─────────►│ dim_skill  │
    └────────────┘          │          └────────────┘
                             │
                    ┌────────▼────────┐
                    │dim_job (SCD2)   │
                    └─────────────────┘
```

### 🔑 Dimensions (Conformed)

| Dimension | Type | Purpose | Source |
|-----------|------|---------|--------|
| **dim_date** | Type 1 | Calendar attributes, fiscal periods | Generated |
| **dim_source** | Type 1 | Data source systems | silver.silver_jobs_current |
| **dim_company** | Type 1 | Canonical company entities | semantic.inter_company_canonical |
| **dim_company_alias** | Type 1 | Company name variations | semantic.inter_company_canonical |
| **dim_location** | Type 1 | Geographic hierarchy | silver.silver_jobs_current |
| **dim_sector** | Type 1 | Industry sectors | semantic.inter_sector_map |
| **dim_skill** | Type 1 | Skills catalog | semantic.inter_skill_catalog |
| **dim_role** | Type 1 | Canonical job roles | semantic.inter_job_role_map |
| **dim_job** | **Type 2** | Job postings with history | silver.silver_jobs_current |

### 📊 Fact Tables (Transactional)

| Fact Table | Grain | Purpose |
|------------|-------|----------|
| **fact_job_postings** | One row per job posting event | Core transactional fact |
| **fact_job_lifecycle** | One row per job state change | Lifecycle transitions |
| **fact_salary** | One row per job with salary | Salary analytics |
| **fact_pipeline_runs** | One row per pipeline execution | ETL operational metrics |

### 🔗 Bridge Tables

| Bridge Table | Purpose |
|--------------|----------|
| **bridge_job_skill** | Many-to-many job-to-skill relationships with confidence scores |

---

## Notebook Execution Order

### Phase 1: Conformed Dimensions (No Dependencies)

Run these notebooks in **any order** (they have no inter-dependencies):

```bash
1. wh_dim_date          # Generate calendar dimension
2. wh_dim_source        # Load source systems
3. wh_dim_sector        # Load industry sectors
4. wh_dim_skill         # Load skills catalog
5. wh_dim_role          # Load canonical job roles
6. wh_dim_location      # Load geographic locations
```

### Phase 2: Company Dimensions (Sequential)

Run these notebooks **in order** (company_alias depends on company):

```bash
7. wh_dim_company       # Load canonical companies (requires dim_sector)
8. wh_dim_company_alias # Load company name variations (requires dim_company)
```

### Phase 3: Job Dimension (SCD2)

**Critical**: Must run after all Phase 1 & 2 dimensions are loaded:

```bash
9. wh_dim_job_scd2      # Load job dimension with SCD2 logic
                        # Requires: dim_company, dim_location, dim_sector, dim_role
```

### Phase 4: Bridge Tables

Run after job dimension is loaded:

```bash
10. wh_bridge_job_skill # Load job-skill bridge (requires dim_job, dim_skill)
```

### Phase 5: Fact Tables

Run after all dimensions and bridges are loaded. These can run **in parallel**:

```bash
11. wh_fact_job_postings   # Core transactional facts
12. wh_fact_job_lifecycle  # Lifecycle events
13. wh_fact_salary         # Salary facts
14. wh_fact_pipeline_runs  # Operational metrics
```

---

## Key Concepts & Patterns

### 🔑 Stable Surrogate Keys

**All dimension tables** use surrogate keys (SKs) that are:
* **Stable across loads**: Once assigned, never changes
* **Integer-based**: Efficient joins and indexing
* **Decoupled from business keys**: Protects against source system changes

**Implementation Pattern**:
```sql
COALESCE(
  existing_dim.sk,  -- Reuse existing key if found
  ROW_NUMBER() OVER (ORDER BY business_key) + COALESCE(MAX(sk), 0)  -- Generate new
) as surrogate_key
```

### 📅 SCD Type 2 (Slowly Changing Dimensions)

**dim_job** tracks historical changes using Type 2 SCD:

**Key Fields**:
* `job_sk` - Surrogate key (unique per version)
* `enterprise_job_id` - Business key (stable across versions)
* `effective_from` - Version start timestamp
* `effective_to` - Version end timestamp (NULL = current)
* `is_current` - Boolean flag for current version
* `record_hash` - Change detection hash

**SCD2 Logic**:
1. **Detect changes**: Compare `record_hash` between source and current dimension
2. **Close old version**: Set `effective_to` and `is_current = FALSE`
3. **Insert new version**: New row with new `job_sk`, `effective_from = now`, `is_current = TRUE`

**Time Travel Joins** (Facts → SCD2 Dimensions):
```sql
FROM fact_table f
LEFT JOIN dim_job j
  ON f.enterprise_job_id = j.enterprise_job_id
  AND f.event_timestamp >= j.effective_from
  AND (f.event_timestamp < j.effective_to OR j.effective_to IS NULL)
```

### 🆔 Canonical Job Identity

**Problem**: Same job posted across multiple sources needs unified identity

**Solution**: `silver.silver_job_identity_map` provides canonical mapping:
* Maps `(source_name, source_job_id)` → `enterprise_job_id`
* Match scores and rules for fuzzy matching
* All warehouse loads use `enterprise_job_id` as the stable business key

### 🔗 Foreign Key Resolution

**All fact tables** resolve foreign keys using:
1. **Direct lookups** for Type 1 dimensions (current values only)
2. **Time travel joins** for Type 2 dimensions (SCD2 effective date windows)
3. **-1 placeholder** for missing/unknown dimension values

**Example** (fact_job_postings):
```sql
-- SCD2 time travel join
LEFT JOIN dim_job j
  ON f.enterprise_job_id = j.enterprise_job_id
  AND f.posting_timestamp >= j.effective_from
  AND (f.posting_timestamp < j.effective_to OR j.effective_to IS NULL)

-- Type 1 lookup
LEFT JOIN dim_company c
  ON j.company_sk = c.company_sk  -- Already resolved in dim_job
```

---

## Notebook Descriptions

### Dimension Loaders

#### `wh_dim_date`
Generates a comprehensive date dimension (2020-2030) with:
* Date keys in YYYYMMDD integer format
* Calendar attributes (year, quarter, month, week, day)
* Business day flags (weekends, month/quarter/year boundaries)
* Fiscal year support (July start)

#### `wh_dim_source`
Maintains data source systems:
* Extracts distinct sources from silver layer
* Tracks ingestion methods (API, scrape, etc.)
* Type 1 SCD (overwrites on change)

#### `wh_dim_sector`
Industry sector hierarchy:
* Canonical sector names from intermediate layer
* Sector categories and levels
* Parent-child relationships for drill-down

#### `wh_dim_company`
Canonical company entities:
* Resolves company name variations via intermediate layer
* Links to sector dimension
* Tracks alias counts and match confidence

#### `wh_dim_company_alias`
Company name variation lookup:
* Maps all company name variations to canonical companies
* Enables fuzzy company name matching
* Confidence scores and match methods

#### `wh_dim_location`
Geographic hierarchy:
* City, state/province, country parsing
* Remote work type classification
* Location normalization

#### `wh_dim_skill`
Skills catalog:
* Technical vs. soft skills classification
* Skill hierarchies and categories
* Demand scores and proficiency levels

#### `wh_dim_role`
Canonical job roles:
* Role families and career levels
* Seniority classification (junior, senior, manager, executive)
* Role categories and hierarchies

#### `wh_dim_job_scd2` ⭐
**Type 2 slowly changing dimension** for job postings:
* Tracks job attribute changes over time
* Effective date windows for time travel
* Resolves FKs to all conformed dimensions
* Change detection via record hash comparison
* **Critical**: Run after all other dimensions are loaded

### Bridge Tables

#### `wh_bridge_job_skill`
Many-to-many job-to-skill relationships:
* Links jobs to extracted skills
* Confidence scores (0-1) and evidence types
* Temporal alignment with job SCD2 versions
* Automatically closes when job versions update

### Fact Tables

#### `wh_fact_job_postings`
**Core transactional fact** - one row per job posting event:
* Foreign keys to all dimensions (SCD2-aware joins)
* Date key (YYYYMMDD) for efficient date filtering
* Event type flags (is_new_job, is_update, is_soft_delete, is_restore)
* Active status tracking

#### `wh_fact_job_lifecycle`
Job state transition events:
* Tracks lifecycle changes (created, activated, deactivated, deleted, restored)
* Duration metrics between states
* Change type classification
* Supports lifecycle analysis and funnel reporting

#### `wh_fact_salary`
Salary analytics:
* Salary ranges (min, max, midpoint)
* Currency normalization to USD
* Employment type context
* Aggregatable metrics for compensation analysis

#### `wh_fact_pipeline_runs`
ETL operational metrics:
* Pipeline execution status and duration
* Records processed (read, written, failed, quarantined)
* Stage-level aggregations
* Data quality metrics and success rates
* Supports operational monitoring and alerting

---

## Dependencies & Prerequisites

### Upstream Tables (Must Exist)

**Silver Layer**:
* `workspace.silver.silver_jobs_current` - Current job snapshot
* `workspace.silver.silver_job_changes` - Change event log
* `workspace.silver.silver_job_identity_map` - Canonical job identity

**Intermediate Layer**:
* `workspace.intermediate.inter_company_canonical` - Company mapping
* `workspace.intermediate.inter_company_map` - Company-to-sector
* `workspace.intermediate.inter_sector_map` - Sector hierarchy
* `workspace.intermediate.inter_skill_catalog` - Skills catalog
* `workspace.intermediate.inter_job_role_map` - Role mapping
* `workspace.intermediate.inter_job_skill_evidence` - Job-skill relationships

**Audit Layer** (for fact_pipeline_runs):
* `workspace.audit.pipeline_run_log` - Pipeline execution logs
* `workspace.audit.pipeline_stage_metrics` - Stage-level metrics

### Warehouse Tables (Created by These Notebooks)

All notebooks create their target tables with `CREATE OR REPLACE` or `MERGE` logic.

---

## Usage Patterns

### Initial Load (Full Refresh)

1. **Run dimensions** in phases 1-2 (parallel within phase)
2. **Run dim_job_scd2** (phase 3)
3. **Run bridge tables** (phase 4)
4. **Run fact tables** (phase 5, parallel)

### Incremental Load (Delta Processing)

**All notebooks are idempotent** - they can be run repeatedly:

* **Dimensions**: MERGE logic updates existing records or inserts new
* **SCD2 (dim_job)**: Detects changes and creates new versions
* **Bridge**: Syncs with current job versions
* **Facts**: INSERT with duplicate detection or MERGE on unique keys

**Recommended Schedule**:
```
Dimensions (Type 1)    → Daily (or after silver layer updates)
SCD2 (dim_job)         → Daily (or after silver layer updates)
Bridge (job_skill)     → Daily (after dim_job)
Facts                  → Hourly or Daily (based on latency requirements)
```

### Querying the Warehouse

**Example**: Jobs posted in last 30 days by company and location
```sql
SELECT 
  c.company_name,
  l.city,
  l.state_province,
  r.role_name,
  COUNT(DISTINCT f.job_sk) as job_count,
  AVG(s.salary_midpoint_usd) as avg_salary
FROM workspace.warehouse.fact_job_postings f
INNER JOIN workspace.warehouse.dim_date d 
  ON f.posting_date_sk = d.date_sk
INNER JOIN workspace.warehouse.dim_job j 
  ON f.job_sk = j.job_sk
INNER JOIN workspace.warehouse.dim_company c 
  ON f.company_sk = c.company_sk
INNER JOIN workspace.warehouse.dim_location l 
  ON f.location_sk = l.location_sk
INNER JOIN workspace.warehouse.dim_role r 
  ON f.role_sk = r.role_sk
LEFT JOIN workspace.warehouse.fact_salary s 
  ON f.job_sk = s.job_sk
WHERE d.date_value >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND f.active_flag = TRUE
GROUP BY c.company_name, l.city, l.state_province, r.role_name
ORDER BY job_count DESC
LIMIT 20;
```

**Example**: Job lifecycle analysis
```sql
SELECT 
  l.lifecycle_event_type,
  COUNT(*) as event_count,
  AVG(l.days_in_previous_state) as avg_days_before_event
FROM workspace.warehouse.fact_job_lifecycle l
INNER JOIN workspace.warehouse.dim_date d 
  ON l.change_date_sk = d.date_sk
WHERE d.year = 2026
GROUP BY l.lifecycle_event_type
ORDER BY event_count DESC;
```

---

## Data Quality & Validation

### Built-in Validations

Each notebook includes validation queries:
* **Record counts** and distinct keys
* **Foreign key coverage** (% with valid FKs vs. -1 placeholders)
* **SCD2 integrity** (one current version per business key)
* **Date coverage** and temporal consistency

### Monitoring Queries

**Check for orphaned facts** (FKs = -1):
```sql
SELECT 
  'company_sk' as dimension,
  COUNT(*) as orphaned_records
FROM workspace.warehouse.fact_job_postings
WHERE company_sk = -1
UNION ALL
SELECT 'location_sk', COUNT(*)
FROM workspace.warehouse.fact_job_postings
WHERE location_sk = -1;
```

**SCD2 integrity check** (multiple current versions):
```sql
SELECT 
  enterprise_job_id,
  COUNT(*) as current_version_count
FROM workspace.warehouse.dim_job
WHERE is_current = TRUE
GROUP BY enterprise_job_id
HAVING COUNT(*) > 1;  -- Should return 0 rows
```

---

## Troubleshooting

### Common Issues

**Issue**: "Table or view not found" errors
* **Cause**: Upstream silver/semantic tables don't exist yet
* **Fix**: Run silver and intermediate layer notebooks first

**Issue**: Foreign keys resolving to -1 (unknown)
* **Cause**: Dimension data missing or join keys don't match
* **Fix**: Check dimension load logs, verify company/location normalization

**Issue**: SCD2 creating too many versions
* **Cause**: record_hash includes volatile fields (timestamps, batch IDs)
* **Fix**: Review hash calculation in silver layer - only hash stable attributes

**Issue**: Fact table row counts don't match silver layer
* **Cause**: FK resolution filtering out records with missing dimensions
* **Fix**: Review validation queries, add unknown dimension records (-1 keys)

### Performance Tuning

**Large dimension lookups**:
* Ensure dimensions are properly indexed
* Use broadcast hints for small dimensions: `BROADCAST(dim_company)`

**Slow SCD2 processing**:
* Partition dim_job by `is_current` flag
* Index on `(enterprise_job_id, is_current, effective_from)`

**Fact table loads**:
* Use Z-ORDER clustering on common filter columns (date_sk, company_sk)
* Partition facts by date for time-based queries

---

## Next Steps

### After Warehouse is Built

1. **Create gold layer aggregates** for common queries
2. **Build intermediate layer** (metrics, KPIs) on top of warehouse
3. **Connect BI tools** (Tableau, Power BI) to warehouse schema
4. **Implement data observability** monitoring on fact/dimension freshness
5. **Add role-based security** using Unity Catalog grants

### Enhancement Opportunities

* **Add Type 1 history tracking** with audit columns (updated_by, updated_at)
* **Implement mini-dimensions** for frequently changing attributes
* **Create aggregate fact tables** for performance (monthly rollups)
* **Build helper views** for common join patterns
* **Add data lineage** metadata to track source-to-warehouse flow

---

## References

### Dimensional Modeling Best Practices
* [The Data Warehouse Toolkit (Kimball)](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/)
* [Slowly Changing Dimensions](https://en.wikipedia.org/wiki/Slowly_changing_dimension)
* [Star Schema Design](https://docs.databricks.com/lakehouse/data-modeling.html)

### Databricks Documentation
* [Delta Lake Merge](https://docs.databricks.com/delta/merge.html)
* [SQL Reference](https://docs.databricks.com/sql/language-manual/index.html)
* [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)

---

## Contact & Support

For questions or issues with warehouse notebooks:
* Review validation queries in each notebook
* Check upstream silver/intermediate layer data quality
* Verify execution order (dimensions → SCD2 → bridges → facts)
* Consult data engineering team for schema changes

**Last Updated**: 2026-06-04  
**Maintainer**: Data Engineering Team  
**Version**: 1.0
