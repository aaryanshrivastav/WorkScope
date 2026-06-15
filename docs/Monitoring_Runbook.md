# LMIP Monitoring Runbook

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: Platform operators, SREs, on-call engineers

---

## Overview

This runbook provides monitoring procedures, alert definitions, and troubleshooting steps for LMIP platform operations.

**Monitoring Layers**:
1. Workflow execution status
2. Data freshness and completeness
3. Data quality metrics
4. Resource utilization
5. External API health

---

## Key Metrics & SLAs

### Workflow Execution SLAs

| Workflow | Target Duration | Max Timeout | SLA |
|----------|----------------|-------------|-----|
| Daily_Ingestion | 20-30 min | 2 hours | <2 hours |
| Silver_Processing | 45-60 min | 3 hours | <3 hours |
| Intermediate_Processing | 60-90 min | 4 hours | <4 hours |
| Gold_Build | 2-3 hours | 5 hours | <5 hours |
| Gold_Build | 2-3 hours | 4 hours | <4 hours |
| Publishing | 1-2 hours | 3 hours | <3 hours |
| **End-to-End** | 6-9 hours | 12 hours | <12 hours |

### Data Freshness SLAs

| Layer | SLA | Alert Threshold |
|-------|-----|----------------|
| Bronze | <24 hours | >30 hours |
| Silver | <25 hours | >32 hours |
| Gold | <28 hours | >36 hours |
| Gold | <30 hours | >40 hours |
| Published (Supabase) | <32 hours | >48 hours |

### Data Quality Targets

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| DQ Pass Rate | >95% | <90% |
| Quarantine Rate | <5% | >10% |
| CDC Accuracy | >99% | <95% |
| Skill Extraction Confidence | >0.75 | <0.60 |
| Sector Assignment Confidence | >0.70 | <0.55 |

---

## Daily Health Check (15 minutes)

Perform these checks every morning:

### Step 1: Workflow Status Check (5 min)

```sql
-- Check last 24 hours of workflow runs
SELECT 
  pipeline_name,
  status,
  start_time,
  end_time,
  ROUND(TIMESTAMPDIFF(MINUTE, start_time, end_time), 2) as runtime_minutes,
  error_message
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
ORDER BY start_time DESC;

-- Expected result: All workflows SUCCESS
-- Alert if: Any workflow FAILED or runtime > SLA
```

### Step 2: Data Freshness Check (5 min)

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
  MAX(posting_timestamp),
  ROUND(TIMESTAMPDIFF(HOUR, MAX(posting_timestamp), CURRENT_TIMESTAMP()), 2)
FROM gold.fact_job_postings
UNION ALL
SELECT 
  'gold',
  MAX(created_at),
  ROUND(TIMESTAMPDIFF(HOUR, MAX(created_at), CURRENT_TIMESTAMP()), 2)
FROM gold.gold_salary_trends;

-- Expected result: All layers <24 hours stale
-- Alert if: Any layer >30 hours stale
```

### Step 3: Data Quality Check (5 min)

```sql
-- Check DQ pass rate for last batch
WITH latest_batch AS (
  SELECT MAX(current_batch_id) as batch_id
  FROM silver.silver_jobs_current
)
SELECT 
  dq_overall_status,
  COUNT(*) as record_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM silver.silver_jobs_current
WHERE current_batch_id = (SELECT batch_id FROM latest_batch)
GROUP BY dq_overall_status;

-- Expected result: PASS >95%
-- Alert if: PASS <90% or FAIL >10%

-- Check quarantine backlog
SELECT 
  quarantine_status,
  COUNT(*) as record_count
FROM quarantine.quarantine_jobs
GROUP BY quarantine_status;

-- Expected result: PENDING <100
-- Alert if: PENDING >500
```

---

## Alert Definitions

### Critical Alerts (Page On-Call)

#### Alert 1: Workflow Failure

**Trigger**: Any workflow status = FAILED

**Query**:
```sql
SELECT COUNT(*)
FROM audit.audit_pipeline_runs
WHERE status = 'FAILED'
  AND start_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;
```

**Threshold**: >= 1

**Action**: Investigate error_message, check Recovery Runbook

#### Alert 2: Data Freshness SLA Breach

**Trigger**: Any layer >36 hours stale

**Query**:
```sql
SELECT 
  TIMESTAMPDIFF(HOUR, MAX(ingestion_timestamp), CURRENT_TIMESTAMP()) as hours_stale
FROM bronze.bronze_job_snapshot;
```

**Threshold**: >= 36 hours

**Action**: Check workflow trigger chain, verify API health

#### Alert 3: DQ Pass Rate Drop

**Trigger**: DQ pass rate <90% for current batch

**Query**:
```sql
WITH latest_batch AS (
  SELECT MAX(current_batch_id) as batch_id
  FROM silver.silver_jobs_current
)
SELECT 
  100.0 * SUM(CASE WHEN dq_overall_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
FROM silver.silver_jobs_current
WHERE current_batch_id = (SELECT batch_id FROM latest_batch);
```

**Threshold**: < 90%

**Action**: Review quarantine records, check for API schema changes

### Warning Alerts (Email Only)

#### Alert 4: Workflow Duration Exceeds Target

**Trigger**: Workflow runtime >1.5x target duration

**Query**:
```sql
SELECT 
  pipeline_name,
  TIMESTAMPDIFF(MINUTE, start_time, end_time) as runtime_minutes
FROM audit.audit_pipeline_runs
WHERE end_time >= CURRENT_TIMESTAMP() - INTERVAL 2 HOURS
  AND status = 'SUCCESS'
  AND (
    (pipeline_name = 'LMIP_Daily_Ingestion' AND TIMESTAMPDIFF(MINUTE, start_time, end_time) > 45) OR
    (pipeline_name = 'LMIP_Silver_Processing' AND TIMESTAMPDIFF(MINUTE, start_time, end_time) > 90) OR
    (pipeline_name = 'LMIP_Gold_Build' AND TIMESTAMPDIFF(MINUTE, start_time, end_time) > 270)
  );
```

**Threshold**: >= 1 row

**Action**: Investigate query performance, check cluster size

#### Alert 5: Quarantine Backlog Growing

**Trigger**: Quarantine PENDING count >500

**Query**:
```sql
SELECT COUNT(*)
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING';
```

**Threshold**: >= 500

**Action**: Review quarantine records, trigger recovery to approve/reject

#### Alert 6: Low Source Coverage

**Trigger**: <2 sources ingesting data

**Query**:
```sql
SELECT COUNT(DISTINCT source_name)
FROM bronze.bronze_job_snapshot
WHERE ingestion_date = CURRENT_DATE();
```

**Threshold**: < 2

**Action**: Check API health for missing sources

---

## Monitoring Dashboards

### Dashboard 1: Pipeline Health Overview

**Refresh**: Every 15 minutes

**Widgets**:
1. **Workflow Status** (last 24 hours)
   * Pie chart: SUCCESS, FAILED, RUNNING counts
2. **Workflow Duration Trend** (last 7 days)
   * Line chart: Runtime by workflow
3. **Data Freshness** (current)
   * KPI cards: Hours since last update per layer
4. **DQ Pass Rate** (last 10 batches)
   * Bar chart: PASS/WARN/FAIL percentages

**SQL**:
```sql
-- Widget 1: Workflow status
SELECT 
  status,
  COUNT(*) as run_count
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
GROUP BY status;

-- Widget 2: Duration trend
SELECT 
  pipeline_name,
  DATE(start_time) as run_date,
  AVG(TIMESTAMPDIFF(MINUTE, start_time, end_time)) as avg_runtime_minutes
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND status = 'SUCCESS'
GROUP BY pipeline_name, DATE(start_time)
ORDER BY run_date, pipeline_name;
```

### Dashboard 2: Data Quality Metrics

**Refresh**: Every hour

**Widgets**:
1. **DQ Pass Rate Trend** (last 30 days)
   * Line chart: Daily pass rate
2. **Quarantine Volume** (last 30 days)
   * Area chart: Quarantine PENDING count over time
3. **Top Failure Reasons** (current)
   * Bar chart: failed_rule counts
4. **Confidence Distribution** (current)
   * Histogram: Skill/sector assignment confidence

**SQL**:
```sql
-- Widget 1: DQ pass rate trend
SELECT 
  DATE(updated_at) as date,
  100.0 * SUM(CASE WHEN dq_overall_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*) as pass_rate
FROM silver.silver_jobs_current
WHERE updated_at >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(updated_at)
ORDER BY date;

-- Widget 3: Top failure reasons
SELECT 
  failed_rule,
  COUNT(*) as failure_count
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
GROUP BY failed_rule
ORDER BY failure_count DESC
LIMIT 10;
```

### Dashboard 3: Resource Utilization

**Refresh**: Every 5 minutes

**Widgets**:
1. **Cluster CPU Usage** (last 1 hour)
   * Line chart: CPU % over time
2. **Cluster Memory Usage** (last 1 hour)
   * Line chart: Memory % over time
3. **Delta Cache Hit Rate** (last 24 hours)
   * KPI card: Cache hit %
4. **Query Duration P95** (last 24 hours)
   * KPI card: 95th percentile query time

**Note**: Use Databricks System Tables for cluster metrics

---

## Troubleshooting Guides

### Issue 1: Workflow Not Starting

**Symptom**: Workflow remains in PENDING state for >1 hour

**Diagnosis**:
1. Check cluster availability
```sql
-- View cluster status (use Databricks CLI or API)
```

2. Check trigger file
```python
# Verify trigger file exists
dbutils.fs.ls("dbfs:/databricks/workflows/triggers/")
```

3. Check workflow pause status
* Navigate to Workflows UI
* Verify trigger is not paused

**Resolution**:
* If cluster down: Start cluster or use auto-scaling
* If trigger missing: Manually create trigger file
* If paused: Un-pause trigger

---

### Issue 2: High Quarantine Rate

**Symptom**: DQ pass rate <90%, many records in quarantine

**Diagnosis**:
1. Identify failure patterns
```sql
SELECT 
  failed_rule,
  COUNT(*) as failure_count,
  MIN(quarantined_at) as first_occurrence
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
GROUP BY failed_rule
ORDER BY failure_count DESC;
```

2. Sample failing records
```sql
SELECT *
FROM quarantine.quarantine_jobs
WHERE failed_rule = '<most_common_failure>'
LIMIT 10;
```

**Root Causes**:
* **API Schema Change**: New fields added/removed
* **Data Format Change**: Date format, currency symbol
* **Business Rule Too Strict**: DQ rule needs relaxation

**Resolution**:
* If API change: Update ingestion/parsing logic
* If format change: Add data normalization step
* If rule too strict: Update DQ rules, approve quarantined records

**See**: Recovery Runbook, Scenario 2

---

### Issue 3: Slow Query Performance

**Symptom**: Workflow tasks taking 2x expected duration

**Diagnosis**:
1. Check query plans
```sql
EXPLAIN EXTENDED
SELECT ...
FROM gold.fact_job_postings
WHERE posting_timestamp >= '2026-06-01';

-- Look for: Full table scans, shuffle operations
```

2. Check table statistics
```sql
DESCRIBE DETAIL gold.fact_job_postings;

-- Check: numFiles, sizeInBytes
-- Alert if: numFiles >10K (small file problem)
```

3. Check partition pruning
```sql
-- Verify partition column in WHERE clause
SELECT COUNT(*)
FROM gold.fact_job_postings
WHERE posting_timestamp >= '2026-06-01';  -- Good: uses partition

SELECT COUNT(*)
FROM gold.fact_job_postings
WHERE job_sk = 12345;  -- Bad: full scan
```

**Resolution**:
* If small files: Run OPTIMIZE on affected tables
```sql
OPTIMIZE gold.fact_job_postings ZORDER BY (sector_sk, company_sk);
```
* If missing partition filter: Update query to include date filter
* If large shuffle: Use broadcast joins for small dimensions

---

### Issue 4: API Rate Limiting

**Symptom**: Ingestion task fails with HTTP 429 errors

**Diagnosis**:
```sql
-- Check API response logs
SELECT 
  source_name,
  http_status_code,
  rate_limit_hit,
  COUNT(*) as request_count
FROM bronze.bronze_api_response_log
WHERE request_timestamp >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
GROUP BY source_name, http_status_code, rate_limit_hit
ORDER BY source_name, http_status_code;
```

**Resolution**:
* Add exponential backoff to API calls
* Reduce request rate (increase sleep time between calls)
* Contact API provider for rate limit increase
* Cache API responses (if allowed by ToS)

---

### Issue 5: Supabase Sync Failure

**Symptom**: Publishing workflow fails at Supabase_Upsert task

**Diagnosis**:
1. Check network connectivity
```python
# Test Supabase connection
import psycopg2
try:
    conn = psycopg2.connect(connection_string)
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

2. Check row count mismatch
```sql
-- In Databricks
SELECT 'databricks' as source, COUNT(*) as row_count
FROM gold.gold_salary_trends
UNION ALL
-- In Supabase (via psycopg2)
SELECT 'supabase', COUNT(*)
FROM gold_salary_trends;
```

**Resolution**:
* If network timeout: Increase batch timeout, reduce batch size
* If row count mismatch: Run full DELETE + INSERT
* If Supabase outage: Wait for resolution, then re-run Publishing workflow

**See**: Recovery Runbook, Scenario 5

---

## Operational Procedures

### Weekly Maintenance (30 minutes)

Perform every Monday morning:

#### 1. Table Optimization (15 min)

```sql
-- Optimize high-traffic tables
OPTIMIZE bronze.bronze_job_snapshot ZORDER BY (source_name, ingestion_date);
OPTIMIZE silver.silver_jobs_current ZORDER BY (updated_at, source_name);
OPTIMIZE gold.fact_job_postings ZORDER BY (posting_timestamp, sector_sk);
OPTIMIZE gold.fact_salary ZORDER BY (observation_date_sk, sector_sk, role_sk);
OPTIMIZE gold.gold_salary_trends ZORDER BY (salary_date_sk, sector_sk);
```

#### 2. Quarantine Review (10 min)

```sql
-- Review and approve/reject pending quarantine records
SELECT 
  failed_rule,
  COUNT(*) as pending_count
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
GROUP BY failed_rule;

-- Trigger recovery with quarantine_action=approve or reject
```

#### 3. Audit Log Archival (5 min)

```sql
-- Archive old audit logs (retain 90 days)
CREATE TABLE IF NOT EXISTS audit.audit_pipeline_runs_archive AS
SELECT *
FROM audit.audit_pipeline_runs
WHERE start_time < CURRENT_DATE() - INTERVAL 90 DAYS;

DELETE FROM audit.audit_pipeline_runs
WHERE start_time < CURRENT_DATE() - INTERVAL 90 DAYS;
```

### Monthly Maintenance (1 hour)

Perform first Monday of each month:

#### 1. VACUUM Old Versions (30 min)

```sql
-- Remove old Delta versions (retain 30 days for time travel)
VACUUM bronze.bronze_job_snapshot RETAIN 720 HOURS;  -- 30 days
VACUUM silver.silver_jobs_current RETAIN 720 HOURS;
VACUUM gold.fact_job_postings RETAIN 720 HOURS;
VACUUM gold.fact_salary RETAIN 720 HOURS;
VACUUM gold.gold_salary_trends RETAIN 720 HOURS;
```

#### 2. Schema Drift Check (15 min)

```sql
-- Compare actual schema vs contract
DESCRIBE TABLE EXTENDED silver.silver_jobs_current;

-- Manually compare to /LMIP/contracts/silver/silver_jobs_current.yaml
-- Alert if: Mismatch found (undocumented columns, wrong types)
```

#### 3. Performance Review (15 min)

```sql
-- Review query performance trends
SELECT 
  DATE_TRUNC('week', start_time) as week,
  pipeline_name,
  AVG(TIMESTAMPDIFF(MINUTE, start_time, end_time)) as avg_runtime_minutes,
  MAX(TIMESTAMPDIFF(MINUTE, start_time, end_time)) as max_runtime_minutes
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND status = 'SUCCESS'
GROUP BY DATE_TRUNC('week', start_time), pipeline_name
ORDER BY week DESC, pipeline_name;

-- Alert if: Trend shows consistent increase in runtime
```

---

## Escalation Matrix

### Severity Levels

| Severity | Definition | Response Time | Example |
|----------|------------|---------------|----------|
| **P0** | Complete platform outage | 15 minutes | All workflows failing |
| **P1** | Critical workflow failure | 1 hour | Daily_Ingestion failed |
| **P2** | Data quality degradation | 4 hours | DQ pass rate <80% |
| **P3** | Performance degradation | 1 business day | Queries 2x slower |
| **P4** | Minor issue | 3 business days | Cosmetic dashboard issue |

### Escalation Path

**P0/P1**: Page on-call engineer immediately
1. Platform Operator (aaryan.shrivastav1403@gmail.com)
2. Data Engineering Lead (if no response in 30 minutes)
3. Architecture Team (if unresolved in 2 hours)

**P2/P3**: Email notification
1. Platform Operator
2. Data Engineering Lead (if unresolved in 8 hours)

**P4**: Create Jira ticket, no immediate escalation

---

## Monitoring Tools & Access

### Databricks Native Tools

* **Workflows UI**: Monitor job runs, view logs, retry failures
* **SQL Warehouses**: Run monitoring queries
* **System Tables**: Cluster metrics, query history
* **Alerts (future)**: Automated alerts via Databricks Alerts

### External Tools (Future)

* **Datadog**: Centralized monitoring, dashboards, alerts
* **PagerDuty**: On-call rotations, incident management
* **Slack**: Real-time notifications (#lmip-alerts channel)

### Access Requirements

**Platform Operators**:
* Databricks Workspace Admin
* Unity Catalog READ on all schemas
* Workflow MANAGE on all LMIP workflows

**On-Call Engineers**:
* Databricks Workspace User
* Unity Catalog READ on audit/quarantine schemas
* Workflow VIEW on all LMIP workflows

---

## Key Monitoring Queries (Copy-Paste)

### Quick Health Check

```sql
-- Paste this for instant health overview
SELECT 'Workflow Status' as metric, status as value, COUNT(*) as count
FROM audit.audit_pipeline_runs
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
GROUP BY status
UNION ALL
SELECT 'Data Freshness (Bronze)', 
       CONCAT(ROUND(TIMESTAMPDIFF(HOUR, MAX(ingestion_timestamp), CURRENT_TIMESTAMP()), 1), ' hours'), 
       NULL
FROM bronze.bronze_job_snapshot
UNION ALL
SELECT 'DQ Pass Rate', 
       CONCAT(ROUND(100.0 * SUM(CASE WHEN dq_overall_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 1), '%'), 
       NULL
FROM silver.silver_jobs_current
WHERE current_batch_id = (SELECT MAX(current_batch_id) FROM silver.silver_jobs_current)
UNION ALL
SELECT 'Quarantine Backlog', NULL, COUNT(*)
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING';
```

### Drill-Down: Failed Workflows

```sql
-- When Quick Health Check shows failures
SELECT 
  run_id,
  pipeline_name,
  start_time,
  error_message
FROM audit.audit_pipeline_runs
WHERE status = 'FAILED'
  AND start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
ORDER BY start_time DESC;
```

### Drill-Down: Quarantine Details

```sql
-- When Quick Health Check shows high quarantine count
SELECT 
  failed_rule,
  COUNT(*) as failure_count,
  MIN(quarantined_at) as first_occurrence
FROM quarantine.quarantine_jobs
WHERE quarantine_status = 'PENDING'
GROUP BY failed_rule
ORDER BY failure_count DESC;
```

---

## References

* **Recovery Runbook**: `/LMIP/docs/Recovery_Runbook.md` - Incident response procedures
* **Pipeline Flow**: `/LMIP/docs/Pipeline_Flow.md` - Workflow dependencies and data flow
* **Data Model**: `/LMIP/docs/Data_Model.md` - Schema definitions and lineage
* **Audit Tables**: `audit.audit_pipeline_runs`, `audit.audit_dq_results`

---

**Document Owner**: LMIP Platform Engineering Team  
**Review Frequency**: Quarterly  
**Next Review Date**: 2026-09-07