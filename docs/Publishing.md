# LMIP Publishing Layer & Export Specification

**Document Version**: 1.0  
**Last Updated**: 2026-06-20  
**Target Audience**: Data engineers, platform operators, and data consumers

---

## 1. Overview & Architecture

The **Publishing Layer** distributes transformed analytics, Kimball star schema tables, and pre-aggregated reporting metrics to external consumer systems and storage targets via:

1. **Compressed CSV Export Bundles**: Written to Databricks Unity Catalog Volumes (`/Volumes/workspace/publish/snapshots/`).
2. **Schema Manifests**: JSON metadata containing SHA256/MD5 checksums, row counts, and column definitions.
3. **Supabase Postgres Database**: Queryable PostgreSQL interface for web apps and external APIs.

### Publishing Pipeline Flow

```
Gold & Reporting Tables (workspace.gold.*, workspace.reporting.*)
                      │
                      ▼
     1. Publish_CSV_Snapshot_Export
        ├── Compress to gzip (level 6)
        ├── Write to Unity Catalog Volume
        └── Calculate MD5 / SHA256 checksums
                      │
                      ▼
     2. Publish_Manifest_Write
        ├── Generate bundle manifest.json
        └── Record file sizes, row counts, and column metadata
                      │
                      ▼
     3. Publish_Load_Order_Check
        ├── Validate Foreign Key dependencies
        └── Verify Phase 1 (Dimensions) before Phase 2 (Facts/Marts)
                      │
                      ▼
     4. Publish_Supabase_Upsert
        ├── Connect to Supabase Postgres instance
        ├── Execute batch upserts (1,000 rows/batch)
        └── Log execution in publish_export_log
```

---

## 2. Export Order & Dependency Graph

To maintain referential integrity in downstream databases (e.g. Supabase Postgres), exports follow a strict 2-phase load graph:

```
Phase 1: Dimensions (No FK Dependencies)
├── dim_sector
├── dim_source
├── dim_company
├── dim_location
├── dim_role
└── dim_skill

Phase 2: Facts & Reporting Marts (Depends on Phase 1)
├── gold_fact_job_postings   ──► (dim_job, dim_company, dim_role, dim_sector, dim_location)
├── gold_fact_salary         ──► (dim_company, dim_role, dim_sector, dim_location)
├── reporting_salary_trends  ──► (dim_sector, dim_role, dim_location, dim_company)
├── reporting_skill_demand   ──► (dim_sector, dim_role, dim_location, dim_skill)
└── reporting_company_hiring ──► (dim_sector, dim_company, dim_location)
```

### Execution Rules
- **Sequential Phase Execution**: Phase 1 dimensions must complete before Phase 2 facts/marts begin.
- **Parallel Export**: Tables within the same phase export concurrently.
- **Atomic Batch**: Export bundles succeed or fail as an entire atomic unit.

---

## 3. CSV File Specification & Volume Paths

### File Naming Convention
```
<table_name>_<YYYYMMDD>_<HHmm>.csv.gz
```

### CSV Format Standards
- **Delimiter**: Comma (`,`)
- **Header**: Included on row 1
- **Encoding**: UTF-8
- **Compression**: gzip (level 6)
- **Null Representation**: Empty string (`""`)
- **Date Format**: `YYYY-MM-DD`
- **Timestamp Format**: `YYYY-MM-DD HH:mm:ss`
- **Boolean Format**: `true` / `false`

### Volume Directory Structure
```
/Volumes/workspace/publish/snapshots/<YYYY>/<MM>/<DD>/<table_name>_<timestamp>.csv.gz
```

---

## 4. Manifest JSON Schema Specification

Every export bundle generates a standardized `manifest.json` at the volume root and logs to `publish.publish_manifest`:

```json
{
  "bundle_id": "bundle_20260620_143000",
  "export_timestamp": "2026-06-20T14:30:00Z",
  "version": "1.0",
  "tables": [
    {
      "table_name": "reporting_salary_trends",
      "file_path": "/Volumes/workspace/publish/snapshots/2026/06/20/reporting_salary_trends_20260620_1430.csv.gz",
      "file_size_bytes": 524288,
      "row_count": 5432,
      "checksum_md5": "a1b2c3d4e5f67890123456789abcdef0",
      "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "columns": [
        {"name": "sector_key", "type": "STRING", "nullable": false},
        {"name": "avg_salary", "type": "DOUBLE", "nullable": true}
      ]
    }
  ]
}
```

---

## 5. Consumer Tools & Scripts

Scripts for exporting and consuming bundles are located in `publish/scripts/`:

- **`publish/scripts/export_bundle.py`**: Databricks notebook / script to export CSV bundles and write `manifest.json`.
- **`publish/scripts/load_bundle.py`**: Standalone consumer loader script to download and import CSV bundles into local Postgres or SQLite without Databricks.
- **`publish/scripts/load_dimensions.sql`**: DDL script for creating dimension tables in consumer databases.
- **`publish/scripts/load_facts.sql`**: DDL script for creating fact and reporting tables in consumer databases.

See [publish/README.md](../publish/README.md) for usage documentation.