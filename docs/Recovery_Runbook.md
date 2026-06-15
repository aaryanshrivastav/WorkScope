# LMIP Recovery Runbook

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: Platform operators, on-call engineers

---

## Overview

This runbook covers recovery procedures for LMIP platform failures, data quality issues, and operational incidents.

**Recovery Workflow**: `LMIP_Recovery` (manual trigger, PAUSED by default)

---

## Recovery Workflow Architecture

### Purpose

The Recovery workflow provides manual intervention capabilities for:
1. **Backfilling missing data** from specific date ranges
2. **Reprocessing failed batches** after bug fixes
3. **Managing quarantined records** (approve/reject)
4. **Full pipeline rebuilds** after schema changes
5. **Historical data corrections**

### Task Flow

```
Recovery_Bronze_Replay_Backfill
(Replay historical bronze batches for date range)
              ↓
Recovery_Quarantine_Manage (parallel)
(Review and process quarantined records)
              ↓
Recovery_Silver_Reprocess
(Full reprocess mode for silver layer)
              ↓
Recovery_CDC_Reprocess
(Recalculate change data capture)
              ↓
Recovery_Intermediate_Reprocess
(Re-run intermediate enrichment)
              ↓
Recovery_Gold_Rebuild
(Full refresh of gold layer)
              ↓
Recovery_Validation_Report (always runs)
(Generate validation summary report)
```

### Parameters

**Job-Level Parameters** (set when triggering workflow):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | DATE | 2026-06-01 | Beginning of backfill range |
| `end_date` | DATE | 2026-06-07 | End of backfill range |
| `source_filter` | STRING | remotive,arbeitnow | Comma-separated source names |
| `batch_id` | STRING | latest | Specific batch UUID to reprocess |
| `quarantine_action` | STRING | review | review, approve, reject |
| `entity_type` | STRING | all | jobs, skills, companies, all |
| `mode` | STRING | full | incremental or full |

---

## Common Recovery Scenarios

### Scenario 1: API Outage - Missing Bronze Data

**Symptom**: Ingestion failed for specific dates, no bronze records

**Root Cause**: External API downtime (Remotive, Arbeitnow)

**Impact**: Missing job postings in silver/gold layers

**Recovery Steps**:

1. **Verify Missing Dates**
```sql
-- Check for missing ingestion dates
SELECT DISTINCT ingestion_date
FROM bronze.bronze_job_snapshot
WHERE source_name = 'remotive'
  AND ingestion_date BETWEEN '2026-06-01' AND '2026-06-07'
ORDER BY ingestion_date;

-- Find gaps
WITH expected_dates AS (
  SELECT DATE_ADD('2026-06-01', seq) AS expected_date
  FROM RANGE(0, 7)
),
actual_dates AS (
  SELECT DISTINCT ingestion_date AS actual_date
  FROM bronze.bronze_job_snapshot
  WHERE source_name = 'remotive'
)
SELECT e.expected_date
FROM expected_dates e
LEFT JOIN actual_dates a ON e.expected_date = a.actual_date
WHERE a.actual_date IS NULL;
```

2. **Trigger Recovery Workflow**
* Navigate to Workflows → LMIP_Recovery
* Click "Run Now"
* Set parameters:
  * `start_date`: 2026-06-01
  * `end_date`: 2026-06-03 (example: missing dates)
  * `source_filter`: remotive
  * Leave other parameters at defaults

3. **Monitor Execution**
```sql
-- Check recovery run status
SELECT 
  run_id,
  status,
  start_time,
  end_time,
  error_message
FROM audit.audit_pipeline_runs
WHERE pipeline_name = 'LMIP_Recovery'
ORDER BY start_time DESC
LIMIT 5;
```

4. **Validate Backfill**
```sql
-- Verify bronze records created
SELECT 
  ingestion_date,
  COUNT(*) as record_count
FROM bronze.bronze_job_snapshot
WHERE source_name = 'remotive'
  AND ingestion_date BETWEEN '2026-06-01' AND '2026-06-03'
GROUP BY ingestion_date
ORDER BY ingestion_date;

-- Verify silver propagation
SELECT COUNT(*) as new_jobs
FROM silver.silver_jobs_current
WHERE created_at >= '2026-06-01'
  AND source_name = 'remotive';
```

**Expected Outcome**: Bronze records created, silver/gold/reporting automatically updated

**Rollback**: If backfill is incorrect, delete by batch_id:
```sql
DELETE FROM bronze.bronze_job_snapshot
WHERE batch_id = '<recovery_batch_id>';
```

---

### Scenario 2: Data Quality Failures - Quarantined Records

**Symptom**: Records failing DQ validation, landing in quarantine tables

**Root Cause**: 
* API schema changes (new fields, missing fields)
* Invalid data (malformed URLs, wrong date formats)
* Business rule violations (salary_max < salary_min)

**Impact**: Records not progressing to gold/reporting layers

**Recovery Steps**:

1. **Inspect Quarantined Records**
```sql
-- View quarantined jobs
SELECT 
  quarantine_id,
  enterprise_job_id,
  source_name,
  quarantine_reason,
  failed_rule,
  quarantined_at
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
ORDER BY quarantined_at DESC
LIMIT 100;

-- Group by failure reason
SELECT 
  failed_rule,
  COUNT(*) as failure_count
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
GROUP BY failed_rule
ORDER BY failure_count DESC;
```

2. **Decide Action**

**Option A: Approve (data is valid, rule too strict)**
* Trigger recovery with `quarantine_action=approve`
* Records move to silver with override flag

**Option B: Reject (data is invalid)**
* Trigger recovery with `quarantine_action=reject`
* Records permanently marked as rejected

**Option C: Fix and Reprocess**
* Update DQ rules in `/LMIP/notebooks/silver/silver_dq_validate.py`
* Redeploy workflow
* Trigger recovery with `quarantine_action=review` (re-validate)

3. **Trigger Recovery**
* Set `quarantine_action`: approve, reject, or review
* Set `entity_type`: jobs (most common)

4. **Validate Results**
```sql
-- Check quarantine resolution
SELECT 
  quarantine_status,
  COUNT(*) as record_count
FROM quarantine.quarantine_jobs
GROUP BY quarantine_status;

-- Verify approved records in silver
SELECT COUNT(*)
FROM silver.silver_jobs_current
WHERE dq_overall_status = 'OVERRIDE';
```

**Expected Outcome**: Quarantined records either approved (move to silver) or rejected (stay in quarantine)

---

### Scenario 3: Bug Fix - Reprocess Specific Batch

**Symptom**: Bug discovered in transformation logic, affecting specific batches

**Example**: Skill extraction regex incorrect, missing Python mentions

**Impact**: Silver skill mappings incomplete

**Recovery Steps**:

1. **Identify Affected Batches**
```sql
-- Find batches in date range
SELECT DISTINCT batch_id, ingestion_timestamp
FROM bronze.bronze_job_snapshot
WHERE ingestion_date BETWEEN '2026-06-01' AND '2026-06-07'
ORDER BY ingestion_timestamp;
```

2. **Deploy Bug Fix**
* Update notebook code (e.g., `/LMIP/notebooks/silver/silver_skill_extract.py`)
* Commit changes to Git
* Verify fix in dev environment

3. **Trigger Recovery for Specific Batch**
* Set `batch_id`: <affected_batch_uuid>
* Set `mode`: full (forces complete reprocess)
* Set `entity_type`: skills

4. **Validate Fix**
```sql
-- Check skill extraction before fix
SELECT COUNT(*)
FROM silver.silver_skill_mapping
WHERE batch_id = '<old_batch_id>'
  AND skill_name_normalized = 'Python';

-- Check skill extraction after fix
SELECT COUNT(*)
FROM silver.silver_skill_mapping
WHERE batch_id = '<recovery_batch_id>'
  AND skill_name_normalized = 'Python';

-- Should see increase in Python mentions
```

**Expected Outcome**: Affected records reprocessed with corrected logic

---

### Scenario 4: Schema Change - Full Pipeline Rebuild

**Symptom**: Added new column or changed business logic, need historical rebuild

**Example**: Added `remote_type` column, need to populate for all historical records

**Impact**: Historical data missing new column

**Recovery Steps**:

1. **Update Schema**
* Modify contracts: `/LMIP/contracts/silver/silver_jobs_current.yaml`
* Update notebooks to populate new column
* Deploy changes

2. **Test on Small Date Range**
* Trigger recovery with `start_date=2026-06-06`, `end_date=2026-06-07`
* Verify new column populated correctly

3. **Full Rebuild** (if test passes)
* Set `start_date`: <earliest_date_in_bronze>
* Set `end_date`: <current_date>
* Set `mode`: full
* Set `entity_type`: all
* **Warning**: This can take 6+ hours

4. **Monitor Progress**
```sql
-- Check rebuild progress
SELECT 
  DATE(updated_at) as processing_date,
  COUNT(*) as records_processed
FROM silver.silver_jobs_current
WHERE updated_at >= CURRENT_DATE()
GROUP BY DATE(updated_at)
ORDER BY processing_date;
```

**Expected Outcome**: All historical records updated with new column/logic

**Rollback**: If rebuild fails midway, truncate affected tables and re-run

---

### Scenario 5: Downstream Consumer Sync Failure

**Symptom**: Gold layer updated but Supabase not synced

**Root Cause**: Network timeout, Supabase outage, row count mismatch

**Impact**: Dashboards showing stale data

**Recovery Steps**:

1. **Verify Gold Layer Freshness**
```sql
SELECT 
  MAX(created_at) as last_refresh,
  COUNT(*) as total_rows
FROM gold.gold_salary_trends;
```

2. **Check Supabase Sync Status**
```sql
-- Check last successful publish
SELECT 
  run_id,
  status,
  end_time,
  error_message
FROM audit.audit_pipeline_runs
WHERE pipeline_name = 'LMIP_Publishing'
ORDER BY start_time DESC
LIMIT 5;
```

3. **Manual Supabase Sync**
* Navigate to Workflows → LMIP_Publishing
* Click "Run Now"
* No parameters needed (uses latest gold data)

4. **Validate Sync**
* Connect to Supabase Postgres
* Compare row counts:
```sql
-- In Databricks
SELECT COUNT(*) FROM gold.gold_salary_trends;

-- In Supabase
SELECT COUNT(*) FROM gold_salary_trends;
```

**Expected Outcome**: Row counts match, dashboard data refreshed

---

## Recovery Workflow Monitoring

### Real-Time Monitoring

**Databricks Workflows UI**:
1. Navigate to Workflows → LMIP_Recovery
2. Click on active run
3. View task progress, logs, and errors

**SQL Monitoring**:
```sql
-- Current recovery runs
SELECT 
  run_id,
  status,
  start_time,
  ROUND(TIMESTAMPDIFF(MINUTE, start_time, CURRENT_TIMESTAMP()), 2) as runtime_minutes
FROM audit.audit_pipeline_runs
WHERE pipeline_name = 'LMIP_Recovery'
  AND status IN ('RUNNING', 'PENDING')
ORDER BY start_time DESC;
```

### Post-Recovery Validation

**Validation Report** (always generated by last task):
* Location: `dbfs:/databricks/recovery_reports/<run_id>_validation_report.json`
* Contents: Row counts, data quality metrics, errors

**Sample Validation Checks**:
```sql
-- Check record counts by layer
SELECT 'bronze' as layer, COUNT(*) as record_count
FROM bronze.bronze_job_snapshot
WHERE batch_id = '<recovery_batch_id>'
UNION ALL
SELECT 'silver', COUNT(*)
FROM silver.silver_jobs_current
WHERE current_batch_id = '<recovery_batch_id>'
UNION ALL
SELECT 'gold', COUNT(*)
FROM gold.fact_job_postings
WHERE batch_id = '<recovery_batch_id>';

-- Check DQ pass rate
SELECT 
  dq_overall_status,
  COUNT(*) as record_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM silver.silver_jobs_current
WHERE current_batch_id = '<recovery_batch_id>'
GROUP BY dq_overall_status;
```

---

## Rollback Procedures

### Rollback Bronze Layer

**Use Case**: Incorrect backfill, need to delete recovery batch

```sql
-- Delete bronze records by batch_id
DELETE FROM bronze.bronze_job_snapshot
WHERE batch_id = '<recovery_batch_id>';

DELETE FROM bronze.bronze_api_response_log
WHERE batch_id = '<recovery_batch_id>';
```

### Rollback Silver Layer

**Use Case**: CDC errors propagated bad data

```sql
-- Restore from silver_job_changes (audit log)
MERGE INTO silver.silver_jobs_current AS target
USING (
  SELECT enterprise_job_id, old_value_json
  FROM silver.silver_job_changes
  WHERE batch_id = '<recovery_batch_id>'
    AND change_type = 'UPDATE'
) AS source
ON target.enterprise_job_id = source.enterprise_job_id
WHEN MATCHED THEN UPDATE SET *;

-- Delete newly inserted records
DELETE FROM silver.silver_jobs_current
WHERE current_batch_id = '<recovery_batch_id>'
  AND created_at >= CURRENT_DATE();
```

### Rollback Gold Layer

**Use Case**: Full rebuild failed, need to restore from previous snapshot

```sql
-- Use Delta time travel to restore
RESTORE TABLE gold.dim_job_scd2 TO VERSION AS OF <previous_version>;
RESTORE TABLE gold.fact_job_postings TO VERSION AS OF <previous_version>;

-- Find previous version:
DESCRIBE HISTORY gold.dim_job_scd2;
```

### Rollback Gold Layer

**Use Case**: Aggregation logic error

```sql
-- Drop and recreate from gold
DROP TABLE gold.gold_salary_trends;

-- Re-run gold build workflow
-- (Manually trigger LMIP_Gold_Build)
```

---

## Emergency Contacts

**On-Call Engineer**: aaryan.shrivastav1403@gmail.com

**Escalation Path**:
1. Platform Operator (first responder)
2. Data Engineering Lead (if recovery fails)
3. Architecture Team (for major incidents)

**Slack Channels**:
* `#lmip-incidents` - Real-time incident coordination
* `#lmip-support` - General support questions

---

## Post-Incident Review

After every recovery operation:

1. **Document Incident**
   * What happened
   * Root cause
   * Impact (users, tables, date range)
   * Resolution steps
   * Time to recovery

2. **Update Runbook** (if new scenario)
   * Add recovery steps
   * Include validation queries

3. **Improve Monitoring** (if incident was not detected promptly)
   * Add alerts
   * Improve logging

4. **Prevent Recurrence**
   * Fix root cause
   * Add automated tests
   * Update documentation

---

## Best Practices

### Before Recovery

1. **Understand Impact**: Query affected tables to quantify missing/incorrect data
2. **Test on Small Range**: Start with 1-2 days before full backfill
3. **Backup Critical Tables**: Use Delta time travel or CLONE
4. **Schedule During Off-Peak**: Avoid business hours if possible

### During Recovery

1. **Monitor Continuously**: Check workflow UI and logs every 15 minutes
2. **Watch Resource Usage**: Ensure cluster has sufficient resources
3. **Track Progress**: Query record counts periodically
4. **Document Steps**: Keep notes in incident channel

### After Recovery

1. **Validate Data**: Run comprehensive validation queries
2. **Notify Stakeholders**: Email consumers about data refresh
3. **Update Documentation**: Add notes to runbook if new pattern
4. **Schedule Cleanup**: Delete temporary tables, old snapshots

---

## Troubleshooting Recovery Failures

### Issue: Recovery Timeout

**Symptom**: Task times out after 6 hours

**Resolution**:
* Increase task timeout in workflow JSON
* Break date range into smaller chunks (weekly instead of monthly)
* Increase cluster size (more workers)

### Issue: Out of Memory

**Symptom**: "Java heap space" or "OutOfMemoryError"

**Resolution**:
* Reduce batch size in notebook widgets
* Increase executor memory in cluster config
* Use broadcast joins for small dimensions

### Issue: Deadlock

**Symptom**: "Transaction aborted due to conflict"

**Resolution**:
* Ensure no other workflows running in parallel
* Use `OPTIMIZE` before recovery to compact small files
* Retry recovery after cooldown period

---

## References

* **Recovery Workflow Definition**: `/LMIP/workflows/recovery.json`
* **Audit Tables**: `audit.audit_pipeline_runs`, `audit.audit_dq_results`
* **Quarantine Tables**: `quarantine.quarantine_jobs`, `quarantine.quarantine_skills`
* **Monitoring Runbook**: `/LMIP/docs/Monitoring_Runbook.md`

---

**Document Owner**: LMIP Platform Engineering Team  
**Review Frequency**: After each major incident  
**Next Review Date**: 2026-09-07