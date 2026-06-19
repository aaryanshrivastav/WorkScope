# Taxonomy Tables Migration — June 2026

**Date**: 2026-06-17  
**Status**: ✅ COMPLETE  
**Impact**: Resolved `TABLE_OR_VIEW_NOT_FOUND` errors in bootstrap metadata seeding

---

## Executive Summary

**Problem**: Bootstrap.py was failing with `TABLE_OR_VIEW_NOT_FOUND` errors when attempting to seed metadata. The seeding logic referenced four taxonomy tables that did not exist in the DDL layer.

**Root Causes**:
1. Missing DDL files for four taxonomy tables
2. Incomplete `seed_metadata()` function in bootstrap.py (called but never implemented)
3. Architecture mismatch: CSV files existed in metadata/ directory, but corresponding tables were never created

**Solution**: Created 4 missing DDL files, implemented the `seed_metadata()` function with CSV-to-table merge logic, and added taxonomy tables to the DDL execution order.

**Before**: Bootstrap failed at metadata seeding step  
**After**: Bootstrap creates 4 taxonomy tables and seeds 80 records automatically  
**Deployment Time**: < 5 minutes

---

## Files Created/Modified

### New DDL Files (4)
* `sql/ddl/metadata_taxonomy_sectors.sql` — 19 sector records
* `sql/ddl/metadata_taxonomy_role_families.sql` — 13 role family records
* `sql/ddl/metadata_taxonomy_role_canonical.sql` — 22 canonical role records
* `sql/ddl/metadata_taxonomy_skill_catalog.sql` — 26 canonical skill records

### Modified Files (1)
* `deployment/bootstrap.py` — +108 lines
  * Updated `DDL_EXECUTION_ORDER` to include 4 new taxonomy DDLs
  * Implemented `seed_metadata()` function with CSV parsing and MERGE logic
  * Added `_get_merge_condition()` helper for idempotent seeding

---

## Taxonomy Tables Overview

### 1. taxonomy_sectors
**Source**: `metadata/sectors.csv`  
**Records**: 19 sectors (8 top-level, 11 subsectors)  
**Purpose**: Hierarchical sector taxonomy with NAICS mapping  
**Usage**: → inter_sector_map → gold.dim_sector

**Schema**:
```
sector_key       STRING  PRIMARY KEY  'TECH', 'HOSP', 'HEAL'
sector_name      STRING  NOT NULL     'Technology', 'Hospitality'
parent_sector    STRING  FOREIGN KEY  Self-referential hierarchy
naics_code       STRING  NULLABLE     '51', '72', '62'
keywords         STRING  PIPE-DELIM   'tech|IT|software|digital'
```

### 2. taxonomy_role_families
**Source**: `metadata/role_families.csv`  
**Records**: 13 families across 6 sectors  
**Purpose**: Role family groupings within sectors  
**Usage**: → inter_job_role_map → gold.dim_role

**Schema**:
```
family_key       STRING  PRIMARY KEY  'ENG', 'DATA', 'HOSP_OPS'
family_name      STRING  NOT NULL     'Engineering', 'Data & Analytics'
sector_key       STRING  FOREIGN KEY  → taxonomy_sectors
description      STRING  NULLABLE     'Software engineering roles'
```

### 3. taxonomy_role_canonical
**Source**: `metadata/canonical_roles.csv`  
**Records**: 22 roles across 6 sectors  
**Purpose**: Master role taxonomy for job title normalization  
**Usage**: → inter_job_role_map → gold.dim_role

**Schema**:
```
role_key         STRING  PRIMARY KEY  'ENG_SWE', 'DATA_DS'
canonical_role   STRING  NOT NULL     'Software Engineer', 'Data Scientist'
family_key       STRING  FOREIGN KEY  → taxonomy_role_families
sector_key       STRING  FOREIGN KEY  → taxonomy_sectors
seniority        STRING  ENUM         'junior','mid','senior','executive'
aliases          STRING  PIPE-DELIM   'software engineer|swe|developer'
```

### 4. taxonomy_skill_catalog
**Source**: `metadata/canonical_skills.csv`  
**Records**: 26 skills (23 sector-specific, 3 cross-sector)  
**Purpose**: Master skill catalog for skill extraction  
**Usage**: → inter_skill_catalog → gold.dim_skill

**Schema**:
```
skill_key        STRING  PRIMARY KEY  'TECH_PYTHON', 'HOSP_REV_MGT'
canonical_skill  STRING  NOT NULL     'Python', 'Revenue Management'
skill_category   STRING  NOT NULL     'Technical', 'Operations', 'Soft Skill'
sector_key       STRING  NULLABLE     → taxonomy_sectors (NULL for soft skills)
aliases          STRING  PIPE-DELIM   'python|py|python3'
```

---

## Deployment Steps

### Quick Deploy (3 Commands)

```bash
# 1. Dry run (verify no errors)
python deployment/bootstrap.py --catalog workspace --dry-run

# 2. Production run
python deployment/bootstrap.py --catalog workspace

# 3. Verify results
databricks-sql-cli --execute "
  SELECT 'sectors' AS table, COUNT(*) AS count FROM workspace.metadata.taxonomy_sectors
  UNION ALL SELECT 'families', COUNT(*) FROM workspace.metadata.taxonomy_role_families
  UNION ALL SELECT 'roles', COUNT(*) FROM workspace.metadata.taxonomy_role_canonical
  UNION ALL SELECT 'skills', COUNT(*) FROM workspace.metadata.taxonomy_skill_catalog
"
```

**Expected Counts**: sectors=19, families=13, roles=22, skills=26

---

## Technical Implementation

### DDL Execution Order

The taxonomy tables were added to `DDL_EXECUTION_ORDER` in bootstrap.py in dependency order:

```python
# Metadata tables (added taxonomy tables)
"metadata_pipeline_run_control.sql",
"metadata_source_config.sql",
"metadata_staging_to_current_batches.sql",
"metadata_taxonomy_sectors.sql",           # 1. Base taxonomy (no dependencies)
"metadata_taxonomy_role_families.sql",     # 2. Depends on sectors
"metadata_taxonomy_role_canonical.sql",    # 3. Depends on families + sectors
"metadata_taxonomy_skill_catalog.sql",     # 4. Depends on sectors
```

### Seeding Logic

The `seed_metadata()` function implements idempotent CSV-to-table seeding:

1. **CSV Parsing**: Reads CSV files from metadata/ directory with UTF-8 encoding
2. **Schema Inference**: Detects column types (STRING for text, TIMESTAMP for datetime columns)
3. **DataFrame Creation**: Converts CSV rows to Spark DataFrames
4. **Merge Operation**: Uses `MERGE INTO` with natural keys for idempotency
   - New records are inserted
   - Existing records are updated
   - No duplicate records created on rerun

**Natural Keys Used**:
* taxonomy_sectors: `sector_key`
* taxonomy_role_families: `family_key`
* taxonomy_role_canonical: `role_key`
* taxonomy_skill_catalog: `skill_key`

---

## Verification

### Success Indicators

✅ Bootstrap completes without `TABLE_OR_VIEW_NOT_FOUND` errors  
✅ All 4 taxonomy tables created in `workspace.metadata`  
✅ CSV data seeded (80 total records)  
✅ Timestamp columns populated (created_at, updated_at)  
✅ Hierarchical relationships intact (parent_sector, family_key, sector_key FKs)

### Quick Verification Query

```sql
SELECT 
  'PASS' AS status,
  (SELECT COUNT(*) FROM workspace.metadata.taxonomy_sectors) AS sectors,
  (SELECT COUNT(*) FROM workspace.metadata.taxonomy_role_families) AS families,
  (SELECT COUNT(*) FROM workspace.metadata.taxonomy_role_canonical) AS roles,
  (SELECT COUNT(*) FROM workspace.metadata.taxonomy_skill_catalog) AS skills
WHERE 
  (SELECT COUNT(*) FROM workspace.metadata.taxonomy_sectors) = 19
  AND (SELECT COUNT(*) FROM workspace.metadata.taxonomy_role_families) = 13
  AND (SELECT COUNT(*) FROM workspace.metadata.taxonomy_role_canonical) = 22
  AND (SELECT COUNT(*) FROM workspace.metadata.taxonomy_skill_catalog) = 26;
```

**Expected**: Returns 1 row with `status='PASS'` and correct counts

---

## Data Flow Architecture

```
CSV FILES                    TAXONOMY TABLES                  INTERMEDIATE LAYER              GOLD LAYER
─────────────────────────────────────────────────────────────────────────────────────────────────────────
canonical_roles.csv    →    taxonomy_role_canonical    →    inter_job_role_map        →    dim_role
role_families.csv      →    taxonomy_role_families     →    inter_job_role_map        →    dim_role
sectors.csv            →    taxonomy_sectors           →    inter_sector_map          →    dim_sector
canonical_skills.csv   →    taxonomy_skill_catalog     →    inter_skill_catalog       →    dim_skill
```

### Dependency Chain

1. **Sectors** (independent) → role_families, role_canonical, skill_catalog
2. **Role Families** (depends on sectors) → role_canonical
3. **Role Canonical** (depends on families + sectors) → intermediate layer
4. **Skill Catalog** (depends on sectors) → intermediate layer

---

## Related Work

### Gold Dimension Updates (Task 6)

After taxonomy tables were created, the gold dimension tables were updated to reference the new governed taxonomy:

**Files Modified**:
* `sql/ddl/gold_dim_sector.sql` — Added taxonomy columns
* `sql/ddl/gold_dim_role.sql` — Added taxonomy columns
* `sql/ddl/gold_dim_skill.sql` — Added taxonomy columns

**Notebook Loaders Updated**:
* `notebooks/gold/gold_dim_sector.ipynb` — Now sources from taxonomy_sectors
* `notebooks/gold/gold_dim_role.ipynb` — Now sources from taxonomy_role_canonical + taxonomy_role_families
* `notebooks/gold/gold_dim_skill.ipynb` — Now sources from taxonomy_skill_catalog

**Key Schema Changes**: All three dimensions now include:
* Natural keys from taxonomy (sector_key, role_key, skill_key)
* Cross-references to taxonomy hierarchy
* Audit timestamps (updated_at, taxonomy_updated_at)

---

## Rollback Procedure

If rollback is needed:

```bash
# 1. Drop taxonomy tables
databricks-sql-cli --execute "
  DROP TABLE IF EXISTS workspace.metadata.taxonomy_skill_catalog;
  DROP TABLE IF EXISTS workspace.metadata.taxonomy_role_canonical;
  DROP TABLE IF EXISTS workspace.metadata.taxonomy_role_families;
  DROP TABLE IF EXISTS workspace.metadata.taxonomy_sectors;
"

# 2. Revert bootstrap.py changes
git checkout HEAD~1 deployment/bootstrap.py

# 3. Re-bootstrap without taxonomy tables
python deployment/bootstrap.py --catalog workspace
```

---

## References

This consolidated guide combines information from three original migration documents:

1. **METADATA_MIGRATION_GUIDE.md** (597 lines) — Complete technical implementation, CSV schemas, dependency analysis, step-by-step deployment
2. **QUICK_DEPLOY_REFERENCE.md** (103 lines) — 3-command quick deploy, verification queries, success indicators
3. **TASK_6_MIGRATION_GUIDE.md** (24 lines) — Gold dimension updates following taxonomy table creation

For the complete original documentation with full implementation details, see the archived files in this directory (if preserved).

---

**Migration Completed**: 2026-06-17  
**Production Ready**: Yes  
**Deployment Validated**: Yes  
**Owner**: Data Engineering Team
