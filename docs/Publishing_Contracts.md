# LMIP Data Publishing Contracts

**Version:** 1.0.0  
**Last Updated:** 2026-06-12  
**Status:** Active

## Overview

This document defines the complete publishing architecture for LMIP (Labor Market Information Platform). It ensures reproducible, versioned, and recoverable data distribution to Supabase, CSV bundles, and consumer deployments without requiring Databricks infrastructure.

---

## 1. Export Order

### Phase 1: Dimension Tables (Dependencies First)

Dimensions must be exported before facts to maintain referential integrity.

**Export Sequence:**

1. **dim_sector** - No dependencies
2. **dim_source** - No dependencies
3. **dim_company** - No dependencies
4. **dim_location** - No dependencies
5. **dim_role** - No dependencies
6. **dim_skill** - No dependencies

### Phase 2: Gold Layer Facts (After Dimensions)

**Export Sequence:**

7. **gold_company_hiring** - Depends on: dim_sector, dim_company, dim_location
8. **gold_company_activity** - Depends on: dim_sector, dim_company
9. **gold_location_trends** - Depends on: dim_sector, dim_location
10. **gold_salary_trends** - Depends on: dim_sector, dim_role, dim_location, dim_company
11. **gold_skill_demand** - Depends on: dim_sector, dim_role, dim_location, dim_skill

### Export Execution Rules

* **Sequential Phase Execution:** All Phase 1 tables must complete before Phase 2 begins
* **Parallel Within Phase:** Tables within the same phase can be exported in parallel
* **Atomic Batch:** Each export batch is atomic - all succeed or all roll back
* **Validation Gate:** Each phase validates referential integrity before proceeding

---

## 2. Dependency Order

### Dependency Graph

```
Phase 1 (Dimensions - No Dependencies)
├── dim_sector
├── dim_source
├── dim_company
├── dim_location
├── dim_role
└── dim_skill

Phase 2 (Gold Facts - Depends on Phase 1)
├── gold_company_hiring
│   ├── → dim_sector
│   ├── → dim_company
│   └── → dim_location
├── gold_company_activity
│   ├── → dim_sector
│   └── → dim_company
├── gold_location_trends
│   ├── → dim_sector
│   └── → dim_location
├── gold_salary_trends
│   ├── → dim_sector
│   ├── → dim_role
│   ├── → dim_location
│   └── → dim_company
└── gold_skill_demand
    ├── → dim_sector
    ├── → dim_role
    ├── → dim_location
    └── → dim_skill
```

### Foreign Key Constraints

**Gold Tables → Dimension Tables:**

* All `*_sk` columns in gold tables reference corresponding `*_sk` in dimension tables
* NULL values are permitted where specified (e.g., `location_sk`, `role_sk`, `company_sk` for aggregate rows)
* All non-NULL foreign keys must exist in dimension tables before fact export

---

## 3. Manifest Schema

### Manifest File: `manifest.json`

**Location:** Root of every published bundle

**Schema:**

```json
{
  "$schema": "https://lmip.publishing/manifest/v1.0.schema.json",
  "manifest_version": "1.0",
  "publication": {
    "bundle_id": "lmip_export_20260607_120000",
    "bundle_version": "2026.23.1",
    "published_at": "2026-06-07T12:00:00Z",
    "publisher": "LMIP_ETL_Pipeline",
    "environment": "production"
  },
  "data_period": {
    "start_date": "20260101",
    "end_date": "20260607",
    "granularity": "daily",
    "is_incremental": false,
    "incremental_from_version": null
  },
  "tables": [
    {
      "table_name": "dim_sector",
      "file_name": "dimensions/dim_sector.csv",
      "row_count": 15,
      "file_size_bytes": 2048,
      "checksum_sha256": "abc123...",
      "export_timestamp": "2026-06-07T12:00:05Z",
      "table_type": "dimension",
      "dependencies": [],
      "columns": [
        {"name": "sector_sk", "type": "integer", "nullable": false, "primary_key": true},
        {"name": "sector_name", "type": "string", "nullable": false},
        {"name": "sector_family", "type": "string", "nullable": true},
        {"name": "sector_aliases", "type": "string", "nullable": true},
        {"name": "active_flag", "type": "boolean", "nullable": false}
      ]
    }
  ],
  "statistics": {
    "total_tables": 11,
    "total_rows": 1250000,
    "total_size_bytes": 52428800,
    "dimension_tables": 6,
    "fact_tables": 5
  },
  "quality_checks": {
    "referential_integrity_passed": true,
    "null_checks_passed": true,
    "row_count_variance_pct": 0.5,
    "validation_timestamp": "2026-06-07T12:15:00Z"
  },
  "compatibility": {
    "min_consumer_version": "1.0.0",
    "breaking_changes": false,
    "deprecated_fields": []
  }
}
```

### Manifest Generation Process

1. **Pre-Export:** Initialize manifest with metadata
2. **During Export:** Update table entries as each export completes
3. **Post-Export:** Calculate checksums, statistics, and run quality checks
4. **Finalization:** Sign and publish manifest

---

## 4. CSV Bundle Structure

### Directory Layout

```
lmip_export_YYYYMMDD_HHMMSS/
├── manifest.json
├── README.md
├── CHANGELOG.md
├── dimensions/
│   ├── dim_sector.csv
│   ├── dim_company.csv
│   ├── dim_location.csv
│   ├── dim_role.csv
│   ├── dim_skill.csv
│   └── dim_source.csv
├── facts/
│   ├── gold_company_hiring.csv
│   ├── gold_company_activity.csv
│   ├── gold_location_trends.csv
│   ├── gold_salary_trends.csv
│   └── gold_skill_demand.csv
├── schemas/
│   ├── dimensions.json
│   └── facts.json
└── scripts/
    ├── load_dimensions.sql
    ├── load_facts.sql
    ├── validate_import.sql
    └── load_bundle.py
```

### CSV Format Specifications

**Encoding:** UTF-8 with BOM  
**Delimiter:** Comma (`,`)  
**Quote Character:** Double quote (`"`)  
**Escape Character:** Double quote (`""`)  
**Line Terminator:** `\r\n` (CRLF)  
**Header:** First row contains column names  
**NULL Representation:** Empty string for NULL values

**Date Format:** `YYYYMMDD` (integer)  
**Timestamp Format:** ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)  
**Boolean Format:** `true` / `false` (lowercase)

### File Naming Convention

**Pattern:** `{table_name}.csv`  
**Example:** `dim_sector.csv`, `gold_company_hiring.csv`

### Bundle Compression

**Format:** `.tar.gz`  
**Naming:** `lmip_export_YYYYMMDD_HHMMSS.tar.gz`  
**Example:** `lmip_export_20260607_120000.tar.gz`

---

## 5. Versioning Strategy

### Semantic Versioning: `YYYY.WW.PATCH`

**Format:** `{YEAR}.{WEEK}.{PATCH}`

* **YEAR:** 4-digit year (e.g., 2026)
* **WEEK:** ISO week number (01-53)
* **PATCH:** Incremental number for republishes within the same week (0-based)

**Examples:**
* `2026.23.0` - First publication of week 23 in 2026
* `2026.23.1` - Second publication of week 23 (correction or update)
* `2026.24.0` - First publication of week 24

### Version Control Metadata

**Tracked in:** `version_history` table in Supabase

**Schema:**
```sql
CREATE TABLE version_history (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bundle_version VARCHAR(20) NOT NULL UNIQUE,
  bundle_id VARCHAR(100) NOT NULL,
  published_at TIMESTAMPTZ NOT NULL,
  data_start_date INT NOT NULL,
  data_end_date INT NOT NULL,
  is_incremental BOOLEAN NOT NULL,
  parent_version VARCHAR(20),
  row_counts JSONB NOT NULL,
  file_checksums JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  deprecated_at TIMESTAMPTZ,
  notes TEXT
);
```

### Breaking Change Policy

**Major Version Increment (Year Change):** Natural yearly boundary

**Breaking Changes Include:**
* Removing tables or columns
* Changing column data types
* Changing primary/foreign key relationships
* Modifying date range semantics

**Non-Breaking Changes:**
* Adding new tables
* Adding new columns (at end)
* Expanding data ranges
* Performance optimizations

---

## 6. Incremental Publishing Strategy

### Incremental Modes

#### Mode 1: Full Refresh (Default)

**When:** Initial load, monthly full snapshots, major corrections  
**Behavior:** Export all data regardless of previous publications  
**manifest.json:** `"is_incremental": false`

#### Mode 2: Date Range Incremental

**When:** Daily/weekly updates  
**Behavior:** Export only records with `*_date_sk` >= last published `data_end_date`  
**manifest.json:** `"is_incremental": true`

**Implementation:**
```sql
-- Example: Incremental export for gold_company_hiring
SELECT *
FROM workspace.gold.gold_company_hiring
WHERE hiring_date_sk > (
  SELECT MAX(data_end_date) 
  FROM version_history 
  WHERE status = 'active'
)
```

#### Mode 3: Dimension Delta

**When:** Dimension changes (new companies, roles, skills)  
**Behavior:** Export only changed/new dimension records  
**Tracking:** Requires `last_modified_ts` column in dimension tables

**Implementation:**
```sql
-- Export only changed dimensions
SELECT *
FROM workspace.gold.dim_company
WHERE last_modified_ts > (
  SELECT MAX(published_at) 
  FROM version_history 
  WHERE status = 'active'
)
```

### Incremental Merge Strategy

**Consumer Side (Supabase/Local DB):**

1. **Dimensions:** UPSERT based on surrogate keys (`*_sk`)
2. **Facts:** INSERT new records (date range filter prevents duplicates)
3. **Validation:** Verify referential integrity post-merge
4. **Rollback:** On failure, restore from last successful version

**SQL Pattern (PostgreSQL/Supabase):**
```sql
-- Dimension upsert
INSERT INTO dim_company (company_sk, canonical_company_name, company_nk, industry, active_flag)
SELECT * FROM staging.dim_company
ON CONFLICT (company_sk) 
DO UPDATE SET
  canonical_company_name = EXCLUDED.canonical_company_name,
  company_nk = EXCLUDED.company_nk,
  industry = EXCLUDED.industry,
  active_flag = EXCLUDED.active_flag;

-- Fact append (date range ensures no duplicates)
INSERT INTO gold_company_hiring
SELECT * FROM staging.gold_company_hiring
WHERE hiring_date_sk NOT IN (
  SELECT DISTINCT hiring_date_sk 
  FROM gold_company_hiring
);
```

### Incremental Schedule

**Daily Incremental:** Monday-Saturday, 02:00 UTC  
**Weekly Full Refresh:** Sunday, 04:00 UTC  
**Monthly Full Archive:** First Sunday of month, 06:00 UTC

---

## 7. Recovery Strategy

### Recovery Scenarios

#### Scenario A: Failed Export (Pre-Publication)

**Detection:** Export script returns error code  
**Impact:** No published artifact, no consumer impact

**Recovery Steps:**
1. Alert on-call engineer
2. Inspect error logs
3. Fix source issue (data quality, infrastructure)
4. Retry export
5. Validate and publish

**Automation:** Automatic retry (3 attempts, 15-minute intervals)

#### Scenario B: Corrupted Bundle (Post-Publication)

**Detection:** Checksum mismatch, failed validation checks  
**Impact:** Consumers may download corrupted bundle

**Recovery Steps:**
1. **Immediate:** Mark version as `deprecated` in version_history
2. **Notification:** Alert consumers via status page/API
3. **Rollback:** Publish rollback manifest pointing to previous version
4. **Re-export:** Generate corrected bundle
5. **Validation:** Enhanced validation before republishing
6. **Communication:** Update status page with incident report

#### Scenario C: Bad Data Published

**Detection:** Consumer reports anomalies, post-publication quality checks  
**Impact:** Incorrect analytics, potential downstream corruption

**Recovery Steps:**
1. **Immediate Deprecation:** Mark bad version as `deprecated`
2. **Rollback Advisory:** Publish advisory with rollback instructions
3. **Consumer Rollback:** Consumers restore from previous version
4. **Root Cause:** Identify and fix upstream data issue
5. **Re-publication:** Export corrected data as new PATCH version
6. **Validation:** Extended validation before marking as `active`

#### Scenario D: Complete Data Loss

**Detection:** Database corruption, infrastructure failure  
**Impact:** Cannot generate new exports

**Recovery Steps:**
1. **Archive Restoration:** Restore Databricks tables from Delta Lake time travel
2. **Fallback:** Use last known good published bundle as seed
3. **Incremental Rebuild:** Re-run ETL from last checkpoint
4. **Validation:** Full data quality assessment
5. **Resume Publishing:** Return to normal schedule

### Backup Strategy

**Databricks Delta Tables:**
* **Retention:** 90-day time travel window
* **Snapshots:** Weekly full snapshots to external storage (S3/Azure Blob)

**Published Bundles:**
* **Retention:** All versions kept for 1 year
* **Storage:** Distributed storage (S3 + Mirror)
* **Access:** Publicly accessible via versioned URLs

**Supabase Database:**
* **Backups:** Daily automated backups (Supabase native)
* **Point-in-Time Recovery:** Available for last 7 days
* **Export Copies:** Weekly CSV dumps stored in external storage

### Rollback Procedures

**Consumer Rollback (SQL):**

```sql
-- Step 1: Identify rollback target
SELECT version_id, bundle_version, published_at
FROM version_history
WHERE status = 'active'
  AND published_at < (SELECT published_at FROM version_history WHERE bundle_version = '{bad_version}')
ORDER BY published_at DESC
LIMIT 1;

-- Step 2: Truncate tables (DANGER: Backup first!)
TRUNCATE TABLE gold_company_hiring CASCADE;
TRUNCATE TABLE gold_company_activity CASCADE;
TRUNCATE TABLE gold_location_trends CASCADE;
TRUNCATE TABLE gold_salary_trends CASCADE;
TRUNCATE TABLE gold_skill_demand CASCADE;

-- Step 3: Reload from good version
-- Run load_bundle.py with --version {good_version}

-- Step 4: Validate
SELECT 
  table_name,
  COUNT(*) as current_count,
  vh.row_counts->>table_name as expected_count
FROM information_schema.tables
CROSS JOIN version_history vh
WHERE vh.bundle_version = '{good_version}'
  AND table_schema = 'public'
  AND table_name LIKE 'gold_%' OR table_name LIKE 'dim_%';
```

### Monitoring & Alerting

**Metrics to Monitor:**
* Export duration (alert if > 2x baseline)
* Row count variance (alert if > 10% deviation)
* Checksum validation failures
* Consumer download errors
* Referential integrity violations

**Alert Channels:**
* PagerDuty for critical failures
* Slack #data-engineering for warnings
* Status page for consumer-facing issues

---

## 8. Consumer Deployment Guide

### Reproducibility Requirements

**Principle:** Consumers must be able to ingest and query data using ONLY the published bundle - no Databricks access required.

**Provided Artifacts:**
1. CSV data files
2. Manifest with metadata
3. SQL schema definitions
4. Loading scripts (Python, SQL)
5. Validation scripts

### Reference Implementation: PostgreSQL/Supabase

**Environment Requirements:**
* PostgreSQL 14+ or Supabase project
* Python 3.9+ with `pandas`, `psycopg2`, `jsonschema`
* 10 GB available storage

**Deployment Steps:**

```bash
# Step 1: Download bundle
wget https://lmip.publishing/exports/lmip_export_20260607_120000.tar.gz
tar -xzf lmip_export_20260607_120000.tar.gz
cd lmip_export_20260607_120000

# Step 2: Validate bundle
python scripts/load_bundle.py --validate-only --manifest manifest.json

# Step 3: Create database schema
psql $DATABASE_URL -f scripts/load_dimensions.sql
psql $DATABASE_URL -f scripts/load_facts.sql

# Step 4: Load data
python scripts/load_bundle.py \
  --database-url $DATABASE_URL \
  --manifest manifest.json \
  --mode full

# Step 5: Validate import
psql $DATABASE_URL -f scripts/validate_import.sql
```

### Incremental Update (Consumer)

```bash
# Download incremental bundle
wget https://lmip.publishing/exports/lmip_export_20260614_120000.tar.gz
tar -xzf lmip_export_20260614_120000.tar.gz
cd lmip_export_20260614_120000

# Verify incremental compatibility
python scripts/load_bundle.py --validate-incremental --manifest manifest.json

# Apply incremental update
python scripts/load_bundle.py \
  --database-url $DATABASE_URL \
  --manifest manifest.json \
  --mode incremental
```

---

## 9. Publication Targets

### Target 1: Supabase (Primary)

**Connection:** Direct PostgreSQL protocol  
**Update Frequency:** Daily incremental, Weekly full refresh  
**Access:** Authenticated API, Row Level Security enabled

**Publication Method:**
* Automated via Databricks Job
* Uses `load_bundle.py` script
* Validates before committing
* Atomic transactions

### Target 2: CSV Bundles (Archive)

**Storage:** S3 bucket `s3://lmip-public-exports/`  
**Access:** Public read, versioned URLs  
**Retention:** Indefinite (all versions)

**URL Pattern:**
```
https://lmip.publishing/exports/{bundle_id}.tar.gz
https://lmip.publishing/exports/latest.tar.gz (symlink)
```

### Target 3: Consumer Deployments

**Distribution:** Direct download from public S3  
**Support:** Documentation, reference implementations  
**Feedback:** GitHub issues, support email

---

## 10. Quality Gates

### Pre-Publication Validation

**Must Pass Before Publishing:**

1. **Row Count Sanity:** 
   * Dimensions: Within 20% of previous version (unless intentional)
   * Facts: Within 10% of expected (based on date range)

2. **Referential Integrity:**
   * All foreign keys exist in dimension tables
   * No orphaned fact records

3. **NULL Constraints:**
   * Primary keys are never NULL
   * Non-nullable columns validated

4. **Data Range:**
   * Date keys are valid (`YYYYMMDD` format)
   * No future dates beyond publication date

5. **Checksum Validation:**
   * All CSV files match manifest checksums
   * Manifest itself is valid JSON

### Post-Publication Monitoring

**First 24 Hours:**
* Monitor consumer download success rates
* Check for validation failures
* Track load times and errors

**Ongoing:**
* Query performance on Supabase
* Data freshness alerts
* Consumer feedback

---

## Appendix A: Table Schemas

### Dimension Tables

#### dim_sector
```sql
CREATE TABLE dim_sector (
  sector_sk INTEGER PRIMARY KEY,
  sector_name VARCHAR(100) NOT NULL,
  sector_family VARCHAR(100),
  sector_aliases TEXT,
  active_flag BOOLEAN NOT NULL DEFAULT true
);
```

#### dim_company
```sql
CREATE TABLE dim_company (
  company_sk INTEGER PRIMARY KEY,
  canonical_company_name VARCHAR(200) NOT NULL,
  company_nk VARCHAR(100) NOT NULL,
  industry VARCHAR(100),
  active_flag BOOLEAN NOT NULL DEFAULT true
);
```

#### dim_location
```sql
CREATE TABLE dim_location (
  location_sk INTEGER PRIMARY KEY,
  location_nk VARCHAR(200) NOT NULL,
  location_name VARCHAR(200) NOT NULL,
  city VARCHAR(100),
  state VARCHAR(100),
  country VARCHAR(100) NOT NULL,
  region VARCHAR(100),
  iso_country_code VARCHAR(3),
  iso_region_code VARCHAR(10),
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  active_flag BOOLEAN NOT NULL DEFAULT true
);
```

#### dim_role
```sql
CREATE TABLE dim_role (
  role_sk INTEGER PRIMARY KEY,
  canonical_role_id VARCHAR(100) NOT NULL,
  role_name VARCHAR(200) NOT NULL,
  role_family VARCHAR(100),
  seniority_default VARCHAR(50)
);
```

#### dim_skill
```sql
CREATE TABLE dim_skill (
  skill_sk INTEGER PRIMARY KEY,
  canonical_skill_id VARCHAR(100) NOT NULL,
  skill_name VARCHAR(200) NOT NULL,
  skill_category VARCHAR(100)
);
```

#### dim_source
```sql
CREATE TABLE dim_source (
  source_sk INTEGER PRIMARY KEY,
  source_name VARCHAR(100) NOT NULL,
  source_endpoint VARCHAR(500),
  active_flag BOOLEAN NOT NULL DEFAULT true
);
```

### Gold Tables

#### gold_company_hiring
```sql
CREATE TABLE gold_company_hiring (
  hiring_date_sk INTEGER NOT NULL,
  sector_sk INTEGER NOT NULL REFERENCES dim_sector(sector_sk),
  company_sk INTEGER NOT NULL REFERENCES dim_company(company_sk),
  location_sk INTEGER REFERENCES dim_location(location_sk),
  active_jobs INTEGER NOT NULL DEFAULT 0,
  new_jobs INTEGER NOT NULL DEFAULT 0,
  closed_jobs INTEGER NOT NULL DEFAULT 0,
  net_change INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (hiring_date_sk, sector_sk, company_sk, COALESCE(location_sk, -1))
);
```

#### gold_company_activity
```sql
CREATE TABLE gold_company_activity (
  activity_date_sk INTEGER NOT NULL,
  sector_sk INTEGER NOT NULL REFERENCES dim_sector(sector_sk),
  company_sk INTEGER NOT NULL REFERENCES dim_company(company_sk),
  active_jobs INTEGER NOT NULL DEFAULT 0,
  new_jobs INTEGER NOT NULL DEFAULT 0,
  closed_jobs INTEGER NOT NULL DEFAULT 0,
  net_change INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (activity_date_sk, sector_sk, company_sk)
);
```

#### gold_salary_trends
```sql
CREATE TABLE gold_salary_trends (
  salary_date_sk INTEGER NOT NULL,
  sector_sk INTEGER NOT NULL REFERENCES dim_sector(sector_sk),
  role_sk INTEGER REFERENCES dim_role(role_sk),
  location_sk INTEGER REFERENCES dim_location(location_sk),
  company_sk INTEGER REFERENCES dim_company(company_sk),
  salary_min_median DECIMAL(12, 2),
  salary_max_median DECIMAL(12, 2),
  salary_min_p25 DECIMAL(12, 2),
  salary_max_p75 DECIMAL(12, 2),
  observation_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (salary_date_sk, sector_sk, COALESCE(role_sk, -1), COALESCE(location_sk, -1), COALESCE(company_sk, -1))
);
```

#### gold_skill_demand
```sql
CREATE TABLE gold_skill_demand (
  demand_date_sk INTEGER NOT NULL,
  sector_sk INTEGER NOT NULL REFERENCES dim_sector(sector_sk),
  role_sk INTEGER REFERENCES dim_role(role_sk),
  location_sk INTEGER REFERENCES dim_location(location_sk),
  skill_sk INTEGER NOT NULL REFERENCES dim_skill(skill_sk),
  mentions_count INTEGER NOT NULL DEFAULT 0,
  unique_jobs_count INTEGER NOT NULL DEFAULT 0,
  avg_confidence DECIMAL(5, 3),
  delta_vs_prev_period INTEGER,
  PRIMARY KEY (demand_date_sk, sector_sk, COALESCE(role_sk, -1), COALESCE(location_sk, -1), skill_sk)
);
```

#### gold_location_trends
```sql
CREATE TABLE gold_location_trends (
  location_date_sk INTEGER NOT NULL,
  sector_sk INTEGER NOT NULL REFERENCES dim_sector(sector_sk),
  location_sk INTEGER NOT NULL REFERENCES dim_location(location_sk),
  active_jobs INTEGER NOT NULL DEFAULT 0,
  new_jobs INTEGER NOT NULL DEFAULT 0,
  unique_companies INTEGER NOT NULL DEFAULT 0,
  unique_roles INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (location_date_sk, sector_sk, location_sk)
);
```

---

## Appendix B: Changelog Template

**File:** `CHANGELOG.md` (included in each bundle)

```markdown
# LMIP Export Changelog

## Version 2026.23.1 - 2026-06-07

### Changed
- Updated gold_company_hiring with corrections to net_change calculations
- Refreshed dim_company with 15 new companies

### Data Range
- Start: 2026-01-01
- End: 2026-06-07

### Statistics
- Total Rows: 1,250,000
- Tables: 11 (6 dimensions, 5 facts)

### Quality
- Referential Integrity: PASS
- NULL Constraints: PASS
- Row Count Variance: 0.5%

## Version 2026.23.0 - 2026-06-01
...
```

---

## Appendix C: Contact & Support

**Data Team:** data-engineering@lmip.org  
**Issue Tracker:** https://github.com/lmip/data-publishing/issues  
**Status Page:** https://status.lmip.publishing  
**Documentation:** https://docs.lmip.publishing

---

**End of Document**