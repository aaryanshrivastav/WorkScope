# LMIP Publishing Layer Documentation

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: Platform operators, consumer integration teams

---

## Executive Summary

The Publishing layer distributes gold-layer analytics to external consumer systems via:
1. **CSV Snapshots** - Compressed files in Unity Catalog Volumes
2. **Supabase Postgres** - Real-time queryable database
3. **Schema Manifests** - JSON metadata for schema validation

**Publishing Workflow**: Runs after gold build completion, takes 1-2 hours

---

## Architecture

### Publishing Pipeline

```
Gold Layer (workspace.gold.*)
      ↓
Publish_CSV_Snapshot_Export
  → Compress to gzip
  → Write to /Volumes/workspace/publish/snapshots/
  → Generate MD5 checksums
      ↓
Publish_Manifest_Write
  → Generate JSON schema definitions
  → Include version info, checksums
  → Write to /Volumes/workspace/publish/manifests/
      ↓
Publish_Load_Order_Check
  → Validate FK dependencies
  → Ensure parent tables loaded before children
      ↓
Publish_Supabase_Upsert
  → Connect to Supabase Postgres
  → Full upsert (DELETE + INSERT)
  → Batch processing (1000 rows/batch)
  → Verify row counts
```

---

## CSV Export Format

### File Naming Convention

```
<table_name>_<YYYYMMDD>_<HHmm>.csv.gz
```

**Examples**:
* `gold_salary_trends_20260607_1430.csv.gz`
* `gold_skill_demand_20260607_1430.csv.gz`

### CSV Structure

* **Delimiter**: Comma (`,`)
* **Header Row**: Yes (column names)
* **Encoding**: UTF-8
* **Compression**: gzip (level 6)
* **Null Representation**: Empty string
* **Date Format**: `YYYY-MM-DD`
* **Timestamp Format**: `YYYY-MM-DD HH:mm:ss`
* **Boolean**: `true`/`false`

### Storage Location

**Unity Catalog Volume Path**:
```
/Volumes/workspace/publish/snapshots/<YYYY>/<MM>/<DD>/<table_name>_<timestamp>.csv.gz
```

**Example**:
```
/Volumes/workspace/publish/snapshots/2026/06/07/gold_salary_trends_20260607_1430.csv.gz
```

---

## Schema Manifests

### Manifest Format (JSON)

```json
{
  "table_name": "gold_salary_trends",
  "export_timestamp": "2026-06-07T14:30:15Z",
  "file_path": "/Volumes/workspace/publish/snapshots/2026/06/07/gold_salary_trends_20260607_1430.csv.gz",
  "file_size_bytes": 524288,
  "row_count": 5432,
  "checksum_md5": "a1b2c3d4e5f6...",
  "schema_version": "1.0",
  "columns": [
    {
      "name": "salary_trend_sk",
      "type": "BIGINT",
      "nullable": false,
      "description": "Surrogate key"
    },
    {
      "name": "salary_date_sk",
      "type": "INT",
      "nullable": false,
      "description": "Date in YYYYMMDD format"
    },
    ...
  ],
  "dependencies": [
    "workspace.gold.dim_date",
    "workspace.gold.dim_sector"
  ]
}
```

### Manifest Storage

```
/Volumes/workspace/publish/manifests/<table_name>_manifest.json
```

---

## Supabase Integration

### Connection Configuration

**Secret Scope**: `lmip-superset`

**Secrets**:
* `superset-db-connection-string` - Postgres connection URL
* `superset-api-token` - Supabase API token

**Connection String Format**:
```
postgresql://<user>:<password>@<host>:<port>/<database>?sslmode=require
```

### Sync Strategy

**Method**: Full Upsert

**Rationale**: Simplicity over incremental complexity; gold tables are small (<10K rows)

**Steps**:
1. **Truncate**: `DELETE FROM <table_name>`
2. **Insert**: `COPY FROM` or batched `INSERT` (1000 rows/batch)
3. **Verify**: Compare row counts
4. **Commit**: Atomic transaction

### Table Mapping

Databricks tables are synced to Supabase with same names:

| Databricks Table | Supabase Table |
|------------------|----------------|
| `workspace.gold.gold_salary_trends` | `public.gold_salary_trends` |
| `workspace.gold.gold_skill_demand` | `public.gold_skill_demand` |
| `workspace.gold.gold_hiring_trends` | `public.gold_hiring_trends` |
| `workspace.gold.gold_company_hiring` | `public.gold_company_hiring` |
| `workspace.gold.gold_location_trends` | `public.gold_location_trends` |
| `workspace.gold.gold_sector_overview` | `public.gold_sector_overview` |

### Performance Considerations

* **Batch Size**: 1000 rows per batch
* **Network Timeout**: 60 seconds per batch
* **Retry Logic**: 3 retries with exponential backoff (180s intervals)
* **Parallelization**: One table at a time (sequential)

---

## Load Order Validation

### Dependency Graph

Publish tables in dependency order to respect FK constraints:

```
Dimensions (no dependencies)
  → gold_sector_overview
  → gold_location_trends

Facts (depend on dimensions)
  → gold_salary_trends
  → gold_skill_demand
  → gold_hiring_trends
  → gold_company_hiring

Aggregates (depend on facts)
  → gold_hiring_activity
  → gold_skill_demand_by_sector
  → gold_company_activity
```

### Validation Logic

```python
# Check if parent tables exist and have data
for table in tables_to_publish:
    for parent in table.dependencies:
        if not table_exists(parent):
            raise ValueError(f"Parent table {parent} does not exist")
        if get_row_count(parent) == 0:
            raise ValueError(f"Parent table {parent} is empty")
```

---

## Consumer Access Patterns

### CSV Consumption

**Use Cases**:
* Bulk downloads for local analysis
* Data warehouse ingestion
* Archival and compliance

**Access Methods**:
1. **Direct Volume Access** (Databricks users only)
2. **Presigned URLs** (external consumers, future)
3. **SFTP/S3 export** (future)

**Example** (PySpark):
```python
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("/Volumes/workspace/publish/snapshots/2026/06/07/gold_salary_trends_20260607_1430.csv.gz")
```

### Supabase Consumption

**Use Cases**:
* Real-time dashboard queries
* API endpoints for web/mobile apps
* Low-latency analytics

**Access Methods**:
1. **Direct SQL** (Postgres clients)
2. **Supabase REST API**
3. **Supabase GraphQL API**

**Example** (Python + psycopg2):
```python
import psycopg2

conn = psycopg2.connect(connection_string)
cur = conn.cursor()

cur.execute("""
    SELECT sector_name, salary_p50, observation_count
    FROM gold_salary_trends
    WHERE salary_date_sk >= 20260601
    ORDER BY salary_p50 DESC
    LIMIT 10
""")

results = cur.fetchall()
```

---

## Monitoring & Alerts

### Success Criteria

**Publishing workflow succeeds if**:
1. All CSV exports complete without errors
2. All manifests generated successfully
3. Load order validation passes
4. Supabase sync completes with matching row counts
5. No checksum mismatches

### Email Alerts

**Recipients**: aaryan.shrivastav1403@gmail.com

**Alert Triggers**:
* **On Success**: Email with summary (row counts, file sizes, duration)
* **On Failure**: Email with error details and failed task

**Alert Content**:
```
Subject: [LMIP] Publishing Workflow - SUCCESS/FAILURE

Workflow: LMIP_Publishing
Status: SUCCESS
Duration: 1h 23m
Tables Published: 9
Total Rows: 45,231
Total Size: 12.5 MB (compressed)

Details:
- gold_salary_trends: 5,432 rows, 2.1 MB
- gold_skill_demand: 8,765 rows, 3.4 MB
- ...

Supabase Sync: SUCCESS
- All tables synced successfully
- Row count verification passed

Next Steps: None (workflow completed successfully)
```

### Monitoring Queries

```sql
-- Check last successful publish
SELECT 
  MAX(run_id) as last_run_id,
  MAX(end_time) as last_publish_time,
  TIMESTAMPDIFF(HOUR, MAX(end_time), CURRENT_TIMESTAMP()) as hours_since_publish
FROM audit.audit_pipeline_runs
WHERE pipeline_name = 'LMIP_Publishing'
  AND status = 'SUCCESS';

-- Check file counts in volumes
SELECT 
  COUNT(*) as file_count,
  SUM(size) / 1024 / 1024 as total_size_mb,
  MAX(modification_time) as latest_file
FROM dbutils.fs.ls('/Volumes/workspace/publish/snapshots/')
WHERE path LIKE '%.csv.gz';
```

---

## Troubleshooting

### Issue 1: CSV Export Timeout

**Symptom**: Publish_CSV_Snapshot_Export task times out

**Root Causes**:
1. Large table size (>1M rows)
2. Complex data types (nested structs, arrays)
3. Slow disk I/O

**Resolution**:
1. Increase task timeout to 7200s
2. Partition export by date range
3. Use Parquet instead of CSV for large tables (future)

### Issue 2: Supabase Row Count Mismatch

**Symptom**: Databricks row count != Supabase row count after sync

**Root Causes**:
1. Partial batch failure (transaction not rolled back)
2. Network timeout during COPY
3. Duplicate key violations

**Resolution**:
1. Wrap sync in transaction (BEGIN/COMMIT)
2. Add retry logic with full rollback
3. Verify primary keys before upsert

### Issue 3: Checksum Mismatch

**Symptom**: Manifest checksum != actual file checksum

**Root Causes**:
1. File modified after manifest generation
2. Gzip compression level mismatch
3. Encoding issues (UTF-8 vs ASCII)

**Resolution**:
1. Generate manifest AFTER file write completes
2. Use consistent gzip level (6)
3. Enforce UTF-8 encoding in all steps

---

## Security & Access Control

### Unity Catalog Volumes

**Permissions**:
* Publishing workflow: READ WRITE
* External consumers: READ ONLY (via presigned URLs, future)
* Data engineers: READ WRITE

**Volume Path**:
```
/Volumes/workspace/publish/
  snapshots/
  manifests/
```

### Supabase Access

**Database Roles**:
* `lmip_publisher`: Write access (used by publishing workflow)
* `lmip_consumer`: Read-only access (for dashboards, APIs)

**Row-Level Security** (RLS):
* Not currently implemented
* Future: Filter by geographic region or company

### Secret Management

**Databricks Secret Scopes**:
* `lmip-superset`: Supabase credentials

**Secret Rotation**:
* Quarterly rotation of Supabase tokens
* Use Databricks CLI: `databricks secrets put --scope lmip-superset --key superset-api-token`

---

## Future Enhancements

### Short-Term (3 months)
1. **Presigned URLs**: Generate time-limited URLs for external CSV downloads
2. **Delta Sharing**: Share gold tables via Delta Sharing protocol
3. **Incremental Sync**: Switch from full upsert to CDC-based incremental

### Medium-Term (6 months)
1. **API Gateway**: REST API for real-time queries
2. **Caching Layer**: Redis cache for hot queries
3. **Data Catalog**: Expose manifests via Unity Catalog REST API

### Long-Term (12 months)
1. **Multi-Tenant Publishing**: Separate outputs per client
2. **Custom Export Formats**: Parquet, Avro, JSON
3. **Push Notifications**: Webhook callbacks when data refreshes

---

## References

* **Publishing Workflow**: `/LMIP/workflows/publishing.json`
* **Notebook Documentation**: `/LMIP/notebooks/publish/README.md`
* **Consumer Bootstrap Guide**: `/LMIP/docs/Consumer_Bootstrap.md`
* **Supabase Documentation**: https://supabase.com/docs

---

**Document Owner**: LMIP Platform Engineering Team  
**Review Frequency**: Quarterly  
**Next Review Date**: 2026-09-07