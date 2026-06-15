# LMIP Pipeline Flow Documentation

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: DevOps engineers, platform operators

---

## Executive Summary

LMIP uses **7 Databricks Workflows** orchestrated via file-arrival triggers to implement an end-to-end data pipeline:
1. Daily_Ingestion (periodic trigger, daily)
2. Silver_Processing (file trigger)
3. Intermediate_Processing (file trigger)
4. Gold_Build (file trigger)
5. Reporting_Build (file trigger)
6. Publishing (file trigger)
7. Recovery (manual, PAUSED)

**End-to-End Latency**: 6-9 hours from ingestion to publishing

---

## Workflow 1: LMIP_Daily_Ingestion

**Purpose**: Ingest job postings from external APIs to Bronze layer

**Trigger**: Periodic (daily at midnight)

**Duration**: 20-30 minutes

**Task Flow**:
```
Ingest_Remotive (→23 jobs, 5-10s)
              ↓
Ingest_Arbeitnow (→~100 jobs, 5-10s)
              ↓
Bronze_Write_API_Log (write API telemetry)
              ↓
Bronze_Write_Job_Snapshot (persist raw payloads)
              ↓
Bronze_Dedupe_Raw_Payload (hash-based dedup)
              ↓
Bronze_Finalize_Batch (mark complete, trigger downstream)
```

**Outputs**:
* `bronze.bronze_job_snapshot`
* `bronze.bronze_api_response_log`
* Trigger file: `dbfs:/databricks/workflows/triggers/bronze_batch_complete`

**Failure Handling**:
* AT_LEAST_ONE_SUCCESS: Pipeline continues if at least one source succeeds
* API timeout → 2 retries with 30s intervals
* Email alert on complete failure

**Recovery**: Reprocess specific dates using `LMIP_Recovery` workflow

---

## Workflow 2: LMIP_Silver_Processing

**Purpose**: Transform raw bronze data into cleansed, standardized silver tables

**Trigger**: File arrival after bronze batch complete

**Duration**: 45-60 minutes

**Task Flow**:
```
Silver_Standardize_Jobs (normalize fields, generate hashes)
              ↓
Silver_Detect_CDC (INSERT/UPDATE/DELETE/RESTORE)
              ↓
Silver_Apply_Soft_Delete_Restore (handle expirations)
              ↓
Silver_DQ_Validate (data quality checks, quarantine routing)
              ↓
      ┌───────┴───────┐
      │ (parallel)    │
Silver_Skill_Extract   Silver_Sector_Assign
      │                │
      └───────┬───────┘
              ↓
Silver_Job_Identity_Map (cross-source dedup)
              ↓
        Write trigger: silver_processing_complete
```

**Key Operations**:
1. **Standardization**: Company name normalization (uppercase, remove legal suffixes), title normalization, location parsing
2. **CDC**: Hash-based change detection (SHA-256 of company+title+description+location)
3. **Soft Delete**: Jobs missing for 7+ days → `soft_delete_flag=true`, `is_active=false`
4. **DQ Validation**: Completeness, uniqueness, referential integrity, format checks
5. **Skill Extraction**: Regex + NLP (LLM optional, disabled by default)
6. **Sector Assignment**: Rule-based + ML (confidence threshold 0.7)

**Outputs**:
* `silver.silver_jobs_current`
* `silver.silver_job_changes`
* `silver.silver_skill_mapping`
* `silver.silver_job_identity_map`

**Failure Handling**:
* CDC failures block downstream processing
* DQ failures route records to `quarantine.quarantine_jobs`
* Low-confidence sector assignments queue for review

**Parameters**:
* `mode`: incremental (default) or full
* `batch_id`: Specific batch to process
* `validation_level`: strict, standard (default), permissive

---

## Workflow 3: LMIP_Intermediate_Processing

**Purpose**: Enrich silver data with canonical entities and intermediate enrichments

**Trigger**: File arrival after silver processing complete

**Duration**: 60-90 minutes

**Task Flow**:
```
      ┌─────────────────────┴─────────────────────┐
      │ (parallel)                              │
Intermediate_Role_Map                  Intermediate_Company_Canonicalize
(title → canonical role)          (company → master entity)
      │                                      │
      └─────────────────┬──────────────────┘
                      ↓
        Intermediate_Sector_Normalize
        (normalize sector assignments)
                      ↓
        Intermediate_Skill_Catalog_Sync
        (sync skills to master catalog)
                      ↓
        Intermediate_Skill_Graph_Build
        (build co-occurrence graph)
                      ↓
        Intermediate_Review_Resolver (runs even if upstream fails)
        (process low-confidence review queue)
```

**Key Operations**:
1. **Role Mapping**: Dictionary → Regex → LLM fallback (optional)
2. **Company Canonicalization**: Exact → Alias → Fuzzy match (Levenshtein threshold 0.85)
3. **Sector Normalization**: Rule-based mapping to master taxonomy
4. **Skill Catalog Sync**: Add new skills to `intermediate.skill_catalog`
5. **Skill Graph**: Build co-occurrence matrix and hierarchies

**Outputs**:
* `intermediate.job_role_map`
* `intermediate.company_map`
* `intermediate.sector_map`
* `intermediate.skill_catalog`
* `intermediate.skill_graph`

**Confidence Thresholds**:
* High confidence (≥0.85): Auto-process
* Medium confidence (0.70-0.84): Auto-process with review flag
* Low confidence (<0.70): Queue for manual review

**Parameters**:
* `confidence_threshold`: 0.7 (default)
* `enable_llm_fallback`: false (default, cost optimization)
* `auto_approve_high_confidence`: true (threshold 0.90)

---

## Workflow 4: LMIP_Gold_Build

**Purpose**: Build dimensional star schema (gold layer) model

**Trigger**: File arrival after intermediate processing complete

**Duration**: 2-3 hours

**Task Flow** (5 phases):

```
Phase 1: Conformed Dimensions (parallel)
  Dim_Date | Dim_Source | Dim_Sector | Dim_Skill | Dim_Role | Dim_Location
                              ↓
Phase 2: Company Dimensions (sequential)
              Dim_Company (depends on Dim_Sector)
                      ↓
              Dim_Company_Alias
                      ↓
Phase 3: SCD2 Job Dimension
              Dim_Job_SCD2 (depends on Phase 1 & 2)
                      ↓
Phase 4: Bridge Tables
              Bridge_Job_Skill
                      ↓
Phase 5: Fact Tables (parallel)
  Fact_Job_Postings | Fact_Job_Lifecycle | Fact_Salary | Fact_Pipeline_Runs
```

**Key Operations**:
1. **Surrogate Key Generation**: Auto-incrementing BIGINT keys
2. **SCD Type 2**: Job dimension tracks history (effective_start_date, effective_end_date, is_current)
3. **Fact Grain**: Job postings = one row per job per posting event
4. **Bridge Table**: Many-to-many job ↔ skill relationships

**Outputs**:
* 9 dimension tables
* 4 fact tables
* 1 bridge table

**Dependencies**:
* dim_company requires dim_sector
* dim_company_alias requires dim_company
* dim_job_scd2 requires all Phase 1 & 2 dims
* Facts require respective dimensions

**SCD Type 2 Logic**:
* When job attributes change (title, location, company), new row inserted
* Previous row's `effective_end_date` set to change date
* Previous row's `is_current` set to false
* Enables historical analysis ("What was this job's title last month?")

---

## Workflow 5: LMIP_Reporting_Build

**Purpose**: Pre-aggregate business intelligence marts for analytics for dashboard consumption

**Trigger**: File arrival after gold build complete

**Duration**: 2-3 hours

**Task Flow** (3 phases):

```
Phase 1: Core Analytics (parallel)
  Reporting_Salary_Trends | Reporting_Skill_Demand | Reporting_Hiring_Trends | 
  Reporting_Company_Hiring | Reporting_Location_Trends | Reporting_Sector_Overview
                      ↓
Phase 2: Operational Monitoring
              Reporting_Pipeline_Health (runs even if upstream fails)
                      ↓
Phase 3: Industry-Specific (parallel)
  Reporting_Company_Activity | Reporting_Hiring_Activity | Reporting_Skill_Demand_By_Sector
```

**Key Operations**:
1. **Salary Trends**: Percentile calculations (P25/P50/P75/P90), MoM/QoQ changes
2. **Skill Demand**: Co-occurrence rankings, skill velocity (week-over-week %)
3. **Hiring Trends**: 7-day moving average of new postings, WoW comparisons
4. **Multiple Grain Levels**: Total → Sector → Role → Location (NULL dims = rollup)

**Outputs**:
* 6 core analytics tables
* 1 operational table
* 3 sector-aware analytics tables

**Performance Optimizations**:
* Pre-computed aggregations (avoid expensive joins at query time)
* Partitioned by date, Z-ordered by common filters
* Target query performance: <2 seconds for dashboards

---

## Workflow 6: LMIP_Publishing

**Purpose**: Export gold layer data to external consumer systems

**Trigger**: File arrival after gold build complete

**Duration**: 1-2 hours

**Task Flow**:
```
Publish_CSV_Snapshot_Export (export to Unity Catalog Volumes)
              ↓
Publish_Manifest_Write (generate schema manifests)
              ↓
Publish_Load_Order_Check (validate FK dependencies)
              ↓
Publish_Supabase_Upsert (sync to Supabase Postgres)
```

**Key Operations**:
1. **CSV Export**: Gzipped CSV files in `/Volumes/workspace/publish/snapshots/`
2. **Manifest**: JSON schema definitions with version info and checksums
3. **Load Order**: Validate parent tables loaded before children (FK constraints)
4. **Supabase Sync**: Full upsert (DELETE + INSERT) for simplicity

**Outputs**:
* CSV snapshots: `<table_name>_<YYYYMMDD>_<HHmm>.csv.gz`
* Manifests: `<table_name>_manifest.json`
* Supabase tables: Real-time queryable Postgres

**Retry Logic**:
* CSV export: 2 retries
* Supabase sync: 3 retries with exponential backoff (180s intervals)
* Email alerts on success AND failure

---

## Workflow 7: LMIP_Recovery

**Purpose**: Manual recovery and backfill workflow for data quality issues

**Trigger**: Manual/On-demand (PAUSED by default)

**Duration**: 3-6 hours (depends on date range)

**Parameters** (job-level):
* `start_date`: Beginning of backfill range (default: 2026-06-01)
* `end_date`: End of backfill range (default: 2026-06-07)
* `source_filter`: Comma-separated sources (default: remotive,arbeitnow)
* `batch_id`: Specific batch to reprocess (default: latest)
* `quarantine_action`: review, approve, reject (default: review)
* `entity_type`: jobs, skills, companies, all (default: all)

**Task Flow**:
```
Recovery_Bronze_Replay_Backfill (replay historical bronze batches)
              ↓
Recovery_Quarantine_Manage (parallel: manage quarantined records)
              ↓
Recovery_Silver_Reprocess (full reprocess mode)
              ↓
Recovery_CDC_Reprocess (recalculate CDC)
              ↓
Recovery_Intermediate_Reprocess (re-run intermediate enrichment)
              ↓
Recovery_Gold_Rebuild (full refresh)
              ↓
Recovery_Validation_Report (always runs, generates summary)
```

**Use Cases**:
1. Backfill missing dates due to API outage
2. Reprocess failed batches after bug fix
3. Recover quarantined records after data quality rule update
4. Full pipeline re-run after schema changes
5. Historical data corrections

**Idempotency**: All operations are safe to re-run (Delta merge, CREATE OR REPLACE)

**Monitoring**: Validation report always generated (run_if: ALL_DONE)

---

## Trigger Mechanism

### File Arrival Triggers

Workflows trigger each other via empty marker files:

| Trigger File Path | Triggered Workflow |
|-------------------|--------------------|
| `dbfs:/databricks/workflows/triggers/bronze_batch_complete` | LMIP_Silver_Processing |
| `dbfs:/databricks/workflows/triggers/silver_processing_complete` | LMIP_Intermediate_Processing |
| `dbfs:/databricks/workflows/triggers/inter_processing_complete` | LMIP_Gold_Build |
| `dbfs:/databricks/workflows/triggers/gold_build_complete` | LMIP_Reporting_Build |
| `dbfs:/databricks/workflows/triggers/gold_build_complete` | LMIP_Publishing |

**Implementation**:
```python
# Last notebook in each workflow
dbutils.fs.put(
    "dbfs:/databricks/workflows/triggers/<next_stage>_complete",
    "",
    overwrite=True
)
```

**Min Time Between Triggers**: 3600 seconds (1 hour) to prevent rapid re-triggering

---

## SLA & Performance Targets

| Workflow | Target Duration | Max Timeout | Critical Path |
|----------|----------------|-------------|---------------|
| Daily_Ingestion | 20-30 min | 2 hours | Bronze writes |
| Silver_Processing | 45-60 min | 3 hours | CDC + Identity mapping |
| Intermediate_Processing | 60-90 min | 4 hours | Skill graph build |
| Gold_Build | 2-3 hours | 5 hours | Dim_Job_SCD2 + Facts |
| Gold_Build | 2-3 hours | 4 hours | Core analytics |
| Publishing | 1-2 hours | 3 hours | CSV export + Supabase sync |
| Recovery | 3-6 hours | 6 hours | Full pipeline reprocess |

**End-to-End Pipeline**: Daily ingestion → Publishing = **6-9 hours**

---

## Retry & Error Handling Strategy

### Retry Configuration by Layer

| Layer | Max Retries | Retry Interval | Retry on Timeout |
|-------|-------------|----------------|------------------|
| **Ingestion (API)** | 2 | 30s | Yes |
| **Bronze** | 1-2 | 60s | No |
| **Silver** | 2 | 60s | No |
| **Intermediate** | 2 | 120s | No (LLM timeouts) |
| **Gold** | 2 | Standard | No |
| **Reporting** | 2 | 120s | No |
| **Publishing** | 3 | 180s | Yes (Supabase only) |
| **Recovery** | 1-2 | Standard | No |

### Error Notification Strategy

**Email Alerts**:
* **Daily_Ingestion**: on_failure only
* **Silver/Intermediate/Gold/Reporting**: on_failure only
* **Publishing**: on_success AND on_failure
* **Recovery**: on_start, on_success, AND on_failure

**Alert Recipients**: aaryan.shrivastav1403@gmail.com

**Future Enhancements**: Slack webhooks, PagerDuty integration

---

## Monitoring Queries

### Check Workflow Status

```sql
-- View recent workflow runs
SELECT 
  run_id,
  pipeline_name,
  status,
  start_time,
  end_time,
  ROUND((UNIX_TIMESTAMP(end_time) - UNIX_TIMESTAMP(start_time)) / 60, 2) as runtime_minutes,
  rows_written,
  error_message
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY start_time DESC;
```

### Check Data Freshness

```sql
-- Check last ingestion per layer
SELECT 
  'bronze' as layer,
  MAX(ingestion_timestamp) as last_updated,
  ROUND(TIMESTAMPDIFF(HOUR, MAX(ingestion_timestamp), CURRENT_TIMESTAMP()), 2) as hours_stale
FROM bronze.bronze_job_snapshot
UNION ALL
SELECT 
  'silver',
  MAX(updated_at),
  ROUND(TIMESTAMPDIFF(HOUR, MAX(updated_at), CURRENT_TIMESTAMP()), 2)
FROM silver.silver_jobs_current
UNION ALL
SELECT 
  'gold',
  MAX(created_at),
  ROUND(TIMESTAMPDIFF(HOUR, MAX(created_at), CURRENT_TIMESTAMP()), 2)
FROM gold.gold_salary_trends;
```

### Check DQ Pass Rate

```sql
-- Data quality validation results
SELECT 
  batch_id,
  COUNT(*) as total_records,
  SUM(CASE WHEN dq_overall_status = 'PASS' THEN 1 ELSE 0 END) as passed,
  SUM(CASE WHEN dq_overall_status = 'FAIL' THEN 1 ELSE 0 END) as failed,
  ROUND(100.0 * SUM(CASE WHEN dq_overall_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate_pct
FROM silver.silver_jobs_current
GROUP BY batch_id
ORDER BY batch_id DESC
LIMIT 10;
```

---

## Troubleshooting Common Issues

### Issue 1: Workflow Not Triggering

**Symptom**: Silver workflow doesn't start after bronze completes

**Root Causes**:
1. Trigger file not written (check last notebook in bronze workflow)
2. Min time between triggers not elapsed (check `min_time_between_triggers_seconds`)
3. Workflow paused (check trigger `pause_status`)

**Resolution**:
```bash
# Manually create trigger file
dbutils.fs.put(
    "dbfs:/databricks/workflows/triggers/bronze_batch_complete",
    "",
    overwrite=True
)
```

### Issue 2: CDC Detecting False Changes

**Symptom**: `silver_job_changes` shows UPDATE events with no actual changes

**Root Cause**: Hash calculation includes whitespace or timestamp fields

**Resolution**: Normalize fields before hashing (trim, lowercase, remove special chars)

### Issue 3: Supabase Sync Timeout

**Symptom**: Publishing workflow fails at Supabase_Upsert task

**Root Causes**:
1. Network latency to Supabase endpoint
2. Large batch size (>10K rows)
3. Supabase rate limiting

**Resolution**:
1. Reduce batch size in `publish_supabase_upsert` notebook
2. Increase timeout from 3600s to 7200s
3. Add exponential backoff retry logic

### Issue 4: Out-of-Order Execution

**Symptom**: Gold build starts before intermediate processing completes

**Root Cause**: Trigger file written prematurely

**Resolution**: Ensure trigger file is written only in last cell of last notebook

---

## Best Practices

### Notebook Development

1. **Idempotency**: Use MERGE instead of INSERT, CREATE OR REPLACE instead of CREATE
2. **Parameterization**: All notebooks accept widgets for batch_id, mode, etc.
3. **Logging**: Log start/end of each major operation
4. **Error Handling**: Try/catch with detailed error messages
5. **Testing**: Test with `mode=full` on small date range before production

### Workflow Configuration

1. **Timeouts**: Set task timeout to 2-3x expected duration
2. **Retries**: Enable retries for transient failures (API calls, network)
3. **Email Alerts**: Configure on_failure for all workflows
4. **Max Concurrent Runs**: Set to 1 to prevent overlapping executions
5. **Queue**: Enable job queueing to handle backlog

### Performance Optimization

1. **Partition Pruning**: Always filter on partition columns (date)
2. **Broadcast Joins**: Use broadcast hint for small dimensions
3. **Z-Ordering**: Apply to high-cardinality filter columns
4. **OPTIMIZE**: Run weekly on all Delta tables
5. **VACUUM**: Run monthly (retain 30 days for time travel)

---

## References

* **Workflow Definitions**: `/LMIP/workflows/*.json`
* **Workflow Dependency Graph**: `/LMIP/workflows/workflow_dependency_graph.md`
* **Notebook Documentation**: `/LMIP/notebooks/<layer>/README_<LAYER>.md`
* **Recovery Procedures**: `/LMIP/docs/Recovery_Runbook.md`
* **Monitoring Procedures**: `/LMIP/docs/Monitoring_Runbook.md`

---

**Document Owner**: LMIP Platform Engineering Team  
**Review Frequency**: Quarterly  
**Next Review Date**: 2026-09-07