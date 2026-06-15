# LMIP Bronze Batch Rollback Mechanism

## Overview

The rollback mechanism provides a clean way to undo a bronze batch ingestion by toggling the `batch_status` flag in `bronze.dedupe_tracking`. This is the safest approach for handling data quality issues or incorrect batches.

## Architecture

### Key Components

1. **`bronze.dedupe_tracking` table** — now includes a `batch_status` column with values:
   - `PROCESSED` (default) — batch is active and included in downstream processing
   - `ROLLED_BACK` — batch is marked as invalid, excluded from downstream processing

2. **`bronze_rollback_batch.py` notebook** — orchestrates the rollback:
   - Marks batch as `ROLLED_BACK` in dedupe tracking
   - Soft-deletes affected rows in `silver_jobs_current` (sets `is_deleted = true`)
   - Writes an audit record to `audit.audit_pipeline_runs`

3. **Recovery workflow integration** — `recovery.json` includes an optional pre-step:
   - `Recovery_Rollback_Batch_Optional` task runs before `Recovery_Bronze_Replay_Backfill`
   - Controlled by job parameters: `rollback_batch_id`, `rollback_reason`, `rollback_dry_run`

## Usage

### Manual Rollback (Standalone)

Run the notebook with parameters:

```python
# Example: Rollback batch_20260607_123456 in dry-run mode
dbutils.notebook.run(
    "/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP/notebooks/bronze/bronze_rollback_batch",
    timeout_seconds=3600,
    arguments={
        "batch_id": "batch_20260607_123456",
        "catalog": "workspace",
        "reason": "Data quality issue - duplicate records detected",
        "dry_run": "true"  # Set to "false" to execute
    }
)
```

### Rollback via Recovery Workflow

Add rollback parameters to the recovery job:

```json
{
  "rollback_batch_id": "batch_20260607_123456",
  "rollback_reason": "Data quality issue",
  "rollback_dry_run": "false"
}
```

If `rollback_batch_id` is empty, the rollback task skips automatically.

## Rollback Process

### Step 1: Verify Batch Exists

Queries `bronze.dedupe_tracking` to:
- Confirm the batch exists
- Get current `batch_status`
- Count affected records
- Identify the source table

### Step 2: Identify Affected Silver Records

Queries `silver.silver_jobs_current` to find all records with the target `batch_id`. Shows:
- Total count of affected records
- Sample of records to be soft-deleted
- Current `is_deleted` status

### Step 3: Execute Rollback

**Dry Run Mode (`dry_run=true`):**
- Shows what would be rolled back
- No changes made to tables
- Returns preview of actions

**Execute Mode (`dry_run=false`):**
1. **Update dedupe tracking:**
   ```sql
   UPDATE bronze.dedupe_tracking
   SET batch_status = 'ROLLED_BACK',
       tracking_timestamp = current_timestamp()
   WHERE batch_id = '{batch_id}'
   ```

2. **Soft-delete silver records:**
   ```sql
   UPDATE silver.silver_jobs_current
   SET is_deleted = true,
       updated_at = current_timestamp()
   WHERE batch_id = '{batch_id}'
   ```

3. **Write audit record:**
   - Records rollback in `audit.audit_pipeline_runs`
   - Includes batch_id, reason, affected counts, duration

### Step 4: Return Results

Returns JSON with:
- `status`: "success", "dry_run", or "skipped"
- `batch_id`: The rolled back batch
- `dedupe_records_marked`: Count of dedupe records marked as ROLLED_BACK
- `silver_records_deleted`: Count of silver records soft-deleted
- `reason`: Rollback reason
- `timestamp`: When rollback was executed

## Safety Features

### Dry Run Mode

Always run with `dry_run=true` first to preview:
- Batch metadata (status, record count, date range)
- Affected silver records
- No table modifications

### Idempotency

Running rollback multiple times on the same batch is safe:
- If already `ROLLED_BACK`, the notebook exits with "skipped" status
- No duplicate audit records or errors

### Audit Trail

Every rollback is logged with:
- Pipeline name: `bronze_rollback_batch`
- Run ID, status, duration
- Rows affected (reads and writes)
- Full metadata: batch_id, reason, affected tables

## Downstream Impact

### Immediate Effects

- **Silver layer**: Records soft-deleted (`is_deleted = true`)
- **Gold**: Records excluded from views and aggregations (filtered by `is_deleted = false`)
- **Reporting**: KPIs and metrics automatically exclude rolled back data

### Recovery After Rollback

To re-ingest after fixing the issue:

1. **Run `bronze_replay_backfill`** with the same date range:
   - Fetches fresh data from the source API
   - Creates a new batch_id
   - Inserts into `bronze_job_snapshot`

2. **Run the full recovery workflow** or trigger downstream pipelines:
   - `silver_standardize_jobs` — processes new batch
   - `silver_detect_cdc` — tracks changes
   - Downstream intermediate and gold layers rebuild

## DDL Changes

### Updated `bronze.dedupe_tracking` Schema

```sql
CREATE TABLE IF NOT EXISTS workspace.bronze.dedupe_tracking (
  dedupe_id STRING NOT NULL,
  source_table STRING NOT NULL,
  batch_id STRING NOT NULL,
  dedupe_key_hash STRING NOT NULL,
  first_seen_record_id STRING,
  first_seen_batch_id STRING,
  duplicate_count INT NOT NULL,
  first_seen_timestamp TIMESTAMP,
  last_seen_timestamp TIMESTAMP,
  batch_status STRING NOT NULL DEFAULT 'PROCESSED',  -- NEW COLUMN
  tracking_timestamp TIMESTAMP NOT NULL,
  PRIMARY KEY (dedupe_id)
)
COMMENT 'Tracks duplicate payload occurrences in Bronze tables without deleting data'
PARTITIONED BY (tracking_timestamp)
USING DELTA;
```

### Migration for Existing Tables

If `bronze.dedupe_tracking` already exists without `batch_status`:

```sql
-- Add the column with default value
ALTER TABLE workspace.bronze.dedupe_tracking
ADD COLUMN batch_status STRING NOT NULL DEFAULT 'PROCESSED'
COMMENT 'Batch processing status: PROCESSED, ROLLED_BACK';

-- Backfill existing records
UPDATE workspace.bronze.dedupe_tracking
SET batch_status = 'PROCESSED'
WHERE batch_status IS NULL;
```

## Recovery Workflow Integration

### Task Order

```
Recovery_Rollback_Batch_Optional
  ↓
Recovery_Bronze_Replay_Backfill
  ↓
Recovery_Silver_Reprocess
  ↓
Recovery_CDC_Reprocess
  ↓
Recovery_Intermediate_Reprocess
  ↓
Recovery_Gold_Rebuild
  ↓
Recovery_Quarantine_Manage
  ↓
Recovery_Validation_Report
  ↓
Log_Pipeline_Execution
  ↓
Notify_On_Failure (run_if: AT_LEAST_ONE_FAILED)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rollback_batch_id` | `""` | Batch ID to rollback (empty = skip rollback) |
| `rollback_reason` | `"Data quality issue"` | Reason for rollback (audit trail) |
| `rollback_dry_run` | `"true"` | Dry run mode (preview only) |

### Example: Recovery with Rollback

```bash
# Rollback bad batch, then replay correct data
databricks jobs run-now \
  --job-id 123456 \
  --json '{
    "rollback_batch_id": "batch_20260607_bad",
    "rollback_reason": "Duplicate records detected",
    "rollback_dry_run": "false",
    "start_date": "2026-06-07",
    "end_date": "2026-06-07",
    "source_filter": "remotive,arbeitnow"
  }'
```

## Best Practices

### When to Rollback

- **Data quality issues**: Duplicates, malformed data, incorrect transformations
- **Source API issues**: Incomplete responses, wrong API version
- **Pipeline bugs**: Logic errors in bronze ingestion
- **Testing/debugging**: Undo test batches in dev environments

### When NOT to Rollback

- **Minor inconsistencies**: Use quarantine instead
- **Partial failures**: Re-run the specific layer, don't rollback bronze
- **Historical corrections**: Use CDC updates in silver layer

### Rollback Checklist

1. ✓ Identify the exact `batch_id` to rollback
2. ✓ Document the reason (data quality issue, source error, etc.)
3. ✓ Run in `dry_run=true` first — review affected records
4. ✓ Execute rollback with `dry_run=false`
5. ✓ Verify audit logs
6. ✓ Re-ingest correct data via replay/backfill
7. ✓ Validate downstream layers rebuilt correctly

## Monitoring and Alerts

### Query Rolled Back Batches

```sql
SELECT 
  batch_id,
  source_table,
  batch_status,
  COUNT(*) as record_count,
  MIN(first_seen_timestamp) as earliest_record,
  MAX(last_seen_timestamp) as latest_record
FROM workspace.bronze.dedupe_tracking
WHERE batch_status = 'ROLLED_BACK'
GROUP BY batch_id, source_table, batch_status
ORDER BY latest_record DESC;
```

### Audit Rollback History

```sql
SELECT 
  pipeline_name,
  run_id,
  status,
  start_time,
  end_time,
  duration_seconds,
  rows_read,
  rows_written,
  metadata
FROM workspace.audit.audit_pipeline_runs
WHERE pipeline_name = 'bronze_rollback_batch'
ORDER BY start_time DESC
LIMIT 20;
```

### Alert on Rollbacks

Set up alerts when rollbacks occur:
- Slack/email notification via `audit_notification_dispatch`
- Dashboard widget showing recent rollbacks
- Threshold alert if rollback count > N per day

## Troubleshooting

### Batch Not Found

**Error:** `Batch batch_xyz not found in bronze.dedupe_tracking`

**Solution:**
- Verify the batch_id is correct
- Check if the batch was ingested: `SELECT * FROM bronze.bronze_job_snapshot WHERE batch_id = 'batch_xyz'`
- Ensure dedupe tracking ran after bronze ingestion

### Rollback Already Exists

**Warning:** `Batch is already in ROLLED_BACK status`

**Solution:**
- This is expected if you're re-running the rollback
- No action needed — notebook exits with "skipped" status

### No Silver Records Found

**Warning:** `No affected records found in silver_jobs_current`

**Explanation:**
- The batch exists in bronze dedupe tracking, but hasn't been processed to silver yet
- Or silver records were already deleted manually

**Solution:**
- Check if silver processing ran: `SELECT COUNT(*) FROM silver.silver_jobs_current WHERE batch_id = 'batch_xyz'`
- Proceed with rollback — it will still mark dedupe tracking as ROLLED_BACK

## Related Documentation

- [Bronze Layer README](../notebooks/bronze/README_BRONZE.ipynb)
- [Recovery Workflow](../workflows/recovery.json)
- [Audit & Logging Standards](./audit-logging-standards.md)
- [Data Quality Framework](./data-quality-framework.md)

---

**Last Updated:** 2026-06-14  
**Owner:** Data Engineering Team  
**Status:** Production Ready
